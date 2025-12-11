"""
FastAPI приложение GreMuiv
"""
from fastapi import FastAPI
from backend.config import setup_cors
from backend.routes import groups, subjects, students, grades, stats, student
from backend.utils.auth import init_auth

# Создаем FastAPI приложение
app = FastAPI(
    title="GreMuiv API",
    version="1.0.0",
    description="API для системы журнала оценок студентов"
)

# Настраиваем CORS
setup_cors(app)

# Инициализируем систему аутентификации
# ВАЖНО: На Vercel startup events не работают, поэтому инициализация происходит лениво
# при первом запросе через get_or_create_token()
try:
    # Пытаемся инициализировать токен при импорте (только если не на Vercel)
    import os
    if not os.getenv("VERCEL"):
        from backend.utils.auth import TOKEN_FILE
        token = init_auth()
        print(f"\n{'='*60}")
        print(f"🔑 ТОКЕН ДОСТУПА К API")
        print(f"{'='*60}")
        print(f"Токен: {token}")
        print(f"")
        print(f"📁 Файл с токенами: {TOKEN_FILE}")
        print(f"")
        print(f"📝 Использование:")
        print(f"   Заголовок: Authorization: Bearer {token}")
        print(f"")
        print(f"🌐 Получить токен через API: GET http://localhost:5000/api/token")
        print(f"{'='*60}\n")
except Exception as e:
    # На Vercel это нормально - инициализация произойдет при первом запросе
    pass

# Подключаем роуты
app.include_router(groups.router)
app.include_router(subjects.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(stats.router)
app.include_router(student.router)


@app.get("/")
async def root():
    """Корневой эндпоинт (публичный, не требует токена)"""
    from backend.utils.auth import get_or_create_token, TOKEN_FILE
    
    token = get_or_create_token()
    
    return {
        "message": "GreMuiv API",
        "version": "1.0.0",
        "docs": "/docs",
        "auth_required": True,
        "token_info": {
            "how_to_get": "Токен выводится в консоль при запуске сервера или доступен через GET /api/token",
            "token_file": str(TOKEN_FILE),
            "current_token": token
        },
        "endpoints": {
            "get_token": "/api/token (публичный, без авторизации)",
            "groups": "/api/groups",
            "subjects": "/api/subjects",
            "students": "/api/students",
            "grades": "/api/grades",
            "stats": "/api/stats",
            "rating_absences": "/api/stats/rating/absences",
            "rating_grades": "/api/stats/rating/grades"
        },
        "note": "Все эндпоинты (кроме / и /api/token) требуют токен доступа в заголовке Authorization: Bearer <token>"
    }


@app.get("/api/token")
async def get_token():
    """
    Получить текущий токен доступа (публичный эндпоинт, не требует авторизации)
    
    Returns:
        dict: Информация о токене доступа
    """
    from backend.utils.auth import get_or_create_token, TOKEN_FILE, load_tokens
    
    token = get_or_create_token()
    tokens_data = load_tokens()
    token_info = tokens_data.get(token, {})
    
    return {
        "token": token,
        "token_file": str(TOKEN_FILE),
        "created_at": token_info.get("created_at"),
        "last_used": token_info.get("last_used"),
        "usage": "Используйте этот токен в заголовке: Authorization: Bearer <token>",
        "example": f"Authorization: Bearer {token}"
    }

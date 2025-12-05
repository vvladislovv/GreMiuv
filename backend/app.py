"""
FastAPI приложение GreMuiv
"""
from fastapi import FastAPI
from backend.config import setup_cors
from backend.routes import groups, subjects, students, grades, stats

# Создаем FastAPI приложение
app = FastAPI(
    title="GreMuiv API",
    version="1.0.0",
    description="API для системы журнала оценок студентов"
)

# Настраиваем CORS
setup_cors(app)

# Подключаем роуты
app.include_router(groups.router)
app.include_router(subjects.router)
app.include_router(students.router)
app.include_router(grades.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "GreMuiv API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "groups": "/api/groups",
            "subjects": "/api/subjects",
            "students": "/api/students",
            "grades": "/api/grades",
            "stats": "/api/stats",
            "rating_absences": "/api/stats/rating/absences",
            "rating_grades": "/api/stats/rating/grades"
        }
    }

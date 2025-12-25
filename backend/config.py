"""
Конфигурация бэкенда
"""
from fastapi.middleware.cors import CORSMiddleware

# CORS настройки
# Добавляем поддержку Vercel доменов
import os

# Получаем Vercel URL из переменных окружения (если есть)
VERCEL_URL = os.getenv("VERCEL_URL", "")
VERCEL_ENV = os.getenv("VERCEL_ENV", "")

# Базовые CORS настройки
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://horribly-fun-stint.cloudpub.ru",
    # Production домен
    "https://vildanai.ru",
    "https://www.vildanai.ru",
    "http://vildanai.ru",
    "http://www.vildanai.ru",
]

# Добавляем Vercel домены, если они есть
if VERCEL_URL:
    # Добавляем https версию
    if not VERCEL_URL.startswith("http"):
        CORS_ORIGINS.append(f"https://{VERCEL_URL}")
    else:
        CORS_ORIGINS.append(VERCEL_URL)

# Добавляем все возможные Vercel домены (для preview и production)
# Vercel автоматически устанавливает эти переменные
if VERCEL_ENV:
    # Production домен будет установлен в переменных окружения Vercel
    # Preview домены будут иметь формат: <project-name>-<hash>.vercel.app
    pass

# Разрешаем все домены Vercel (для preview деплоев)
# В production лучше указать конкретный домен
CORS_ORIGINS.append("https://*.vercel.app")

# Добавляем Render.com домены
RENDER_SERVICE_URL = os.getenv("RENDER_SERVICE_URL", "")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")
if RENDER_SERVICE_URL:
    if not RENDER_SERVICE_URL.startswith("http"):
        CORS_ORIGINS.append(f"https://{RENDER_SERVICE_URL}")
    else:
        CORS_ORIGINS.append(RENDER_SERVICE_URL)
if RENDER_EXTERNAL_URL:
    if not RENDER_EXTERNAL_URL.startswith("http"):
        CORS_ORIGINS.append(f"https://{RENDER_EXTERNAL_URL}")
    else:
        CORS_ORIGINS.append(RENDER_EXTERNAL_URL)
# Разрешаем все домены Render (для preview деплоев)
CORS_ORIGINS.append("https://*.onrender.com")

# Добавляем Fly.io домены
FLY_APP_NAME = os.getenv("FLY_APP_NAME", "")
if FLY_APP_NAME:
    CORS_ORIGINS.append(f"https://{FLY_APP_NAME}.fly.dev")
# Разрешаем все домены Fly.io (для preview деплоев)
CORS_ORIGINS.append("https://*.fly.dev")

# Настройки сервера
# Render.com и Fly.io автоматически устанавливают переменную PORT
SERVER_HOST = os.getenv("HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", 5000))

def setup_cors(app):
    """Настройка CORS для приложения"""
    # Получаем список разрешенных доменов
    allow_origins = CORS_ORIGINS.copy()
    
    # Добавляем Vercel домены из переменных окружения
    vercel_url = os.getenv("VERCEL_URL", "")
    if vercel_url:
        # Добавляем https версию, если её нет
        if not vercel_url.startswith("http"):
            allow_origins.append(f"https://{vercel_url}")
        else:
            allow_origins.append(vercel_url)
    
    # Добавляем кастомный домен из переменных окружения (если указан)
    custom_domain = os.getenv("CUSTOM_DOMAIN", "")
    if custom_domain:
        if not custom_domain.startswith("http"):
            allow_origins.append(f"https://{custom_domain}")
        else:
            allow_origins.append(custom_domain)
    
    # Добавляем Render.com домены из переменных окружения
    render_service_url = os.getenv("RENDER_SERVICE_URL", "")
    render_external_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if render_service_url:
        if not render_service_url.startswith("http"):
            allow_origins.append(f"https://{render_service_url}")
        else:
            allow_origins.append(render_service_url)
    if render_external_url:
        if not render_external_url.startswith("http"):
            allow_origins.append(f"https://{render_external_url}")
        else:
            allow_origins.append(render_external_url)
    
    # Добавляем Fly.io домены из переменных окружения
    fly_app_name = os.getenv("FLY_APP_NAME", "")
    if fly_app_name:
        allow_origins.append(f"https://{fly_app_name}.fly.dev")
    
    # Для разработки на Vercel можно временно разрешить все домены
    # В production лучше указать конкретные домены через переменные окружения
    # Разрешаем все домены только если установлена переменная ALLOW_ALL_ORIGINS=true
    if os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true":
        allow_origins = ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

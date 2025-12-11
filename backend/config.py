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

# Настройки сервера
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

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

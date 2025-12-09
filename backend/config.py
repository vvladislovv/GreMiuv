"""
Конфигурация бэкенда
"""
from fastapi.middleware.cors import CORSMiddleware

# CORS настройки
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "https://agilely-remarkable-fieldfare.cloudpub.ru",
]

# Настройки сервера
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

def setup_cors(app):
    """Настройка CORS для приложения"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

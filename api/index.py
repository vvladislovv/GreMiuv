"""
Vercel Serverless Function для FastAPI приложения
Это точка входа для всех API запросов на Vercel
"""
import sys
import os
from pathlib import Path

try:
    # Добавляем корневую директорию проекта в путь
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Импортируем FastAPI приложение
    from backend.app import app
    
    # Импортируем Mangum для адаптации ASGI к Vercel
    from mangum import Mangum
    
    # Создаем ASGI handler для Vercel
    # Vercel автоматически вызывает handler для каждого запроса
    handler = Mangum(app, lifespan="off")
    
    # Экспортируем handler для Vercel
    # Vercel ищет переменную 'handler' в файле
    # Также экспортируем app на случай, если Vercel будет искать его
    __all__ = ['app', 'handler']
    
except Exception as e:
    # Если есть ошибка при импорте, создаем простой handler для диагностики
    import traceback
    error_message = f"Error initializing app: {str(e)}\n{traceback.format_exc()}"
    print(error_message)
    
    from mangum import Mangum
    from fastapi import FastAPI
    
    # Создаем минимальное приложение для диагностики
    error_app = FastAPI()
    
    @error_app.get("/{path:path}")
    async def error_handler(path: str):
        return {
            "error": "Application initialization failed",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    
    handler = Mangum(error_app, lifespan="off")
    __all__ = ['handler']

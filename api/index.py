"""
Vercel Serverless Function для FastAPI приложения
Это точка входа для всех API запросов на Vercel
"""
import sys
import os
from pathlib import Path

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

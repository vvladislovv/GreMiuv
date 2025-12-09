"""Утилиты для работы с БД в Telegram боте"""
import sys
import os
from pathlib import Path

# Добавляем путь к parsing для импорта database
project_root = Path(__file__).parent.parent
parsing_path = project_root / "parsing"
if str(parsing_path) not in sys.path:
    sys.path.insert(0, str(parsing_path))

from database import get_db, TelegramUser

__all__ = ['get_db', 'TelegramUser']

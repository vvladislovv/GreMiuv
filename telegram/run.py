#!/usr/bin/env python3
"""
Запуск Telegram бота
"""
import sys
import os
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Инициализируем БД перед запуском бота
from parsing.database import init_db

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 Запуск Telegram бота GreMuiv...")
    print("=" * 60)
    
    # Инициализация БД (создание таблиц, если их нет)
    print("📊 Инициализация базы данных...")
    init_db()
    print("✅ База данных готова")
    
    # Запуск бота
    print("🚀 Запуск бота...")
    from telegram.bot import main
    import asyncio
    asyncio.run(main())

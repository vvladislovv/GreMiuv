#!/usr/bin/env python3
"""
Скрипт запуска парсера
Используйте: python run.py
"""
import sys
import os

# Добавляем папку parsing в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Запускаем главный файл
from main import main

if __name__ == "__main__":
    main()


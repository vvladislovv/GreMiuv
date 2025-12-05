#!/usr/bin/env python3
"""
Запуск FastAPI бэкенда
"""
import sys
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from backend.config import SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    print("🚀 Запуск FastAPI бэкенда...")
    print(f"🌐 API доступен на http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"📚 Документация: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("")
    
    uvicorn.run(
        "backend.app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True
    )

#!/usr/bin/env python3
"""
Запуск всего приложения: парсер + API сервер
"""
import sys
import time
from threading import Thread
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.config import SERVER_HOST, SERVER_PORT


def run_parser():
    """Запуск парсера в отдельном потоке"""
    from pathlib import Path
    
    # Добавляем папку parsing в путь
    parsing_path = project_root / "parsing"
    sys.path.insert(0, str(parsing_path))
    
    from main import main
    main()


def run_backend():
    """Запуск FastAPI бэкенда"""
    import uvicorn
    uvicorn.run(
        "backend.app:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=False
    )


if __name__ == "__main__":
    print("🚀 Запуск приложения GreMuiv...")
    print("📊 Парсер: обновление каждые 15 минут")
    print(f"🌐 API сервер: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"📚 Документация: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("🎨 Фронтенд: http://localhost:3001 (запустите отдельно: cd frontend && npm run dev)")
    print("")
    
    # Запускаем парсер в отдельном потоке
    parser_thread = Thread(target=run_parser, daemon=True)
    parser_thread.start()
    
    # Ждем немного для инициализации БД
    time.sleep(2)
    
    # Запускаем бэкенд (блокирующий вызов)
    try:
        run_backend()
    except KeyboardInterrupt:
        print("\n🛑 Остановка приложения...")
        sys.exit(0)

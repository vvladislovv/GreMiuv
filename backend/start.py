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
    try:
        # Добавляем папку parsing в путь
        parsing_path = project_root / "parsing"
        if str(parsing_path) not in sys.path:
            sys.path.insert(0, str(parsing_path))
        
        from main import main
        print("📊 Парсер запущен, обновление каждые 15 минут...")
        main()
    except Exception as e:
        print(f"❌ Ошибка в парсере: {e}")
        import traceback
        traceback.print_exc()


def run_backend():
    """Запуск FastAPI бэкенда"""
    import uvicorn
    try:
        uvicorn.run(
            "backend.app:app",
            host=SERVER_HOST,
            port=SERVER_PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Ошибка в бэкенде: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Запуск приложения GreMuiv...")
    print("=" * 60)
    print(f"📊 Парсер: обновление каждые 15 минут (00, 15, 30, 45 минут каждого часа)")
    print(f"🌐 API сервер: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"📚 Документация: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("🎨 Фронтенд: http://localhost:3001 (запустите отдельно)")
    print("=" * 60)
    print("")
    
    # Запускаем парсер в отдельном потоке
    parser_thread = Thread(target=run_parser, daemon=True)
    parser_thread.start()
    
    # Ждем немного для инициализации БД и первого парсинга
    print("⏳ Ожидание инициализации БД и первого парсинга...")
    time.sleep(5)
    
    # Запускаем бэкенд (блокирующий вызов)
    try:
        print("✅ Запуск API сервера...")
        run_backend()
    except KeyboardInterrupt:
        print("\n🛑 Остановка приложения...")
        sys.exit(0)

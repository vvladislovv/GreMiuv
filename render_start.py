#!/usr/bin/env python3
"""
Запуск всего приложения на Render.com: парсер + API сервер + Telegram бот
"""
import sys
import os
import time
import asyncio
from threading import Thread
from pathlib import Path

# Добавляем корневую папку в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Инициализируем БД перед запуском
parsing_path = project_root / "parsing"
if str(parsing_path) not in sys.path:
    sys.path.insert(0, str(parsing_path))

from backend.config import SERVER_HOST, SERVER_PORT
from parsing.database import init_db
from logger import log_backend_info, log_backend_error
import uvicorn
import signal


def run_parser():
    """Запуск парсера в отдельном потоке"""
    try:
        parsing_path = project_root / "parsing"
        if str(parsing_path) not in sys.path:
            sys.path.insert(0, str(parsing_path))
        
        from main import main
        print("📊 Парсер запущен, обновление каждые 15 минут...")
        log_backend_info(
            "Парсер запущен",
            "Парсер запущен в отдельном потоке, обновление каждые 15 минут"
        )
        main()
    except Exception as e:
        print(f"❌ Ошибка в парсере: {e}")
        log_backend_error(
            f"Ошибка в парсере: {str(e)}",
            error=e,
            description="Критическая ошибка в потоке парсера"
        )
        import traceback
        traceback.print_exc()


def run_backend():
    """Запуск FastAPI бэкенда"""
    def signal_handler(sig, frame):
        """Обработчик сигнала для корректного завершения"""
        print("\n🛑 Получен сигнал остановки сервера...")
        log_backend_info(
            "Получен сигнал остановки сервера",
            f"Сигнал: {sig}, остановка API сервера"
        )
        raise KeyboardInterrupt
    
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Получаем порт из переменных окружения Render (если есть)
        port = int(os.getenv("PORT", SERVER_PORT))
        host = os.getenv("HOST", SERVER_HOST)
        
        log_backend_info(
            f"Запуск API сервера",
            f"Сервер запускается на {host}:{port}"
        )
        uvicorn.run(
            "backend.app:app",
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        log_backend_info(
            "API сервер остановлен",
            "Сервер корректно завершил работу"
        )
        raise
    except Exception as e:
        print(f"❌ Ошибка в бэкенде: {e}")
        log_backend_error(
            f"Ошибка в бэкенде: {str(e)}",
            error=e,
            description="Критическая ошибка в API сервере"
        )
        import traceback
        traceback.print_exc()


def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке с собственным event loop"""
    try:
        telegram_path = project_root / "telegram"
        if str(telegram_path) not in sys.path:
            sys.path.insert(0, str(telegram_path))
        
        from telegram.config import BOT_TOKEN
        if not BOT_TOKEN or BOT_TOKEN == "вставьте_свой_токен_сюда":
            print("⚠️  Telegram бот не запущен: токен не установлен в переменных окружения")
            print("   Установите переменную BOT_TOKEN в настройках Render")
            log_backend_info(
                "Telegram бот не запущен",
                "Токен бота не установлен в переменных окружения"
            )
            return
        
        # Инициализируем БД перед запуском бота
        init_db()
        
        # Импортируем модули бота
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from telegram.handlers import common, registration, settings
        from logger import log_telegram_info, log_telegram_error
        import logging
        
        # Отключаем uvloop для этого потока
        os.environ['AIOGRAM_USE_UVLOOP'] = '0'
        
        # Настройка логирования для бота
        bot_logger = logging.getLogger("telegram_bot")
        bot_logger.setLevel(logging.INFO)
        if not bot_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - [BOT] - %(levelname)s - %(message)s'))
            bot_logger.addHandler(handler)
        
        # Создаем новый event loop для этого потока
        if sys.platform != 'win32':
            loop = asyncio.SelectorEventLoop()
        else:
            loop = asyncio.ProactorEventLoop()
        
        asyncio.set_event_loop(loop)
        
        bot = None
        dp = None
        
        async def bot_main():
            """Асинхронная функция запуска бота"""
            nonlocal bot, dp
            try:
                bot = Bot(token=BOT_TOKEN)
                
                bot_logger.info("Проверка подключения к Telegram API...")
                log_telegram_info(
                    "Проверка подключения к Telegram API",
                    description="Попытка подключения к Telegram Bot API"
                )
                try:
                    bot_info = await bot.get_me()
                    bot_logger.info(f"Бот подключен: @{bot_info.username} ({bot_info.first_name})")
                    print(f"✅ Бот подключен: @{bot_info.username}")
                    log_telegram_info(
                        f"Бот подключен: @{bot_info.username}",
                        description=f"Бот успешно подключен к Telegram API, имя: {bot_info.first_name}"
                    )
                except Exception as e:
                    bot_logger.error(f"Не удалось подключиться к Telegram API: {e}")
                    print(f"❌ Ошибка подключения к Telegram API: {e}")
                    log_telegram_error(
                        "Не удалось подключиться к Telegram API",
                        error=e,
                        description="Ошибка подключения к Telegram Bot API, проверьте токен"
                    )
                    return
                
                storage = MemoryStorage()
                dp = Dispatcher(storage=storage)
                
                # Регистрация роутеров
                dp.include_router(common.router)
                dp.include_router(registration.router)
                dp.include_router(settings.router)
                
                bot_logger.info("Бот запущен и готов к работе!")
                print("🤖 Telegram бот успешно запущен и готов принимать команды!")
                
                log_telegram_info(
                    "Бот запущен и готов к работе",
                    description="Telegram бот успешно запущен, polling начат"
                )
                
                await dp.start_polling(bot, skip_updates=True, handle_signals=False)
            except asyncio.CancelledError:
                bot_logger.info("Получен сигнал отмены для бота...")
                log_telegram_info(
                    "Получен сигнал отмены для бота",
                    description="Остановка polling бота"
                )
                raise
            except Exception as e:
                bot_logger.error(f"Ошибка при работе бота: {e}")
                log_telegram_error(
                    f"Ошибка при работе бота: {str(e)}",
                    error=e,
                    description="Критическая ошибка в работе Telegram бота"
                )
                import traceback
                traceback.print_exc()
                print(f"❌ Критическая ошибка в боте: {e}")
            finally:
                if dp:
                    try:
                        await dp.stop_polling()
                    except:
                        pass
                if bot:
                    try:
                        await bot.session.close()
                    except:
                        pass
        
        # Запускаем бота в event loop
        try:
            loop.run_until_complete(bot_main())
        except (KeyboardInterrupt, asyncio.CancelledError):
            bot_logger.info("Остановка бота...")
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                pass
        except Exception as e:
            bot_logger.error(f"Ошибка в event loop бота: {e}")
        finally:
            try:
                if not loop.is_closed():
                    if not loop.is_running():
                        try:
                            pending = asyncio.all_tasks(loop)
                            for task in pending:
                                if not task.done():
                                    task.cancel()
                            if pending:
                                loop.run_until_complete(
                                    asyncio.gather(*pending, return_exceptions=True)
                                )
                        except:
                            pass
                        loop.close()
            except RuntimeError:
                pass
            except Exception:
                pass
            
    except Exception as e:
        print(f"❌ Ошибка в Telegram боте: {e}")
        log_backend_error(
            f"Ошибка в Telegram боте: {str(e)}",
            error=e,
            description="Критическая ошибка при запуске Telegram бота"
        )
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Запуск приложения GreMuiv на Render.com...")
    print("=" * 60)
    
    # Создаем директорию data, если её нет (для SQLite)
    data_dir = project_root / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана директория: {data_dir}")
    
    # Инициализируем БД
    print("📊 Инициализация базы данных...")
    try:
        init_db()
        print("✅ База данных готова\n")
        log_backend_info(
            "Инициализация базы данных",
            "База данных инициализирована, все таблицы созданы"
        )
    except Exception as e:
        print(f"⚠️  Предупреждение при инициализации БД: {e}")
        print("   Продолжаем запуск...\n")
    
    # Получаем порт из переменных окружения Render
    port = int(os.getenv("PORT", SERVER_PORT))
    host = os.getenv("HOST", SERVER_HOST)
    
    print(f"📊 Парсер: обновление каждые 15 минут (00, 15, 30, 45 минут каждого часа)")
    print(f"🌐 API сервер: http://{host}:{port}")
    print(f"📚 Документация: http://{host}:{port}/docs")
    print("🤖 Telegram бот: запущен (если токен установлен)")
    print("=" * 60)
    print("")
    
    # Запускаем парсер в отдельном потоке (daemon=True - не блокирует завершение)
    parser_thread = Thread(target=run_parser, daemon=True, name="ParserThread")
    parser_thread.start()
    print("✅ Парсер запущен в отдельном потоке")
    log_backend_info(
        "Парсер запущен в отдельном потоке",
        "Поток парсера успешно запущен"
    )
    
    # Запускаем Telegram бота в отдельном потоке (daemon=True - не блокирует завершение)
    telegram_thread = Thread(target=run_telegram_bot, daemon=True, name="TelegramBotThread")
    telegram_thread.start()
    print("✅ Telegram бот запущен в отдельном потоке")
    log_backend_info(
        "Telegram бот запущен в отдельном потоке",
        "Поток Telegram бота успешно запущен"
    )
    
    # Ждем немного для инициализации потоков
    print("⏳ Ожидание инициализации потоков...")
    time.sleep(2)
    
    # Проверяем, что потоки запущены
    if parser_thread.is_alive():
        print("✅ Поток парсера активен")
    if telegram_thread.is_alive():
        print("✅ Поток Telegram бота активен")
    print("")
    
    # Запускаем бэкенд (блокирующий вызов)
    try:
        print("✅ Запуск API сервера...")
        run_backend()
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
        print("⏳ Корректное завершение работы...")
        time.sleep(1)
        print("✅ Приложение остановлено")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


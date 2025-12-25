#!/usr/bin/env python3
"""
Запуск всего приложения: парсер + API сервер + Telegram бот
Универсальный скрипт для Docker и локального запуска
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

from backend.config import SERVER_HOST, SERVER_PORT

# Импортируем систему логирования
parsing_path = project_root / "parsing"
if str(parsing_path) not in sys.path:
    sys.path.insert(0, str(parsing_path))
from logger import log_backend_info, log_backend_error


def run_parser():
    """Запуск парсера в отдельном потоке"""
    try:
        parsing_path = project_root / "parsing"
        if str(parsing_path) not in sys.path:
            sys.path.insert(0, str(parsing_path))
        
        from main import main
        print("=" * 60, flush=True)
        print("📊 [PARSER] Парсер запущен", flush=True)
        print("📊 [PARSER] Обновление: раз в час (в 00 минут каждого часа)", flush=True)
        print("=" * 60, flush=True)
        log_backend_info(
            "Парсер запущен",
            "Парсер запущен в отдельном потоке, обновление раз в час"
        )
        main()
    except Exception as e:
        print(f"❌ [PARSER] Ошибка в парсере: {e}", flush=True)
        log_backend_error(
            f"Ошибка в парсере: {str(e)}",
            error=e,
            description="Критическая ошибка в потоке парсера"
        )
        import traceback
        traceback.print_exc()


def run_backend():
    """Запуск FastAPI бэкенда"""
    import uvicorn
    import signal
    
    def signal_handler(sig, frame):
        """Обработчик сигнала для корректного завершения"""
        print("\n🛑 [API] Получен сигнал остановки сервера...", flush=True)
        log_backend_info(
            "Получен сигнал остановки сервера",
            f"Сигнал: {sig}, остановка API сервера"
        )
        raise KeyboardInterrupt
    
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Получаем порт из переменных окружения (Docker/Render/Fly.io устанавливают автоматически)
        port = int(os.getenv("PORT", SERVER_PORT))
        host = os.getenv("HOST", SERVER_HOST)
        
        print("=" * 60, flush=True)
        print(f"🌐 [API] Запуск FastAPI сервера", flush=True)
        print(f"🌐 [API] Адрес: http://{host}:{port}", flush=True)
        print(f"🌐 [API] Документация: http://{host}:{port}/docs", flush=True)
        print("=" * 60, flush=True)
        
        log_backend_info(
            f"Запуск API сервера",
            f"Сервер запускается на {host}:{port}"
        )
        uvicorn.run(
            "backend.app:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True
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
            print("=" * 60, flush=True)
            print("⚠️  [BOT] Telegram бот не запущен: токен не установлен", flush=True)
            print("   [BOT] Установите переменную окружения BOT_TOKEN", flush=True)
            print("=" * 60, flush=True)
            log_backend_info(
                "Telegram бот не запущен",
                "Токен бота не установлен в переменных окружения"
            )
            return
        
        # Инициализируем БД перед запуском бота
        from parsing.database import init_db
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
                    print("=" * 60, flush=True)
                    print(f"✅ [BOT] Бот подключен: @{bot_info.username} ({bot_info.first_name})", flush=True)
                    print("=" * 60, flush=True)
                    log_telegram_info(
                        f"Бот подключен: @{bot_info.username}",
                        description=f"Бот успешно подключен к Telegram API, имя: {bot_info.first_name}"
                    )
                except Exception as e:
                    bot_logger.error(f"Не удалось подключиться к Telegram API: {e}")
                    print(f"❌ [BOT] Ошибка подключения к Telegram API: {e}", flush=True)
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
                print("=" * 60, flush=True)
                print("🤖 [BOT] Telegram бот успешно запущен и готов принимать команды!", flush=True)
                print("=" * 60, flush=True)
                
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
    print("🚀 Запуск приложения GreMuiv...")
    print("=" * 60)
    
    # Создаем директорию data, если её нет (для SQLite)
    data_dir = project_root / "data"
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Создана директория: {data_dir}")
    
    # Инициализируем БД
    parsing_path = project_root / "parsing"
    if str(parsing_path) not in sys.path:
        sys.path.insert(0, str(parsing_path))
    
    from parsing.database import init_db
    print("=" * 60, flush=True)
    print("🚀 [STARTUP] Запуск приложения GreMuiv", flush=True)
    print("=" * 60, flush=True)
    print("📊 [STARTUP] Инициализация базы данных...", flush=True)
    try:
        init_db()
        print("✅ [STARTUP] База данных готова", flush=True)
        log_backend_info(
            "Инициализация базы данных",
            "База данных инициализирована, все таблицы созданы"
        )
    except Exception as e:
        print(f"⚠️  [STARTUP] Предупреждение при инициализации БД: {e}", flush=True)
        print("   [STARTUP] Продолжаем запуск...", flush=True)
    
    # Получаем порт из переменных окружения
    port = int(os.getenv("PORT", SERVER_PORT))
    host = os.getenv("HOST", SERVER_HOST)
    
    print("=" * 60, flush=True)
    print("📋 [STARTUP] Конфигурация:", flush=True)
    print(f"   📊 Парсер: обновление раз в час (в 00 минут каждого часа)", flush=True)
    print(f"   🌐 API сервер: http://{host}:{port}", flush=True)
    print(f"   📚 Документация: http://{host}:{port}/docs", flush=True)
    print("   🤖 Telegram бот: запустится (если токен установлен)", flush=True)
    print("=" * 60, flush=True)
    print("", flush=True)
    
    # Запускаем парсер в отдельном потоке (daemon=True - не блокирует завершение)
    parser_thread = Thread(target=run_parser, daemon=True, name="ParserThread")
    parser_thread.start()
    print("✅ [STARTUP] Парсер запущен в отдельном потоке", flush=True)
    log_backend_info(
        "Парсер запущен в отдельном потоке",
        "Поток парсера успешно запущен"
    )
    
    # Запускаем Telegram бота в отдельном потоке (daemon=True - не блокирует завершение)
    telegram_thread = Thread(target=run_telegram_bot, daemon=True, name="TelegramBotThread")
    telegram_thread.start()
    print("✅ [STARTUP] Telegram бот запущен в отдельном потоке", flush=True)
    log_backend_info(
        "Telegram бот запущен в отдельном потоке",
        "Поток Telegram бота успешно запущен"
    )
    
    # Ждем немного для инициализации потоков
    print("⏳ [STARTUP] Ожидание инициализации потоков...", flush=True)
    time.sleep(2)
    
    # Проверяем, что потоки запущены
    if parser_thread.is_alive():
        print("✅ [STARTUP] Поток парсера активен", flush=True)
    if telegram_thread.is_alive():
        print("✅ [STARTUP] Поток Telegram бота активен", flush=True)
    print("", flush=True)
    
    # Запускаем бэкенд (блокирующий вызов)
    try:
        print("✅ [STARTUP] Запуск API сервера...", flush=True)
        run_backend()
    except KeyboardInterrupt:
        print("\n🛑 [SHUTDOWN] Получен сигнал остановки...", flush=True)
        print("⏳ [SHUTDOWN] Корректное завершение работы...", flush=True)
        time.sleep(1)
        print("✅ Приложение остановлено")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




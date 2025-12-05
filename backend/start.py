#!/usr/bin/env python3
"""
Запуск всего приложения: парсер + API сервер + Telegram бот
"""
import sys
import time
import asyncio
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
    import signal
    
    def signal_handler(sig, frame):
        """Обработчик сигнала для корректного завершения"""
        print("\n🛑 Получен сигнал остановки сервера...")
        raise KeyboardInterrupt
    
    # Устанавливаем обработчик сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        uvicorn.run(
            "backend.app:app",
            host=SERVER_HOST,
            port=SERVER_PORT,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        # Корректное завершение при Ctrl+C
        raise
    except Exception as e:
        print(f"❌ Ошибка в бэкенде: {e}")
        import traceback
        traceback.print_exc()


def run_telegram_bot():
    """Запуск Telegram бота в отдельном потоке с собственным event loop"""
    try:
        # Проверяем наличие токена перед запуском
        telegram_path = project_root / "telegram"
        if str(telegram_path) not in sys.path:
            sys.path.insert(0, str(telegram_path))
        
        from telegram.config import BOT_TOKEN
        if not BOT_TOKEN or BOT_TOKEN == "вставьте_свой_токен_сюда":
            print("⚠️  Telegram бот не запущен: токен не установлен в .env файле")
            print("   Для запуска бота создайте файл .env в корне проекта и добавьте BOT_TOKEN")
            return
        
        # Инициализируем БД перед запуском бота
        from parsing.database import init_db
        init_db()
        
        # Импортируем модули бота
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from telegram.handlers import common, registration, settings
        import logging
        import os
        
        # Отключаем uvloop для этого потока (устанавливаем переменную окружения)
        # Это заставит aiogram использовать стандартный asyncio
        os.environ['AIOGRAM_USE_UVLOOP'] = '0'
        
        # Настройка логирования для бота
        bot_logger = logging.getLogger("telegram_bot")
        bot_logger.setLevel(logging.INFO)
        if not bot_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - [BOT] - %(levelname)s - %(message)s'))
            bot_logger.addHandler(handler)
        
        # Создаем новый event loop для этого потока
        # Явно используем стандартный asyncio.SelectorEventLoop вместо uvloop
        # (uvloop не поддерживает signal handlers в потоках)
        if sys.platform != 'win32':
            # На Unix системах используем SelectorEventLoop
            loop = asyncio.SelectorEventLoop()
        else:
            # На Windows используем ProactorEventLoop
            loop = asyncio.ProactorEventLoop()
        
        asyncio.set_event_loop(loop)
        
        bot = None
        dp = None
        
        async def bot_main():
            """Асинхронная функция запуска бота"""
            nonlocal bot, dp
            try:
                # Инициализация бота и диспетчера
                bot = Bot(token=BOT_TOKEN)
                
                # Проверяем подключение к Telegram API
                bot_logger.info("Проверка подключения к Telegram API...")
                try:
                    bot_info = await bot.get_me()
                    bot_logger.info(f"Бот подключен: @{bot_info.username} ({bot_info.first_name})")
                    print(f"✅ Бот подключен: @{bot_info.username}")
                except Exception as e:
                    bot_logger.error(f"Не удалось подключиться к Telegram API: {e}")
                    print(f"❌ Ошибка подключения к Telegram API: {e}")
                    print("   Проверьте правильность токена в файле .env")
                    return
                
                storage = MemoryStorage()
                dp = Dispatcher(storage=storage)
                
                # Регистрация роутеров
                dp.include_router(common.router)
                dp.include_router(registration.router)
                dp.include_router(settings.router)
                
                bot_logger.info("Бот запущен и готов к работе!")
                print("🤖 Telegram бот успешно запущен и готов принимать команды!")
                print("   Отправьте /start боту для начала работы")
                
                # Запуск polling с отключенной обработкой сигналов
                # (так как мы не в главном потоке)
                await dp.start_polling(bot, skip_updates=True, handle_signals=False)
            except asyncio.CancelledError:
                bot_logger.info("Получен сигнал отмены для бота...")
                raise
            except Exception as e:
                bot_logger.error(f"Ошибка при работе бота: {e}")
                import traceback
                traceback.print_exc()
                print(f"❌ Критическая ошибка в боте: {e}")
            finally:
                # Корректное закрытие бота
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
            # Корректная остановка всех задач
            try:
                # Получаем все незавершенные задачи
                pending = asyncio.all_tasks(loop)
                # Отменяем все задачи
                for task in pending:
                    task.cancel()
                # Ждем завершения отмененных задач (игнорируем исключения)
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:
                # Игнорируем ошибки при отмене задач
                pass
        except Exception as e:
            bot_logger.error(f"Ошибка в event loop бота: {e}")
        finally:
            # Корректное закрытие event loop
            try:
                # Проверяем, что loop не запущен
                if not loop.is_closed():
                    # Пытаемся остановить, если запущен
                    if loop.is_running():
                        # Это не должно произойти, но на всякий случай
                        pass
                    else:
                        # Закрываем loop только если он не запущен
                        try:
                            # Завершаем все оставшиеся задачи
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
                        # Закрываем loop
                        loop.close()
            except RuntimeError:
                # Игнорируем ошибку "Cannot close a running event loop"
                pass
            except Exception:
                # Игнорируем другие ошибки при закрытии
                pass
            
    except Exception as e:
        print(f"❌ Ошибка в Telegram боте: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Запуск приложения GreMuiv...")
    print("=" * 60)
    print(f"📊 Парсер: обновление каждые 15 минут (00, 15, 30, 45 минут каждого часа)")
    print(f"🌐 API сервер: http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"📚 Документация: http://{SERVER_HOST}:{SERVER_PORT}/docs")
    print("🤖 Telegram бот: запущен")
    print("🎨 Фронтенд: http://localhost:3001 (запустите отдельно)")
    print("=" * 60)
    print("")
    
    # Добавляем папку parsing в путь перед импортом
    parsing_path = project_root / "parsing"
    if str(parsing_path) not in sys.path:
        sys.path.insert(0, str(parsing_path))
    
    # Инициализируем БД
    from parsing.database import init_db
    print("📊 Инициализация базы данных...")
    init_db()
    print("✅ База данных готова\n")
    
    # Запускаем парсер в отдельном потоке (daemon=True - не блокирует завершение)
    parser_thread = Thread(target=run_parser, daemon=True, name="ParserThread")
    parser_thread.start()
    print("✅ Парсер запущен в отдельном потоке")
    
    # Запускаем Telegram бота в отдельном потоке (daemon=True - не блокирует завершение)
    telegram_thread = Thread(target=run_telegram_bot, daemon=True, name="TelegramBotThread")
    telegram_thread.start()
    print("✅ Telegram бот запущен в отдельном потоке")
    
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
        # Даем время потокам завершиться
        time.sleep(1)
        print("✅ Приложение остановлено")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

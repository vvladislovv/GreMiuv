"""Общие обработчики команд"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..keyboards import get_main_menu
from ..database import get_db, TelegramUser
from ..states import RegistrationStates

# Импортируем систему логирования
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
if str(parsing_path) not in sys.path:
    sys.path.insert(0, str(parsing_path))
from logger import log_telegram_info, log_telegram_error

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    import logging
    logger = logging.getLogger("telegram_bot")
    user_id = message.from_user.id
    username = message.from_user.username
    
    logger.info(f"Получена команда /start от пользователя {user_id} (@{username})")
    log_telegram_info(
        f"Команда /start от пользователя @{username}",
        user_id=user_id,
        description=f"Пользователь {user_id} (@{username}) отправил команду /start",
        details={"username": username, "first_name": message.from_user.first_name}
    )
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()
        
        if user and user.is_registered:
            # Пользователь уже зарегистрирован
            await message.answer(
                f"👋 Привет, {user.full_name or user.first_name or 'пользователь'}!\n\n"
                "Выберите действие:",
                reply_markup=get_main_menu(user_fio=user.full_name)
            )
        else:
            # Новый пользователь или незавершенная регистрация
            if not user:
                # Создаем нового пользователя
                user = TelegramUser(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    is_registered=0
                )
                db.add(user)
                db.commit()
            
            # Начинаем регистрацию - переводим в состояние ожидания ФИО
            await state.set_state(RegistrationStates.waiting_for_full_name)
            await message.answer(
                "👋 Добро пожаловать в GreMuiv Bot!\n\n"
                "Для начала работы необходимо пройти регистрацию.\n"
                "Пожалуйста, введите ваше полное ФИО (Фамилия Имя Отчество):"
            )
    except Exception as e:
        db.rollback()
        log_telegram_error(
            f"Ошибка в команде /start: {str(e)}",
            error=e,
            user_id=message.from_user.id,
            description="Ошибка при обработке команды /start"
        )
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        db.close()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
📚 Справка по боту GreMuiv

🔹 /start - Начать работу с ботом
🔹 /help - Показать эту справку
🔹 /settings - Открыть настройки

Основные функции:
• Просмотр своих оценок
• Статистика посещаемости
• Настройки аккаунта
"""
    await message.answer(help_text)


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Обработчик команды /settings"""
    from ..database import get_db, TelegramUser
    from ..keyboards import get_settings_menu
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == message.from_user.id
        ).first()
        
        if not user or not user.is_registered:
            await message.answer(
                "❌ Вы не зарегистрированы. Пожалуйста, начните с команды /start"
            )
            return
        
        user_info = (
            f"👤 Ваш профиль:\n\n"
            f"📝 ФИО: {user.full_name or 'не указано'}\n"
            f"🏷️ Тег: @{user.username or 'не указан'}\n"
            f"📱 Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"📅 Дата регистрации: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        await message.answer(user_info, reply_markup=get_settings_menu())
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        db.close()

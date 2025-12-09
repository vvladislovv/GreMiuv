"""Обработчики регистрации"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from datetime import datetime

from ..states import RegistrationStates
from ..database import get_db, TelegramUser
from ..keyboards import get_main_menu, get_confirm_fio_keyboard, get_main_menu_reply
from ..utils import safe_edit_message

# Импортируем систему логирования
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
if str(parsing_path) not in sys.path:
    sys.path.insert(0, str(parsing_path))
from logger import log_telegram_info, log_telegram_error

router = Router()

# Защита от спама - храним время последнего запроса
_last_request_time = {}
_throttle_seconds = 1  # Минимальный интервал между запросами (1 секунда)


def _check_throttle(user_id: int) -> bool:
    """Проверка защиты от спама"""
    current_time = datetime.now().timestamp()
    last_time = _last_request_time.get(user_id, 0)
    
    if current_time - last_time < _throttle_seconds:
        return False  # Слишком быстро
    
    _last_request_time[user_id] = current_time
    return True


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    """Обработка ввода полного ФИО"""
    # Защита от спама
    if not _check_throttle(message.from_user.id):
        return
    
    full_name = message.text.strip()
    
    # Проверка на минимальную длину
    if len(full_name) < 5:
        await message.answer(
            "❌ ФИО слишком короткое. Пожалуйста, введите полное ФИО "
            "(например: Иванов Иван Иванович):"
        )
        return
    
    # Проверка на наличие только букв и пробелов
    if not all(c.isalpha() or c.isspace() for c in full_name):
        await message.answer(
            "❌ ФИО должно содержать только буквы и пробелы. "
            "Пожалуйста, введите корректное ФИО:"
        )
        return
    
    # Сохраняем ФИО в состояние для подтверждения
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationStates.confirming_full_name)
    
    # Отправляем сообщение с подтверждением и inline кнопками
    confirm_text = (
        f"📝 Проверьте введенные данные:\n\n"
        f"Ваше ФИО: <b>{full_name}</b>\n\n"
        f"Всё правильно?"
    )
    
    await message.answer(
        confirm_text,
        reply_markup=get_confirm_fio_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_fio", StateFilter(RegistrationStates.confirming_full_name))
async def confirm_fio(callback: CallbackQuery, state: FSMContext):
    """Подтверждение ФИО и завершение регистрации"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    data = await state.get_data()
    full_name = data.get("full_name")
    
    if not full_name:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        await state.clear()
        return
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback.from_user.id
        ).first()
        
        if user:
            # Нормализуем ФИО в формат "Фамилия И.О."
            from ..utils.fio_normalizer import normalize_fio_to_initials
            normalized_fio = normalize_fio_to_initials(full_name)
            
            # Обновляем данные пользователя
            user.full_name = normalized_fio
            user.is_registered = 1
            user.username = callback.from_user.username
            user.first_name = callback.from_user.first_name
            user.last_name = callback.from_user.last_name
            
            db.commit()
            
            # Обновляем сообщение вместо отправки нового
            success_text = (
                f"✅ Регистрация завершена!\n\n"
                f"📝 Ваше ФИО: <b>{normalized_fio}</b>\n"
                f"👤 Тег: @{callback.from_user.username or 'не указан'}\n"
                f"📱 Имя аккаунта: {callback.from_user.first_name or ''} "
                f"{callback.from_user.last_name or ''}\n\n"
                f"Теперь вы можете использовать все функции бота!"
            )
            
            # Логируем успешную регистрацию
            log_telegram_info(
                f"Регистрация завершена: {full_name}",
                user_id=callback.from_user.id,
                description=f"Пользователь {callback.from_user.id} (@{callback.from_user.username}) успешно зарегистрирован",
                details={
                    "full_name": full_name,
                    "username": callback.from_user.username,
                    "first_name": callback.from_user.first_name,
                    "last_name": callback.from_user.last_name
                }
            )
            
            # Безопасное обновление сообщения
            await safe_edit_message(
                callback,
                success_text,
                reply_markup=get_main_menu(user_fio=normalized_fio),
                parse_mode="HTML"
            )
            await callback.answer("✅ Регистрация завершена!")
        else:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
    except Exception as e:
        db.rollback()
        log_telegram_error(
            f"Ошибка при регистрации: {str(e)}",
            error=e,
            user_id=callback.from_user.id,
            description="Ошибка при завершении регистрации пользователя"
        )
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    finally:
        db.close()
        await state.clear()


@router.callback_query(F.data == "change_fio", StateFilter(RegistrationStates.confirming_full_name))
async def change_fio(callback: CallbackQuery, state: FSMContext):
    """Изменение ФИО - возврат к вводу"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    # Возвращаемся к состоянию ввода ФИО
    await state.set_state(RegistrationStates.waiting_for_full_name)
    
    # Безопасное обновление сообщения
    await safe_edit_message(
        callback,
        "👋 Добро пожаловать в GreMuiv Bot!\n\n"
        "Для начала работы необходимо пройти регистрацию.\n"
        "Пожалуйста, введите ваше полное ФИО (Фамилия Имя Отчество):"
    )
    await callback.answer("✏️ Введите ФИО заново")


@router.callback_query(F.data == "journal")
async def show_journal(callback: CallbackQuery):
    """Обработчик для журнала (используется если Mini App URL не настроен)"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback.from_user.id
        ).first()
        
        if not user or not user.is_registered:
            await callback.answer("❌ Вы не зарегистрированы. Используйте /start", show_alert=True)
            return
        
        # Проверяем, настроен ли Mini App URL
        from ..config import MINI_APP_URL
        from ..keyboards import is_valid_web_app_url
        
        if is_valid_web_app_url(MINI_APP_URL):
            # Если URL валидный, но почему-то пришли сюда через callback
            journal_text = (
                "📓 <b>Журнал оценок</b>\n\n"
                "Для открытия журнала используйте кнопку '📓 Журнал' выше.\n\n"
                "Она откроет Mini App с журналом оценок."
            )
        else:
            # Если URL не настроен, показываем информацию
            journal_text = (
                "📓 <b>Журнал оценок</b>\n\n"
                "Функция просмотра оценок будет доступна в ближайшее время.\n\n"
                "Мы работаем над интеграцией с базой данных оценок.\n\n"
                "<i>Для настройки Mini App укажите валидный HTTPS URL в переменной окружения MINI_APP_URL</i>"
            )
        
        user_fio = user.full_name if user and user.is_registered else None
        await safe_edit_message(
            callback,
            journal_text,
            reply_markup=get_main_menu(user_fio=user_fio),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    finally:
        db.close()


@router.message(F.text == "📓 Журнал")
async def show_journal_message(message: Message):
    """Показать журнал оценок (для reply кнопки)"""
    # Защита от спама
    if not _check_throttle(message.from_user.id):
        return
    
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
        
        # Здесь будет логика получения оценок из БД
        # Пока заглушка
        journal_text = (
            "📓 <b>Журнал оценок</b>\n\n"
            "Функция просмотра оценок будет доступна в ближайшее время.\n\n"
            "Мы работаем над интеграцией с базой данных оценок."
        )
        
        user_fio = user.full_name if user else None
        await message.answer(
            journal_text,
            reply_markup=get_main_menu(user_fio=user_fio),
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        db.close()

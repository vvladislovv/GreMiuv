"""Обработчики настроек"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from datetime import datetime

from ..database import get_db, TelegramUser
from ..keyboards import get_settings_menu, get_delete_confirm_keyboard, get_main_menu
from ..config import BOT_NAME, BOT_DESCRIPTION
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

# Защита от спама
_last_request_time = {}
_throttle_seconds = 1


def _check_throttle(user_id: int) -> bool:
    """Проверка защиты от спама"""
    current_time = datetime.now().timestamp()
    last_time = _last_request_time.get(user_id, 0)
    
    if current_time - last_time < _throttle_seconds:
        return False
    
    _last_request_time[user_id] = current_time
    return True


@router.callback_query(F.data == "settings")
async def show_settings_callback(callback: CallbackQuery):
    """Показать меню настроек через callback"""
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
        
        user_info = (
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"📝 ФИО: {user.full_name or 'не указано'}\n"
            f"🏷️ Тег: @{user.username or 'не указан'}\n"
            f"📱 Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"📅 Дата регистрации: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        await safe_edit_message(
            callback,
            user_info,
            reply_markup=get_settings_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    finally:
        db.close()


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать меню настроек через сообщение"""
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
            f"👤 <b>Ваш профиль:</b>\n\n"
            f"📝 ФИО: {user.full_name or 'не указано'}\n"
            f"🏷️ Тег: @{user.username or 'не указан'}\n"
            f"📱 Имя: {user.first_name or ''} {user.last_name or ''}\n"
            f"📅 Дата регистрации: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Выберите действие:"
        )
        
        await message.answer(user_info, reply_markup=get_settings_menu(), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
    finally:
        db.close()


@router.callback_query(F.data == "bot_info")
async def show_bot_info(callback: CallbackQuery):
    """Показать информацию о боте"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    info_text = (
        f"🤖 {BOT_NAME}\n\n"
        f"{BOT_DESCRIPTION}\n\n"
        f"📊 Версия: 1.0.0\n"
        f"🔧 Разработчик: GreMuiv Team\n\n"
        f"Для получения помощи используйте команду /help"
    )
    
    await safe_edit_message(callback, info_text, reply_markup=get_settings_menu())
    await callback.answer()


@router.callback_query(F.data == "delete_account")
async def confirm_delete_account(callback: CallbackQuery):
    """Подтверждение удаления аккаунта"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    warning_text = (
        "⚠️ ВНИМАНИЕ!\n\n"
        "Вы собираетесь удалить свой аккаунт из базы данных.\n\n"
        "Это действие:\n"
        "• Удалит все ваши данные\n"
        "• Отменит вашу регистрацию\n"
        "• Потребует повторной регистрации для использования бота\n\n"
        "Вы уверены, что хотите продолжить?"
    )
    
    await safe_edit_message(
        callback,
        warning_text,
        reply_markup=get_delete_confirm_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "confirm_delete")
async def delete_account(callback: CallbackQuery):
    """Удаление аккаунта из БД"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback.from_user.id
        ).first()
        
        if user:
            user_id = callback.from_user.id
            username = callback.from_user.username
            
            db.delete(user)
            db.commit()
            
            log_telegram_info(
                f"Аккаунт удален: @{username}",
                user_id=user_id,
                description=f"Пользователь {user_id} (@{username}) удалил свой аккаунт",
                details={"username": username, "full_name": user.full_name}
            )
            
            await safe_edit_message(
                callback,
                "✅ Ваш аккаунт успешно удален из базы данных.\n\n"
                "Для повторной регистрации используйте команду /start"
            )
            await callback.answer("Аккаунт удален")
        else:
            await safe_edit_message(
                callback,
                "❌ Аккаунт не найден в базе данных."
            )
            await callback.answer("Аккаунт не найден")
    except Exception as e:
        db.rollback()
        await safe_edit_message(
            callback,
            f"❌ Произошла ошибка при удалении: {str(e)}"
        )
        await callback.answer("Ошибка при удалении")
    finally:
        db.close()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    """Отмена удаления аккаунта"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    await safe_edit_message(
        callback,
        "❌ Удаление аккаунта отменено.",
        reply_markup=get_settings_menu()
    )
    await callback.answer("Отменено")


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback.from_user.id
        ).first()
        
        if user:
            menu_text = f"👋 Привет, {user.full_name or user.first_name or 'пользователь'}!\n\nВыберите действие:"
        else:
            menu_text = "Главное меню:"
        
        user_fio = user.full_name if user else None
        await safe_edit_message(
            callback,
            menu_text,
            reply_markup=get_main_menu(user_fio=user_fio)
        )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    """Вернуться в настройки"""
    # Защита от спама
    if not _check_throttle(callback.from_user.id):
        await callback.answer("⏳ Подождите немного...", show_alert=False)
        return
    
    db = get_db()
    try:
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == callback.from_user.id
        ).first()
        
        if user:
            user_info = (
                f"👤 <b>Ваш профиль:</b>\n\n"
                f"📝 ФИО: {user.full_name or 'не указано'}\n"
                f"🏷️ Тег: @{user.username or 'не указан'}\n"
                f"📱 Имя: {user.first_name or ''} {user.last_name or ''}\n"
                f"📅 Дата регистрации: {user.registered_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Выберите действие:"
            )
            await safe_edit_message(
                callback,
                user_info,
                reply_markup=get_settings_menu(),
                parse_mode="HTML"
            )
        else:
            await safe_edit_message(
                callback,
                "⚙️ Настройки",
                reply_markup=get_settings_menu()
            )
        await callback.answer()
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
    finally:
        db.close()

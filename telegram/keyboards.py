"""Клавиатуры для бота"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from .config import MINI_APP_URL
import re


def is_valid_web_app_url(url: str) -> bool:
    """
    Проверяет, является ли URL валидным для Telegram Mini App
    
    Требования:
    - Должен начинаться с https://
    - Не должен быть localhost или 127.0.0.1
    - Должен быть публичным доменом
    """
    if not url:
        return False
    
    # Проверяем, что начинается с https://
    if not url.startswith("https://"):
        return False
    
    # Проверяем, что не localhost
    if "localhost" in url.lower() or "127.0.0.1" in url:
        return False
    
    # Проверяем базовый формат URL
    url_pattern = re.compile(
        r'^https://'  # https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # домен
        r'localhost|'  # localhost (но мы уже проверили выше)
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # опциональный порт
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def get_main_menu(web_app_url: str = None, user_fio: str = None):
    """Главное меню с inline кнопками"""
    # Используем переданный URL или из конфига
    app_url = web_app_url or MINI_APP_URL
    
    # Убеждаемся, что URL заканчивается на слэш (если нет параметров)
    if app_url and not app_url.endswith('/') and '?' not in app_url:
        app_url = app_url.rstrip('/') + '/'
    
    # Используем start_param для передачи ФИО (более надежный способ для Telegram Mini App)
    start_param = None
    print(f"🔍 get_main_menu вызван с user_fio: {user_fio}, тип: {type(user_fio)}")
    
    if user_fio:
        from urllib.parse import quote
        # Кодируем ФИО для start_param (максимум 64 символа)
        # Telegram ограничивает start_param до 64 символов
        fio_encoded = quote(str(user_fio)[:64], safe='')
        start_param = fio_encoded
        print(f"🔗 Используем start_param для передачи ФИО: {start_param[:50]}... (полная длина: {len(start_param)})")
    else:
        print(f"⚠️ user_fio не передан или пустой, start_param не будет установлен")
    
    # Убеждаемся, что URL заканчивается на слэш
    if app_url and not app_url.endswith('/'):
        app_url = app_url.rstrip('/') + '/'
    
    print(f"🔗 Mini App URL: {app_url}")
    
    # Проверяем валидность URL для Mini App
    if is_valid_web_app_url(app_url):
        print(f"✅ URL валиден для Mini App: {app_url}")
        # Используем Mini App (web_app) с start_param
        if start_param:
            web_app_info = WebAppInfo(url=app_url, start_param=start_param)
            print(f"✅ Создан WebAppInfo с start_param: {start_param[:50]}...")
            print(f"   WebAppInfo.url: {web_app_info.url}")
            print(f"   WebAppInfo.start_param: {web_app_info.start_param}")
        else:
            web_app_info = WebAppInfo(url=app_url)
            print(f"⚠️ WebAppInfo создан БЕЗ start_param")
        journal_button = InlineKeyboardButton(
            text="📓 Журнал",
            web_app=web_app_info
        )
    else:
        # Используем обычную callback кнопку
        journal_button = InlineKeyboardButton(
            text="📓 Журнал",
            callback_data="journal"
        )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [journal_button],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
        ]
    )
    return keyboard


def get_main_menu_reply():
    """Главное меню (reply keyboard для совместимости)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📓 Журнал")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_confirm_fio_keyboard():
    """Клавиатура подтверждения ФИО"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, правильно", callback_data="confirm_fio"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="change_fio")
            ]
        ]
    )
    return keyboard


def get_settings_menu():
    """Меню настроек"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Информация о боте", callback_data="bot_info")],
            [InlineKeyboardButton(text="🗑️ Удалить аккаунт", callback_data="delete_account")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard


def get_delete_confirm_keyboard():
    """Клавиатура подтверждения удаления"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
            ]
        ]
    )
    return keyboard


def get_back_keyboard():
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

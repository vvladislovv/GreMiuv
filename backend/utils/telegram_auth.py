"""
Авторизация через Telegram Mini App
"""
import hmac
import hashlib
import json
import urllib.parse
from typing import Optional, Dict
from fastapi import HTTPException, status, Header
from datetime import datetime, timedelta


def validate_telegram_init_data(init_data: str, bot_token: str) -> Optional[Dict]:
    """
    Валидирует initData от Telegram Mini App
    
    Args:
        init_data: Строка initData от Telegram
        bot_token: Токен бота
    
    Returns:
        dict: Данные пользователя или None если невалидно
    """
    try:
        # Парсим initData
        parsed_data = urllib.parse.parse_qs(init_data)
        
        if 'hash' not in parsed_data:
            return None
        
        received_hash = parsed_data['hash'][0]
        
        # Удаляем hash из данных для проверки
        data_check = []
        for key, value in parsed_data.items():
            if key != 'hash':
                data_check.append(f"{key}={value[0]}")
        
        data_check_string = '\n'.join(sorted(data_check))
        
        # Создаем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Вычисляем hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Проверяем hash
        if calculated_hash != received_hash:
            return None
        
        # Проверяем время (auth_date не должен быть старше 24 часов)
        if 'auth_date' in parsed_data:
            auth_date = int(parsed_data['auth_date'][0])
            if datetime.now().timestamp() - auth_date > 86400:  # 24 часа
                return None
        
        # Извлекаем данные пользователя
        user_data = {}
        if 'user' in parsed_data:
            user_data = json.loads(parsed_data['user'][0])
        
        return {
            'user': user_data,
            'auth_date': int(parsed_data.get('auth_date', [0])[0]),
            'query_id': parsed_data.get('query_id', [None])[0],
            'start_param': parsed_data.get('start_param', [None])[0]
        }
    except Exception:
        return None


async def verify_telegram_user(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
) -> Dict:
    """
    Middleware для проверки Telegram пользователя
    
    Args:
        init_data: initData из заголовка
    
    Returns:
        dict: Данные пользователя
    
    Raises:
        HTTPException: Если авторизация не прошла
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("BOT_TOKEN", "")
    
    if not bot_token:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN не настроен на сервере"
        )
    
    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация через Telegram Mini App"
        )
    
    user_data = validate_telegram_init_data(init_data, bot_token)
    
    if not user_data or 'user' not in user_data:
        raise HTTPException(
            status_code=401,
            detail="Невалидные данные авторизации Telegram"
        )
    
    return user_data


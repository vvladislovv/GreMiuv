"""
Система аутентификации с токенами
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import json
from pathlib import Path

# Схема безопасности
security = HTTPBearer()

# Путь к файлу с токенами
TOKEN_FILE = Path(__file__).parent.parent.parent / "data" / "api_tokens.json"


def generate_token() -> str:
    """Генерирует новый безопасный токен"""
    return secrets.token_urlsafe(32)


def load_tokens() -> dict:
    """Загружает токены из файла"""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_tokens(tokens: dict):
    """Сохраняет токены в файл"""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)


def create_token(name: str = "default") -> str:
    """Создает новый токен и сохраняет его"""
    tokens = load_tokens()
    token = generate_token()
    tokens[token] = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "last_used": None
    }
    save_tokens(tokens)
    return token


def validate_token(token: str) -> bool:
    """Проверяет валидность токена"""
    tokens = load_tokens()
    if token in tokens:
        # Обновляем время последнего использования
        tokens[token]["last_used"] = datetime.now().isoformat()
        save_tokens(tokens)
        return True
    return False


def get_or_create_token() -> str:
    """Получает существующий токен или создает новый"""
    tokens = load_tokens()
    if tokens:
        # Возвращаем первый доступный токен
        return list(tokens.keys())[0]
    else:
        # Создаем новый токен
        return create_token("auto_generated")


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Проверяет токен из заголовка Authorization
    Вызывает HTTPException если токен невалиден
    """
    token = credentials.credentials
    
    if not validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или отсутствующий токен доступа",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


def init_auth():
    """Инициализирует систему аутентификации - создает токен если его нет"""
    tokens = load_tokens()
    if not tokens:
        token = create_token("auto_generated")
        return token
    return list(tokens.keys())[0]






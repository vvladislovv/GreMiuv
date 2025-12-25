"""
Система логирования в БД для всех модулей приложения
"""
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from database import get_db, AppLog


def log_to_db(
    module: str,
    level: str,
    message: str,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None,
    error: Optional[Exception] = None
):
    """
    Сохраняет лог в базу данных
    
    Args:
        module: Модуль ('parser', 'backend', 'telegram')
        level: Уровень лога ('INFO', 'WARNING', 'ERROR', 'DEBUG')
        message: Основное сообщение
        description: Дополнительное описание
        details: Дополнительные данные (словарь)
        user_id: ID пользователя (для телеграм)
        error: Объект исключения (если есть)
    """
    db = get_db()
    try:
        error_traceback = None
        if error:
            error_traceback = ''.join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))
        
        details_json = None
        if details:
            details_json = json.dumps(details, ensure_ascii=False, default=str)
        
        log_entry = AppLog(
            timestamp=datetime.now(),
            module=module,
            level=level,
            message=message,
            description=description,
            details=details_json,
            user_id=user_id,
            error_traceback=error_traceback
        )
        
        db.add(log_entry)
        db.commit()
    except Exception as e:
        # Если не удалось сохранить лог в БД, выводим в консоль
        print(f"⚠️ Ошибка при сохранении лога в БД: {e}")
        db.rollback()
    finally:
        db.close()


def log_parser_info(message: str, description: str = None, details: Dict[str, Any] = None):
    """Лог информации парсера"""
    log_to_db('parser', 'INFO', message, description, details)


def log_parser_error(message: str, error: Exception = None, description: str = None, details: Dict[str, Any] = None):
    """Лог ошибки парсера"""
    log_to_db('parser', 'ERROR', message, description, details, error=error)


def log_backend_info(message: str, description: str = None, details: Dict[str, Any] = None):
    """Лог информации бэкенда"""
    log_to_db('backend', 'INFO', message, description, details)


def log_backend_error(message: str, error: Exception = None, description: str = None, details: Dict[str, Any] = None):
    """Лог ошибки бэкенда"""
    log_to_db('backend', 'ERROR', message, description, details, error=error)


def log_telegram_info(message: str, user_id: int = None, description: str = None, details: Dict[str, Any] = None):
    """Лог информации телеграм бота"""
    log_to_db('telegram', 'INFO', message, description, details, user_id=user_id)


def log_telegram_error(message: str, error: Exception = None, user_id: int = None, description: str = None, details: Dict[str, Any] = None):
    """Лог ошибки телеграм бота"""
    log_to_db('telegram', 'ERROR', message, description, details, user_id=user_id, error=error)


def log_telegram_warning(message: str, user_id: int = None, description: str = None, details: Dict[str, Any] = None):
    """Лог предупреждения телеграм бота"""
    log_to_db('telegram', 'WARNING', message, description, details, user_id=user_id)















"""
Утилиты для Telegram бота
"""
from .fio_normalizer import normalize_fio_to_initials
from .message_utils import safe_edit_message

__all__ = ['normalize_fio_to_initials', 'safe_edit_message']

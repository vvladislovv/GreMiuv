"""
Вспомогательные функции
"""
from datetime import date


def date_to_str(date_obj):
    """Конвертирует date объект в строку"""
    if date_obj is None:
        return None
    if isinstance(date_obj, str):
        return date_obj
    if isinstance(date_obj, date):
        return date_obj.strftime('%Y-%m-%d')
    return str(date_obj)

"""Утилиты для работы с сообщениями"""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery


async def safe_edit_message(
    message_or_callback: Message | CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode: str = None,
    **kwargs
):
    """
    Безопасное обновление сообщения с обработкой ошибки "message is not modified"
    
    Args:
        message_or_callback: Message или CallbackQuery объект
        text: Текст сообщения
        reply_markup: Клавиатура
        parse_mode: Режим парсинга (HTML, Markdown)
        **kwargs: Дополнительные параметры для edit_text
    
    Returns:
        True если сообщение обновлено, False если не было изменений
    """
    try:
        if isinstance(message_or_callback, CallbackQuery):
            message = message_or_callback.message
        else:
            message = message_or_callback
        
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs
        )
        return True
    except TelegramBadRequest as e:
        # Обрабатываем ошибку "message is not modified"
        if "message is not modified" in str(e).lower():
            # Сообщение уже имеет такое содержимое - это нормально
            return False
        # Другая ошибка - пробрасываем дальше
        raise
    except Exception as e:
        # Другие ошибки - пробрасываем
        raise










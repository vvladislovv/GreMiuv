"""
Утилита для нормализации ФИО в формат "Фамилия И.О."
"""
import re


def normalize_fio_to_initials(fio: str) -> str:
    """
    Преобразует ФИО в формат "Фамилия И.О."
    
    Примеры:
    - "Иванов Иван Иванович" -> "Иванов И.И."
    - "Петров Петр" -> "Петров П."
    - "Сидоров С.С." -> "Сидоров С.С." (уже в нужном формате)
    - "Ельченинов Владислав Антонович" -> "Ельченинов В.А."
    
    Args:
        fio: Полное ФИО или ФИО в любом формате
    
    Returns:
        str: ФИО в формате "Фамилия И.О."
    """
    if not fio:
        return fio
    
    # Убираем лишние пробелы
    fio = ' '.join(fio.strip().split())
    
    # Если уже в формате "Фамилия И.О." или "Фамилия И.О", оставляем как есть
    if re.match(r'^[А-ЯЁ][а-яё]+\s+[А-ЯЁ]\.\s*[А-ЯЁ]?\.?$', fio):
        return fio
    
    # Разбиваем на части
    parts = fio.split()
    
    if len(parts) == 0:
        return fio
    
    # Фамилия - первая часть
    surname = parts[0]
    
    # Имя - вторая часть (если есть)
    if len(parts) >= 2:
        first_name_initial = parts[1][0].upper() if parts[1] else ''
    else:
        first_name_initial = ''
    
    # Отчество - третья часть (если есть)
    if len(parts) >= 3:
        last_name_initial = parts[2][0].upper() if parts[2] else ''
    else:
        last_name_initial = ''
    
    # Формируем результат
    if first_name_initial and last_name_initial:
        return f"{surname} {first_name_initial}.{last_name_initial}."
    elif first_name_initial:
        return f"{surname} {first_name_initial}."
    else:
        return surname



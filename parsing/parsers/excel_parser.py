"""
ПАРСЕР EXCEL ФАЙЛОВ
===================

Логика работы:
1. Загружает Excel файл (openpyxl)
2. Пропускает первые 3 вкладки (SKIP_FIRST_SHEETS)
3. Парсит вкладки до "УП технической разработки" (STOP_SHEET_NAME)
4. Для каждой вкладки:
   - Парсит ВЕСЬ документ до конца (включая продолжение, второй журнал со строки 65-70 и т.д.)
   - Находит ВСЕ строки заголовков (поиск "ФИО" по всему листу)
   - Для каждого найденного журнала:
     * Находит колонку с ФИО студентов
     * Находит строку с месяцами (обычно строка 5 или около заголовка)
     * Определяет месяц для каждой колонки с датами
     * Находит колонки с датами и правильно парсит их с учетом месяца
     * Извлекает данные: ФИО, дата, оценка/пропуск
     * Парсит данные до следующего заголовка или до конца листа
5. Возвращает список словарей с данными (включая данные из всех журналов)

Функции:
- parse_excel_file() - главная функция парсинга файла
- parse_sheet() - парсинг одной вкладки (поддерживает несколько журналов, парсит весь документ)
- parse_date() - парсинг даты из различных форматов
- parse_grade_value() - парсинг оценки/пропуска
- find_student_column() - поиск колонки с ФИО
- find_date_columns() - поиск колонок с датами (определяет месяц для каждой колонки)
- find_month_in_cell() - поиск названия месяца в ячейке
"""

import os
import re
from openpyxl import load_workbook
from datetime import datetime, date as date_type
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SKIP_FIRST_SHEETS, STOP_SHEET_NAME


def normalize_fio_to_initials(fio: str) -> str:
    """
    Преобразует ФИО в формат "Фамилия И.О."
    
    Примеры:
    - "Иванов Иван Иванович" -> "Иванов И.И."
    - "Петров Петр" -> "Петров П."
    - "Сидоров С.С." -> "Сидоров С.С." (уже в нужном формате)
    - "Ельченинов Владислав Антонович" -> "Ельченинов В.А."
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


def parse_date(date_value):
    """
    Парсинг даты из различных форматов
    
    Поддерживает:
    - datetime объекты
    - date объекты
    - Числа Excel (номер дня с 1900-01-01)
    - Строки в форматах: %d.%m.%Y, %Y-%m-%d, %d/%m/%Y, %Y/%m/%d
    """
    if isinstance(date_value, (datetime, date_type)):
        if isinstance(date_value, datetime):
            parsed_date = date_value.date()
        else:
            parsed_date = date_value
        
        # Проверяем, что дата разумная (не 1900 год)
        if parsed_date.year < 2000:
            return None
        return parsed_date
    
    elif isinstance(date_value, (int, float)):
        # Excel хранит даты как числа (дни с 1900-01-01)
        try:
            from openpyxl.utils.datetime import from_excel
            parsed_date = from_excel(date_value).date()
            
            # Проверяем, что дата разумная (не 1900 год)
            if parsed_date.year < 2000:
                # Пробуем альтернативный способ - может быть это номер дня в другом формате
                # Если число маленькое (1-31), это может быть день месяца, а не дата Excel
                if date_value < 100:
                    return None
                return None
            return parsed_date
        except Exception as e:
            return None
    
    elif isinstance(date_value, str):
        # Пытаемся распарсить строку
        date_str = date_value.strip()
        
        # Пробуем разные форматы
        formats = [
            "%d.%m.%Y", 
            "%Y-%m-%d", 
            "%d/%m/%Y", 
            "%Y/%m/%d",
            "%d.%m.%y",  # короткий год
            "%d/%m/%y"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt).date()
                # Проверяем, что дата разумная
                if parsed_date.year >= 2000:
                    return parsed_date
            except:
                continue
        
        # Если не получилось распарсить, возвращаем None
        return None
    
    return None


def parse_grade_value(value):
    """
    Парсинг значения оценки/пропуска
    
    Логика:
    - Если содержит слова "пропуск", "н", "н/я" и т.д. → возвращает "пропуск"
    - Иначе пытается извлечь число (оценку)
    - Исключает даты и другие некорректные значения
    - Возвращает строку с оценкой или "пропуск"
    """
    if value is None:
        return None
    
    # Если это дата - не парсим как оценку
    if isinstance(value, (datetime, date_type)):
        return None
    
    value_str = str(value).strip()
    
    if not value_str:
        return None
    
    value_lower = value_str.lower()
    
    # Проверяем на пропуск (включая символ *)
    if any(word in value_lower for word in ['пропуск', 'н', 'н/я', 'неявка', 'нб', 'н/б']) or value_str == '*':
        return "пропуск"
    
    # Исключаем даты (формат YYYY-MM-DD или похожий)
    if re.match(r'^\d{4}-\d{2}-\d{2}', value_str):
        return None
    
    # Исключаем значения, которые выглядят как даты с временем
    if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}', value_str):
        return None
    
    # Пытаемся извлечь оценку (число)
    numbers = re.findall(r'\d+', value_str)
    if numbers:
        grade = numbers[0]
        # Проверяем, что это разумная оценка (1-5 или 0-100)
        if grade in ['1', '2', '3', '4', '5']:
            return grade
        elif len(grade) <= 3 and int(grade) <= 100:  # Может быть 0-100
            return grade
    
    # Если это короткая строка (1-2 символа) и не дата - возвращаем как есть
    if len(value_str) <= 2:
        return value_str
    
    # Иначе игнорируем (вероятно, это не оценка)
    return None


def find_student_column(header_row):
    """
    Поиск колонки с ФИО студентов
    
    Ищет колонку, содержащую слова: "фио", "студент", "фамилия", "имя" и т.д.
    Если не находит, берет первую колонку с текстом
    """
    for idx, cell in enumerate(header_row):
        if cell.value:
            value = str(cell.value).lower().strip()
            if any(word in value for word in ['фио', 'студент', 'фамилия', 'имя', 'ученик', 'учащийся']):
                return idx
    # Если не нашли, пробуем первую колонку с текстом
    for idx, cell in enumerate(header_row):
        if cell.value and isinstance(cell.value, str) and len(cell.value.strip()) > 2:
            return idx
    return None


def find_month_in_cell(cell_value):
    """
    Ищет название месяца в значении ячейки
    
    Returns:
        (month_num, year) или None
    """
    if not cell_value:
        return None
    
    cell_str = str(cell_value).lower().strip()
    current_year = datetime.now().year
    
    # Ищем названия месяцев (полные и сокращенные)
    months = {
        'январь': 1, 'янв': 1, 'февраль': 2, 'фев': 2,
        'март': 3, 'апрель': 4, 'апр': 4,
        'май': 5, 'июнь': 6, 'июль': 7, 'август': 8, 'авг': 8,
        'сентябрь': 9, 'сен': 9, 'сент': 9,
        'октябрь': 10, 'окт': 10,
        'ноябрь': 11, 'ноя': 11,
        'декабрь': 12, 'дек': 12, 'дек абрь': 12, 'декабр': 12
    }
    
    for month_name, month_num in months.items():
        if month_name in cell_str:
            # Пытаемся найти год
            year = current_year
            # Ищем год в формате YYYY
            year_match = re.search(r'20\d{2}', cell_str)
            if year_match:
                year = int(year_match.group())
            
            return (month_num, year)
    
    return None


def find_date_columns(header_row, worksheet, header_row_idx):
    """
    Поиск колонок с датами с учетом месяцев на строке 5 (или около заголовка)
    
    Логика:
    1. Ищет строку с месяцами (обычно строка 5 или около заголовка)
    2. Для каждой колонки определяет месяц из соответствующей ячейки строки с месяцами
    3. Использует месяц для построения полных дат из чисел (дней)
    4. Парсит весь документ, включая продолжение
    
    Возвращает список кортежей: (индекс_колонки, дата)
    """
    date_columns = []
    current_year = datetime.now().year
    
    # Ищем строку с месяцами - проверяем строки выше заголовка (особенно строку 5)
    # Обычно месяц указан на строке 5 или около заголовка
    month_row_idx = None
    month_row = None
    
    # Сначала проверяем конкретные строки: 5, 4, 3, 2, 1 (если они выше заголовка)
    check_rows = [5, 4, 3, 2, 1]
    for check_row_num in check_rows:
        if check_row_num < header_row_idx:
            check_row = list(worksheet[check_row_num])
            # Проверяем, есть ли в этой строке названия месяцев
            for cell in check_row:
                if cell.value and find_month_in_cell(cell.value):
                    month_row_idx = check_row_num
                    month_row = check_row
                    break
            if month_row:
                break
    
    # Если не нашли на конкретных строках, ищем в диапазоне выше заголовка (до 15 строк)
    if not month_row:
        for row_offset in range(1, min(16, header_row_idx + 1)):
            check_row_idx = header_row_idx - row_offset
            if check_row_idx < 1:
                break
            
            check_row = list(worksheet[check_row_idx])
            # Проверяем, есть ли в этой строке названия месяцев
            for cell in check_row:
                if cell.value and find_month_in_cell(cell.value):
                    month_row_idx = check_row_idx
                    month_row = check_row
                    break
            if month_row:
                break
    
    # Если нашли строку с месяцами, используем её для определения месяца каждой колонки
    # Иначе используем общий месяц (если найдем)
    column_months = {}  # индекс_колонки -> (month, year)
    general_month_year = None
    
    if month_row:
        # Для каждой колонки определяем месяц из соответствующей ячейки
        for idx, cell in enumerate(month_row):
            month_year = find_month_in_cell(cell.value)
            if month_year:
                column_months[idx] = month_year
                # Также сохраняем как общий месяц (на случай если не все колонки имеют месяц)
                if general_month_year is None:
                    general_month_year = month_year
    else:
        # Если не нашли строку с месяцами, ищем общий месяц в любом месте
        for row_offset in range(1, min(16, header_row_idx + 1)):
            check_row_idx = header_row_idx - row_offset
            if check_row_idx < 1:
                break
            
            check_row = list(worksheet[check_row_idx])
            for cell in check_row:
                month_year = find_month_in_cell(cell.value)
                if month_year:
                    general_month_year = month_year
                    break
            if general_month_year:
                break
    
    # Парсим даты из заголовков
    for idx, cell in enumerate(header_row):
        if not cell.value:
            continue
        
        cell_value = cell.value
        
        # Если это число от 1 до 31 - это день месяца
        if isinstance(cell_value, (int, float)) and 1 <= cell_value <= 31:
            day = int(cell_value)
            
            # Определяем месяц для этой колонки
            month_year = column_months.get(idx, general_month_year)
            
            if month_year:
                month, year = month_year
                try:
                    parsed_date = date_type(year, month, day)
                    date_columns.append((idx, parsed_date))
                    continue
                except ValueError:
                    pass
        
        # Пытаемся распарсить как полную дату
        parsed_date = parse_date(cell_value)
        if parsed_date:
            date_columns.append((idx, parsed_date))
    
    return date_columns


def parse_topics_table(worksheet, group_name, subject_name, start_row=1):
    """
    Парсит таблицу с темами занятий (Форма 1, где в колонке "Кол-во часов" всегда "2")
    
    Ищет таблицу с заголовками:
    - "Дата проведения"
    - "Кол-во часов" 
    - "Наименование учебного занятия"
    
    Возвращает список тем занятий
    """
    topics_data = []
    max_row = worksheet.max_row
    max_col = worksheet.max_column
    
    # Ищем заголовок таблицы с темами
    header_row_idx = None
    date_col = None
    hours_col = None
    topic_col = None
    
    # Ищем строку с заголовками "Кол-во часов" или "Наименование учебного занятия"
    # Ищем по всему листу, не только в первых 100 строках
    for row_idx in range(start_row, max_row + 1):
        row = list(worksheet[row_idx])
        row_text_lower = ' '.join([str(cell.value).lower() if cell.value else '' for cell in row])
        
        # Ищем ключевые слова заголовков - более гибкий поиск
        has_hours = 'кол-во часов' in row_text_lower or 'количество часов' in row_text_lower or 'часов' in row_text_lower
        has_topic = 'наименование учебного занятия' in row_text_lower or ('наименование' in row_text_lower and 'занятия' in row_text_lower) or 'наименование' in row_text_lower
        
        if has_hours and has_topic:
            header_row_idx = row_idx
            
            # Находим колонки
            for col_idx, cell in enumerate(row):
                if not cell.value:
                    continue
                cell_value = str(cell.value).lower().strip()
                
                if 'дата проведения' in cell_value:
                    date_col = col_idx
                elif 'кол-во часов' in cell_value or 'количество часов' in cell_value or ('часов' in cell_value and 'кол' in cell_value):
                    hours_col = col_idx
                elif 'наименование учебного занятия' in cell_value or ('наименование' in cell_value and 'занятия' in cell_value):
                    topic_col = col_idx
            
            if hours_col is not None and topic_col is not None:
                break
    
    if not header_row_idx or hours_col is None or topic_col is None:
        return topics_data
    
    # Парсим строки с темами (начинаем со следующей строки после заголовка)
    for row_idx in range(header_row_idx + 1, max_row + 1):
        row = list(worksheet[row_idx])
        
        if len(row) <= max(hours_col, topic_col):
            continue
        
        hours_cell = row[hours_col] if hours_col < len(row) else None
        topic_cell = row[topic_col] if topic_col < len(row) else None
        
        if not topic_cell or not topic_cell.value:
            continue
        
        topic_name = str(topic_cell.value).strip()
        
        # Пропускаем пустые строки и заголовки
        if not topic_name or len(topic_name) < 3:
            continue
        
        # Проверяем, что это не заголовок
        if any(keyword in topic_name.lower() for keyword in ['наименование', 'занятия', 'дата', 'кол-во', 'часов']):
            continue
        
        # Получаем количество часов (обычно "2")
        hours_value = None
        if hours_cell and hours_cell.value:
            try:
                hours_value = int(float(str(hours_cell.value).strip()))
            except:
                hours_value = str(hours_cell.value).strip()
        
        # Получаем дату проведения (если есть)
        date_value = None
        if date_col is not None and date_col < len(row):
            date_cell = row[date_col]
            if date_cell and date_cell.value:
                parsed_date = parse_date(date_cell.value)
                if parsed_date:
                    date_value = parsed_date
        
        # Добавляем тему (даже если часов нет, но есть название темы)
        topics_data.append({
            'group': group_name,
            'subject': subject_name,
            'topic': topic_name,
            'hours': hours_value if hours_value else 2,  # По умолчанию 2, как указал пользователь
            'date': date_value
        })
    
    return topics_data


def parse_sheet(worksheet, group_name, subject_name):
    """
    Парсинг одного листа Excel с поддержкой нескольких журналов
    
    Логика:
    1. Парсит ВЕСЬ документ до конца (включая продолжение, второй журнал со строки 65-70 и т.д.)
    2. Ищет все строки заголовков (ищет "ФИО" по всему листу)
    3. Для каждого найденного заголовка:
       - Находит колонку с ФИО
       - Находит колонки с датами (определяет месяц для каждой колонки из строки с месяцами)
       - Парсит данные до следующего заголовка или до конца листа
    4. Также парсит таблицу с темами занятий (где "Кол-во часов" = 2)
    5. Возвращает список словарей с данными (все данные из всех журналов + темы)
    """
    data = []
    max_row = worksheet.max_row
    
    # Находим все строки с заголовками "ФИО" по всему листу
    header_rows = []
    for idx in range(1, max_row + 1):
        row = list(worksheet[idx])
        for cell in row:
            if cell.value:
                cell_value = str(cell.value).lower().strip()
                if 'фио' in cell_value or 'студент' in cell_value:
                    header_rows.append(idx)
                    break
    
    if not header_rows:
        return data
    
    # Список заголовков, которые не являются студентами
    header_keywords = [
        'месяц/число', 'фио обучающихся', 'фио', 'кол-во часов', 
        'количество часов', 'часы', 'студент', 'обучающийся',
        'фамилия', 'имя', 'отчество', 'дата', 'оценка', 'пропуск'
    ]
    
    def is_header_row(fio_text):
        """Проверяет, является ли строка заголовком, а не студентом"""
        fio_lower = fio_text.lower().strip()
        # Если содержит ключевые слова заголовков
        if any(keyword in fio_lower for keyword in header_keywords):
            return True
        # Если слишком короткое или содержит только цифры/символы
        if len(fio_lower) < 3:
            return True
        # Если содержит только цифры или специальные символы
        if fio_lower.replace(' ', '').replace('.', '').replace('-', '').isdigit():
            return True
        return False
    
    # Парсим каждый найденный журнал
    for journal_idx, header_row_idx in enumerate(header_rows):
        # Определяем границы журнала
        # Начало: строка после заголовка
        start_row = header_row_idx + 1
        # Конец: следующий заголовок или конец листа
        if journal_idx + 1 < len(header_rows):
            end_row = header_rows[journal_idx + 1]
        else:
            end_row = max_row + 1
        
        # Получаем строку заголовков
        header_row = list(worksheet[header_row_idx])
        student_col = find_student_column(header_row)
        date_columns = find_date_columns(header_row, worksheet, header_row_idx)
        
        if student_col is None:
            continue
        
        if not date_columns:
            continue
        
        # Парсим данные студентов в этом журнале
        for row_idx in range(start_row, end_row):
            row = list(worksheet[row_idx])
            
            if len(row) <= student_col:
                continue
            
            student_cell = row[student_col]
            if not student_cell or not student_cell.value:
                continue
            
            student_fio = str(student_cell.value).strip()
            
            # Пропускаем заголовки (на случай, если они повторяются)
            if is_header_row(student_fio):
                continue
            
            if not student_fio or len(student_fio) < 3:  # Минимум 3 символа для ФИО
                continue
            
            # Нормализуем ФИО (убираем лишние пробелы)
            student_fio = ' '.join(student_fio.split())
            
            # Преобразуем в формат "Фамилия И.О." если это полное ФИО
            student_fio = normalize_fio_to_initials(student_fio)
            
            # Парсим оценки для каждой даты
            for date_col_idx, date in date_columns:
                if len(row) > date_col_idx:
                    cell = row[date_col_idx]
                    grade_value = parse_grade_value(cell.value)
                    if grade_value:
                        data.append({
                            'group': group_name,
                            'subject': subject_name,
                            'fio': student_fio,
                            'date': date,
                            'grade': grade_value
                        })
    
    # Парсим таблицу с темами занятий (ищем по всему листу)
    topics_data = parse_topics_table(worksheet, group_name, subject_name, start_row=1)
    
    # Добавляем темы к данным (сохраняем как специальный тип данных)
    for topic in topics_data:
        data.append({
            'group': group_name,
            'subject': subject_name,
            'type': 'topic',  # Помечаем как тему
            'topic': topic['topic'],
            'hours': topic['hours'],
            'date': topic.get('date')
        })
    
    return data


def parse_excel_file(file_path):
    """
    Парсинг Excel файла
    
    Логика:
    1. Загружает файл
    2. Извлекает название группы из имени файла
    3. Пропускает первые SKIP_FIRST_SHEETS вкладок
    4. Парсит вкладки до STOP_SHEET_NAME
    5. Для каждой вкладки вызывает parse_sheet()
    6. Возвращает объединенные данные
    """
    
    try:
        # Загружаем файл с data_only=True для получения вычисленных значений
        # Но даты будем парсить специальным образом
        workbook = load_workbook(file_path, data_only=True)
        sheet_names = workbook.sheetnames
        
        # Извлекаем название группы из имени файла
        filename = os.path.basename(file_path)  # Получаем только имя файла
        group_name = filename.replace('Испп ', '').replace('.xslm', '').replace('.xlsx', '').replace('temp_', '')
        
        all_data = []
        
        # Пропускаем первые 3 вкладки
        start_idx = min(SKIP_FIRST_SHEETS, len(sheet_names))
        end_idx = len(sheet_names)
        
        # Находим индекс вкладки "УП технической разработки"
        for idx, sheet_name in enumerate(sheet_names):
            if STOP_SHEET_NAME.lower() in sheet_name.lower():
                end_idx = idx
                break
        
        if start_idx >= end_idx:
            workbook.close()
            return all_data
        
        # Парсим нужные вкладки (без вывода информации о парсинге)
        for idx in range(start_idx, end_idx):
            sheet_name = sheet_names[idx]
            worksheet = workbook[sheet_name]
            
            # Извлекаем название предмета из названия вкладки
            subject_name = sheet_name
            
            sheet_data = parse_sheet(worksheet, group_name, subject_name)
            all_data.extend(sheet_data)
        
        workbook.close()
        return all_data
        
    except Exception as e:
        print(f"Ошибка при парсинге файла {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return []


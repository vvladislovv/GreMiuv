"""
ПАРСЕР EXCEL ФАЙЛОВ
===================

Логика работы:
1. Загружает Excel файл (openpyxl)
2. Пропускает первые 3 вкладки (SKIP_FIRST_SHEETS)
3. Парсит вкладки до "УП технической разработки" (STOP_SHEET_NAME)
4. Для каждой вкладки:
   - Находит строку заголовков (поиск "ФИО")
   - Находит колонку с ФИО студентов
   - Находит колонки с датами
   - Извлекает данные: ФИО, дата, оценка/пропуск
5. Возвращает список словарей с данными

Функции:
- parse_excel_file() - главная функция парсинга файла
- parse_sheet() - парсинг одной вкладки
- parse_date() - парсинг даты из различных форматов
- parse_grade_value() - парсинг оценки/пропуска
- find_student_column() - поиск колонки с ФИО
- find_date_columns() - поиск колонок с датами
"""

import os
import re
from openpyxl import load_workbook
from datetime import datetime, date as date_type
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SKIP_FIRST_SHEETS, STOP_SHEET_NAME


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


def find_date_columns(header_row, worksheet, header_row_idx):
    """
    Поиск колонок с датами
    
    Логика:
    1. Ищет строку с месяцем/годом (обычно строка выше заголовков)
    2. Если находит месяц - использует его для построения полных дат
    3. Иначе пытается парсить даты напрямую из заголовков
    
    Возвращает список кортежей: (индекс_колонки, дата)
    """
    date_columns = []
    
    # Ищем месяц и год в строках выше заголовков
    month_year = None
    current_year = datetime.now().year
    
    # Проверяем строки выше заголовков (до 10 строк выше)
    for row_offset in range(1, min(11, header_row_idx)):
        check_row_idx = header_row_idx - row_offset
        if check_row_idx < 1:
            break
        
        check_row = list(worksheet[check_row_idx])
        row_text = ' '.join([str(cell.value) for cell in check_row if cell.value]).lower()
        
        # Ищем названия месяцев
        months = {
            'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
            'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
            'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
        }
        
        for month_name, month_num in months.items():
            if month_name in row_text:
                # Пытаемся найти год
                year = current_year
                # Ищем год в формате YYYY в любой ячейке строки
                for cell in check_row:
                    if cell.value:
                        cell_str = str(cell.value)
                        year_match = re.search(r'20\d{2}', cell_str)
                        if year_match:
                            year = int(year_match.group())
                            break
                
                month_year = (month_num, year)
                break
        
        if month_year:
            break
    
    # Парсим даты из заголовков
    for idx, cell in enumerate(header_row):
        if not cell.value:
            continue
        
        cell_value = cell.value
        
        # Если это число от 1 до 31 - это день месяца
        if isinstance(cell_value, (int, float)) and 1 <= cell_value <= 31:
            day = int(cell_value)
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


def parse_sheet(worksheet, group_name, subject_name):
    """
    Парсинг одного листа Excel
    
    Логика:
    1. Ищет строку заголовков (первые 20 строк, ищет "ФИО")
    2. Находит колонку с ФИО
    3. Находит колонки с датами
    4. Проходит по строкам и извлекает данные
    5. Возвращает список словарей с данными
    """
    data = []
    
    # Находим строку заголовков
    header_row_idx = None
    max_row = worksheet.max_row
    
    for idx in range(1, min(max_row + 1, 20)):  # Ищем в первых 20 строках
        row = list(worksheet[idx])
        for cell in row:
            if cell.value:
                cell_value = str(cell.value).lower().strip()
                if 'фио' in cell_value or 'студент' in cell_value:
                    header_row_idx = idx
                    break
        if header_row_idx:
            break
    
    if not header_row_idx:
        return data
    
    # Получаем строку заголовков
    header_row = list(worksheet[header_row_idx])
    student_col = find_student_column(header_row)
    date_columns = find_date_columns(header_row, worksheet, header_row_idx)
    
    if student_col is None:
        return data
    
    if not date_columns:
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
    
    # Парсим данные студентов
    for row_idx in range(header_row_idx + 1, max_row + 1):
        row = list(worksheet[row_idx])
        
        if len(row) <= student_col:
            continue
        
        student_cell = row[student_col]
        if not student_cell or not student_cell.value:
            continue
        
        student_fio = str(student_cell.value).strip()
        
        # Пропускаем заголовки
        if is_header_row(student_fio):
            continue
        
        if not student_fio or len(student_fio) < 3:  # Минимум 3 символа для ФИО
            continue
        
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


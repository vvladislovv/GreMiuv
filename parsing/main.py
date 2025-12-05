"""
ГЛАВНЫЙ ФАЙЛ ПРИЛОЖЕНИЯ
========================

Логика работы:
1. Проверяет время последнего обновления файлов
2. Если прошло больше 15 минут - скачивает новые файлы
3. Парсит Excel файлы (извлечение данных о студентах, оценках, датах)
4. Сохраняет метаданные (время обновления) в БД
5. Выводит подробно один предмет со всеми строками таблицы

Точка входа: main()
"""

import os
import sys
import re
import schedule
import time
from datetime import datetime, timedelta

# Добавляем папку parsing в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, UpdateLog, Group, Student, Subject, Grade
from downloaders.google_drive import download_target_files
from parsers.excel_parser import parse_excel_file
from config import PARSE_INTERVAL_MINUTES


def should_update_file(file_name):
    """
    Проверяет, нужно ли обновлять файл
    
    Логика:
    - Если файл не обновлялся или прошло больше PARSE_INTERVAL_MINUTES минут
    - Возвращает True если нужно обновить
    """
    db = get_db()
    try:
        log_entry = db.query(UpdateLog).filter(UpdateLog.file_name == file_name).first()
        
        if not log_entry:
            # Файл еще не обновлялся
            return True
        
        # Проверяем, прошло ли достаточно времени
        time_diff = datetime.now() - log_entry.last_update_time
        minutes_passed = time_diff.total_seconds() / 60
        
        return minutes_passed >= PARSE_INTERVAL_MINUTES
    finally:
        db.close()


def save_update_log(file_name):
    """Сохраняет время последнего обновления файла в БД"""
    db = get_db()
    try:
        log_entry = db.query(UpdateLog).filter(UpdateLog.file_name == file_name).first()
        
        if log_entry:
            # Обновляем время
            log_entry.last_update_time = datetime.now()
        else:
            # Создаем новую запись
            log_entry = UpdateLog(
                file_name=file_name,
                last_update_time=datetime.now()
            )
            db.add(log_entry)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении лога обновления: {e}")
    finally:
        db.close()


def save_to_database(parsed_data_per_file):
    """
    Сохраняет распарсенные данные в БД
    
    Логика:
    1. Для каждого файла получает данные
    2. Создает/обновляет группы, студентов, предметы
    3. Сохраняет оценки/пропуски
    """
    db = get_db()
    try:
        # Заголовки, которые не являются студентами
        header_keywords = [
            'месяц/число', 'фио обучающихся', 'фио', 'кол-во часов', 
            'количество часов', 'часы', 'студент', 'обучающийся'
        ]
        
        def is_valid_student(fio):
            """Проверяет, является ли запись валидным студентом"""
            if not fio:
                return False
            fio_lower = str(fio).lower().strip()
            if any(keyword in fio_lower for keyword in header_keywords):
                return False
            if len(fio_lower) < 3:
                return False
            return True
        
        for file_name, all_data in parsed_data_per_file.items():
            if not all_data:
                continue
            
            # Группируем данные по группам
            groups_data = {}
            for item in all_data:
                if not is_valid_student(item.get('fio')):
                    continue
                
                group_name = item['group']
                if group_name not in groups_data:
                    groups_data[group_name] = {}
                
                subject_name = item['subject']
                if subject_name not in groups_data[group_name]:
                    groups_data[group_name][subject_name] = []
                
                groups_data[group_name][subject_name].append(item)
            
            # Сохраняем в БД
            for group_name, subjects_data in groups_data.items():
                # Создаем или получаем группу
                group = db.query(Group).filter(Group.name == group_name).first()
                if not group:
                    group = Group(name=group_name)
                    db.add(group)
                    db.flush()
                
                # Обрабатываем предметы
                for subject_name, items in subjects_data.items():
                    # Создаем или получаем предмет
                    subject = db.query(Subject).filter(
                        Subject.name == subject_name,
                        Subject.group_id == group.id
                    ).first()
                    if not subject:
                        subject = Subject(name=subject_name, group_id=group.id)
                        db.add(subject)
                        db.flush()
                    
                    # Обрабатываем студентов и оценки
                    students_map = {}  # ФИО -> Student объект
                    for item in items:
                        fio = item['fio']
                        date = item['date']
                        grade_value = item.get('grade', '')
                        
                        # Пропускаем некорректные даты
                        if not date or (hasattr(date, 'year') and date.year < 2000):
                            continue
                        
                        # Создаем или получаем студента
                        if fio not in students_map:
                            student = db.query(Student).filter(
                                Student.fio == fio,
                                Student.group_id == group.id
                            ).first()
                            if not student:
                                student = Student(fio=fio, group_id=group.id)
                                db.add(student)
                                db.flush()
                            students_map[fio] = student
                        else:
                            student = students_map[fio]
                        
                        # Проверяем, нет ли уже такой оценки
                        existing_grade = db.query(Grade).filter(
                            Grade.student_id == student.id,
                            Grade.subject_id == subject.id,
                            Grade.date == date
                        ).first()
                        
                        if not existing_grade:
                            # Создаем новую оценку
                            grade = Grade(
                                student_id=student.id,
                                subject_id=subject.id,
                                date=date,
                                value=str(grade_value)
                            )
                            db.add(grade)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении данных в БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def print_detailed_subject(parsed_data_per_file):
    """
    Вывод подробной информации по одному предмету из каждого файла в виде таблицы
    
    Логика:
    - Для каждого файла берет первый предмет
    - Выводит все строки таблицы: ФИО | Дата | Оценка/Пропуск
    - Добавляет статистику: количество пропусков, оценок, посещаемость
    """
    if not parsed_data_per_file:
        return
    
    # Заголовки, которые не являются студентами
    header_keywords = [
        'месяц/число', 'фио обучающихся', 'фио', 'кол-во часов', 
        'количество часов', 'часы', 'студент', 'обучающийся'
    ]
    
    def is_valid_student(fio):
        """Проверяет, является ли запись валидным студентом"""
        if not fio:
            return False
        fio_lower = str(fio).lower().strip()
        if any(keyword in fio_lower for keyword in header_keywords):
            return False
        if len(fio_lower) < 3:
            return False
        return True
    
    # Обрабатываем каждый файл
    for file_name, all_data_from_file in parsed_data_per_file.items():
        if not all_data_from_file:
            continue
        
        # Группируем данные по группам и предметам
        groups_data = {}
        for item in all_data_from_file:
            # Фильтруем заголовки
            if not is_valid_student(item.get('fio')):
                continue
            
            group_name = item['group']
            subject_name = item['subject']
            
            if group_name not in groups_data:
                groups_data[group_name] = {}
            if subject_name not in groups_data[group_name]:
                groups_data[group_name][subject_name] = []
            
            groups_data[group_name][subject_name].append(item)
        
        if not groups_data:
            continue
        
        # Берем первый предмет из первой группы
        first_group = list(groups_data.keys())[0]
        subjects = groups_data[first_group]
        if not subjects:
            continue
        
        first_subject = list(subjects.keys())[0]
        subject_data = subjects[first_subject]
        
        # Фильтруем записи с валидными датами и исключаем даты в оценках
        valid_data = []
        for item in subject_data:
            date = item['date']
            grade = str(item.get('grade', '')).strip()
            
            # Пропускаем записи, где оценка содержит дату (формат YYYY-MM-DD)
            if re.match(r'^\d{4}-\d{2}-\d{2}', grade):
                continue
            
            # Пропускаем записи, где оценка содержит дату с временем
            if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}', grade):
                continue
            
            # Проверяем валидность даты
            if date and hasattr(date, 'year') and date.year >= 2000:
                valid_data.append(item)
            elif date and isinstance(date, str) and '202' in str(date):
                valid_data.append(item)
        
        if not valid_data:
            continue
        
        # Группируем по студентам для статистики
        students_data = {}
        for item in valid_data:
            fio = item['fio']
            if fio not in students_data:
                students_data[fio] = {
                    'records': [],
                    'absences': 0,
                    'grades': 0,
                    'total': 0
                }
            
            students_data[fio]['records'].append(item)
            students_data[fio]['total'] += 1
            
            grade = str(item['grade']).lower()
            if 'пропуск' in grade or grade in ['н', 'н/я', 'неявка']:
                students_data[fio]['absences'] += 1
            else:
                students_data[fio]['grades'] += 1
        
        # Выводим только статистику по каждому студенту
        print("\n" + "="*120)
        print(f"ПРЕДМЕТ: {first_subject} | ГРУППА: {first_group} | ФАЙЛ: {file_name}")
        print("="*120)
        print(f"{'ФИО':<45} | {'Пропусков':<12} | {'Оценок':<12} | {'Всего':<12} | {'Посещаемость':<15}")
        print("-"*120)
        
        for fio in sorted(students_data.keys()):
            stats = students_data[fio]
            total = stats['total']
            absences = stats['absences']
            grades = stats['grades']
            
            # Вычисляем посещаемость в процентах
            if total > 0:
                attendance = ((total - absences) / total) * 100
                attendance_str = f"{attendance:.1f}%"
            else:
                attendance_str = "0%"
            
            fio_short = fio[:43]
            print(f"{fio_short:<45} | {absences:<12} | {grades:<12} | {total:<12} | {attendance_str:<15}")
        
        print("="*120)


def parse_and_save():
    """
    Основная функция парсинга и сохранения
    
    Логика работы:
    1. Проверяет время последнего обновления
    2. Если нужно - скачивает новые файлы
    3. Парсит Excel файлы
    4. Сохраняет метаданные в БД
    5. Выводит подробные результаты
    """
    downloaded_files = []
    
    try:
        # Проверяем, нужно ли обновлять файлы
        from config import TARGET_FILES
        
        need_update = False
        for file_name in TARGET_FILES:
            if should_update_file(file_name):
                need_update = True
                break
        
        if not need_update:
            # Используем существующие файлы из папки data/downloaded_files
            # Путь относительно корня проекта
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            download_dir = os.path.join(base_dir, "data", "downloaded_files")
            if os.path.exists(download_dir):
                for file_name in TARGET_FILES:
                    file_path = os.path.join(download_dir, file_name)
                    if os.path.exists(file_path):
                        downloaded_files.append(file_path)
        else:
            # Скачиваем файлы (сообщения о скачивании/удалении выводятся в download_target_files)
            try:
                downloaded_files = download_target_files()
            except Exception as e:
                return
            
            if not downloaded_files:
                return
        
        # Парсим файлы
        parsed_data_per_file = {}
        for file_path in downloaded_files:
            try:
                data = parse_excel_file(file_path)
                file_name = os.path.basename(file_path)
                parsed_data_per_file[file_name] = data
                
                # Сохраняем время обновления для каждого файла
                save_update_log(file_name)
                
            except Exception as e:
                pass
        
        # Сохраняем данные в БД
        if parsed_data_per_file:
            save_to_database(parsed_data_per_file)
        
        # Выводим только статистику по одному предмету из каждого файла
        if parsed_data_per_file:
            print_detailed_subject(parsed_data_per_file)
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass


def main():
    """
    Главная функция - точка входа в приложение
    
    Логика:
    1. Инициализация БД
    2. Первый запуск парсинга
    3. Настройка автоматического обновления каждые 15 минут
    4. Запуск планировщика
    """
    init_db()
    
    # Выполняем первый парсинг сразу
    parse_and_save()
    
    # Настраиваем автоматический запуск каждые 15 минут
    schedule.every(PARSE_INTERVAL_MINUTES).minutes.do(parse_and_save)
    
    # Запускаем планировщик
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту


if __name__ == "__main__":
    main()

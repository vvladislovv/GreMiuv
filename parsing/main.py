"""
ГЛАВНЫЙ ФАЙЛ ПРИЛОЖЕНИЯ
========================

Логика работы:
1. Скачивает файлы с Google Drive
2. Парсит Excel файлы (извлечение данных о студентах, оценках, датах)
3. Удаляет старые данные для обновляемых групп
4. Сохраняет новые данные в БД
5. Сохраняет информацию о парсинге в таблицу ParseLog
6. Выводит сообщение о завершении парсинга в консоль
7. Автоматически обновляется раз в час
   (в 00 минут каждого часа)

Точка входа: main()
"""

import os
import sys
import re
import json
import schedule
import time
from datetime import datetime, timedelta

# Добавляем папку parsing в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, Group, Student, Subject, Grade, Topic, ParseLog
from downloaders.google_drive import download_target_files
from parsers.excel_parser import parse_excel_file
from logger import log_parser_info, log_parser_error


def save_to_database(parsed_data_per_file):
    """
    Сохраняет распарсенные данные в БД
    
    Логика:
    1. Собирает все группы, которые будут обновлены
    2. Удаляет все старые данные (оценки, студентов, предметы) для этих групп
    3. Сохраняет новые данные
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
        
        # Сначала собираем все группы, которые будут обновлены
        groups_to_update = set()
        groups_data = {}
        
        for file_name, all_data in parsed_data_per_file.items():
            if not all_data:
                continue
            
            # Группируем данные по группам
            for item in all_data:
                group_name = item['group']
                groups_to_update.add(group_name)
                
                if group_name not in groups_data:
                    groups_data[group_name] = {}
                
                subject_name = item['subject']
                if subject_name not in groups_data[group_name]:
                    groups_data[group_name][subject_name] = []
                
                # Добавляем все элементы (включая темы, статистику, даже если нет ФИО)
                # Для тем и статистики проверка is_valid_student не нужна
                if item.get('type') == 'topic' or item.get('type') == 'statistics' or is_valid_student(item.get('fio')):
                    groups_data[group_name][subject_name].append(item)
        
        # Удаляем все старые данные для обновляемых групп
        for group_name in groups_to_update:
            group = db.query(Group).filter(Group.name == group_name).first()
            if group:
                # Удаляем все оценки студентов этой группы
                students_in_group = db.query(Student).filter(Student.group_id == group.id).all()
                for student in students_in_group:
                    db.query(Grade).filter(Grade.student_id == student.id).delete()
                
                # Удаляем всех студентов группы
                db.query(Student).filter(Student.group_id == group.id).delete()
                
                # Удаляем все темы предметов группы
                subjects_in_group = db.query(Subject).filter(Subject.group_id == group.id).all()
                for subject in subjects_in_group:
                    db.query(Topic).filter(Topic.subject_id == subject.id).delete()
                
                # Удаляем все предметы группы
                db.query(Subject).filter(Subject.group_id == group.id).delete()
                
                # Удаляем саму группу
                db.delete(group)
        
        db.flush()
        
        # Сохраняем новые данные
        for group_name, subjects_data in groups_data.items():
            # Создаем новую группу
            group = Group(name=group_name)
            db.add(group)
            db.flush()
            
            # Импортируем функцию нормализации ФИО
            from parsers.excel_parser import normalize_fio_to_initials
            
            # Сначала собираем всех уникальных студентов для группы
            # Это нужно сделать до обработки предметов, чтобы не создавать дубликаты
            all_students_fio = set()
            for subject_name, items in subjects_data.items():
                for item in items:
                    fio = item.get('fio', '')
                    if fio:
                        fio_normalized = normalize_fio_to_initials(str(fio).strip())
                        if fio_normalized and len(fio_normalized) >= 3:
                            all_students_fio.add(fio_normalized)
            
            # Создаем всех студентов группы один раз
            students_map = {}  # ФИО -> Student объект
            for fio_normalized in all_students_fio:
                # Проверяем, не существует ли уже такой студент (на случай если БД не пересоздана)
                existing_student = db.query(Student).filter(
                    Student.fio == fio_normalized,
                    Student.group_id == group.id
                ).first()
                
                if existing_student:
                    students_map[fio_normalized] = existing_student
                else:
                    student = Student(fio=fio_normalized, group_id=group.id)
                    db.add(student)
                    students_map[fio_normalized] = student
            
            db.flush()  # Сохраняем всех студентов перед созданием оценок
            
            # Теперь обрабатываем предметы и оценки
            for subject_name, items in subjects_data.items():
                # Создаем новый предмет
                subject = Subject(name=subject_name, group_id=group.id)
                db.add(subject)
                db.flush()
                
                # Отделяем темы от оценок и статистики
                topics_items = [item for item in items if item.get('type') == 'topic']
                statistics_items = [item for item in items if item.get('type') == 'statistics']
                grades_items = [item for item in items if item.get('type') != 'topic' and item.get('type') != 'statistics' and item.get('fio')]
                
                # Сохраняем темы занятий
                for topic_item in topics_items:
                    topic_name = topic_item.get('topic', '').strip()
                    if topic_name and len(topic_name) >= 3:
                        # Проверяем, не существует ли уже такая тема
                        existing_topic = db.query(Topic).filter(
                            Topic.subject_id == subject.id,
                            Topic.name == topic_name
                        ).first()
                        
                        if not existing_topic:
                            topic = Topic(
                                subject_id=subject.id,
                                name=topic_name,
                                hours=topic_item.get('hours', 2),
                                date=topic_item.get('date')
                            )
                            db.add(topic)
                
                db.flush()
                
                # Обрабатываем оценки (только те, что не являются темами)
                for item in grades_items:
                    fio = item.get('fio', '')
                    date = item.get('date')
                    grade_value = item.get('grade', '')
                    
                    # КРИТИЧЕСКИ ВАЖНО: Строгие проверки валидности данных
                    # Пропускаем некорректные даты
                    if not date:
                        continue
                    
                    # Проверяем, что дата валидна (год >= 2000, месяц 1-12, день 1-31)
                    if hasattr(date, 'year'):
                        if date.year < 2000 or date.year > 2100:
                            continue
                        if date.month < 1 or date.month > 12:
                            continue
                        if date.day < 1 or date.day > 31:
                            continue
                    else:
                        continue
                    
                    # Проверяем, что оценка не пустая
                    if not grade_value or str(grade_value).strip() == '':
                        continue
                    
                    # Проверяем, что ФИО не пустое
                    if not fio or str(fio).strip() == '':
                        continue
                    
                    # Нормализуем ФИО в формат "Фамилия И.О."
                    fio_normalized = normalize_fio_to_initials(str(fio).strip())
                    
                    # Проверяем, что нормализованное ФИО валидно
                    if not fio_normalized or len(fio_normalized) < 3:
                        continue
                    
                    # Получаем студента из словаря (он уже должен быть создан)
                    student = students_map.get(fio_normalized)
                    if not student:
                        continue  # Пропускаем если студент не найден (не должен случиться)
                    
                    # Проверяем, не существует ли уже такая оценка (на случай дубликатов)
                    existing_grade = db.query(Grade).filter(
                        Grade.student_id == student.id,
                        Grade.subject_id == subject.id,
                        Grade.date == date
                    ).first()
                    
                    if not existing_grade:
                        # Создаем оценку только если её еще нет
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
    finally:
        db.close()


def parse_and_save():
    """
    Основная функция парсинга и сохранения
    
    Логика работы:
    1. Скачивает новые файлы с Google Drive
    2. Парсит Excel файлы
    3. Удаляет старые данные и сохраняет новые в БД
    4. Сохраняет информацию о парсинге в таблицу ParseLog
    """
    parse_start_time = datetime.now()
    files_processed = 0
    groups_updated_list = []
    status = "success"
    error_message = None
    
    try:
        print("=" * 60, flush=True)
        print(f"🔄 [PARSER] Начало парсинга: {parse_start_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print("=" * 60, flush=True)
        log_parser_info(
            "Начало парсинга",
            "Запуск процесса парсинга Excel файлов с Google Drive"
        )
        
        # Скачиваем файлы
        print("📥 [PARSER] Скачивание файлов с Google Drive...", flush=True)
        downloaded_files = download_target_files()
        
        if not downloaded_files:
            status = "error"
            error_message = "Файлы не были скачаны"
            print("❌ [PARSER] Файлы не были скачаны", flush=True)
            log_parser_error(
                "Файлы не были скачаны",
                description="Не удалось скачать файлы с Google Drive"
            )
            return
        
        print(f"✅ [PARSER] Скачано файлов: {len(downloaded_files)}", flush=True)
        for f in downloaded_files:
            print(f"   📄 [PARSER] - {os.path.basename(f)}", flush=True)
        log_parser_info(
            f"Скачано файлов: {len(downloaded_files)}",
            f"Файлы: {', '.join([os.path.basename(f) for f in downloaded_files])}"
        )
        
        # Парсим файлы
        print("📊 [PARSER] Начало парсинга Excel файлов...", flush=True)
        parsed_data_per_file = {}
        for file_path in downloaded_files:
            try:
                file_name = os.path.basename(file_path)
                print(f"   🔍 [PARSER] Обработка файла: {file_name}...", flush=True)
                log_parser_info(
                    f"Парсинг файла: {file_name}",
                    f"Обработка Excel файла"
                )
                
                data = parse_excel_file(file_path)
                parsed_data_per_file[file_name] = data
                files_processed += 1
                
                print(f"   ✅ [PARSER] Файл обработан: {file_name} (записей: {len(data)})", flush=True)
                log_parser_info(
                    f"Файл обработан: {file_name}",
                    f"Найдено записей: {len(data)}"
                )
            except Exception as e:
                error_message = f"Ошибка при парсинге {file_path}: {str(e)}"
                log_parser_error(
                    f"Ошибка при парсинге {os.path.basename(file_path)}",
                    error=e,
                    description=f"Не удалось распарсить файл: {file_path}"
                )
        
        # Сохраняем данные в БД
        if parsed_data_per_file:
            # Получаем список обновленных групп
            groups_updated_list = list(set(
                item.get('group') 
                for file_data in parsed_data_per_file.values() 
                for item in file_data 
                if item.get('group')
            ))
            
            print(f"💾 [PARSER] Сохранение данных в БД...", flush=True)
            print(f"   👥 [PARSER] Групп для обновления: {len(groups_updated_list)}", flush=True)
            if groups_updated_list:
                print(f"   📋 [PARSER] Группы: {', '.join(groups_updated_list)}", flush=True)
            log_parser_info(
                f"Сохранение данных в БД",
                f"Обновление групп: {', '.join(groups_updated_list) if groups_updated_list else 'нет'}"
            )
            
            save_to_database(parsed_data_per_file)
            
            print(f"✅ [PARSER] Данные сохранены в БД", flush=True)
            log_parser_info(
                f"Данные сохранены в БД",
                f"Обновлено групп: {len(groups_updated_list)}"
            )
        
        # Сохраняем информацию о парсинге в таблицу
        db = get_db()
        try:
            parse_log = ParseLog(
                parse_time=parse_start_time,
                files_processed=files_processed,
                groups_updated=json.dumps(groups_updated_list, ensure_ascii=False) if groups_updated_list else None,
                status=status,
                error_message=error_message
            )
            db.add(parse_log)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
        
        # Выводим сообщение о завершении парсинга
        parse_end_time = datetime.now()
        duration = (parse_end_time - parse_start_time).total_seconds()
        groups_str = ", ".join(groups_updated_list) if groups_updated_list else "нет"
        
        log_parser_info(
            "Парсинг завершен успешно",
            f"Обработано файлов: {files_processed}, обновлено групп: {len(groups_updated_list)}, длительность: {duration:.2f} сек",
            details={
                "files_processed": files_processed,
                "groups_count": len(groups_updated_list),
                "groups": groups_updated_list,
                "duration_seconds": duration
            }
        )
        
        print("=" * 60, flush=True)
        print(f"✅ [PARSER] Парсинг завершен успешно!", flush=True)
        print(f"   📅 [PARSER] Время: {parse_end_time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"   ⏱️  [PARSER] Длительность: {duration:.2f} сек", flush=True)
        print(f"   📁 [PARSER] Файлов обработано: {files_processed}", flush=True)
        print(f"   👥 [PARSER] Групп обновлено: {len(groups_updated_list)} ({groups_str})", flush=True)
        print(f"   💾 [PARSER] Данные сохранены в БД", flush=True)
        print("=" * 60, flush=True)
        print("", flush=True)
        
    except KeyboardInterrupt:
        status = "error"
        error_message = "Парсинг прерван пользователем"
        log_parser_error(
            "Парсинг прерван пользователем",
            description="Пользователь остановил процесс парсинга"
        )
        # Сохраняем информацию об ошибке
        db = get_db()
        try:
            parse_log = ParseLog(
                parse_time=parse_start_time,
                files_processed=files_processed,
                groups_updated=None,
                status=status,
                error_message=error_message
            )
            db.add(parse_log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception as e:
        status = "error"
        error_message = str(e)
        log_parser_error(
            f"Ошибка при парсинге: {error_message}",
            error=e,
            description="Критическая ошибка в процессе парсинга"
        )
        # Сохраняем информацию об ошибке
        db = get_db()
        try:
            parse_log = ParseLog(
                parse_time=parse_start_time,
                files_processed=files_processed,
                groups_updated=None,
                status=status,
                error_message=error_message
            )
            db.add(parse_log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        print("=" * 60, flush=True)
        print(f"❌ [PARSER] Ошибка при парсинге: {error_message}", flush=True)
        print("=" * 60, flush=True)
        print("", flush=True)


def main():
    """
    Главная функция - точка входа в приложение
    
    Логика:
    1. Инициализация БД
    2. Первый запуск парсинга
    3. Настройка автоматического обновления раз в час
       (в 00 минут каждого часа)
    4. Запуск планировщика
    """
    init_db()
    
    # Выполняем первый парсинг сразу (без вывода)
    parse_and_save()
    
    # Настраиваем автоматический запуск раз в час
    # Запуск в 00 минут каждого часа
    schedule.every().hour.at(":00").do(parse_and_save)
    
    # Запускаем планировщик
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту


if __name__ == "__main__":
    main()

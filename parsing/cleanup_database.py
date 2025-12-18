"""
Скрипт для очистки дубликатов в базе данных

Использование:
    python cleanup_database.py

Логика:
    1. Находит всех студентов-дубликатов (одинаковое ФИО в одной группе)
    2. Оставляет одного студента (с минимальным ID)
    3. Переносит все оценки от дубликатов к оставшемуся студенту
    4. Удаляет дубликаты студентов
    5. Пересоздает таблицы с уникальными индексами
"""

import sys
import os
from pathlib import Path

# Добавляем путь к parsing для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, Student, Grade, Group, Subject
from sqlalchemy import func


def cleanup_duplicates():
    """
    Очищает дубликаты студентов в базе данных
    """
    db = get_db()
    try:
        print("🔍 Поиск дубликатов студентов...")
        
        # Находим всех студентов-дубликатов (одинаковое ФИО в одной группе)
        duplicates_query = db.query(
            Student.fio,
            Student.group_id,
            func.count(Student.id).label('count')
        ).group_by(
            Student.fio,
            Student.group_id
        ).having(
            func.count(Student.id) > 1
        ).all()
        
        if not duplicates_query:
            print("✅ Дубликатов не найдено!")
            return
        
        print(f"📊 Найдено {len(duplicates_query)} групп дубликатов")
        
        total_removed = 0
        
        for fio, group_id, count in duplicates_query:
            print(f"\n🔄 Обработка: {fio} (группа {group_id}), дубликатов: {count}")
            
            # Находим всех студентов с таким ФИО в этой группе
            students = db.query(Student).filter(
                Student.fio == fio,
                Student.group_id == group_id
            ).order_by(Student.id).all()
            
            if len(students) <= 1:
                continue
            
            # Оставляем первого студента (с минимальным ID)
            main_student = students[0]
            duplicates = students[1:]
            
            print(f"   ✅ Оставляем студента ID={main_student.id}")
            print(f"   ❌ Удаляем {len(duplicates)} дубликатов")
            
            # Переносим все оценки от дубликатов к основному студенту
            for duplicate in duplicates:
                # Получаем все оценки дубликата
                duplicate_grades = db.query(Grade).filter(
                    Grade.student_id == duplicate.id
                ).all()
                
                transferred = 0
                skipped = 0
                
                for grade in duplicate_grades:
                    # Проверяем, нет ли уже такой оценки у основного студента
                    existing = db.query(Grade).filter(
                        Grade.student_id == main_student.id,
                        Grade.subject_id == grade.subject_id,
                        Grade.date == grade.date
                    ).first()
                    
                    if existing:
                        # Если оценка уже есть, удаляем дубликат
                        db.delete(grade)
                        skipped += 1
                    else:
                        # Переносим оценку к основному студенту
                        grade.student_id = main_student.id
                        transferred += 1
                
                print(f"      📝 Перенесено оценок: {transferred}, пропущено дубликатов: {skipped}")
                
                # Удаляем дубликат студента
                db.delete(duplicate)
                total_removed += 1
            
            db.flush()
        
        db.commit()
        print(f"\n✅ Очистка завершена! Удалено {total_removed} дубликатов студентов")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при очистке: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def recreate_database():
    """
    Пересоздает базу данных с нуля (удаляет все данные!)
    """
    db = get_db()
    try:
        print("⚠️  ВНИМАНИЕ: Это удалит ВСЕ данные из базы!")
        response = input("Продолжить? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Отменено")
            return
        
        print("🗑️  Удаление всех таблиц...")
        
        # Удаляем все таблицы
        from database import Base, engine
        Base.metadata.drop_all(engine)
        
        print("✅ Таблицы удалены")
        print("🔨 Создание новых таблиц с уникальными индексами...")
        
        # Создаем таблицы заново
        init_db()
        
        print("✅ База данных пересоздана!")
        print("💡 Теперь запустите парсинг для заполнения базы данных")
        
    except Exception as e:
        print(f"❌ Ошибка при пересоздании БД: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """
    Главная функция
    """
    print("=" * 60)
    print("ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    print()
    print("Выберите действие:")
    print("1. Очистить дубликаты (безопасно, сохраняет данные)")
    print("2. Пересоздать БД с нуля (удалит ВСЕ данные!)")
    print("3. Выход")
    print()
    
    choice = input("Ваш выбор (1-3): ").strip()
    
    if choice == '1':
        cleanup_duplicates()
    elif choice == '2':
        recreate_database()
    elif choice == '3':
        print("👋 Выход")
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()







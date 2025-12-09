"""
Роуты для работы с данными конкретного студента по ФИО
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import sys
from pathlib import Path
from datetime import datetime, date

# Добавляем путь к parsing для импорта моделей
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
parsing_path_str = str(parsing_path)
if parsing_path_str not in sys.path:
    sys.path.insert(0, parsing_path_str)

from database import get_db, Student, Subject, Grade, Group, TelegramUser
from backend.utils.helpers import date_to_str
from backend.utils.auth import verify_token
from backend.utils.telegram_auth import verify_telegram_user
from sqlalchemy import func

router = APIRouter(prefix="/api/student", tags=["student"])


def find_student_by_fio(db: Session, fio: str) -> Student:
    """
    Вспомогательная функция для поиска студента по ФИО с гибким поиском
    
    Args:
        db: Сессия базы данных
        fio: ФИО студента
    
    Returns:
        Student: Найденный студент
    
    Raises:
        HTTPException: Если студент не найден
    """
    # Нормализуем ФИО для поиска (убираем лишние пробелы, приводим к единому формату)
    fio_normalized = ' '.join(fio.strip().split())
    
    # Ищем студента по ФИО (точное совпадение после нормализации)
    student = db.query(Student).filter(Student.fio == fio_normalized).first()
    
    # Если не найдено, пробуем поиск без учета регистра
    if not student:
        student = db.query(Student).filter(
            func.lower(Student.fio) == fio_normalized.lower()
        ).first()
    
    # Если все еще не найдено, пробуем поиск по частичному совпадению
    if not student:
        # Ищем по началу ФИО (фамилия и имя)
        parts = fio_normalized.split()
        if len(parts) >= 2:
            # Пробуем найти по фамилии и инициалам (если в базе "Фамилия И.О.", а ищут "Фамилия Имя Отчество")
            # Извлекаем фамилию и первую букву имени
            surname = parts[0]
            first_name_initial = parts[1][0].upper() if parts[1] else ''
            
            # Ищем по паттерну "Фамилия И.%"
            search_pattern = f"{surname} {first_name_initial}%"
            student = db.query(Student).filter(
                func.lower(Student.fio).like(search_pattern.lower())
            ).first()
            
            # Если не найдено, пробуем просто по фамилии и началу имени
            if not student:
                search_pattern = f"{parts[0]} {parts[1]}%"
                student = db.query(Student).filter(
                    func.lower(Student.fio).like(search_pattern.lower())
                ).first()
    
    if not student:
        # Пробуем найти похожие ФИО для подсказки
        parts = fio_normalized.split()
        search_term = parts[0] if parts else fio_normalized
        
        # Ищем похожие ФИО
        similar = db.query(Student).filter(
            func.lower(Student.fio).like(f"%{search_term.lower()}%")
        ).limit(10).all()
        
        # Также получаем несколько случайных студентов для примера
        all_students = db.query(Student).limit(20).all()
        
        similar_names = [s.fio for s in similar]
        example_names = [s.fio for s in all_students[:5] if s.fio not in similar_names]
        
        error_detail = f"Студент с ФИО '{fio}' не найден в базе данных."
        
        if similar_names:
            error_detail += f"\n\nПохожие ФИО (начинаются с '{search_term}'):\n" + "\n".join([f"  • {name}" for name in similar_names[:5]])
        
        if example_names:
            error_detail += f"\n\nПримеры ФИО из базы данных:\n" + "\n".join([f"  • {name}" for name in example_names[:5]])
        
        raise HTTPException(
            status_code=404,
            detail=error_detail
        )
    
    return student


@router.get("/by-fio")
async def get_student_by_fio(
    fio: str = Query(..., description="ФИО студента"),
    token: str = Depends(verify_token)
):
    """
    Получить информацию о студенте по ФИО
    
    Returns:
        dict: Информация о студенте с группами
    """
    db: Session = get_db()
    try:
        # Используем вспомогательную функцию для поиска
        student = find_student_by_fio(db, fio)
        
        # Получаем группу студента
        group = db.query(Group).filter(Group.id == student.group_id).first()
        
        return {
            "id": int(student.id),
            "fio": str(student.fio),
            "group_id": int(student.group_id),
            "group_name": str(group.name) if group else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()


@router.get("/subjects")
async def get_student_subjects(
    fio: str = Query(..., description="ФИО студента"),
    token: str = Depends(verify_token)
):
    """
    Получить все предметы студента по ФИО
    
    Returns:
        List[dict]: Список предметов с основной статистикой
    """
    db: Session = get_db()
    try:
        # Используем вспомогательную функцию для поиска
        student = find_student_by_fio(db, fio)
        
        # Получаем все предметы группы студента
        subjects = db.query(Subject).filter(
            Subject.group_id == student.group_id
        ).order_by(Subject.name).all()
        
        # Для каждого предмета считаем статистику
        subjects_data = []
        for subject in subjects:
            # Получаем все оценки студента по этому предмету
            grades = db.query(Grade).filter(
                Grade.student_id == student.id,
                Grade.subject_id == subject.id
            ).all()
            
            # Подсчитываем статистику
            total = len(grades)
            grades_count = sum(1 for g in grades if g.value and g.value.strip() and g.value.lower() not in ['пропуск', 'н', 'н/я'])
            absences = sum(1 for g in grades if g.value and (g.value.lower() in ['пропуск', 'н', 'н/я'] or not g.value.strip()))
            
            # Вычисляем посещаемость
            attendance = 0.0
            if total > 0:
                attendance = round((grades_count / total) * 100, 1)
            
            subjects_data.append({
                "id": int(subject.id),
                "name": str(subject.name),
                "group_id": int(subject.group_id),
                "stats": {
                    "total": total,
                    "grades": grades_count,
                    "absences": absences,
                    "attendance": attendance
                }
            })
        
        return subjects_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()


@router.get("/grades")
async def get_student_grades_by_subject(
    fio: str = Query(..., description="ФИО студента"),
    subject_id: int = Query(..., description="ID предмета"),
    token: str = Depends(verify_token)
):
    """
    Получить все оценки студента по конкретному предмету с датами
    
    Returns:
        dict: Данные в формате:
        {
            "subject": {...},
            "student": {...},
            "grades": [
                {"date": "2024-01-01", "value": "5"},
                ...
            ],
            "calendar": {
                "2024-01": [
                    {"date": "2024-01-01", "value": "5", "day": 1},
                    ...
                ]
            }
        }
    """
    db: Session = get_db()
    try:
        # Используем вспомогательную функцию для поиска
        student = find_student_by_fio(db, fio)
        
        # Проверяем предмет
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Предмет с ID {subject_id} не найден"
            )
        
        # Проверяем, что предмет принадлежит группе студента
        if subject.group_id != student.group_id:
            raise HTTPException(
                status_code=400,
                detail="Предмет не принадлежит группе студента"
            )
        
        # Получаем все оценки студента по предмету
        grades = db.query(Grade).filter(
            Grade.student_id == student.id,
            Grade.subject_id == subject_id
        ).order_by(Grade.date).all()
        
        # Формируем список оценок
        grades_list = []
        calendar_data = {}  # Группировка по месяцам
        
        for grade in grades:
            date_str = date_to_str(grade.date)
            grade_data = {
                "date": date_str,
                "value": grade.value
            }
            grades_list.append(grade_data)
            
            # Группируем по месяцам для календаря
            if isinstance(grade.date, date):
                month_key = grade.date.strftime("%Y-%m")
                if month_key not in calendar_data:
                    calendar_data[month_key] = []
                calendar_data[month_key].append({
                    "date": date_str,
                    "value": grade.value,
                    "day": grade.date.day
                })
        
        return {
            "subject": {
                "id": int(subject.id),
                "name": str(subject.name),
                "group_id": int(subject.group_id)
            },
            "student": {
                "id": int(student.id),
                "fio": str(student.fio),
                "group_id": int(student.group_id)
            },
            "grades": grades_list,
            "calendar": calendar_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()


@router.get("/stats")
async def get_student_overall_stats(
    fio: str = Query(..., description="ФИО студента"),
    token: str = Depends(verify_token)
):
    """
    Получить общую статистику студента по всем предметам
    
    Returns:
        dict: Общая статистика
    """
    db: Session = get_db()
    try:
        # Используем вспомогательную функцию для поиска
        student = find_student_by_fio(db, fio)
        
        # Получаем все оценки студента
        all_grades = db.query(Grade).filter(
            Grade.student_id == student.id
        ).all()
        
        # Получаем все предметы студента
        subjects = db.query(Subject).filter(
            Subject.group_id == student.group_id
        ).all()
        
        # Подсчитываем общую статистику
        total = len(all_grades)
        grades_count = sum(1 for g in all_grades if g.value and g.value.strip() and g.value.lower() not in ['пропуск', 'н', 'н/я'])
        absences = sum(1 for g in all_grades if g.value and (g.value.lower() in ['пропуск', 'н', 'н/я'] or not g.value.strip()))
        
        # Вычисляем средний балл (только числовые оценки)
        numeric_grades = []
        for g in all_grades:
            if g.value and g.value.strip():
                try:
                    grade_val = float(g.value)
                    if 2 <= grade_val <= 5:  # Валидные оценки
                        numeric_grades.append(grade_val)
                except ValueError:
                    pass
        
        avg_grade = round(sum(numeric_grades) / len(numeric_grades), 2) if numeric_grades else 0.0
        
        # Вычисляем посещаемость
        attendance = 0.0
        if total > 0:
            attendance = round((grades_count / total) * 100, 1)
        
        return {
            "student": {
                "id": int(student.id),
                "fio": str(student.fio),
                "group_id": int(student.group_id)
            },
            "stats": {
                "total_subjects": len(subjects),
                "total_lessons": total,
                "grades": grades_count,
                "absences": absences,
                "attendance": attendance,
                "average_grade": avg_grade
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()


@router.get("/fio-by-telegram-id")
async def get_fio_by_telegram_id(
    telegram_user: dict = Depends(verify_telegram_user)
):
    """
    Получить ФИО пользователя по telegram_id из initData
    
    Returns:
        dict: ФИО пользователя или None если не зарегистрирован
    """
    db: Session = get_db()
    try:
        telegram_id = telegram_user.get('user', {}).get('id')
        if not telegram_id:
            raise HTTPException(status_code=400, detail="telegram_id не найден в initData")
        
        user = db.query(TelegramUser).filter(
            TelegramUser.telegram_id == telegram_id
        ).first()
        
        if not user or not user.is_registered:
            return {"fio": None, "is_registered": False}
        
        return {
            "fio": user.full_name,
            "is_registered": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()


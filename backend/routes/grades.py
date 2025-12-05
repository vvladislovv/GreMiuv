"""
Роуты для работы с оценками
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Добавляем путь к parsing для импорта моделей (ВАЖНО: в начало списка!)
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
parsing_path_str = str(parsing_path)
if parsing_path_str not in sys.path:
    sys.path.insert(0, parsing_path_str)

from database import get_db, Student, Grade
from backend.utils.helpers import date_to_str
from typing import Optional

router = APIRouter(prefix="/api/grades", tags=["grades"])


@router.get("")
async def get_grades(subject_id: int, group_id: Optional[int] = None):
    """
    Получить оценки по предмету (и опционально по группе)
    
    Args:
        subject_id: ID предмета (обязательно, integer)
        group_id: ID группы (опционально, integer). Если не указан, берется из предмета
    
    Returns:
        dict: Данные в формате:
        {
            "dates": ["2024-01-01", "2024-01-02", ...],
            "students": [
                {
                    "id": 1,
                    "fio": "Иванов И.И.",
                    "grades": {
                        "2024-01-01": "5",
                        "2024-01-02": "пропуск",
                        ...
                    }
                },
                ...
            ]
        }
    
    Raises:
        HTTPException 404: Если предмет не найден или группа не совпадает
        HTTPException 500: При ошибке базы данных
    """
    db: Session = get_db()
    try:
        from database import Group, Subject
        
        # Проверяем существование предмета
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(
                status_code=404,
                detail=f"Предмет с ID {subject_id} не найден"
            )
        
        # Если group_id не указан, берем его из предмета
        if group_id is None:
            group_id = subject.group_id
        
        # Проверяем, что указанный group_id совпадает с group_id предмета
        if group_id != subject.group_id:
            raise HTTPException(
                status_code=404,
                detail=f"Предмет с ID {subject_id} не принадлежит группе {group_id}. Предмет принадлежит группе {subject.group_id}"
            )
        
        # Проверяем существование группы
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Группа с ID {group_id} не найдена"
            )
        
        # Получаем всех студентов группы
        students = db.query(Student).filter(
            Student.group_id == group_id
        ).order_by(Student.fio).all()
        
        # Получаем все оценки для предмета и студентов группы
        grades = db.query(Grade).join(Student).filter(
            Grade.subject_id == subject_id,
            Student.group_id == group_id
        ).order_by(Grade.date).all()
        
        # Собираем уникальные даты
        dates_set = set()
        for grade in grades:
            dates_set.add(grade.date)
        dates = sorted(list(dates_set))
        dates_str = [date_to_str(d) for d in dates]
        
        # Группируем оценки по студентам
        students_data = []
        for student in students:
            student_grades = {}
            for grade in grades:
                if grade.student_id == student.id:
                    date_str = date_to_str(grade.date)
                    student_grades[date_str] = grade.value
            
            students_data.append({
                "id": student.id,
                "fio": student.fio,
                "grades": student_grades
            })
        
        return {
            "dates": dates_str,
            "students": students_data
        }
    except HTTPException:
        # Пробрасываем HTTP исключения как есть
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении данных: {str(e)}")
    finally:
        db.close()

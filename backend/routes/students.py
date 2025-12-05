"""
Роуты для работы со студентами
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import sys
from pathlib import Path

# Добавляем путь к parsing для импорта моделей (ВАЖНО: в начало списка!)
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
parsing_path_str = str(parsing_path)
if parsing_path_str not in sys.path:
    sys.path.insert(0, parsing_path_str)

from database import get_db, Student

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("")
async def get_students(group_id: Optional[int] = None):
    """
    Получить список студентов
    
    Args:
        group_id: Опциональный ID группы для фильтрации
    
    Returns:
        List[dict]: Список студентов с id, fio и group_id
    """
    db: Session = get_db()
    try:
        query = db.query(Student)
        if group_id:
            query = query.filter(Student.group_id == group_id)
        students = query.order_by(Student.fio).all()
        return [{"id": s.id, "fio": s.fio, "group_id": s.group_id} for s in students]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

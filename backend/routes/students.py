"""
Роуты для работы со студентами
"""
from fastapi import APIRouter, HTTPException, Depends
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
from backend.utils.auth import verify_token

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("")
async def get_students(group_id: Optional[int] = None, token: str = Depends(verify_token)):
    """
    Получить список студентов
    
    Args:
        group_id: Опциональный ID группы для фильтрации (валидируется)
    
    Returns:
        List[dict]: Список студентов с id, fio и group_id
    """
    db: Session = get_db()
    try:
        # Валидация входных данных
        if group_id is not None:
            if not isinstance(group_id, int) or group_id <= 0:
                raise HTTPException(status_code=400, detail="Некорректный ID группы")
        
        # Используем параметризованные запросы для защиты от SQL инъекций
        query = db.query(Student)
        if group_id:
            query = query.filter(Student.group_id == int(group_id))
        students = query.order_by(Student.fio).all()
        return [{"id": int(s.id), "fio": str(s.fio), "group_id": int(s.group_id)} for s in students]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при получении данных")
    finally:
        db.close()

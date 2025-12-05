"""
Роуты для работы с предметами
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

from database import get_db, Subject
from backend.utils.auth import verify_token

router = APIRouter(prefix="/api/subjects", tags=["subjects"])


@router.get("")
async def get_subjects(group_id: Optional[int] = None, token: str = Depends(verify_token)):
    """
    Получить список предметов
    
    Args:
        group_id: Опциональный ID группы для фильтрации
    
    Returns:
        List[dict]: Список предметов с id, name и group_id
    """
    db: Session = get_db()
    try:
        query = db.query(Subject)
        if group_id:
            query = query.filter(Subject.group_id == group_id)
        subjects = query.order_by(Subject.name).all()
        return [{"id": s.id, "name": s.name, "group_id": s.group_id} for s in subjects]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

"""
Роуты для работы с группами
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
import sys
import os
from pathlib import Path

# Добавляем путь к parsing для импорта моделей (ВАЖНО: в начало списка!)
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
parsing_path_str = str(parsing_path)
if parsing_path_str not in sys.path:
    sys.path.insert(0, parsing_path_str)

# Теперь импортируем из parsing
from database import get_db, Group

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.get("")
async def get_groups():
    """
    Получить список всех групп
    
    Returns:
        List[dict]: Список групп с id и name
    """
    db: Session = get_db()
    try:
        groups = db.query(Group).order_by(Group.name).all()
        return [{"id": g.id, "name": g.name} for g in groups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

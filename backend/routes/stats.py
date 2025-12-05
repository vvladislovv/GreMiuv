"""
Роуты для работы со статистикой
"""
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List
import sys
from pathlib import Path

# Добавляем путь к parsing для импорта моделей (ВАЖНО: в начало списка!)
project_root = Path(__file__).parent.parent.parent
parsing_path = project_root / "parsing"
parsing_path_str = str(parsing_path)
if parsing_path_str not in sys.path:
    sys.path.insert(0, parsing_path_str)

from database import get_db, Student, Grade, Group

router = APIRouter(prefix="/api/stats", tags=["stats"])


# Pydantic модели для валидации ответов
class AbsenceRatingItem(BaseModel):
    """Элемент рейтинга по пропускам"""
    id: int = Field(..., description="ID студента")
    fio: str = Field(..., description="ФИО студента")
    absences: int = Field(..., ge=0, description="Количество пропусков")
    position: int = Field(..., ge=1, description="Позиция в рейтинге (от 1 до N)")


class GradeRatingItem(BaseModel):
    """Элемент рейтинга по оценкам"""
    id: int = Field(..., description="ID студента")
    fio: str = Field(..., description="ФИО студента")
    average_grade: float = Field(..., ge=0.0, le=5.0, description="Средний балл")
    total_grades: int = Field(..., ge=0, description="Общее количество оценок")
    position: int = Field(..., ge=1, description="Позиция в рейтинге (от 1 до N)")


@router.get("")
async def get_stats(group_id: int, subject_id: int):
    """
    Получить статистику по группе и предмету
    
    Args:
        group_id: ID группы
        subject_id: ID предмета
    
    Returns:
        List[dict]: Статистика посещаемости для каждого студента:
        [
            {
                "id": 1,
                "fio": "Иванов И.И.",
                "total": 10,
                "absences": 2,
                "grades": 8,
                "attendance": 80.0
            },
            ...
        ]
    """
    db: Session = get_db()
    try:
        students = db.query(Student).filter(
            Student.group_id == group_id
        ).order_by(Student.fio).all()
        
        stats = []
        for student in students:
            grades = db.query(Grade).filter(
                Grade.student_id == student.id,
                Grade.subject_id == subject_id
            ).all()
            
            total = len(grades)
            absences = sum(
                1 for g in grades 
                if 'пропуск' in str(g.value).lower() 
                or str(g.value).lower() in ['н', 'н/я', 'неявка']
            )
            grades_count = total - absences
            attendance = ((total - absences) / total * 100) if total > 0 else 0
            
            stats.append({
                "id": student.id,
                "fio": student.fio,
                "total": total,
                "absences": absences,
                "grades": grades_count,
                "attendance": round(attendance, 1)
            })
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/rating/absences", response_model=List[AbsenceRatingItem])
async def get_absences_rating(
    group_id: int = Query(..., gt=0, description="ID группы (должен быть положительным числом)")
):
    """
    Получить рейтинг группы по пропускам (по всем предметам)
    
    Args:
        group_id: ID группы (обязательно, положительное число)
    
    Returns:
        List[AbsenceRatingItem]: Рейтинг студентов по пропускам (от меньшего к большему):
        - Позиции идут строго от 1 до N
        - Студенты с одинаковым количеством пропусков получают одинаковую позицию
        - Следующий студент получает позицию с учетом пропусков
    
    Raises:
        HTTPException 404: Если группа не найдена
        HTTPException 422: Если group_id невалиден (не положительное число)
        HTTPException 500: При ошибке базы данных
    """
    db: Session = get_db()
    try:
        # Проверяем существование группы
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Группа с ID {group_id} не найдена"
            )
        
        students = db.query(Student).filter(
            Student.group_id == group_id
        ).all()
        
        if not students:
            return []
        
        rating = []
        for student in students:
            # Получаем все оценки студента по всем предметам
            grades = db.query(Grade).filter(
                Grade.student_id == student.id
            ).all()
            
            # Подсчитываем пропуски
            absences = sum(
                1 for g in grades 
                if 'пропуск' in str(g.value).lower() 
                or str(g.value).lower() in ['н', 'н/я', 'неявка']
            )
            
            rating.append({
                "id": student.id,
                "fio": student.fio,
                "absences": absences
            })
        
        # Сортируем по количеству пропусков (от меньшего к большему)
        rating.sort(key=lambda x: (x["absences"], x["fio"]))
        
        # Добавляем позицию в рейтинге с учетом одинаковых значений
        # Позиции идут строго от 1 до N, одинаковые значения получают одинаковую позицию
        for i, item in enumerate(rating):
            if i == 0:
                # Первый элемент всегда позиция 1
                item["position"] = 1
            elif rating[i-1]["absences"] == item["absences"]:
                # Если значение совпадает с предыдущим, позиция та же
                item["position"] = rating[i-1]["position"]
            else:
                # Если значение отличается, позиция = текущий индекс + 1
                item["position"] = i + 1
        
        # Валидация через Pydantic
        return [AbsenceRatingItem(**item) for item in rating]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении рейтинга: {str(e)}")
    finally:
        db.close()


@router.get("/rating/grades", response_model=List[GradeRatingItem])
async def get_grades_rating(
    group_id: int = Query(..., gt=0, description="ID группы (должен быть положительным числом)")
):
    """
    Получить рейтинг группы по оценкам (средний балл по всем предметам)
    
    Args:
        group_id: ID группы (обязательно, положительное число)
    
    Returns:
        List[GradeRatingItem]: Рейтинг студентов по среднему баллу (от большего к меньшему):
        - Позиции идут строго от 1 до N
        - Студенты с одинаковым средним баллом получают одинаковую позицию
        - Следующий студент получает позицию с учетом пропусков
    
    Raises:
        HTTPException 404: Если группа не найдена
        HTTPException 422: Если group_id невалиден (не положительное число)
        HTTPException 500: При ошибке базы данных
    """
    db: Session = get_db()
    try:
        # Проверяем существование группы
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=404,
                detail=f"Группа с ID {group_id} не найдена"
            )
        
        students = db.query(Student).filter(
            Student.group_id == group_id
        ).all()
        
        if not students:
            return []
        
        rating = []
        for student in students:
            # Получаем все оценки студента по всем предметам
            grades = db.query(Grade).filter(
                Grade.student_id == student.id
            ).all()
            
            # Извлекаем только числовые оценки (игнорируем пропуски)
            numeric_grades = []
            for g in grades:
                value_str = str(g.value).strip()
                # Проверяем, что это не пропуск
                if ('пропуск' not in value_str.lower() and 
                    value_str.lower() not in ['н', 'н/я', 'неявка']):
                    try:
                        # Пытаемся преобразовать в число
                        grade_num = float(value_str)
                        if 2 <= grade_num <= 5:  # Валидные оценки от 2 до 5
                            numeric_grades.append(grade_num)
                    except ValueError:
                        # Если не число, пропускаем
                        pass
            
            # Вычисляем средний балл
            if numeric_grades:
                average_grade = sum(numeric_grades) / len(numeric_grades)
            else:
                average_grade = 0.0
            
            rating.append({
                "id": student.id,
                "fio": student.fio,
                "average_grade": round(average_grade, 2),
                "total_grades": len(numeric_grades)
            })
        
        # Сортируем по среднему баллу (от большего к меньшему), при равенстве - по ФИО
        rating.sort(key=lambda x: (-x["average_grade"], x["fio"]))
        
        # Добавляем позицию в рейтинге с учетом одинаковых значений
        # Позиции идут строго от 1 до N, одинаковые значения получают одинаковую позицию
        for i, item in enumerate(rating):
            if i == 0:
                # Первый элемент всегда позиция 1
                item["position"] = 1
            elif rating[i-1]["average_grade"] == item["average_grade"]:
                # Если значение совпадает с предыдущим, позиция та же
                item["position"] = rating[i-1]["position"]
            else:
                # Если значение отличается, позиция = текущий индекс + 1
                item["position"] = i + 1
        
        # Валидация через Pydantic
        return [GradeRatingItem(**item) for item in rating]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении рейтинга: {str(e)}")
    finally:
        db.close()

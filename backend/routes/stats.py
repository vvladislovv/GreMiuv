"""
Роуты для работы со статистикой
"""
from fastapi import APIRouter, HTTPException, Query, Depends
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
from backend.utils.auth import verify_token

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
async def get_stats(group_id: int, subject_id: int, token: str = Depends(verify_token)):
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
    group_id: int = Query(..., gt=0, description="ID группы (должен быть положительным числом)"),
    token: str = Depends(verify_token)
):
    """
    Получить рейтинг группы по пропускам (от меньшего к большему)
    
    Args:
        group_id: ID группы (обязательно, положительное число)
    
    Returns:
        List[AbsenceRatingItem]: Рейтинг студентов по количеству пропусков (от меньшего к большему):
        - Позиции идут строго от 1 до N без повторений
        - Каждый студент получает уникальную позицию, даже при одинаковом количестве пропусков
    
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
        
        # Группируем студентов по ФИО (убираем дубликаты)
        students_by_fio = {}
        for student in students:
            fio_key = student.fio.strip()
            if fio_key not in students_by_fio:
                students_by_fio[fio_key] = {
                    "id": student.id,
                    "fio": student.fio,
                    "all_ids": [student.id]
                }
            else:
                students_by_fio[fio_key]["all_ids"].append(student.id)
        
        # Оптимизация: получаем все оценки для всех студентов одним запросом
        all_student_ids = [s_id for s_data in students_by_fio.values() for s_id in s_data["all_ids"]]
        if all_student_ids:
            all_grades = db.query(Grade).filter(
                Grade.student_id.in_(all_student_ids)
            ).all()
        else:
            all_grades = []
        
        # Группируем оценки по student_id для быстрого доступа
        grades_by_student = {}
        for grade in all_grades:
            if grade.student_id not in grades_by_student:
                grades_by_student[grade.student_id] = []
            grades_by_student[grade.student_id].append(grade)
        
        rating = []
        for fio_key, student_info in students_by_fio.items():
            # Получаем все оценки студента из кэша
            all_student_ids = student_info["all_ids"]
            grades = []
            for student_id in all_student_ids:
                if student_id in grades_by_student:
                    grades.extend(grades_by_student[student_id])
            
            # Подсчитываем пропуски (оптимизированная версия)
            absences = 0
            for g in grades:
                if not g.value:
                    absences += 1
                    continue
                value_str = str(g.value).strip().lower()
                if ('пропуск' in value_str or value_str in ['н', 'н/я', 'неявка']):
                    absences += 1
            
            rating.append({
                "id": student_info["id"],
                "fio": student_info["fio"],
                "absences": absences
            })
        
        # Сортируем по количеству пропусков (от меньшего к большему), при равенстве - по ФИО
        rating.sort(key=lambda x: (x["absences"], x["fio"]))
        
        # Добавляем позицию в рейтинге - каждому студенту уникальное место (без повторений)
        for i, item in enumerate(rating):
            item["position"] = i + 1
        
        # Валидация через Pydantic
        return [AbsenceRatingItem(**item) for item in rating]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении рейтинга по пропускам: {str(e)}")
    finally:
        db.close()


@router.get("/rating/grades", response_model=List[GradeRatingItem])
async def get_grades_rating(
    group_id: int = Query(..., gt=0, description="ID группы (должен быть положительным числом)"),
    token: str = Depends(verify_token)
):
    """
    Получить рейтинг группы по оценкам (средний балл по всем предметам)
    
    Args:
        group_id: ID группы (обязательно, положительное число)
    
    Returns:
        List[GradeRatingItem]: Рейтинг студентов по среднему баллу (от большего к меньшему):
        - Позиции идут строго от 1 до N без повторений
        - Каждый студент получает уникальную позицию, даже при одинаковом среднем балле
    
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
        
        # Группируем студентов по ФИО (убираем дубликаты)
        students_by_fio = {}
        for student in students:
            fio_key = student.fio.strip()
            if fio_key not in students_by_fio:
                students_by_fio[fio_key] = {
                    "id": student.id,
                    "fio": student.fio,
                    "all_ids": [student.id]
                }
            else:
                students_by_fio[fio_key]["all_ids"].append(student.id)
        
        # Оптимизация: получаем все оценки для всех студентов одним запросом
        all_student_ids = [s_id for s_data in students_by_fio.values() for s_id in s_data["all_ids"]]
        all_grades = db.query(Grade).filter(
            Grade.student_id.in_(all_student_ids)
        ).all()
        
        # Группируем оценки по student_id для быстрого доступа
        grades_by_student = {}
        for grade in all_grades:
            if grade.student_id not in grades_by_student:
                grades_by_student[grade.student_id] = []
            grades_by_student[grade.student_id].append(grade)
        
        rating = []
        for fio_key, student_info in students_by_fio.items():
            # Получаем все оценки студента из кэша
            all_student_ids = student_info["all_ids"]
            grades = []
            for student_id in all_student_ids:
                if student_id in grades_by_student:
                    grades.extend(grades_by_student[student_id])
            
            # Извлекаем только числовые оценки (игнорируем пропуски)
            # Используем set для уникальности (дата + предмет + значение)
            numeric_grades_set = set()
            for g in grades:
                if not g.value:
                    continue
                value_str = str(g.value).strip()
                value_lower = value_str.lower()
                # Проверяем, что это не пропуск (оптимизированная проверка)
                if value_lower in ['н', 'н/я', 'неявка'] or 'пропуск' in value_lower:
                    continue
                try:
                    # Пытаемся преобразовать в число
                    grade_num = float(value_str)
                    if 2 <= grade_num <= 5:  # Валидные оценки от 2 до 5
                        # Используем комбинацию даты, предмета и оценки для уникальности
                        numeric_grades_set.add((g.date, g.subject_id, grade_num))
                except (ValueError, TypeError):
                    # Если не число, пропускаем
                    continue
            
            numeric_grades = [g[2] for g in numeric_grades_set]  # Извлекаем только оценки
            
            # Вычисляем средний балл
            if numeric_grades:
                average_grade = sum(numeric_grades) / len(numeric_grades)
            else:
                average_grade = 0.0
            
            rating.append({
                "id": student_info["id"],
                "fio": student_info["fio"],
                "average_grade": round(average_grade, 2),
                "total_grades": len(numeric_grades)
            })
        
        # Сортируем по среднему баллу (от большего к меньшему), при равенстве - по количеству оценок (больше лучше), затем по ФИО
        rating.sort(key=lambda x: (-x["average_grade"], -x["total_grades"], x["fio"]))
        
        # Добавляем позицию в рейтинге - каждому студенту уникальное место (без повторений)
        for i, item in enumerate(rating):
            item["position"] = i + 1
        
        # Валидация через Pydantic
        return [GradeRatingItem(**item) for item in rating]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при получении рейтинга: {str(e)}")
    finally:
        db.close()

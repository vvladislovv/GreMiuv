"""
МОДЕЛИ БАЗЫ ДАННЫХ
==================

Использует SQLAlchemy ORM для работы с базой данных.

Структура БД:
- UpdateLog (лог обновлений)
  - id, file_name, last_update_time
  - Хранит информацию о том, когда последний раз обновлялся каждый файл
- Group (группы)
- Student (студенты)
- Subject (предметы)
- Grade (оценки/пропуски)

Логика:
- init_db() - создает таблицы в БД
- get_db() - возвращает сессию для работы с БД
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()


class UpdateLog(Base):
    """Модель лога обновлений файлов"""
    __tablename__ = 'update_log'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String, unique=True, nullable=False)  # Имя файла
    last_update_time = Column(DateTime, nullable=False, default=datetime.now)  # Время последнего обновления


class Group(Base):
    """Модель группы студентов"""
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Название группы
    
    students = relationship("Student", back_populates="group", cascade="all, delete-orphan")
    subjects = relationship("Subject", back_populates="group", cascade="all, delete-orphan")


class Student(Base):
    """Модель студента"""
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    fio = Column(String, nullable=False)  # ФИО студента
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    
    group = relationship("Group", back_populates="students")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Subject(Base):
    """Модель предмета"""
    __tablename__ = 'subjects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Название предмета
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    
    group = relationship("Group", back_populates="subjects")
    grades = relationship("Grade", back_populates="subject", cascade="all, delete-orphan")


class Grade(Base):
    """Модель оценки/пропуска"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    date = Column(Date, nullable=False)  # Дата
    value = Column(String, nullable=False)  # Оценка или "пропуск"
    
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")


# Создание движка и сессии для работы с БД
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Инициализация базы данных - создает все таблицы"""
    Base.metadata.create_all(engine)


def get_db():
    """Получение сессии БД для выполнения запросов"""
    return SessionLocal()


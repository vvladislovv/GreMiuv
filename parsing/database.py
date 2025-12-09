"""
МОДЕЛИ БАЗЫ ДАННЫХ
==================

Использует SQLAlchemy ORM для работы с базой данных.

Структура БД:
- Group (группы)
- Student (студенты)
- Subject (предметы)
- Grade (оценки/пропуски)

Логика:
- init_db() - создает таблицы в БД
- get_db() - возвращает сессию для работы с БД
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import sys
from pathlib import Path

# Определяем путь к config.py в папке parsing
# Загружаем config напрямую из файла для избежания конфликтов с backend/config.py
parsing_dir = Path(__file__).parent
config_file = parsing_dir / "config.py"

# Загружаем config как модуль напрямую из файла
import importlib.util
spec = importlib.util.spec_from_file_location("parsing_config", config_file)
parsing_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parsing_config)
DATABASE_URL = parsing_config.DATABASE_URL

Base = declarative_base()


class UpdateLog(Base):
    """Модель лога обновлений файлов"""
    __tablename__ = 'update_log'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String, unique=True, nullable=False)  # Имя файла
    last_update_time = Column(DateTime, nullable=False, default=datetime.now)  # Время последнего обновления


class ParseLog(Base):
    """Модель лога парсинга"""
    __tablename__ = 'parse_log'
    
    id = Column(Integer, primary_key=True)
    parse_time = Column(DateTime, nullable=False, default=datetime.now)  # Время парсинга
    files_processed = Column(Integer, nullable=False, default=0)  # Количество обработанных файлов
    groups_updated = Column(String, nullable=True)  # Список обновленных групп (JSON строка)
    status = Column(String, nullable=False, default="success")  # Статус: success, error
    error_message = Column(String, nullable=True)  # Сообщение об ошибке, если есть


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
    
    # Уникальный индекс на комбинацию ФИО и группы - один студент не может быть дважды в одной группе
    __table_args__ = (
        UniqueConstraint('fio', 'group_id', name='uq_student_fio_group'),
    )
    
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
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")


class Topic(Base):
    """Модель темы занятия"""
    __tablename__ = 'topics'
    
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    name = Column(String, nullable=False)  # Название темы
    hours = Column(Integer, nullable=True)  # Количество часов (обычно 2)
    date = Column(Date, nullable=True)  # Дата проведения (если указана)
    
    subject = relationship("Subject", back_populates="topics")


class Grade(Base):
    """Модель оценки/пропуска"""
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('subjects.id'), nullable=False)
    date = Column(Date, nullable=False)  # Дата
    value = Column(String, nullable=False)  # Оценка или "пропуск"
    
    # Уникальный индекс на комбинацию студент-предмет-дата - одна оценка на дату
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'date', name='uq_grade_student_subject_date'),
    )
    
    student = relationship("Student", back_populates="grades")
    subject = relationship("Subject", back_populates="grades")


class TelegramUser(Base):
    """Модель пользователя Telegram бота"""
    __tablename__ = 'telegram_users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)  # ID пользователя в Telegram
    username = Column(String, nullable=True)  # Тег пользователя (@username)
    first_name = Column(String, nullable=True)  # Имя из Telegram
    last_name = Column(String, nullable=True)  # Фамилия из Telegram
    full_name = Column(String, nullable=True)  # Полное ФИО (вводится при регистрации)
    registered_at = Column(DateTime, nullable=False, default=datetime.now)  # Дата регистрации
    is_registered = Column(Integer, nullable=False, default=0)  # 0 - не зарегистрирован, 1 - зарегистрирован


class AppLog(Base):
    """Универсальная модель логов приложения (парсер, бэкенд, телеграм)"""
    __tablename__ = 'app_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)  # Время события
    module = Column(String, nullable=False)  # Модуль: 'parser', 'backend', 'telegram'
    level = Column(String, nullable=False)  # Уровень: 'INFO', 'WARNING', 'ERROR', 'DEBUG'
    message = Column(String, nullable=False)  # Сообщение лога
    description = Column(String, nullable=True)  # Дополнительное описание
    details = Column(String, nullable=True)  # Детали (JSON строка для дополнительных данных)
    user_id = Column(Integer, nullable=True)  # ID пользователя (для телеграм логов)
    error_traceback = Column(String, nullable=True)  # Трассировка ошибки (если есть)


# Создание движка и сессии для работы с БД
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Инициализация базы данных - создает все таблицы"""
    Base.metadata.create_all(engine)


def get_db():
    """Получение сессии БД для выполнения запросов"""
    return SessionLocal()


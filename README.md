# 📚 GreMuiv - Журнал оценок

Система для автоматического парсинга и отображения оценок студентов из Excel файлов.

## 📁 Структура проекта

```
GreMuiv/
├── parsing/              # Парсер Excel файлов
│   ├── main.py          # Главный файл парсера
│   ├── database.py      # Модели БД
│   ├── config.py        # Конфигурация
│   ├── run.py           # Запуск парсера
│   ├── parsers/         # Парсеры Excel
│   └── downloaders/     # Загрузчики файлов
├── backend/             # FastAPI бэкенд
│   ├── main.py         # API сервер
│   ├── run_backend.py  # Запуск API
│   └── start.py        # Запуск парсера + API
├── frontend/            # React + Vite фронтенд
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   ├── hooks/       # Custom hooks
│   │   ├── services/   # API сервисы
│   │   └── utils/      # Утилиты
│   └── package.json
└── data/                # Данные (БД, скачанные файлы)
    ├── students.db
    └── downloaded_files/
```

## 🚀 Быстрый старт

### 1. Установите зависимости

```bash
# Python зависимости
pip3 install -r requirements.txt

# Node.js зависимости (фронтенд)
cd frontend
npm install
cd ..
```

### 2. Запустите приложение

**Вариант 1: Все вместе (парсер + API)**
```bash
cd backend
python3 start.py
```

**Вариант 2: Отдельно**

Терминал 1 - Парсер:
```bash
cd parsing
python3 run.py
```

Терминал 2 - API сервер:
```bash
cd backend
python3 run_backend.py
```

Терминал 3 - Фронтенд:
```bash
cd frontend
npm run dev
```

## 🌐 Доступ

- **Фронтенд**: http://localhost:3000
- **API**: http://localhost:5000
- **API Docs**: http://localhost:5000/docs

## ⚙️ Настройка

Отредактируйте `parsing/config.py` для настройки:
- ID файлов Google Drive
- Интервал обновления (по умолчанию 15 минут)
- Настройки парсинга

## 📊 Функции

- ✅ Автоматическое обновление данных каждые 15 минут
- ✅ Парсинг Excel файлов с Google Drive
- ✅ FastAPI бэкенд с автоматической документацией
- ✅ Красивый React интерфейс с таблицей оценок
- ✅ Статистика посещаемости
- ✅ Цветовая индикация оценок
- ✅ Адаптивный дизайн

## 🎨 Технологии

**Parsing:**
- Python 3.7+
- SQLAlchemy
- openpyxl
- schedule

**Backend:**
- Python 3.7+
- FastAPI
- SQLAlchemy

**Frontend:**
- React 18
- Vite
- Axios

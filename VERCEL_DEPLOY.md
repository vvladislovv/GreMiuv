# Инструкция по деплою на Vercel

## Подготовка проекта

Проект уже настроен для деплоя на Vercel. Структура:
- `api/index.py` - точка входа для Vercel serverless functions
- `vercel.json` - конфигурация Vercel
- `requirements.txt` - зависимости Python

## Шаги для деплоя

### 1. Установка Vercel CLI (если еще не установлен)

```bash
npm i -g vercel
```

### 2. Логин в Vercel

```bash
vercel login
```

### 3. Деплой проекта

```bash
# Из корневой директории проекта
vercel
```

При первом деплое Vercel спросит:
- Set up and deploy? **Yes**
- Which scope? Выберите ваш аккаунт
- Link to existing project? **No** (для первого деплоя)
- Project name? Введите название проекта (например: `gremuiv-api`)
- Directory? **./** (корневая директория)
- Override settings? **No**

### 4. Настройка переменных окружения

После деплоя нужно настроить переменные окружения в Vercel Dashboard:

1. Перейдите в Settings → Environment Variables
2. Добавьте следующие переменные:

```
# База данных (для Vercel нужно использовать внешнюю БД или файловую систему)
DATABASE_URL=sqlite:///tmp/students.db  # Временное решение для Vercel
# Или используйте PostgreSQL через переменную окружения:
# DATABASE_URL=postgresql://user:password@host:port/database

# Google Drive настройки (если используются)
GOOGLE_DRIVE_FOLDER_ID=your_folder_id

# CORS настройки
CUSTOM_DOMAIN=your-domain.com  # Ваш кастомный домен (если есть)
ALLOW_ALL_ORIGINS=false  # true только для разработки

# Другие переменные из .env файла
```

### 5. Настройка базы данных

**ВАЖНО:** Vercel serverless functions имеют временную файловую систему. 
SQLite база данных будет теряться при каждом деплое.

**Рекомендуемые решения:**

1. **Использовать внешнюю БД (PostgreSQL, MySQL):**
   - Настройте внешнюю БД (например, на Railway, Supabase, или другом сервисе)
   - Укажите `DATABASE_URL` в переменных окружения Vercel

2. **Использовать Vercel KV или другой storage:**
   - Для простых данных можно использовать Vercel KV
   - Или использовать внешний storage (S3, Google Cloud Storage)

3. **Использовать отдельный сервер для парсера:**
   - Парсер можно запускать на отдельном сервере (например, на Railway, Render)
   - API на Vercel будет только читать данные из БД

### 6. Обновление CORS для фронтенда

После деплоя получите URL вашего API (например: `https://your-project.vercel.app`)

Обновите `frontend/src/services/api.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://your-project.vercel.app';
```

И добавьте переменную окружения в Vercel для фронтенда:
```
VITE_API_URL=https://your-project.vercel.app
```

### 7. Production деплой

После тестирования на preview деплое:

```bash
vercel --prod
```

## Структура проекта для Vercel

```
.
├── api/
│   └── index.py          # Точка входа для Vercel
├── backend/             # FastAPI приложение
├── parsing/             # Парсер (может работать отдельно)
├── frontend/            # React фронтенд
├── vercel.json          # Конфигурация Vercel
└── requirements.txt     # Python зависимости
```

## Ограничения Vercel

1. **Время выполнения:** Максимум 30 секунд для Hobby плана, 60 секунд для Pro
2. **Файловая система:** Временная, данные теряются при каждом деплое
3. **База данных:** Нужна внешняя БД (не SQLite в файле)
4. **Парсер:** Рекомендуется запускать отдельно (не на Vercel)

## Рекомендации

1. **Парсер:** Запускайте на отдельном сервере (Railway, Render, или VPS)
2. **API:** Деплойте на Vercel для быстрого доступа
3. **База данных:** Используйте внешнюю БД (PostgreSQL рекомендуется)
4. **Фронтенд:** Деплойте на Vercel отдельно или вместе с API

## Troubleshooting

### Ошибка: Module not found
- Убедитесь, что все зависимости в `requirements.txt`
- Проверьте, что пути импортов правильные

### Ошибка: Database locked
- SQLite не подходит для Vercel (множественные инстансы)
- Используйте внешнюю БД

### Ошибка: CORS
- Проверьте переменные окружения `CUSTOM_DOMAIN` и `ALLOW_ALL_ORIGINS`
- Убедитесь, что домен фронтенда добавлен в `CORS_ORIGINS`

### Ошибка: Timeout
- Увеличьте `maxDuration` в `vercel.json` (максимум 60 сек для Pro)
- Оптимизируйте запросы к БД

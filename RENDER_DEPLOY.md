# Деплой на Render.com

## Быстрый старт

1. **Подключите репозиторий к Render.com:**
   - Зайдите на [render.com](https://render.com)
   - Создайте новый Web Service
   - Подключите ваш GitHub/GitLab репозиторий
   - Render автоматически обнаружит `render.yaml` и использует его конфигурацию

2. **Или создайте сервис вручную:**
   - Выберите "New" → "Web Service"
   - Подключите репозиторий
   - Настройки:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python render_start.py`
     - **Environment:** Python 3
     - **Python Version:** 3.11.0

3. **Переменные окружения (опционально):**
   - `BOT_TOKEN` - токен Telegram бота (если хотите запустить бота)
   - `DATABASE_URL` - если используете PostgreSQL вместо SQLite
   - `CUSTOM_DOMAIN` - ваш кастомный домен (для CORS)
   - `ALLOW_ALL_ORIGINS` - установите в `true` для разрешения всех доменов (не рекомендуется для production)

## Важные замечания

### База данных
- По умолчанию используется SQLite (`data/students.db`)
- **Внимание:** На Render файловая система эфемерная, данные SQLite могут теряться при перезапуске
- Для production рекомендуется использовать PostgreSQL:
  1. Создайте PostgreSQL базу данных на Render
  2. Установите переменную окружения `DATABASE_URL` с connection string

### Парсер и Telegram бот
- **Все компоненты запускаются на одном сервисе:**
  - API сервер (основной процесс)
  - Парсер (в отдельном потоке, обновление каждые 15 минут)
  - Telegram бот (в отдельном потоке, если установлен BOT_TOKEN)
- Все компоненты работают параллельно в одном Web Service
- Для работы Telegram бота установите переменную окружения `BOT_TOKEN` в настройках Render

### CORS
- Render домены автоматически добавляются в CORS
- Если используете кастомный домен, добавьте его в переменную `CUSTOM_DOMAIN`

## Структура файлов

- `render.yaml` - конфигурация для автоматического деплоя
- `render_start.py` - скрипт запуска для Render (API сервер + парсер + Telegram бот)
- `backend/config.py` - обновлен для поддержки Render порта и доменов

## Проверка работы

После деплоя проверьте:
- `https://your-service.onrender.com/` - корневой эндпоинт
- `https://your-service.onrender.com/docs` - документация API
- `https://your-service.onrender.com/api/token` - получение токена

## Troubleshooting

### Ошибка порта
- Render автоматически устанавливает переменную `PORT`
- Убедитесь, что `render_start.py` использует `os.getenv("PORT")`

### Ошибка базы данных
- Проверьте права на запись в директорию `data/`
- Рассмотрите использование PostgreSQL для production

### CORS ошибки
- Проверьте, что ваш фронтенд домен добавлен в CORS
- Установите `ALLOW_ALL_ORIGINS=true` для тестирования (не для production!)


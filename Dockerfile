# Production Dockerfile для GreMuiv
# Все в одном контейнере: фронтенд + backend + Caddy

# Этап 1: Сборка фронтенда
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Копируем package файлы
COPY frontend/package*.json ./
COPY frontend/yarn.lock* ./

# Устанавливаем зависимости
RUN if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci; fi

# Копируем исходники фронтенда
COPY frontend/ .

# Собираем фронтенд для production
# Используем относительный путь /api для работы и на localhost и на домене
ENV VITE_API_URL=/api
RUN npm run build || yarn build

# Этап 2: Финальный образ
FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости (включая Caddy и supervisor)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    supervisor \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Caddy
RUN curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update \
    && apt-get install -y caddy \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Копируем собранный фронтенд из первого этапа
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Копируем конфигурацию supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Создаем директории
RUN mkdir -p /app/data /app/logs /var/log/caddy /var/log/supervisor

# Открываем порты
EXPOSE 80 443 5000

# Устанавливаем переменные окружения
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

# Запускаем supervisor (который запустит все процессы)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]

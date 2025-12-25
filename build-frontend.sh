#!/bin/bash

# Скрипт для сборки фронтенда с production API URL

echo "📦 Сборка фронтенда для production..."

cd frontend

# Устанавливаем API URL для production
export VITE_API_URL=https://vildanai.ru/api

# Устанавливаем зависимости если нужно
if [ ! -d "node_modules" ]; then
    echo "📥 Установка зависимостей..."
    if [ -f "yarn.lock" ]; then
        yarn install
    else
        npm install
    fi
fi

# Сборка
echo "🔨 Сборка..."
if [ -f "yarn.lock" ]; then
    yarn build
else
    npm run build
fi

echo "✅ Фронтенд собран!"
echo "📁 Файлы в: frontend/dist/"







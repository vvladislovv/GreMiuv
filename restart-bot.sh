#!/bin/bash

echo "🔄 Перезапуск бота для применения изменений..."
echo ""

# Перезапуск контейнера
docker-compose restart

echo "⏳ Ждем 5 секунд..."
sleep 5

echo "📋 Проверка логов бота:"
docker exec gremuiv-app tail -20 /var/log/supervisor/gremuiv-api.out.log | grep -i "mini\|url\|vildanai" || echo "Нет упоминаний в логах"

echo ""
echo "✅ Перезапуск завершен"
echo ""
echo "🔍 Проверьте что URL правильный:"
docker exec gremuiv-app python3 -c "import os; print('MINI_APP_URL:', os.getenv('MINI_APP_URL', 'НЕ УСТАНОВЛЕН'))"







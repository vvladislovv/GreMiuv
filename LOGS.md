# 📋 Просмотр логов

## Все логи сразу

```bash
docker-compose logs -f
```

## Логи отдельных компонентов

### API (Backend)
```bash
docker exec gremuiv-app tail -f /var/log/supervisor/gremuiv-api.out.log
```

### Ошибки API
```bash
docker exec gremuiv-app tail -f /var/log/supervisor/gremuiv-api.err.log
```

### Caddy (веб-сервер)
```bash
docker exec gremuiv-app tail -f /var/log/supervisor/caddy.out.log
```

### Ошибки Caddy
```bash
docker exec gremuiv-app tail -f /var/log/supervisor/caddy.err.log
```

### Supervisor (управление процессами)
```bash
docker exec gremuiv-app tail -f /var/log/supervisor/supervisord.log
```

## Последние N строк

```bash
# Последние 50 строк API
docker exec gremuiv-app tail -50 /var/log/supervisor/gremuiv-api.out.log

# Последние 100 строк всех логов
docker-compose logs --tail=100
```

## Поиск в логах

```bash
# Поиск "бот" в логах API
docker exec gremuiv-app grep -i "бот\|bot\|telegram" /var/log/supervisor/gremuiv-api.out.log

# Поиск ошибок
docker-compose logs | grep -i error
```







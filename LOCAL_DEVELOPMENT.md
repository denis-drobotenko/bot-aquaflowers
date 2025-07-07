# 🚀 Локальная разработка AuraFlora Bot

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка .env
Скопируй `.env` с продакшн сервера или создай локальный с теми же переменными.

### 3. Запуск локального сервера
```bash
./run_local.sh
```

### 4. Настройка ngrok для получения webhook'ов
```bash
# Установка ngrok
brew install ngrok

# Запуск туннеля
ngrok http 8080
```

### 5. Обновление webhook URL в Meta Developer Console
1. Скопируй ngrok URL (например, `https://abc123.ngrok.io`)
2. Перейди в [Meta Developer Console](https://developers.facebook.com/apps/[YOUR_APP_ID]/whatsapp-business/wa-dev-console)
3. Обнови Webhook URL на: `https://abc123.ngrok.io/webhook`
4. Verify Token должен совпадать с `VERIFY_TOKEN` в `.env`

## Полезные скрипты

### Переключение webhook URL
```bash
# Переключить на локальный ngrok
./switch_webhook.sh local

# Переключить на продакшн
./switch_webhook.sh prod
```

### Проверка здоровья API
```bash
# Локальный healthcheck
curl http://localhost:8080/health

# Расширенный healthcheck
curl http://localhost:8080/health/full
```

## Отладка

### Логи
Локальный сервер выводит логи в консоль с уровнем DEBUG.

### Debug интерфейс
При `DEV_MODE=true` доступен debug интерфейс:
- http://localhost:8080/debug

### Тестирование webhook'ов
```bash
# Тест верификации webhook
curl "http://localhost:8080/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=YOUR_TOKEN"

# Тест получения сообщения (POST)
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[{"id":"123","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"1234567890","phone_number_id":"123"},"contacts":[{"profile":{"name":"Test"},"wa_id":"1234567890"}],"messages":[{"from":"1234567890","id":"msg_123","timestamp":"1234567890","text":{"body":"test"}}]}}]}]}'
```

## Переменные окружения для локальной разработки

Добавь в `.env`:
```bash
LOCAL_DEV=true
ENVIRONMENT=development
DEV_MODE=true
```

## Преимущества локальной разработки

✅ **Быстрая разработка** - изменения применяются мгновенно  
✅ **Отладка в реальном времени** - логи в консоли  
✅ **Полная функциональность** - все API работают локально  
✅ **Безопасность** - тестирование без влияния на продакшн  
✅ **Экономия времени** - не нужно деплоить для каждого изменения  

## Переход на продакшн

Когда разработка завершена:
1. Запусти `./switch_webhook.sh prod`
2. Обнови webhook URL в Meta Developer Console
3. Деплой: `./deploy.sh` 
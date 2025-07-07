#!/bin/bash

echo "🚀 Запуск AuraFlora Bot с ngrok..."

# Проверяем наличие .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Загружаем переменные из .env (правильный способ)
export $(grep -v '^#' .env | xargs)

# Устанавливаем локальные настройки
export ENVIRONMENT=development
export DEV_MODE=true
export LOCAL_DEV=true
export PORT=8080
export LOG_FILE=local_debug.log

echo "✅ Переменные окружения загружены"
echo "🌐 Сервер будет доступен на: http://localhost:8080"
echo "📱 ngrok будет создавать туннель для webhook'ов"
echo "📋 Логи будут сохраняться в: local_debug.log"
echo ""

# Функция для очистки при выходе
cleanup() {
    echo ""
    echo "🛑 Остановка сервисов..."
    
    # Останавливаем ngrok
    if [ ! -z "$NGROK_PID" ]; then
        echo "🛑 Остановка ngrok (PID: $NGROK_PID)..."
        kill $NGROK_PID 2>/dev/null
    fi
    
    # Останавливаем сервер
    if [ ! -z "$SERVER_PID" ]; then
        echo "🛑 Остановка сервера (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null
    fi
    
    echo "✅ Все сервисы остановлены"
    exit 0
}

# Устанавливаем обработчик сигналов
trap cleanup SIGINT SIGTERM

# Запускаем ngrok в фоне
echo "🚀 Запуск ngrok..."
ngrok http 8080 > /dev/null 2>&1 &
NGROK_PID=$!

# Ждем немного, чтобы ngrok запустился
sleep 3

# Проверяем, что ngrok запустился
if ! kill -0 $NGROK_PID 2>/dev/null; then
    echo "❌ Ошибка запуска ngrok"
    exit 1
fi

echo "✅ ngrok запущен (PID: $NGROK_PID)"

# Получаем ngrok URL
echo "🔍 Получение ngrok URL..."
sleep 2

NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data['tunnels']:
        print(data['tunnels'][0]['public_url'])
    else:
        print('')
except:
    print('')
")

if [ -z "$NGROK_URL" ]; then
    echo "❌ Не удалось получить ngrok URL"
    cleanup
fi

echo "✅ ngrok URL: $NGROK_URL"
echo "🔗 Webhook URL для Meta Developer Console: $NGROK_URL/webhook"
echo "🔑 Verify Token: $VERIFY_TOKEN"
echo ""

# Запускаем сервер в фоне
echo "🚀 Запуск FastAPI сервера..."
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload > /dev/null 2>&1 &
SERVER_PID=$!

# Ждем немного, чтобы сервер запустился
sleep 5

# Проверяем, что сервер запустился
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Ошибка запуска сервера"
    cleanup
fi

echo "✅ Сервер запущен (PID: $SERVER_PID)"
echo ""

# Проверяем healthcheck
echo "🔍 Проверка healthcheck..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Сервер работает корректно"
else
    echo "❌ Сервер не отвечает"
    cleanup
fi

echo ""
echo "🎉 Все готово! Система запущена:"
echo "   📱 ngrok: $NGROK_URL"
echo "   🌐 Сервер: http://localhost:8080"
echo "   📋 Логи: local_debug.log"
echo "   🔍 ngrok UI: http://localhost:4040"
echo ""
echo "💡 Для остановки нажми Ctrl+C"
echo ""

# Ждем завершения
wait 
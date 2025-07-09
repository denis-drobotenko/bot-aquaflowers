#!/bin/bash

echo "🚀 Запуск локального сервера AuraFlora Bot..."
echo ""
echo "💡 Рекомендуется использовать run_local_with_ngrok.sh для автоматического запуска ngrok"
echo ""

# Проверяем наличие .env
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    exit 1
fi

# Загружаем переменные из .env (правильный способ)
set -a
source .env
set +a

# Очищаем логи при запуске
echo "🧹 Очищаем логи..."
> local_debug.log
echo "✅ Логи очищены"

# Устанавливаем локальные настройки
export ENVIRONMENT=development
export DEV_MODE=true
export LOCAL_DEV=true
export PORT=8080
export LOG_FILE=local_debug.log
export AUDIO_BUCKET_NAME=aquaf-audio-files

echo "✅ Переменные окружения загружены"
echo "🌐 Сервер будет доступен на: http://localhost:8080"
echo "📱 Для получения webhook'ов от WhatsApp используй ngrok:"
echo "   ngrok http 8080"
echo ""
echo "🔗 После запуска ngrok обнови webhook URL в Meta Developer Console"
echo ""

# Запускаем сервер
echo "🚀 Запуск FastAPI сервера..."
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload 
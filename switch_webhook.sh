#!/bin/bash

# Проверяем аргументы
if [ "$1" = "local" ]; then
    echo "🔄 Переключение на локальный webhook..."
    
    # Запрашиваем ngrok URL
    read -p "Введите ngrok URL (например, https://abc123.ngrok.io): " NGROK_URL
    
    if [ -z "$NGROK_URL" ]; then
        echo "❌ URL не указан!"
        exit 1
    fi
    
    WEBHOOK_URL="$NGROK_URL/webhook"
    echo "✅ Webhook URL для локальной разработки: $WEBHOOK_URL"
    echo ""
    echo "📝 Обнови этот URL в Meta Developer Console:"
    echo "   https://developers.facebook.com/apps/[YOUR_APP_ID]/whatsapp-business/wa-dev-console"
    echo ""
    echo "🔗 Webhook URL: $WEBHOOK_URL"
    echo "🔑 Verify Token: $VERIFY_TOKEN"
    
elif [ "$1" = "prod" ]; then
    echo "🔄 Переключение на продакшн webhook..."
    WEBHOOK_URL="https://auraflora-bot-75152239022.asia-southeast1.run.app/webhook"
    echo "✅ Webhook URL для продакшна: $WEBHOOK_URL"
    echo ""
    echo "📝 Обнови этот URL в Meta Developer Console:"
    echo "   https://developers.facebook.com/apps/[YOUR_APP_ID]/whatsapp-business/wa-dev-console"
    echo ""
    echo "🔗 Webhook URL: $WEBHOOK_URL"
    echo "🔑 Verify Token: $VERIFY_TOKEN"
    
else
    echo "❌ Использование: $0 [local|prod]"
    echo ""
    echo "Примеры:"
    echo "  $0 local  # Переключить на локальный ngrok"
    echo "  $0 prod   # Переключить на продакшн Cloud Run"
    exit 1
fi 
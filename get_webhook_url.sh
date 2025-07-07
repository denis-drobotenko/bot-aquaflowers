#!/bin/bash

echo "🔍 Получение текущего ngrok URL..."

# Проверяем, запущен ли ngrok
if ! curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "❌ ngrok не запущен!"
    echo "💡 Запустите: ./run_local_with_ngrok.sh"
    exit 1
fi

# Получаем URL
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
    exit 1
fi

# Получаем VERIFY_TOKEN из .env
if [ -f ".env" ]; then
    VERIFY_TOKEN=$(grep VERIFY_TOKEN .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ')
else
    VERIFY_TOKEN="my-super-secret-token"
fi

echo ""
echo "✅ ngrok URL: $NGROK_URL"
echo ""
echo "🔗 Для Meta Developer Console:"
echo "   Webhook URL: $NGROK_URL/webhook"
echo "   Verify Token: $VERIFY_TOKEN"
echo ""
echo "📋 Быстрые команды:"
echo "   curl -v \"$NGROK_URL/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=$VERIFY_TOKEN\""
echo ""
echo "🌐 ngrok UI: http://localhost:4040" 
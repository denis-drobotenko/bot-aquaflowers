#!/bin/bash

PORT=${1:-8080}

echo "🔄 Останавливаю процессы на порту $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

echo "🧹 Очищаю порт..."
sleep 2

echo "🚀 Запускаю сервер на порту $PORT..."
PYTHONPATH=. python3 -m uvicorn src.app:app --host 0.0.0.0 --port $PORT --reload

echo "✅ Сервер запущен на http://localhost:$PORT" 
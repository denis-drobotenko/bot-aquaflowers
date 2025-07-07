#!/bin/bash

echo "🔄 Останавливаю процессы на порту 8081..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true

echo "🧹 Очищаю порт..."
sleep 2

echo "🚀 Запускаю сервер на порту 8081..."
PYTHONPATH=. python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8081 --reload

echo "✅ Сервер запущен на http://localhost:8081" 
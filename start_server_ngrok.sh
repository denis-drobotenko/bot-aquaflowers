#!/bin/bash

echo "🚀 Запускаю сервер (без убийства ngrok)..."
PYTHONPATH=. python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload

echo "✅ Сервер запущен на http://localhost:8080" 
#!/bin/bash

# Скрипт для запуска сервера без убийства процесса на порту

PORT=8080
PID=$(lsof -ti:$PORT)

if [ ! -z "$PID" ]; then
    echo "❌ Порт $PORT уже занят процессом PID: $PID"
    echo "Пожалуйста, освободите порт $PORT вручную и повторите запуск."
    exit 1
else
    echo "✅ Порт $PORT свободен. Запускаем сервер..."
fi

# Очищаем лог файл
> app.json

echo "🚀 Запускаем сервер..."
echo "📝 Логи будут в app.json"
echo "🌐 Сервер будет доступен на http://localhost:8080"
echo ""

PYTHONPATH=/Users/denisdrobotenko/bot-aquaflowers python3 src/main.py 
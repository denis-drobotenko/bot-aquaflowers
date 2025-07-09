#!/bin/bash

# Скрипт для запуска сервера в режиме разработки с автоматической перезагрузкой

echo "🚀 Запускаем сервер в режиме разработки..."
echo "📝 Автоматическая перезагрузка при изменениях файлов включена"
echo "🌐 Сервер будет доступен на http://localhost:8080"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo ""

# Проверяем, что порт свободен
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Порт 8080 уже занят. Останавливаем предыдущий процесс..."
    pkill -f "uvicorn.*main:app" || true
    pkill -f "python.*main.py" || true
    sleep 2
fi

# Запускаем uvicorn с автоматической перезагрузкой
cd "$(dirname "$0")"
python3 -m uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --reload \
    --reload-dir src \
    --reload-dir templates \
    --reload-dir static \
    --log-level info 
#!/bin/bash

# Скрипт для запуска сервера с nodemon (если установлен)

echo "🚀 Запускаем сервер с nodemon..."
echo "📝 Автоматическая перезагрузка при изменениях файлов включена"
echo "🌐 Сервер будет доступен на http://localhost:8080"
echo "⏹️  Для остановки нажмите Ctrl+C"
echo ""

# Проверяем, что порт свободен
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Порт 8080 уже занят. Останавливаем предыдущий процесс..."
    pkill -f "nodemon" || true
    pkill -f "python.*main.py" || true
    sleep 2
fi

# Проверяем, установлен ли nodemon
if command -v nodemon &> /dev/null; then
    echo "✅ Используем nodemon для автоматической перезагрузки"
    nodemon --exec "python3 src/main.py" \
        --watch src \
        --watch templates \
        --watch static \
        --ext py,html,css,js,json \
        --ignore "*.pyc" \
        --ignore "__pycache__" \
        --ignore ".git" \
        --ignore "node_modules"
else
    echo "⚠️  nodemon не установлен. Устанавливаем..."
    npm install -g nodemon
    echo "✅ nodemon установлен. Запускаем сервер..."
    nodemon --exec "python3 src/main.py" \
        --watch src \
        --watch templates \
        --watch static \
        --ext py,html,css,js,json \
        --ignore "*.pyc" \
        --ignore "__pycache__" \
        --ignore ".git" \
        --ignore "node_modules"
fi 
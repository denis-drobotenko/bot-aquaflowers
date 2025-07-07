#!/bin/bash

LOG_FILE="local_debug.log"

echo "📋 Просмотр логов AuraFlora Bot"
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Файл логов $LOG_FILE не найден!"
    echo "💡 Убедись, что сервер запущен с ./run_local.sh"
    exit 1
fi

echo "📁 Файл логов: $LOG_FILE"
echo "📊 Размер файла: $(du -h $LOG_FILE | cut -f1)"
echo "🕐 Последнее изменение: $(stat -f "%Sm" $LOG_FILE)"
echo ""

echo "🔍 Выберите режим просмотра:"
echo "1) Последние 50 строк"
echo "2) Следить за логами в реальном времени (tail -f)"
echo "3) Поиск по ключевому слову"
echo "4) Показать только ошибки"
echo "5) Показать только webhook'и"
echo "6) Очистить файл логов"
echo ""

read -p "Введите номер (1-6): " choice

case $choice in
    1)
        echo "📋 Последние 50 строк:"
        tail -50 $LOG_FILE
        ;;
    2)
        echo "👀 Следим за логами в реальном времени (Ctrl+C для выхода):"
        tail -f $LOG_FILE
        ;;
    3)
        read -p "🔍 Введите ключевое слово: " keyword
        echo "🔍 Поиск '$keyword':"
        grep -i "$keyword" $LOG_FILE
        ;;
    4)
        echo "❌ Только ошибки:"
        grep -i "error\|exception\|traceback" $LOG_FILE
        ;;
    5)
        echo "📱 Только webhook'и:"
        grep -i "webhook" $LOG_FILE
        ;;
    6)
        echo "🗑️ Очистка файла логов..."
        > $LOG_FILE
        echo "✅ Файл логов очищен"
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac 
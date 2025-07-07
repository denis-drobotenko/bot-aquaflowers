#!/bin/bash

echo "🧹 Очистка логов..."

# Очищаем основной файл логов
if [ -f "logs/logs.log" ]; then
    echo "📄 Очищаем logs/logs.log"
    > logs/logs.log
    echo "✅ logs/logs.log очищен"
else
    echo "⚠️  Файл logs/logs.log не найден"
fi

# Очищаем архивные логи
if [ -d "archive" ]; then
    echo "📁 Очищаем архивные логи..."
    find archive -name "*.log" -type f -delete
    echo "✅ Архивные логи очищены"
fi

# Очищаем тестовые логи
if [ -f "test_logs.json" ]; then
    echo "🧪 Очищаем test_logs.json"
    > test_logs.json
    echo "✅ test_logs.json очищен"
fi

echo "🎉 Все логи очищены!"
echo ""
echo "💡 Для просмотра логов используйте:"
echo "   tail -f logs/logs.log"
echo "   или"
echo "   ./view_logs.sh" 
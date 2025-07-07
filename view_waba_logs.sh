#!/bin/bash

echo "📋 Просмотр WABA логов"
echo "======================"

if [ -f "WABA.log" ]; then
    echo "📄 Файл WABA.log найден"
    echo ""
    echo "Последние 50 записей:"
    echo "======================"
    tail -50 WABA.log
    echo ""
    echo "💡 Для отслеживания в реальном времени используйте:"
    echo "   tail -f WABA.log"
    echo ""
    echo "💡 Для поиска конкретного wamid:"
    echo "   grep 'wamid:YOUR_WAMID' WABA.log"
else
    echo "❌ Файл WABA.log не найден"
    echo "💡 Логи будут созданы при получении webhook'ов от WABA"
fi 
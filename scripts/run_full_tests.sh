#!/bin/bash
# Полные тесты для глубокой проверки функциональности

echo "=== ЗАПУСК ПОЛНЫХ ТЕСТОВ ==="

# Запуск всех тестов
echo "--- Running all tests ---"
python run_tests.py

if [ $? -ne 0 ]; then
    echo "Full tests failed!"
    exit 1
fi

echo "All tests passed successfully!"
echo "System is fully functional!" 
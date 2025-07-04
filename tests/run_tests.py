#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов перед деплоем
"""

import os
import sys
import subprocess

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

TEST_PREFIX = "test_"

# Собираем все тестовые файлы (теперь все в текущей папке)
files = [f for f in os.listdir('.') if f.startswith(TEST_PREFIX) and f.endswith('.py')]

if not files:
    print("Нет тестовых файлов!")
    sys.exit(1)

all_ok = True
for f in files:
    print(f"\n=== Запуск теста: {f} ===")
    # Настраиваем subprocess на UTF-8
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run([sys.executable, f], capture_output=True, text=True, encoding='utf-8', env=env)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Тест не пройден: {f}")
        print(result.stderr)
        all_ok = False

if not all_ok:
    print("\n❌ Некоторые тесты не прошли! Деплой запрещён.")
    sys.exit(1)
else:
    print("\n✅ Все тесты успешно пройдены. Можно деплоить!")
    sys.exit(0) 
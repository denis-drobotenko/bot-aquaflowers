#!/usr/bin/env python3
"""
Простой тест декоратора логирования
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.utils.logging_decorator import log_function, get_logging_config

# Настраиваем логирование
os.environ["LOG_FILE"] = "logs/simple_test.json"
os.environ["LOG_FORMAT"] = "json"
os.environ["ENVIRONMENT"] = "development"

import logging
log_file = os.environ["LOG_FILE"]
root_logger = logging.getLogger()
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == os.path.abspath(log_file) for h in root_logger.handlers):
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    root_logger.addHandler(file_handler)
root_logger.setLevel(logging.INFO)

@log_function("test_module")
def simple_function(name: str, age: int) -> str:
    """Простая функция для тестирования"""
    return f"Hello {name}, you are {age} years old"

@log_function("test_module")
async def async_function(name: str, age: int) -> str:
    """Async функция для тестирования"""
    import asyncio
    await asyncio.sleep(0.1)  # Имитируем async операцию
    return f"Async hello {name}, you are {age} years old"

if __name__ == "__main__":
    print("🧪 Тестируем декоратор логирования")
    
    # Проверяем конфигурацию
    config = get_logging_config()
    print(f"📋 Конфигурация: file={config.log_file}, format={config.log_format}")
    
    # Тест обычной функции
    print("\n1️⃣ Тестируем обычную функцию...")
    result = simple_function("Alice", 30)
    print(f"   Результат: {result}")
    
    # Тест async функции
    print("\n2️⃣ Тестируем async функцию...")
    import asyncio
    result = asyncio.run(async_function("Bob", 25))
    print(f"   Результат: {result}")
    
    print("\n✅ Тестирование завершено!")
    
    # Проверяем файл логов
    log_file = os.environ["LOG_FILE"]
    if os.path.exists(log_file):
        print(f"📄 Файл логов создан: {os.path.getsize(log_file)} байт")
        with open(log_file, "r") as f:
            lines = f.readlines()
            print(f"📊 Количество записей: {len(lines)}")
            if lines:
                print("📝 Первая запись:")
                print(lines[0][:200] + "...")
    else:
        print("❌ Файл логов не создан") 
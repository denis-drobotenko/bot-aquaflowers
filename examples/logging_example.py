"""
Пример использования системы логирования с декораторами
"""

import asyncio
import os
import sys

# Добавляем путь к модулям
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.logging_decorator import log_function, get_logging_config
from src.config.logging_config import LoggingSettings


# Пример 1: Простая функция с логированием
@log_function("example_module")
def simple_function(name: str, age: int = 25) -> str:
    """Простая функция для демонстрации логирования"""
    return f"Hello {name}, you are {age} years old"


# Пример 2: Асинхронная функция с логированием
@log_function("example_module")
async def async_function(data: dict, delay: float = 1.0) -> dict:
    """Асинхронная функция для демонстрации логирования"""
    await asyncio.sleep(delay)
    return {"processed": True, "data": data, "timestamp": "2024-01-01"}


# Пример 3: Функция с ошибкой
@log_function("example_module")
def function_with_error(param: str) -> str:
    """Функция, которая может вызвать ошибку"""
    if param == "error":
        raise ValueError("This is a test error")
    return f"Success: {param}"


# Пример 4: Функция с чувствительными данными
@log_function("example_module")
def function_with_sensitive_data(user_data: dict) -> dict:
    """Функция с чувствительными данными (пароли, токены)"""
    return {
        "user_id": user_data.get("user_id"),
        "status": "authenticated",
        "token": "secret_token_123"  # Будет отфильтрован в логах
    }


class ExampleService:
    """Пример сервиса с логированием методов"""
    
    def __init__(self):
        self.counter = 0
    
    @log_function("example_service")
    def increment_counter(self, amount: int = 1) -> int:
        """Увеличивает счетчик"""
        self.counter += amount
        return self.counter
    
    @log_function("example_service")
    def get_counter(self) -> int:
        """Получает текущее значение счетчика"""
        return self.counter
    
    @log_function("example_service")
    async def async_operation(self, data: list) -> dict:
        """Асинхронная операция"""
        await asyncio.sleep(0.1)
        return {
            "processed_items": len(data),
            "sum": sum(data) if data else 0
        }


def setup_logging_examples():
    """Настройка логирования для примеров"""
    
    print("=== Настройка логирования ===")
    
    # Вариант 1: Настройка по окружению
    print("1. Настройка по окружению:")
    LoggingSettings.setup_development_logging()
    config = get_logging_config()
    print(f"   Включенные модули: {config.enabled_modules}")
    print(f"   Отключенные модули: {config.disabled_modules}")
    
    # Вариант 2: Кастомная настройка
    print("\n2. Кастомная настройка:")
    LoggingSettings.setup_custom_logging({
        "enabled_modules": ["example_module", "example_service"],
        "disabled_modules": ["test_"],
        "enabled_functions": ["example_module.simple_function"],
        "disabled_functions": ["example_module.noisy_function"]
    })
    
    # Вариант 3: Программное управление
    print("\n3. Программное управление:")
    from src.utils.logging_decorator import enable_logging_for_module, disable_logging_for_module
    
    enable_logging_for_module("custom_module")
    disable_logging_for_module("noisy_module")
    
    print("   Логирование настроено!")


async def run_examples():
    """Запуск примеров логирования"""
    
    print("\n=== Примеры использования ===")
    
    # Пример 1: Простая функция
    print("\n1. Простая функция:")
    result1 = simple_function("Alice", 30)
    print(f"   Результат: {result1}")
    
    # Пример 2: Асинхронная функция
    print("\n2. Асинхронная функция:")
    result2 = await async_function({"key": "value"}, 0.5)
    print(f"   Результат: {result2}")
    
    # Пример 3: Функция с ошибкой
    print("\n3. Функция с ошибкой:")
    try:
        function_with_error("error")
    except ValueError as e:
        print(f"   Поймана ошибка: {e}")
    
    # Пример 4: Функция с чувствительными данными
    print("\n4. Функция с чувствительными данными:")
    sensitive_data = {
        "user_id": "12345",
        "username": "john_doe",
        "password": "secret_password",
        "api_key": "sk-1234567890abcdef"
    }
    result4 = function_with_sensitive_data(sensitive_data)
    print(f"   Результат: {result4}")
    
    # Пример 5: Сервис с методами
    print("\n5. Сервис с методами:")
    service = ExampleService()
    
    service.increment_counter(5)
    service.increment_counter(3)
    current = service.get_counter()
    print(f"   Счетчик: {current}")
    
    # Пример 6: Асинхронный метод сервиса
    print("\n6. Асинхронный метод сервиса:")
    async_result = await service.async_operation([1, 2, 3, 4, 5])
    print(f"   Результат: {async_result}")


def show_logging_config():
    """Показывает текущую конфигурацию логирования"""
    
    print("\n=== Текущая конфигурация логирования ===")
    config = get_logging_config()
    
    print(f"Уровень логирования: {config.log_level}")
    print(f"Формат логов: {config.log_format}")
    print(f"Файл логов: {config.log_file or 'stdout'}")
    print(f"Включенные модули: {config.enabled_modules}")
    print(f"Отключенные модули: {config.disabled_modules}")
    print(f"Включенные функции: {config.enabled_functions}")
    print(f"Отключенные функции: {config.disabled_functions}")


def show_environment_variables():
    """Показывает переменные окружения для настройки логирования"""
    
    print("\n=== Переменные окружения для настройки ===")
    print("LOG_ENABLED_MODULES=order_service,ai_service,command_service")
    print("LOG_DISABLED_MODULES=test_,debug_")
    print("LOG_ENABLED_FUNCTIONS=order_service.create_order,order_service.confirm_order")
    print("LOG_DISABLED_FUNCTIONS=order_service.get_order_status")
    print("LOG_LEVEL=INFO")
    print("LOG_FILE=app.log")
    print("LOG_FORMAT=json")
    print("ENVIRONMENT=development")


async def main():
    """Главная функция для запуска примеров"""
    
    print("🚀 Система логирования с декораторами")
    print("=" * 50)
    
    # Настройка логирования
    setup_logging_examples()
    
    # Показываем конфигурацию
    show_logging_config()
    
    # Запускаем примеры
    await run_examples()
    
    # Показываем переменные окружения
    show_environment_variables()
    
    print("\n✅ Примеры завершены!")
    print("\n📝 Логи будут выведены в консоль или файл в зависимости от настроек.")


if __name__ == "__main__":
    # Устанавливаем переменные окружения для примера
    os.environ["LOG_FORMAT"] = "text"  # Для читаемости в консоли
    os.environ["LOG_LEVEL"] = "INFO"
    
    # Запускаем примеры
    asyncio.run(main()) 
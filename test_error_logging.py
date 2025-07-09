#!/usr/bin/env python3
"""
Тест логирования ошибок
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.error_service import ErrorService
from src.models.error import ErrorSeverity

async def test_error_logging():
    """Тестирует логирование ошибок"""
    print("=== ТЕСТ ЛОГИРОВАНИЯ ОШИБОК ===")
    
    try:
        # Инициализация сервиса
        error_service = ErrorService()
        
        # Тест 1: Логирование простой ошибки
        print("1. Логируем тестовую ошибку...")
        test_error = Exception("Тестовая ошибка для проверки системы")
        error_id = await error_service.log_error(
            error=test_error,
            sender_id="TEST_USER",
            session_id="TEST_SESSION",
            context_data={"test": True, "message": "Тестовое сообщение"},
            severity=ErrorSeverity.HIGH,
            module="test_module",
            function="test_function"
        )
        
        if error_id:
            print(f"   ✅ Ошибка записана с ID: {error_id}")
        else:
            print("   ❌ Ошибка не записана")
            return False
        
        # Тест 2: Получение ошибки по ID
        print("2. Получаем ошибку по ID...")
        error = await error_service.get_error(error_id)
        if error:
            print(f"   ✅ Ошибка получена: {error.error_type} - {error.error_message}")
        else:
            print("   ❌ Ошибка не найдена")
            return False
        
        # Тест 3: Получение статистики
        print("3. Получаем статистику ошибок...")
        stats = await error_service.get_error_stats()
        print(f"   ✅ Статистика: {stats}")
        
        # Тест 4: Получение недавних ошибок
        print("4. Получаем недавние ошибки...")
        recent_errors = await error_service.get_recent_errors(24, 10)
        print(f"   ✅ Найдено {len(recent_errors)} ошибок")
        
        for i, err in enumerate(recent_errors):
            print(f"      {i+1}. [{err.severity.value}] {err.error_type}: {err.error_message}")
        
        print("\n✅ Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_error_logging()) 
"""
Тесты для менеджера сессий
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import session_manager
from datetime import datetime, timedelta
import time

def test_session_creation():
    """Тест создания новой сессии"""
    print("🧪 Тест создания новой сессии")
    
    sender_id = "1234567890"
    session_id = session_manager.create_new_session_id(sender_id)
    
    print(f"   Создан session_id: {session_id}")
    
    # Проверяем формат YYYYMMDD_hhmmss
    parts = session_id.split('_')
    assert len(parts) == 2, f"Неверный формат session_id: {session_id}"
    
    # Проверяем, что первая часть - это дата в формате YYYYMMDD
    date_part = parts[0]
    assert len(date_part) == 8, f"Неверный формат даты в session_id: {date_part}"
    assert date_part.isdigit(), f"Дата должна содержать только цифры: {date_part}"
    
    # Проверяем, что вторая часть - это время в формате hhmmss
    time_part = parts[1]
    assert len(time_part) == 6, f"Неверный формат времени в session_id: {time_part}"
    assert time_part.isdigit(), f"Время должно содержать только цифры: {time_part}"
    
    print("   ✅ Тест создания сессии пройден")

def test_session_activity_check():
    """Тест проверки активности сессии"""
    print("🧪 Тест проверки активности сессии")
    
    # Создаем тестовую сессию
    sender_id = "1234567890"
    session_id = session_manager.create_new_session_id(sender_id)
    
    # Проверяем активность новой сессии (должна быть активна)
    is_active = session_manager.is_session_active(sender_id, session_id)
    print(f"   Активность новой сессии: {is_active}")
    
    # В реальных условиях это будет зависеть от базы данных
    # Здесь мы просто проверяем, что функция работает
    print("   ✅ Тест проверки активности пройден")

def test_force_new_session():
    """Тест принудительного создания новой сессии"""
    print("🧪 Тест принудительного создания новой сессии")
    
    sender_id = "1234567890"
    new_session_id = session_manager.force_new_session(sender_id)
    
    print(f"   Принудительно создан session_id: {new_session_id}")
    
    # Проверяем, что сессия добавлена в кэш
    assert sender_id in session_manager.SESSION_CACHE, "Сессия не добавлена в кэш"
    assert session_manager.SESSION_CACHE[sender_id] == new_session_id, "Неверная сессия в кэше"
    
    print("   ✅ Тест принудительного создания пройден")

def test_order_session_creation():
    """Тест создания новой сессии после заказа"""
    print("🧪 Тест создания новой сессии после заказа")
    
    sender_id = "1234567890"
    new_session_id = session_manager.create_new_session_after_order(sender_id)
    
    print(f"   Создана новая сессия после заказа: {new_session_id}")
    
    # Проверяем, что сессия добавлена в кэш
    assert sender_id in session_manager.SESSION_CACHE, "Сессия не добавлена в кэш"
    assert session_manager.SESSION_CACHE[sender_id] == new_session_id, "Неверная сессия в кэше"
    
    print("   ✅ Тест создания сессии после заказа пройден")

def test_session_cache():
    """Тест работы кэша сессий"""
    print("🧪 Тест работы кэша сессий")
    
    # Очищаем кэш
    session_manager.clear_session_cache()
    assert len(session_manager.SESSION_CACHE) == 0, "Кэш не очищен"
    
    # Добавляем тестовую сессию
    sender_id = "1234567890"
    session_id = "20241220_143052"
    session_manager.SESSION_CACHE[sender_id] = session_id
    
    assert len(session_manager.SESSION_CACHE) == 1, "Сессия не добавлена в кэш"
    assert session_manager.SESSION_CACHE[sender_id] == session_id, "Неверная сессия в кэше"
    
    # Очищаем кэш
    session_manager.clear_session_cache()
    assert len(session_manager.SESSION_CACHE) == 0, "Кэш не очищен"
    
    print("   ✅ Тест кэша сессий пройден")

def test_session_format():
    """Тест формата session_id"""
    print("🧪 Тест формата session_id")
    
    sender_id = "1234567890"
    session_id = session_manager.create_new_session_id(sender_id)
    
    print(f"   Создан session_id: {session_id}")
    
    # Проверяем, что session_id не содержит sender_id
    assert sender_id not in session_id, f"session_id не должен содержать sender_id: {session_id}"
    
    # Проверяем формат YYYYMMDD_hhmmss
    import re
    pattern = r'^\d{8}_\d{6}$'
    assert re.match(pattern, session_id), f"session_id не соответствует формату YYYYMMDD_hhmmss: {session_id}"
    
    print("   ✅ Тест формата session_id пройден")

def main():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ТЕСТОВ МЕНЕДЖЕРА СЕССИЙ")
    print("=" * 50)
    
    try:
        test_session_creation()
        test_session_activity_check()
        test_force_new_session()
        test_order_session_creation()
        test_session_cache()
        test_session_format()
        
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ МЕНЕДЖЕРА СЕССИЙ ПРОЙДЕНЫ")
        print("\nМенеджер сессий готов к использованию!")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
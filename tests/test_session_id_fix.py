#!/usr/bin/env python3
"""
Тест для проверки исправленной логики session_id
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import session_manager, database
import time

def test_session_id_reuse():
    """Тест повторного использования session_id"""
    print("=== ТЕСТ ПОВТОРНОГО ИСПОЛЬЗОВАНИЯ SESSION_ID ===")
    
    # Очищаем кэш
    session_manager.clear_session_cache()
    
    sender_id = "test_user_123"
    
    # Первый вызов - должен создать новую сессию
    print(f"1. Первый вызов get_or_create_session_id для {sender_id}")
    session_id_1 = session_manager.get_or_create_session_id(sender_id)
    print(f"   Создан session_id: {session_id_1}")
    
    # Второй вызов - должен вернуть ту же сессию
    print(f"2. Второй вызов get_or_create_session_id для {sender_id}")
    session_id_2 = session_manager.get_or_create_session_id(sender_id)
    print(f"   Получен session_id: {session_id_2}")
    
    # Проверяем, что session_id одинаковые
    if session_id_1 == session_id_2:
        print("   ✅ Session_id совпадают - логика работает правильно!")
    else:
        print("   ❌ Session_id разные - есть проблема!")
        return False
    
    # Проверяем, что сессия сохранена в базе данных
    print(f"3. Проверка сохранения в базе данных")
    db_session_id = database.get_user_session_id(sender_id)
    print(f"   Session_id в БД: {db_session_id}")
    
    if db_session_id == session_id_1:
        print("   ✅ Session_id сохранен в базе данных!")
    else:
        print("   ❌ Session_id не сохранен в базе данных!")
        return False
    
    return True

def test_session_id_from_database():
    """Тест получения session_id из базы данных"""
    print("\n=== ТЕСТ ПОЛУЧЕНИЯ SESSION_ID ИЗ БАЗЫ ДАННЫХ ===")
    
    # Очищаем кэш
    session_manager.clear_session_cache()
    
    sender_id = "test_user_456"
    
    # Создаем сессию напрямую в базе данных
    test_session_id = "20241201_120000"
    print(f"1. Создаем сессию в базе данных: {sender_id} -> {test_session_id}")
    database.set_user_session_id(sender_id, test_session_id)
    # Добавляем тестовое сообщение, чтобы сессия считалась активной
    database.add_message(sender_id, test_session_id, "user", "Тестовое сообщение")
    
    # Очищаем кэш еще раз после создания сессии в БД
    session_manager.clear_session_cache()
    
    # Получаем сессию через менеджер
    print(f"2. Получаем сессию через get_or_create_session_id")
    retrieved_session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"   Получен session_id: {retrieved_session_id}")
    
    # Проверяем, что получена та же сессия
    if retrieved_session_id == test_session_id:
        print("   ✅ Получена правильная сессия из базы данных!")
    else:
        print("   ❌ Получена неправильная сессия!")
        return False
    
    return True

def test_session_activity_check():
    """Тест проверки активности сессии"""
    print("\n=== ТЕСТ ПРОВЕРКИ АКТИВНОСТИ СЕССИИ ===")
    
    sender_id = "test_user_789"
    session_id = "20241201_130000"
    
    # Создаем сессию
    database.set_user_session_id(sender_id, session_id)
    
    # Добавляем тестовое сообщение
    print(f"1. Добавляем тестовое сообщение в сессию {session_id}")
    database.add_message(sender_id, session_id, "user", "Тестовое сообщение")
    
    # Проверяем активность
    print(f"2. Проверяем активность сессии")
    is_active = session_manager.is_session_active(sender_id, session_id)
    print(f"   Сессия активна: {is_active}")
    
    if is_active:
        print("   ✅ Сессия правильно определена как активная!")
    else:
        print("   ❌ Сессия неправильно определена как неактивная!")
        return False
    
    return True

def main():
    """Запуск всех тестов"""
    print("🧪 ЗАПУСК ТЕСТОВ SESSION_ID")
    print("=" * 50)
    
    tests = [
        test_session_id_reuse,
        test_session_id_from_database,
        test_session_activity_check
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Тест {test.__name__} провален!")
        except Exception as e:
            print(f"❌ Тест {test.__name__} вызвал исключение: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Логика session_id работает правильно.")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
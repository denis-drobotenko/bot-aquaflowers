#!/usr/bin/env python3
"""
Тест сохранения новой сессии в базе данных после команды /newses
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

@pytest.mark.asyncio
async def test_newses_database():
    """Тестирует сохранение новой сессии в базе данных"""
    print("=== ТЕСТ СОХРАНЕНИЯ НОВОЙ СЕССИИ В БД ===")
    
    sender_id = "test_user_newses_db"
    
    # Тест 1: Получаем текущую сессию
    current_session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Текущая сессия: {current_session_id}")
    
    # Проверяем, что сессия сохранена в базе
    saved_session = database.get_user_session_id(sender_id)
    assert saved_session == current_session_id, f"Сессия не сохранена в БД. Ожидалось: {current_session_id}, получено: {saved_session}"
    print(f"✅ Сессия сохранена в БД: {saved_session}")
    
    # Тест 2: Добавляем сообщения в текущую сессию
    print("2. Добавляем сообщения в текущую сессию")
    database.add_message(sender_id, current_session_id, "user", "Тестовое сообщение")
    
    # Проверяем, что сообщение сохранилось
    history = database.get_conversation_history_for_ai(sender_id, current_session_id)
    assert len(history) >= 1, "Сообщение не сохранилось в БД"
    print(f"✅ В сессии {len(history)} сообщений")
    
    # Тест 3: Создаем новую сессию через команду /newses
    print("3. Создаем новую сессию через команду /newses")
    new_session_id = session_manager.create_new_session_after_order(sender_id)
    print(f"Новая сессия: {new_session_id}")
    
    # Тест 4: Проверяем, что новая сессия сохранилась в БД
    print("4. Проверяем сохранение новой сессии в БД")
    updated_session = database.get_user_session_id(sender_id)
    assert updated_session == new_session_id, f"Новая сессия не обновилась в БД. Ожидалось: {new_session_id}, получено: {updated_session}"
    print(f"✅ Новая сессия обновилась в БД: {updated_session}")
    
    # Тест 5: Проверяем, что новая сессия отличается от старой
    assert new_session_id != current_session_id, "Новая сессия должна отличаться от старой"
    print("✅ Новая сессия отличается от старой")
    
    # Тест 6: Проверяем, что в новой сессии нет сообщений
    new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
    assert len(new_history) == 0, f"Новая сессия должна быть пустой, но содержит {len(new_history)} сообщений"
    print("✅ Новая сессия пустая")
    
    # Тест 7: Проверяем, что старая сессия осталась нетронутой
    old_history = database.get_conversation_history_for_ai(sender_id, current_session_id)
    assert len(old_history) >= 1, f"Старая сессия должна содержать минимум 1 сообщение, но содержит {len(old_history)}"
    print("✅ Старая сессия осталась нетронутой")
    
    # Тест 8: Проверяем кэш сессий
    print("5. Проверяем кэш сессий")
    from src.session_manager import SESSION_CACHE
    cached_session = SESSION_CACHE.get(sender_id)
    assert cached_session == new_session_id, f"Кэш не обновился. Ожидалось: {new_session_id}, получено: {cached_session}"
    print(f"✅ Кэш обновился: {cached_session}")
    
    # Тест 9: Проверяем, что get_or_create_session_id возвращает новую сессию
    print("6. Проверяем get_or_create_session_id")
    active_session = session_manager.get_or_create_session_id(sender_id)
    assert active_session == new_session_id, f"get_or_create_session_id должен возвращать новую сессию. Ожидалось: {new_session_id}, получено: {active_session}"
    print(f"✅ get_or_create_session_id возвращает новую сессию: {active_session}")
    
    # Тест 10: Добавляем сообщение в новую сессию и проверяем
    print("7. Добавляем сообщение в новую сессию")
    database.add_message(sender_id, new_session_id, "user", "Сообщение в новой сессии")
    
    final_new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
    assert len(final_new_history) == 1, f"В новой сессии должно быть 1 сообщение, но есть {len(final_new_history)}"
    print("✅ Сообщение добавлено в новую сессию")
    
    print("\n=== ВСЕ ТЕСТЫ СОХРАНЕНИЯ В БД ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_newses_database()) 
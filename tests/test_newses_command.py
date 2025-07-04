#!/usr/bin/env python3
"""
Тест команды /newses для создания новой сессии
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

@pytest.mark.asyncio
async def test_newses_command():
    """Тестирует команду /newses для создания новой сессии"""
    print("=== ТЕСТ КОМАНДЫ /NEWSES ===")
    
    sender_id = "test_user_newses"
    
    # Тест 1: Получаем текущую сессию
    current_session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Текущая сессия: {current_session_id}")
    
    # Тест 2: Добавляем несколько сообщений в текущую сессию
    messages = [
        "Привет! Хочу заказать букет.",
        "Покажите каталог",
        "Мне нравится розовый букет"
    ]
    
    print("2. Добавляем сообщения в текущую сессию")
    for i, msg in enumerate(messages):
        database.add_message(sender_id, current_session_id, "user", msg)
        time.sleep(0.1)
    
    # Проверяем, что сообщения сохранились
    history = database.get_conversation_history_for_ai(sender_id, current_session_id)
    assert len(history) >= len(messages), f"Ожидалось {len(messages)} сообщений, получено {len(history)}"
    print(f"✅ В текущей сессии {len(history)} сообщений")
    
    # Тест 3: Создаем новую сессию через команду /newses
    print("3. Создаем новую сессию через команду /newses")
    new_session_id = session_manager.create_new_session_after_order(sender_id)
    print(f"Новая сессия: {new_session_id}")
    
    # Проверяем, что новая сессия отличается от старой
    assert new_session_id != current_session_id, "Новая сессия должна отличаться от старой"
    print("✅ Новая сессия отличается от старой")
    
    # Тест 4: Проверяем, что в новой сессии нет сообщений
    new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
    assert len(new_history) == 0, f"Новая сессия должна быть пустой, но содержит {len(new_history)} сообщений"
    print("✅ Новая сессия пустая")
    
    # Тест 5: Проверяем, что старая сессия осталась нетронутой
    old_history = database.get_conversation_history_for_ai(sender_id, current_session_id)
    assert len(old_history) >= len(messages), f"Старая сессия должна содержать {len(messages)} сообщений, но содержит {len(old_history)}"
    print("✅ Старая сессия осталась нетронутой")
    
    # Тест 6: Добавляем сообщение в новую сессию
    print("4. Добавляем сообщение в новую сессию")
    database.add_message(sender_id, new_session_id, "user", "Это сообщение в новой сессии")
    
    new_history_after = database.get_conversation_history_for_ai(sender_id, new_session_id)
    assert len(new_history_after) == 1, f"В новой сессии должно быть 1 сообщение, но есть {len(new_history_after)}"
    print("✅ Сообщение добавлено в новую сессию")
    
    # Тест 7: Проверяем, что сессии независимы
    old_history_after = database.get_conversation_history_for_ai(sender_id, current_session_id)
    assert len(old_history_after) >= len(messages), f"Старая сессия должна содержать {len(messages)} сообщений, но содержит {len(old_history_after)}"
    print("✅ Сессии независимы")
    
    print("\n=== ВСЕ ТЕСТЫ /NEWSES ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_newses_command()) 
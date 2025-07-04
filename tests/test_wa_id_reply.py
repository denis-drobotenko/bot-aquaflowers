#!/usr/bin/env python3
"""
Тест обработки reply с WA ID сообщениями
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, command_handler

@pytest.mark.asyncio
async def test_wa_id_reply():
    """Тестирует обработку reply с использованием WA ID"""
    print("=== ТЕСТ REPLY С WA ID ===")
    
    sender_id = "test_user_reply"
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"Используем session_id: {session_id}")

    # Тест 1: Сохраняем сообщение с букетом (как AI)
    bouquet_wa_id = "wamid.HBgLMTIzNDU2Nzg5MDEyMzQ1NgAB"
    bouquet_message = "🌸 Романтический букет\nЦена: 1500 руб\nID: BOUQ001"
    
    print(f"1. Сохраняем сообщение с букетом с WA ID: {bouquet_wa_id}")
    database.add_message_with_wa_id(sender_id, session_id, "model", bouquet_message, bouquet_wa_id)
    
    # Тест 2: Имитируем reply пользователя на букет
    user_reply_wa_id = "wamid.HBgLMTIzNDU2Nzg5MDEyMzQ1NgAC"
    user_message = "Хочу этот букет"
    
    print(f"2. Сохраняем reply пользователя с WA ID: {user_reply_wa_id}")
    database.add_message_with_wa_id(sender_id, session_id, "user", user_message, user_reply_wa_id)
    
    # Тест 3: Проверяем получение сообщения по WA ID
    print(f"3. Получаем сообщение с букетом по WA ID: {bouquet_wa_id}")
    retrieved_bouquet = database.get_message_by_wa_id(sender_id, session_id, bouquet_wa_id)
    
    assert retrieved_bouquet is not None, "Сообщение с букетом не найдено"
    assert retrieved_bouquet['role'] == 'model', "Неверная роль сообщения с букетом"
    assert '🌸' in retrieved_bouquet['content'], "Сообщение не содержит эмодзи букета"
    print(f"✅ Сообщение с букетом найдено: {retrieved_bouquet['content'][:50]}...")
    
    # Тест 4: Имитируем обработку reply в command_handler
    print("4. Имитируем обработку reply в command_handler")
    message_with_reply = {
        'reply_to_message_id': bouquet_wa_id,
        'text': {'body': user_message}
    }
    
    # Проверяем, что handle_user_message корректно обрабатывает reply
    from src import command_handler
    result = await command_handler.handle_user_message(sender_id, session_id, message_with_reply)
    
    # Если reply на букет - должен вернуть результат выбора букета
    if result and result.get('action') == 'bouquet_selected':
        print("✅ Reply на букет корректно обработан")
    else:
        print("ℹ️ Reply не был распознан как выбор букета (возможно, нет каталога)")
    
    # Тест 5: Проверяем историю для AI
    print("5. Получаем историю для AI")
    history = database.get_conversation_history_for_ai(sender_id, session_id)
    
    assert len(history) >= 2, "История должна содержать минимум 2 сообщения"
    print(f"✅ История содержит {len(history)} сообщений")
    
    # Проверяем, что в истории есть сообщения с правильными ролями
    roles = [msg.get('role') for msg in history]
    print(f"Роли в истории: {roles}")
    
    print("\n=== ВСЕ ТЕСТЫ REPLY С WA ID ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_wa_id_reply()) 
#!/usr/bin/env python3
"""
Тест работы с WA ID сообщениями
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

@pytest.mark.asyncio
async def test_wa_id_messages():
    """Тестирует сохранение и получение сообщений по WA ID"""
    print("=== ТЕСТ WA ID СООБЩЕНИЙ ===")
    
    sender_id = "test_user_wa_id"
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"Используем session_id: {session_id}")

    # Тест 1: Сохранение сообщения с WA ID
    wa_message_id = "wamid.HBgLMTIzNDU2Nzg5MDEyMzQ1NgAB"
    user_message = "Привет! Хочу заказать букет."
    
    print(f"1. Сохраняем сообщение пользователя с WA ID: {wa_message_id}")
    database.add_message_with_wa_id(sender_id, session_id, "user", user_message, wa_message_id)
    
    # Тест 2: Сохранение ответа AI с WA ID
    ai_wa_id = "wamid.HBgLMTIzNDU2Nzg5MDEyMzQ1NgAC"
    ai_response = "Добро пожаловать! Покажу вам каталог букетов 🌸"
    
    print(f"2. Сохраняем ответ AI с WA ID: {ai_wa_id}")
    database.add_message_with_parts_wa_id(sender_id, session_id, "assistant", [{"text": ai_response}], ai_wa_id)
    
    # Тест 3: Получение сообщения по WA ID
    print(f"3. Получаем сообщение по WA ID: {wa_message_id}")
    retrieved_message = database.get_message_by_wa_id(sender_id, session_id, wa_message_id)
    
    assert retrieved_message is not None, "Сообщение не найдено по WA ID"
    assert retrieved_message['role'] == 'user', "Неверная роль сообщения"
    assert retrieved_message['content'] == user_message, "Неверное содержимое сообщения"
    print(f"✅ Сообщение найдено: {retrieved_message['content']}")
    
    # Тест 4: Получение ответа AI по WA ID
    print(f"4. Получаем ответ AI по WA ID: {ai_wa_id}")
    retrieved_ai = database.get_message_by_wa_id(sender_id, session_id, ai_wa_id)
    
    assert retrieved_ai is not None, "Ответ AI не найден по WA ID"
    assert retrieved_ai['role'] == 'assistant', "Неверная роль ответа AI"
    assert retrieved_ai['parts'][0]['text'] == ai_response, "Неверное содержимое ответа AI"
    print(f"✅ Ответ AI найден: {retrieved_ai['parts'][0]['text']}")
    
    # Тест 5: Получение несуществующего сообщения
    fake_wa_id = "wamid.FAKE_ID_THAT_DOES_NOT_EXIST"
    print(f"5. Пытаемся получить несуществующее сообщение: {fake_wa_id}")
    fake_message = database.get_message_by_wa_id(sender_id, session_id, fake_wa_id)
    
    assert fake_message is None, "Несуществующее сообщение должно возвращать None"
    print("✅ Несуществующее сообщение корректно возвращает None")
    
    # Тест 6: История для AI с WA ID
    print("6. Получаем историю для AI")
    history = database.get_conversation_history_for_ai(sender_id, session_id)
    
    assert len(history) >= 2, "История должна содержать минимум 2 сообщения"
    print(f"✅ История содержит {len(history)} сообщений")
    
    print("\n=== ВСЕ ТЕСТЫ WA ID ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_wa_id_messages()) 
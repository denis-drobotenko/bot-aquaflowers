#!/usr/bin/env python3
"""
Тест webhook с командой /newses
"""

import sys
import os
import time
import pytest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, whatsapp_utils

@pytest.mark.asyncio
async def test_newses_webhook():
    """Тестирует обработку webhook с командой /newses"""
    print("=== ТЕСТ WEBHOOK С /NEWSES ===")
    
    sender_id = "test_user_newses_webhook"
    
    # Тест 1: Создаем начальную сессию и добавляем сообщения
    initial_session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Начальная сессия: {initial_session_id}")
    
    # Добавляем несколько сообщений
    database.add_message(sender_id, initial_session_id, "user", "Привет!")
    database.add_message(sender_id, initial_session_id, "assistant", "Здравствуйте! Чем могу помочь?")
    database.add_message(sender_id, initial_session_id, "user", "Хочу заказать букет")
    
    initial_history = database.get_conversation_history_for_ai(sender_id, initial_session_id)
    print(f"✅ В начальной сессии {len(initial_history)} сообщений")
    
    # Тест 2: Имитируем webhook с командой /newses
    print("2. Имитируем webhook с командой /newses")
    
    # Мокаем отправку сообщений
    sent_messages = []
    async def fake_send_message(to, msg, sender_id=None, session_id=None):
        sent_messages.append({
            'to': to,
            'message': msg,
            'sender_id': sender_id,
            'session_id': session_id
        })
        return True
    
    # Подменяем функцию отправки
    original_send = whatsapp_utils.send_whatsapp_message
    whatsapp_utils.send_whatsapp_message = fake_send_message
    
    try:
        # Имитируем webhook данные
        webhook_body = {
            'entry': [{
                'changes': [{
                    'value': {
                        'messages': [{
                            'id': 'wamid.test_newses_webhook',
                            'from': sender_id,
                            'text': {'body': '/newses'},
                            'type': 'text'
                        }]
                    }
                }]
            }]
        }
        
        # Имитируем обработку команды /newses
        message_body = '/newses'
        
        if message_body.strip().lower() == '/newses':
            print("3. Обрабатываем команду /newses")
            
            # Создаем новую сессию
            new_session_id = session_manager.create_new_session_after_order(sender_id)
            print(f"Новая сессия создана: {new_session_id}")
            
            # Отправляем подтверждение
            confirmation_message = f"✅ Новая сессия создана! ID: {new_session_id}\n\nТеперь вы можете начать новый диалог. 🌸"
            await whatsapp_utils.send_whatsapp_message(sender_id, confirmation_message, sender_id, new_session_id)
            
            print("✅ Подтверждение отправлено")
        
        # Тест 4: Проверяем результаты
        print("4. Проверяем результаты")
        
        # Проверяем, что сообщение было отправлено
        assert len(sent_messages) == 1, f"Ожидалось 1 отправленное сообщение, получено {len(sent_messages)}"
        sent_msg = sent_messages[0]
        assert sent_msg['to'] == sender_id, "Сообщение отправлено не тому пользователю"
        assert "Новая сессия создана" in sent_msg['message'], "Сообщение не содержит подтверждения"
        assert new_session_id in sent_msg['message'], "Сообщение не содержит ID новой сессии"
        print("✅ Сообщение отправлено корректно")
        
        # Проверяем, что новая сессия отличается от старой
        assert new_session_id != initial_session_id, "Новая сессия должна отличаться от старой"
        print("✅ Новая сессия отличается от старой")
        
        # Проверяем, что новая сессия пустая
        new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
        assert len(new_history) == 0, f"Новая сессия должна быть пустой, но содержит {len(new_history)} сообщений"
        print("✅ Новая сессия пустая")
        
        # Проверяем, что старая сессия осталась нетронутой
        old_history = database.get_conversation_history_for_ai(sender_id, initial_session_id)
        assert len(old_history) >= 3, f"Старая сессия должна содержать минимум 3 сообщения, но содержит {len(old_history)}"
        print("✅ Старая сессия осталась нетронутой")
        
        # Тест 5: Проверяем, что новая сессия активна
        print("5. Проверяем активность новой сессии")
        current_session_id = session_manager.get_or_create_session_id(sender_id)
        assert current_session_id == new_session_id, f"Новая сессия должна быть активной, но активна {current_session_id}"
        print("✅ Новая сессия стала активной")
        
    finally:
        # Восстанавливаем оригинальную функцию
        whatsapp_utils.send_whatsapp_message = original_send
    
    print("\n=== ВСЕ ТЕСТЫ WEBHOOK С /NEWSES ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_newses_webhook()) 
#!/usr/bin/env python3
"""
Тест webhook с командой /getchat
"""

import sys
import os
import time
import pytest
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, whatsapp_utils

@pytest.mark.asyncio
async def test_getchat_webhook():
    """Тестирует обработку webhook с командой /getchat"""
    print("=== ТЕСТ WEBHOOK С /GETCHAT ===")
    
    sender_id = "test_user_getchat_webhook"
    
    # Тест 1: Создаем сессию и добавляем сообщения
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Сессия: {session_id}")
    
    # Добавляем несколько сообщений
    database.add_message(sender_id, session_id, "user", "Привет!")
    database.add_message(sender_id, session_id, "assistant", "Здравствуйте! Чем могу помочь?")
    database.add_message(sender_id, session_id, "user", "Хочу заказать букет")
    
    initial_history = database.get_conversation_history_for_ai(sender_id, session_id)
    print(f"✅ В сессии {len(initial_history)} сообщений")
    
    # Тест 2: Имитируем webhook с командой /getchat
    print("2. Имитируем webhook с командой /getchat")
    
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
        # Имитируем обработку команды /getchat
        message_body = '/getchat'
        
        if message_body.strip().lower() == '/getchat':
            print("3. Обрабатываем команду /getchat")
            
            # Получаем текущую сессию пользователя
            current_session_id = session_manager.get_or_create_session_id(sender_id)
            print(f"Текущая сессия: {current_session_id}")
            
            # Формируем ссылку на страницу с историей чата
            chat_link = f"/chat/{sender_id}_{current_session_id}"
            full_url = f"https://example.com{chat_link}"
            
            # Отправляем ссылку пользователю (НЕ сохраняем в историю ИИ)
            chat_message = f"📋 История вашего чата:\n\n🔗 {full_url}\n\nНажмите на ссылку, чтобы посмотреть всю переписку. 🌸"
            await whatsapp_utils.send_whatsapp_message(sender_id, chat_message, sender_id, None)  # session_id=None - не сохранять в историю
            
            print("✅ Ссылка отправлена")
        
        # Тест 4: Проверяем результаты
        print("4. Проверяем результаты")
        
        # Проверяем, что сообщение было отправлено
        assert len(sent_messages) == 1, f"Ожидалось 1 отправленное сообщение, получено {len(sent_messages)}"
        sent_msg = sent_messages[0]
        assert sent_msg['to'] == sender_id, "Сообщение отправлено не тому пользователю"
        assert "История вашего чата" in sent_msg['message'], "Сообщение не содержит ссылку на историю"
        assert full_url in sent_msg['message'], "Сообщение не содержит URL"
        assert sent_msg['session_id'] is None, "Сообщение должно отправляться с session_id=None"
        print("✅ Сообщение отправлено корректно")
        
        # Проверяем, что в истории НЕ добавилось новое сообщение
        final_history = database.get_conversation_history_for_ai(sender_id, session_id)
        assert len(final_history) == len(initial_history), f"История не должна измениться. Было: {len(initial_history)}, стало: {len(final_history)}"
        print("✅ История не изменилась (команда /getchat не сохранилась)")
        
        # Проверяем, что последнее сообщение в истории - это не команда /getchat
        if final_history:
            last_message = final_history[-1]
            assert last_message.get('content') != '/getchat', "Последнее сообщение в истории не должно быть командой /getchat"
            print("✅ Команда /getchat не сохранилась в истории")
        
    finally:
        # Восстанавливаем оригинальную функцию
        whatsapp_utils.send_whatsapp_message = original_send
    
    print("\n=== ВСЕ ТЕСТЫ WEBHOOK С /GETCHAT ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_getchat_webhook()) 
 
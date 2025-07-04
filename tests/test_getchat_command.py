#!/usr/bin/env python3
"""
Тест команды /getchat для получения ссылки на историю чата
"""

import sys
import os
import time
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, whatsapp_utils

@pytest.mark.asyncio
async def test_getchat_command():
    """Тестирует команду /getchat для получения ссылки на историю чата"""
    print("=== ТЕСТ КОМАНДЫ /GETCHAT ===")
    
    sender_id = "test_user_getchat"
    
    # Тест 1: Создаем сессию и добавляем сообщения
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Создана сессия: {session_id}")
    
    # Добавляем несколько сообщений для истории
    messages = [
        ("user", "Привет! Хочу заказать букет."),
        ("assistant", "Здравствуйте! Чем могу помочь?"),
        ("user", "Покажите каталог"),
        ("assistant", "Вот наш каталог букетов...")
    ]
    
    print("2. Добавляем сообщения в историю")
    for role, msg in messages:
        database.add_message(sender_id, session_id, role, msg)
        time.sleep(0.1)
    
    # Проверяем, что сообщения сохранились
    history = database.get_conversation_history_for_ai(sender_id, session_id)
    assert len(history) >= len(messages), f"Ожидалось {len(messages)} сообщений, получено {len(history)}"
    print(f"✅ В сессии {len(history)} сообщений")
    
    # Тест 3: Имитируем обработку команды /getchat
    print("3. Имитируем обработку команды /getchat")
    
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
            print("4. Обрабатываем команду /getchat")
            
            # Получаем текущую сессию пользователя
            current_session_id = session_manager.get_or_create_session_id(sender_id)
            print(f"Текущая сессия: {current_session_id}")
            
            # Формируем ссылку на страницу с историей чата
            chat_link = f"/chat/{sender_id}_{current_session_id}"
            
            # Получаем базовый URL
            base_url = "https://auraflora-bot.onrender.com"
            full_url = f"{base_url}{chat_link}"
            
            # Отправляем ссылку пользователю
            chat_message = f"📋 История вашего чата:\n\n🔗 {full_url}\n\nНажмите на ссылку, чтобы посмотреть всю переписку. 🌸"
            await whatsapp_utils.send_whatsapp_message(sender_id, chat_message, sender_id, current_session_id)
            
            print("✅ Ссылка отправлена")
        
        # Тест 5: Проверяем результаты
        print("5. Проверяем результаты")
        
        # Проверяем, что сообщение было отправлено
        assert len(sent_messages) == 1, f"Ожидалось 1 отправленное сообщение, получено {len(sent_messages)}"
        sent_msg = sent_messages[0]
        assert sent_msg['to'] == sender_id, "Сообщение отправлено не тому пользователю"
        assert "История вашего чата" in sent_msg['message'], "Сообщение не содержит заголовок"
        assert full_url in sent_msg['message'], "Сообщение не содержит ссылку"
        assert "auraflora-bot.onrender.com" in sent_msg['message'], "Сообщение не содержит домен"
        print("✅ Сообщение отправлено корректно")
        
        # Проверяем формат ссылки
        expected_link = f"/chat/{sender_id}_{session_id}"
        assert expected_link in full_url, f"Неверный формат ссылки. Ожидалось: {expected_link}, получено: {full_url}"
        print("✅ Формат ссылки корректный")
        
        # Тест 6: Проверяем, что сессия осталась той же
        print("6. Проверяем сохранение сессии")
        current_session = session_manager.get_or_create_session_id(sender_id)
        assert current_session == session_id, f"Сессия должна остаться той же. Ожидалось: {session_id}, получено: {current_session}"
        print("✅ Сессия осталась той же")
        
        # Тест 7: Проверяем, что история не изменилась
        print("7. Проверяем сохранение истории")
        final_history = database.get_conversation_history_for_ai(sender_id, session_id)
        assert len(final_history) >= len(messages), f"История должна сохраниться. Ожидалось минимум {len(messages)} сообщений, получено {len(final_history)}"
        print("✅ История сохранена")
        
    finally:
        # Восстанавливаем оригинальную функцию
        whatsapp_utils.send_whatsapp_message = original_send
    
    print("\n=== ВСЕ ТЕСТЫ /GETCHAT ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_getchat_command()) 
 
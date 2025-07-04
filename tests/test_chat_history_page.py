#!/usr/bin/env python3
"""
Тест страницы истории чата
"""

import sys
import os
import pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, template_utils

@pytest.mark.asyncio
async def test_chat_history_page():
    """Тестирует работу страницы истории чата"""
    print("=== ТЕСТ СТРАНИЦЫ ИСТОРИИ ЧАТА ===")
    
    sender_id = "test_user_chat_history"
    
    # Создаем сессию
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Сессия: {session_id}")
    
    # Добавляем тестовые сообщения (старый формат)
    old_messages = [
        ("user", "Привет! Хочу заказать букет."),
        ("assistant", "Здравствуйте! Сейчас покажу вам наш каталог цветов."),
        ("user", "Покажите каталог"),
        ("assistant", "Отправляю каталог...")
    ]
    
    print("2. Добавляем сообщения старого формата")
    for role, content in old_messages:
        database.add_message(sender_id, session_id, role, content)
        print(f"   [{role}] {content}")
    
    # Добавляем сообщения нового формата (parts)
    new_messages = [
        ("user", "Мне нравится букет Spirit"),
        ("assistant", "Отлично! Записал ваш выбор букета 'Spirit'. Нужна ли доставка?")
    ]
    
    print("3. Добавляем сообщения нового формата (parts)")
    for role, content in new_messages:
        database.add_message_with_parts(sender_id, session_id, role, [{"text": content}])
        print(f"   [{role}] {content}")
    
    # Получаем историю для отображения
    print("4. Получаем историю для отображения")
    history = database.get_conversation_history(sender_id, session_id, limit=10)
    print(f"   Получено сообщений: {len(history)}")
    
    for i, msg in enumerate(history, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        print(f"   {i}. [{role}] {content[:50]}...")
    
    # Тестируем обработку сообщений в HTML
    print("5. Тестируем обработку в HTML")
    messages_html = template_utils.process_chat_messages(history)
    
    if messages_html:
        print(f"   ✅ HTML сгенерирован успешно")
        print(f"   Длина HTML: {len(messages_html)} символов")
        
        # Проверяем, что в HTML есть сообщения пользователя и ассистента
        if 'message user' in messages_html:
            print("   ✅ Сообщения пользователя найдены в HTML")
        else:
            print("   ❌ Сообщения пользователя не найдены в HTML")
            
        if 'message model' in messages_html or 'message assistant' in messages_html:
            print("   ✅ Сообщения ассистента найдены в HTML")
        else:
            print("   ❌ Сообщения ассистента не найдены в HTML")
    else:
        print("   ❌ HTML не сгенерирован")
    
    # Формируем ссылку на страницу истории
    chat_link = f"/chat/{sender_id}_{session_id}"
    print(f"\n🔗 Ссылка на страницу истории:")
    print(f"   {chat_link}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")
    
    return len(history) > 0

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_chat_history_page()) 
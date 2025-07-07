#!/usr/bin/env python3
"""
Тест что команда /newses не сохраняется в БД
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.message_processor import MessageProcessor

async def test_newses_no_save():
    """Тестируем что команда /newses не сохраняется в БД"""
    print("=== Тест команды /newses без сохранения в БД ===")
    
    # Тестовые данные
    sender_id = "79140775712"
    message_text = "/newses"
    sender_name = "Денис"
    
    print(f"1. Симулируем обработку команды /newses...")
    
    # Создаем обработчик
    message_processor = MessageProcessor()
    
    # Обрабатываем команду /newses
    message_data = {
        'sender_id': sender_id,
        'message_text': message_text,
        'sender_name': sender_name
    }
    success = await message_processor.process_user_message(message_data)
    
    print(f"   Результат обработки: {success}")
    
    print(f"\n2. Симулируем отправку через webhook flow...")
    
    # Получаем session_id как в webhook
    session_id = await message_processor.session_service.get_or_create_session_id(sender_id)
    print(f"   Session ID: {session_id}")
    
    # Отправляем сообщение как в webhook для /newses (save_to_db=False)
    success = await message_processor.send_message(
        sender_id,
        ai_response,
        msg_type="text",
        save_to_db=False,  # НЕ сохраняем ответ /newses в БД
        session_id=session_id,
        sender_id=sender_id,
        content_en=ai_response_en,
        content_thai=ai_response_thai
    )
    
    print(f"   Результат отправки: {success}")
    
    if success:
        print(f"   ✅ Сообщение отправлено")
        
        # Проверяем что сообщение НЕ сохранилось в БД
        print(f"\n3. Проверяем что сообщение НЕ сохранилось в БД...")
        
        from src.repositories.message_repository import MessageRepository
        message_repo = MessageRepository()
        
        # Получаем последние сообщения
        messages = await message_repo.get_conversation_history_by_sender(sender_id, session_id, limit=5)
        
        print(f"   Найдено сообщений: {len(messages)}")
        
        # Ищем наше сообщение
        found_newses_response = False
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')[:50]
            wa_message_id = msg.get('wa_message_id')
            
            print(f"   [{role}] {content}")
            print(f"       wa_message_id: {wa_message_id}")
            print()
            
            if role == 'assistant' and "Новая сессия создана" in content:
                found_newses_response = True
                print(f"   ❌ НАЙДЕНО сообщение /newses в БД - это ошибка!")
                break
        
        if not found_newses_response:
            print(f"   ✅ Сообщение /newses НЕ найдено в БД - правильно!")
        else:
            print(f"   ❌ Сообщение /newses найдено в БД - это ошибка!")
    else:
        print(f"   ❌ Сообщение НЕ отправлено!")

if __name__ == "__main__":
    asyncio.run(test_newses_no_save()) 
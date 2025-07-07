#!/usr/bin/env python3
"""
Тест универсальной обработки реплаев
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_reply_handling():
    """Тестирует универсальную обработку реплаев"""
    try:
        from src.services.message_processor import MessageProcessor
        from services.message_service import MessageService
        from services.session_service import SessionService
        from models.message import Message, MessageRole
        
        # Создаем обработчики
        message_processor = MessageProcessor()
        message_service = MessageService()
        session_service = SessionService()
        
        # Тестовые данные
        sender_id = "79140775712"
        
        print("🧪 Тестируем универсальную обработку реплаев")
        
        # 1. Получаем или создаем сессию для тестирования
        print("\n1. Получаем сессию для тестирования...")
        session_id = await session_service.get_or_create_session_id(sender_id)
        print(f"✅ Используем сессию: {session_id}")
        
        # 2. Создаем тестовые сообщения в БД
        print("\n2. Создаем тестовые сообщения...")
        
        # Сообщение с букетом
        bouquet_message = Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content="Love is on the air\n2 200,00 ฿ 🌸",
            wa_message_id="wamid.bouquet_message"
        )
        await message_service.add_message_to_conversation(bouquet_message)
        
        # Обычное сообщение
        regular_message = Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content="Привет! Как дела?",
            wa_message_id="wamid.regular_message"
        )
        await message_service.add_message_to_conversation(regular_message)
        
        # Сообщение от пользователя
        user_message = Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.USER,
            content="Хорошо, спасибо!",
            wa_message_id="wamid.user_message"
        )
        await message_service.add_message_to_conversation(user_message)
        
        print("✅ Тестовые сообщения созданы")
        
        # 3. Проверяем историю
        print("\n3. Проверяем историю диалога...")
        history = await message_service.get_conversation_history_for_ai_by_sender(sender_id, session_id, limit=10)
        print(f"✅ История содержит {len(history)} сообщений:")
        for i, msg in enumerate(history[-3:], 1):  # Показываем только последние 3
            print(f"  {i}. [{msg.get('role')}] {msg.get('content', '')[:50]}...")
        
        # 4. Тестируем реплай на сообщение с букетом
        print("\n4. Тестируем реплай на сообщение с букетом...")
        user_reply = "Хочу этот букет"
        
        result = await message_handler.process_text_message(
            sender_id, user_reply, "Test User", "wamid.user_reply", "wamid.bouquet_message"
        )
        
        if result:
            response, response_en, response_thai, command = result
            print(f"✅ Реплай на букет обработан!")
            print(f"Ответ: {response[:100]}...")
        else:
            print("❌ Реплай на букет не обработан")
        
        # 5. Тестируем реплай на обычное сообщение
        print("\n5. Тестируем реплай на обычное сообщение...")
        user_reply2 = "Отлично!"
        
        result2 = await message_handler.process_text_message(
            sender_id, user_reply2, "Test User", "wamid.user_reply2", "wamid.regular_message"
        )
        
        if result2:
            response, response_en, response_thai, command = result2
            print(f"✅ Реплай на обычное сообщение обработан!")
            print(f"Ответ: {response[:100]}...")
        else:
            print("❌ Реплай на обычное сообщение не обработан")
        
        # 6. Тестируем обычное сообщение без реплая
        print("\n6. Тестируем обычное сообщение без реплая...")
        regular_user_message = "Привет!"
        
        result3 = await message_handler.process_text_message(
            sender_id, regular_user_message, "Test User", "wamid.regular_user_message"
        )
        
        if result3:
            response, response_en, response_thai, command = result3
            print(f"✅ Обычное сообщение обработано!")
            print(f"Ответ: {response[:100]}...")
        else:
            print("❌ Обычное сообщение не обработано")
        
        print("\n🎉 Все тесты завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_reply_handling()) 
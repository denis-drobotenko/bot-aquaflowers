#!/usr/bin/env python3
"""
Тест для проверки правильной передачи истории диалога к AI
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_ai_history():
    """Тестирует правильную передачу истории диалога к AI"""
    print("=== ТЕСТ ПЕРЕДАЧИ ИСТОРИИ К AI ===")
    
    try:
        # Инициализация сервисов
        message_service = MessageService()
        session_service = SessionService()
        ai_service = AIService(GEMINI_API_KEY)
        
        # Тест 1: Создание сессии
        test_sender_id = "79140775712"
        session_id = await session_service.get_or_create_session_id(test_sender_id)
        
        if session_id:
            print(f"✅ Создана сессия: {session_id}")
        else:
            print("❌ Сессия не создана")
            return False
            
        # Тест 2: Добавление сообщений в conversations
        test_messages = [
            Message(
                sender_id=test_sender_id,
                session_id=session_id,
                role=MessageRole.USER,
                content="Привет! Хочу заказать букет"
            ),
            Message(
                sender_id=test_sender_id,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content="Здравствуйте! Добро пожаловать в AuraFlORA! Хотите посмотреть наш каталог цветов?"
            ),
            Message(
                sender_id=test_sender_id,
                session_id=session_id,
                role=MessageRole.USER,
                content="Да, покажите каталог"
            )
        ]
        
        print("2. Добавляем сообщения в conversations...")
        for i, msg in enumerate(test_messages):
            result = await message_service.add_message_to_conversation(msg)
            if result:
                print(f"   ✅ Сообщение {i+1} добавлено")
            else:
                print(f"   ❌ Сообщение {i+1} не добавлено")
                return False
        
        # Ждем индексации Firestore
        print("3. Ждем индексации Firestore...")
        await asyncio.sleep(2)
        
        # Тест 4: Получение истории для AI
        print("4. Получаем историю для AI...")
        conversation_history = await message_service.get_conversation_history_for_ai_by_sender(test_sender_id, session_id, limit=10)
        
        if conversation_history:
            print(f"   ✅ История получена: {len(conversation_history)} сообщений")
            for i, msg in enumerate(conversation_history):
                print(f"      {i+1}. [{msg.get('role')}] {msg.get('content', '')[:50]}...")
        else:
            print("   ❌ История не получена")
            return False
        
        # Тест 5: Конвертация в объекты Message
        print("5. Конвертируем в объекты Message...")
        ai_messages = []
        for msg_dict in conversation_history:
            message = Message(
                sender_id=test_sender_id,
                session_id=session_id,
                role=MessageRole.USER if msg_dict.get('role') == 'user' else MessageRole.ASSISTANT,
                content=msg_dict.get('content', ''),
                content_en=msg_dict.get('content_en'),
                content_thai=msg_dict.get('content_thai')
            )
            ai_messages.append(message)
        
        print(f"   ✅ Конвертировано {len(ai_messages)} сообщений")
        for i, msg in enumerate(ai_messages):
            print(f"      {i+1}. [{msg.role.value}] {msg.content[:50]}...")
        
        # Тест 6: Проверка форматирования для AI
        print("6. Проверяем форматирование для AI...")
        from src.utils.ai_utils import format_conversation_for_ai
        formatted_history = await format_conversation_for_ai(ai_messages, session_id, test_sender_id)
        
        if formatted_history:
            print(f"   ✅ Форматирование выполнено: {len(formatted_history)} сообщений")
            for i, text in enumerate(formatted_history):
                print(f"      {i+1}. {text[:50]}...")
        else:
            print("   ❌ Форматирование не выполнено")
            return False
        
        # Тест 7: Генерация ответа AI
        print("7. Генерируем ответ AI...")
        ai_response = await ai_service.generate_response(ai_messages, user_lang='ru')
        
        if ai_response:
            print(f"   ✅ Ответ AI получен: {len(ai_response)} символов")
            print(f"      Ответ: {ai_response[:100]}...")
        else:
            print("   ❌ Ответ AI не получен")
            return False
        
        print("✅ Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_history())
    if not success:
        sys.exit(1) 
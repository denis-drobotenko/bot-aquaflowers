#!/usr/bin/env python3
"""
Тест для проверки формирования истории диалога для AI
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.models.message import Message, MessageRole
from src.chat_history_processor import process_chat_history


def test_conversation_history():
    """Тестирует формирование истории диалога для AI (синхронно)"""
    print("=== ТЕСТ ИСТОРИИ ДИАЛОГА ===")
    try:
        # Инициализация сервисов
        message_service = MessageService()
        session_service = SessionService()
        
        # Тест 1: Создание сессии
        test_sender_id = "79140775712"
        loop = None
        try:
            import asyncio
            loop = asyncio.get_event_loop()
        except:
            pass
        session_id = None
        if loop:
            session_id = loop.run_until_complete(session_service.get_or_create_session_id(test_sender_id))
        else:
            session_id = session_service.get_or_create_session_id(test_sender_id)
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
            if loop:
                result = loop.run_until_complete(message_service.add_message_to_conversation(msg))
            else:
                result = message_service.add_message_to_conversation(msg)
            if result:
                print(f"   ✅ Сообщение {i+1} добавлено")
            else:
                print(f"   ❌ Сообщение {i+1} не добавлено")
                return False
        # Ждем индексации Firestore
        print("3. Ждем индексации Firestore...")
        time.sleep(2)
        # Проверяем наличие сообщений в Firestore напрямую
        print("4. Проверяем сообщения в Firestore напрямую...")
        if message_service.db:
            try:
                session_ref = message_service.db.collection('conversations').document(test_sender_id).collection('sessions').document(session_id)
                messages_ref = session_ref.collection('messages')
                docs = list(messages_ref.stream())
                print(f"   В Firestore реально сообщений: {len(docs)}")
                for i, doc in enumerate(docs):
                    data = doc.to_dict()
                    print(f"      {i+1}. [{data.get('role')}] {data.get('content', '')[:50]}...")
            except Exception as e:
                print(f"   ❌ Ошибка при проверке Firestore: {e}")
        # Тест 5: Получение истории для AI
        print("5. Получаем историю для AI...")
        if loop:
            history = loop.run_until_complete(message_service.get_conversation_history_for_ai_by_sender(test_sender_id, session_id, limit=10))
        else:
            history = message_service.get_conversation_history_for_ai_by_sender(test_sender_id, session_id, limit=10)
        if history:
            print(f"   ✅ История получена: {len(history)} сообщений")
            for i, msg in enumerate(history):
                print(f"      {i+1}. [{msg.get('role')}] {msg.get('content', '')[:50]}...")
        else:
            print("   ❌ История не получена")
            return False
        # Тест 6: Проверка обработки истории чата
        print("6. Тестируем обработку истории чата...")
        session_id_with_sender = f"{test_sender_id}_{session_id}"
        html_content, status_code = process_chat_history(session_id_with_sender)
        if status_code == 200:
            print("   ✅ HTML история сгенерирована успешно")
            print(f"      Длина HTML: {len(html_content)} символов")
        else:
            print(f"   ❌ Ошибка генерации HTML: {status_code}")
            print(f"      Ответ: {html_content}")
            return False
        print("✅ Все тесты прошли успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_conversation_history()
    if not result:
        sys.exit(1) 
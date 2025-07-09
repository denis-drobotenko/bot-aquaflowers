#!/usr/bin/env python3
"""
Тестовый скрипт для проверки поддержки изображений в истории диалога
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.repositories.message_repository import MessageRepository
from src.models.message import Message, MessageRole
from datetime import datetime

async def test_image_support():
    """Тестирует поддержку изображений в сообщениях"""
    print("🧪 Тестирование поддержки изображений в истории диалога")
    
    # Создаем репозиторий
    repo = MessageRepository()
    
    # Тестовые данные
    sender_id = "test_user_123"
    session_id = "test_session_456"
    
    # Создаем тестовое сообщение с изображением
    test_message = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.USER,
        content="Посмотрите на этот красивый букет!",
        content_en="Look at this beautiful bouquet!",
        content_thai="ดูช่อดอกไม้อันสวยงามนี้!",
        image_url="https://scontent.fbkk22-6.fna.fbcdn.net/v/t45.5328-4/503765845_1222228859683151_4028827634893880558_n.jpg",
        timestamp=datetime.now()
    )
    
    print(f"📝 Создано тестовое сообщение:")
    print(f"   - Отправитель: {test_message.sender_id}")
    print(f"   - Сессия: {test_message.session_id}")
    print(f"   - Текст: {test_message.content}")
    print(f"   - URL изображения: {test_message.image_url}")
    
    # Сохраняем сообщение
    print("\n💾 Сохраняем сообщение в БД...")
    success = await repo.add_message_to_conversation(test_message)
    
    if success:
        print("✅ Сообщение успешно сохранено")
    else:
        print("❌ Ошибка сохранения сообщения")
        return
    
    # Получаем историю диалога
    print("\n📖 Получаем историю диалога...")
    history = await repo.get_conversation_history_by_sender(sender_id, session_id, limit=10)
    
    print(f"📊 Получено {len(history)} сообщений")
    
    for i, msg in enumerate(history):
        print(f"\n📨 Сообщение {i+1}:")
        print(f"   - Роль: {msg.get('role')}")
        print(f"   - Текст: {msg.get('content')}")
        print(f"   - URL изображения: {msg.get('image_url', 'Нет')}")
        print(f"   - Время: {msg.get('timestamp')}")
    
    # Тестируем форматирование для веб-интерфейса
    print("\n🌐 Тестируем форматирование для веб-интерфейса...")
    
    from src.routes.chat_routes import format_messages_for_language
    
    # Форматируем сообщения на разных языках
    for lang in ['ru', 'en', 'th']:
        print(f"\n📝 Форматирование на языке {lang}:")
        html = format_messages_for_language(history, lang)
        print(f"HTML (обрезано): {html[:200]}...")
    
    print("\n✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_image_support()) 
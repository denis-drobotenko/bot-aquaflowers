#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки каталога с изображениями
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.catalog_sender import catalog_sender
from src.repositories.message_repository import MessageRepository
from src.models.message import Message, MessageRole
from datetime import datetime
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_catalog_with_images():
    """Тестирует отправку каталога с изображениями"""
    print("🧪 Тестирование отправки каталога с изображениями")
    
    # Тестовые данные
    test_number = "79123456789"  # Замените на реальный номер
    session_id = "test_catalog_session"
    
    print(f"📱 Отправляем каталог на номер: {test_number}")
    print(f"🆔 Session ID: {session_id}")
    
    # Отправляем каталог
    success = await catalog_sender.send_catalog(test_number, session_id)
    
    if success:
        print("✅ Каталог успешно отправлен!")
        
        # Проверяем, что сообщения сохранились в БД с image_url
        repo = MessageRepository()
        messages = await repo.get_conversation_history_by_sender(test_number, session_id, limit=50)
        
        print(f"📊 Найдено {len(messages)} сообщений в истории")
        
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:50] + "..." if len(msg.get('content', '')) > 50 else msg.get('content', '')
            image_url = msg.get('image_url')
            
            print(f"  {i+1}. [{role}] {content}")
            if image_url:
                print(f"     🖼️  Изображение: {image_url}")
            else:
                print(f"     📝 Только текст")
    else:
        print("❌ Ошибка отправки каталога")

async def test_image_display():
    """Тестирует отображение изображений в истории диалога"""
    print("\n🖼️  Тестирование отображения изображений в истории")
    
    # Создаем тестовое сообщение с изображением
    repo = MessageRepository()
    test_sender = "test_image_user"
    test_session = "test_image_session"
    
    # Сначала создаем сессию
    try:
        from src.services.session_service import SessionService
        session_service = SessionService()
        
        # Создаем сессию
        session_id = await session_service.get_or_create_session_id(test_sender)
        test_session = session_id  # Используем созданную сессию
        print(f"✅ Сессия создана: {session_id}")
    except Exception as e:
        print(f"⚠️  Ошибка создания сессии: {e}")
        return
    
    # Создаем сообщение с изображением
    test_message = Message(
        sender_id=test_sender,
        session_id=test_session,
        role=MessageRole.ASSISTANT,
        content="Вот красивый букет! 🌸",
        content_en="Here's a beautiful bouquet! 🌸",
        content_thai="นี่คือช่อดอกไม้ที่สวยงาม! 🌸",
        image_url="https://example.com/bouquet.jpg",
        timestamp=datetime.now()
    )
    
    # Сохраняем сообщение
    success = await repo.add_message_to_conversation(test_message)
    
    if success:
        print("✅ Тестовое сообщение с изображением сохранено")
        
        # Получаем историю
        messages = await repo.get_conversation_history_by_sender(test_sender, test_session, limit=10)
        
        print(f"📊 Получено {len(messages)} сообщений")
        
        for msg in messages:
            if msg.get('image_url'):
                print(f"🖼️  Найдено сообщение с изображением: {msg.get('image_url')}")
                print(f"   Текст: {msg.get('content')}")
    else:
        print("❌ Ошибка сохранения тестового сообщения")

async def test_chat_history_with_images():
    print("🧪 Тестируем отображение изображений в истории диалога")
    
    # Создаем сервисы
    session_service = SessionService()
    message_service = MessageService()
    
    # Получаем реальную сессию из БД
    db = session_service.db
    sessions = db.collection_group('sessions').limit(1).stream()
    session_list = list(sessions)
    
    if not session_list:
        print("❌ Нет сессий в БД для тестирования")
        return
    
    session_doc = session_list[0]
    session_path = session_doc.reference.path
    print(f"📋 Тестируем сессию: {session_path}")
    
    # Извлекаем sender_id и session_id из пути
    path_parts = session_path.split('/')
    sender_id = path_parts[1]
    session_id = path_parts[3]
    
    print(f"👤 Sender ID: {sender_id}")
    print(f"🆔 Session ID: {session_id}")
    
    # Получаем историю диалога
    try:
        chat_history = await message_service.get_conversation_history_for_ai_by_sender(sender_id, session_id)
        print(f"✅ Получена история диалога: {len(chat_history)} сообщений")
        
        # Проверяем сообщения с изображениями
        messages_with_images = [msg for msg in chat_history if msg.get('image_url')]
        print(f"🖼️  Сообщений с изображениями: {len(messages_with_images)}")
        
        if messages_with_images:
            print("\n📸 Примеры сообщений с изображениями:")
            for i, msg in enumerate(messages_with_images[:3]):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:50]
                image_url = msg.get('image_url')
                print(f"  {i+1}. [{role}] {content}...")
                print(f"      🖼️  {image_url}")
        else:
            print("❌ Сообщений с изображениями не найдено")
            
        # Проверяем все сообщения ассистента
        assistant_messages = [msg for msg in chat_history if msg.get('role') == 'assistant']
        print(f"\n🤖 Всего сообщений ассистента: {len(assistant_messages)}")
        
        # Проверяем сообщения каталога
        catalog_messages = []
        for msg in assistant_messages:
            content = msg.get('content', '')
            if '\n' in content and '฿' in content:  # Признак сообщения каталога
                catalog_messages.append(msg)
        
        print(f"📦 Сообщений каталога: {len(catalog_messages)}")
        
        if catalog_messages:
            print("\n📋 Сообщения каталога:")
            for i, msg in enumerate(catalog_messages[:5]):
                content = msg.get('content', '')
                image_url = msg.get('image_url')
                has_image = "✅" if image_url else "❌"
                print(f"  {i+1}. {has_image} {content[:30]}...")
                if image_url:
                    print(f"      🖼️  {image_url[:50]}...")
        
    except Exception as e:
        print(f"❌ Ошибка получения истории диалога: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Устанавливаем переменные окружения
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'src/aquaf.json'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'aquaf-464414'
    
    print("🚀 Запуск тестов каталога с изображениями")
    
    # Запускаем тесты
    asyncio.run(test_image_display())
    
    # Раскомментируйте для тестирования реальной отправки
    # asyncio.run(test_catalog_with_images())
    
    asyncio.run(test_chat_history_with_images()) 
#!/usr/bin/env python3
"""
Тестирование системы логирования по всему проекту
"""

import asyncio
import os
import sys

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(__file__))

from src.config.logging_config import setup_logging_by_environment
from src.services.ai_service import AIService
from src.services.order_service import OrderService
from src.services.command_service import CommandService
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.services.user_service import UserService
from src.services.message_processor import MessageProcessor
from src.handlers.webhook_handler import WebhookHandler
from src.models.message import Message, MessageRole
from src.models.order import OrderStatus
from src.config.settings import GEMINI_API_KEY


async def test_all_services():
    """Тестирует все сервисы с логированием"""
    
    print("🚀 Тестирование системы логирования по всему проекту")
    print("=" * 60)
    
    # Настраиваем логирование
    setup_logging_by_environment()
    print("✅ Логирование настроено")
    
    # Тест 1: AI Service
    print("\n1️⃣ Тестируем AI Service...")
    try:
        ai_service = AIService(GEMINI_API_KEY)
        
        # Тест определения языка
        lang = ai_service.detect_language("Привет, как дела?")
        print(f"   Определен язык: {lang}")
        
        # Тест перевода
        translated = ai_service.translate_text("Hello world", "en", "ru")
        print(f"   Перевод: {translated}")
        
    except Exception as e:
        print(f"   ❌ Ошибка AI Service: {e}")
    
    # Тест 2: Order Service
    print("\n2️⃣ Тестируем Order Service...")
    try:
        order_service = OrderService()
        
        # Тест создания заказа
        order = await order_service.get_or_create_order("test_session_123", "test_user_456")
        print(f"   Создан заказ: {order.order_id}")
        
        # Тест добавления товара
        item_data = {"bouquet": "Роза красная", "quantity": 2, "price": 1500}
        order_id = await order_service.add_item("test_session_123", "test_user_456", item_data)
        print(f"   Добавлен товар в заказ: {order_id}")
        
        # Тест обновления статуса
        await order_service.update_order_status("test_session_123", "test_user_456", OrderStatus.READY)
        print(f"   Статус заказа обновлен")
        
    except Exception as e:
        print(f"   ❌ Ошибка Order Service: {e}")
    
    # Тест 3: Command Service
    print("\n3️⃣ Тестируем Command Service...")
    try:
        command_service = CommandService()
        
        # Тест команды добавления товара
        command = {
            "type": "add_order_item",
            "bouquet": "Тюльпан желтый",
            "quantity": 1,
            "price": 800
        }
        result = await command_service.handle_command("test_user_456", "test_session_123", command)
        print(f"   Результат команды: {result['status']}")
        
    except Exception as e:
        print(f"   ❌ Ошибка Command Service: {e}")
    
    # Тест 4: Session Service
    print("\n4️⃣ Тестируем Session Service...")
    try:
        session_service = SessionService()
        
        # Тест создания сессии
        session_id = await session_service.get_or_create_session_id("test_user_789")
        print(f"   Создана сессия: {session_id}")
        
        # Тест получения информации о пользователе
        user_info = await session_service.get_user_info("test_user_789")
        print(f"   Информация о пользователе: {user_info}")
        
    except Exception as e:
        print(f"   ❌ Ошибка Session Service: {e}")
    
    # Тест 5: Message Service
    print("\n5️⃣ Тестируем Message Service...")
    try:
        message_service = MessageService()
        
        # Тест получения истории
        history = await message_service.get_conversation_history_for_ai("test_session_123", limit=10)
        print(f"   Получена история: {len(history)} сообщений")
        
    except Exception as e:
        print(f"   ❌ Ошибка Message Service: {e}")
    
    # Тест 6: User Service
    print("\n6️⃣ Тестируем User Service...")
    try:
        user_service = UserService()
        
        # Тест получения пользователя
        user = await user_service.get_user("test_user_999")
        print(f"   Получен пользователь: {user is not None}")
        
    except Exception as e:
        print(f"   ❌ Ошибка User Service: {e}")
    
    # Тест 7: Message Processor
    print("\n7️⃣ Тестируем Message Processor...")
    try:
        message_processor = MessageProcessor()
        
        # Тест обработки входящего сообщения
        await message_processor.process_incoming_message(
            from_number="+1234567890",
            content="Тестовое сообщение",
            session_id="test_session_123",
            sender_id="test_user_456"
        )
        print(f"   Обработано входящее сообщение")
        
    except Exception as e:
        print(f"   ❌ Ошибка Message Processor: {e}")
    
    # Тест 8: Webhook Handler
    print("\n8️⃣ Тестируем Webhook Handler...")
    try:
        webhook_handler = WebhookHandler()
        
        # Тест валидации webhook
        test_webhook = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "1234567890",
                            "type": "text",
                            "text": {"body": "Тестовое сообщение"},
                            "id": "test_message_id"
                        }]
                    }
                }]
            }]
        }
        
        result = webhook_handler.validate_webhook(test_webhook)
        print(f"   Валидация webhook: {result['valid']}")
        
    except Exception as e:
        print(f"   ❌ Ошибка Webhook Handler: {e}")
    
    print("\n✅ Тестирование завершено!")
    print(f"📊 Логи сохранены в файл: {os.getenv('LOG_FILE', 'app.json')}")
    print("🌐 Откройте http://localhost:8000/logs для просмотра логов")


if __name__ == "__main__":
    # Устанавливаем переменные окружения для тестирования
    os.environ["LOG_FILE"] = "app.json"
    os.environ["LOG_FORMAT"] = "json"
    os.environ["ENVIRONMENT"] = "development"
    
    # Запускаем тесты
    asyncio.run(test_all_services()) 
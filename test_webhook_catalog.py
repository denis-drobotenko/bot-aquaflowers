#!/usr/bin/env python3
"""
Тест webhook с запросом каталога
"""

import sys
import os
import asyncio
import json

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.message_processor import MessageProcessor
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_webhook_catalog():
    """Тест webhook с запросом каталога"""
    print("=== ТЕСТ WEBHOOK С КАТАЛОГОМ ===")
    
    try:
        # Инициализация обработчика сообщений
        message_processor = MessageProcessor()
        
        # Создаем тестовое сообщение с запросом каталога
        test_message = Message(
            sender_id="+1234567890",  # Тестовый номер
            session_id="test_session_catalog",
            role=MessageRole.USER,
            content="Покажите каталог цветов"
        )
        
        # Обрабатываем сообщение
        print("Обрабатываем сообщение с запросом каталога...")
        message_data = {
            'sender_id': test_message.sender_id,
            'message_text': test_message.content,
            'sender_name': "Test User",
            'wa_message_id': "test_wa_id_123"
        }
        success = await message_processor.process_user_message(message_data)
        
        result = {
            "status": "success" if success else "error",
            "success": success
        }
        
        print(f"Результат обработки: {result}")
        
        if result and result.get("status") == "success":
            print("✅ Сообщение обработано успешно")
            return True
        else:
            print(f"❌ Ошибка обработки: {result}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_webhook_catalog()) 
#!/usr/bin/env python3
"""
Тест отправки каталога через исправленный command_service
"""

import sys
import os
import asyncio

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.command_service import CommandService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_catalog_send():
    """Тест отправки каталога"""
    print("=== ТЕСТ ОТПРАВКИ КАТАЛОГА ===")
    
    try:
        # Инициализация сервиса команд
        command_service = CommandService()
        
        # Тест 1: Проверка обработки команды отправки каталога
        command = {
            "type": "send_catalog"
        }
        
        result = await command_service._handle_send_catalog(
            sender_id="test_user_123",
            session_id="test_session_456", 
            command=command
        )
        
        print(f"Результат отправки каталога: {result}")
        
        if result.get("status") == "success":
            print("✅ Каталог отправлен успешно")
            print(f"   Количество товаров: {result.get('products_count')}")
        elif result.get("status") == "error":
            print(f"❌ Ошибка отправки каталога: {result.get('message')}")
        else:
            print(f"⚠️ Неожиданный результат: {result}")
            
        return result.get("status") == "success"
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_catalog_send()) 
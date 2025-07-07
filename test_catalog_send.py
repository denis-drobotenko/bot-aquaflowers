#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки каталога
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_catalog_send():
    """Тестирует отправку каталога"""
    try:
        from services.catalog_sender import CatalogSender
        from services.catalog_service import CatalogService
        from utils.whatsapp_client import WhatsAppClient
        from config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
        
        # Создаем сервисы
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        whatsapp_client = WhatsAppClient()
        # Создаём CatalogSender без аргументов
        catalog_sender = CatalogSender()
        
        # Тестовый номер (замените на реальный)
        test_number = "79140775712"
        
        print(f"🧪 Тестируем отправку каталога на номер: {test_number}")
        
        # Отправляем каталог
        result = await catalog_sender.send_catalog(test_number, "test_session")
        
        if result:
            print("✅ Каталог отправлен успешно!")
        else:
            print("❌ Ошибка отправки каталога")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_catalog_send()) 
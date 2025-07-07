#!/usr/bin/env python3
"""
Тест каталога с реальным номером телефона
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

from src.services.catalog_service import CatalogService
from src.services.catalog_sender import CatalogSender
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_real_catalog():
    """Тест каталога с реальным номером"""
    print("=== ТЕСТ КАТАЛОГА С РЕАЛЬНЫМ НОМЕРОМ ===")
    
    try:
        # Инициализация сервисов
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        catalog_sender = CatalogSender()
        
        # Тест 1: Проверка получения товаров
        products = await catalog_service.get_available_products()
        print(f"Доступно товаров: {len(products)}")
        
        if not products:
            print("❌ Нет доступных товаров")
            return False
            
        # Тест 2: Проверка отправки каталога (без реальной отправки)
        print("Проверяем формирование сообщений каталога...")
        messages = await catalog_sender.get_catalog_messages("+1234567890")
        
        if messages and len(messages) > 0:
            print(f"✅ Сформировано {len(messages)} сообщений каталога")
            for i, msg in enumerate(messages[:3]):  # Показываем первые 3
                print(f"   {i+1}. {msg.get('type')}: {msg.get('caption', msg.get('content', 'Нет текста'))}")
        else:
            print("❌ Не удалось сформировать сообщения каталога")
            return False
            
        print("✅ Каталог работает корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_real_catalog()) 
#!/usr/bin/env python3
"""
Подробный тестовый скрипт для проверки отправки каталога
"""

import asyncio
import sys
import os
import logging

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_catalog_detailed():
    """Тестирует отправку каталога с подробным логированием"""
    try:
        from services.catalog_service import CatalogService
        from config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
        
        # Тестовый номер
        test_number = "79140775712"
        
        print(f"🧪 Тестируем отправку каталога на номер: {test_number}")
        
        # 1. Создаем сервис каталога
        print("📋 Создаем сервис каталога...")
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        
        # 2. Получаем все товары
        print("🔄 Получаем все товары из каталога...")
        all_products = await catalog_service.get_products()
        print(f"📦 Всего товаров: {len(all_products)}")
        
        # 3. Получаем только доступные товары
        print("✅ Получаем только доступные товары...")
        available_products = await catalog_service.get_available_products()
        print(f"📦 Доступных товаров: {len(available_products)}")
        
        # 4. Показываем информацию о товарах
        print("\n📋 Информация о товарах:")
        for i, product in enumerate(available_products, 1):
            name = product.get('name', 'Без названия')
            price = product.get('price', 'Цена не указана')
            availability = product.get('availability', 'Не указано')
            retailer_id = product.get('retailer_id', 'Нет ID')
            print(f"  {i}. {name} - {price} (Наличие: {availability}, ID: {retailer_id})")
        
        # 5. Тестируем отправку каталога
        print("\n📤 Тестируем отправку каталога...")
        from services.catalog_sender import handle_send_catalog
        
        result = await handle_send_catalog(test_number, test_number, "test_session")
        
        if result:
            print("✅ Каталог отправлен успешно!")
        else:
            print("❌ Ошибка отправки каталога")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_catalog_detailed()) 
#!/usr/bin/env python3
"""
Тест для просмотра содержимого каталога, передаваемого в AI
"""

import asyncio
import os
import sys
sys.path.append('src')

from src.services.catalog_service import CatalogService
from src.utils.ai_utils import format_catalog_for_ai

async def test_catalog_content():
    """Тестирует содержимое каталога"""
    
    # Импортируем настройки
    from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
    
    if not WHATSAPP_CATALOG_ID or not WHATSAPP_TOKEN:
        print("❌ Ошибка: не найдены переменные окружения WHATSAPP_CATALOG_ID или WHATSAPP_TOKEN")
        return
    
    catalog_id = WHATSAPP_CATALOG_ID
    access_token = WHATSAPP_TOKEN
    
    print(f"🔍 Тестируем каталог {catalog_id}")
    
    # Создаем сервис каталога
    catalog_service = CatalogService(catalog_id, access_token)
    
    # Получаем все товары
    print("\n📦 Получаем все товары...")
    all_products = catalog_service.get_products()
    print(f"Всего товаров: {len(all_products)}")
    
    if all_products:
        print("\n📋 Структура первого товара:")
        first_product = all_products[0]
        for key, value in first_product.items():
            print(f"  {key}: {value}")
    
    # Получаем доступные товары
    print("\n✅ Получаем доступные товары...")
    available_products = catalog_service.get_available_products()
    print(f"Доступных товаров: {len(available_products)}")
    
    # Форматируем для AI
    print("\n🤖 Форматирование для AI:")
    catalog_text = format_catalog_for_ai(available_products)
    print("=" * 80)
    print(catalog_text)
    print("=" * 80)
    
    # Показываем детали каждого товара
    print("\n📊 Детали всех доступных товаров:")
    for i, product in enumerate(available_products, 1):
        print(f"\n{i}. {product.get('name', 'Без названия')}")
        print(f"   ID: {product.get('id', 'N/A')}")
        print(f"   Retailer ID: {product.get('retailer_id', 'N/A')}")
        print(f"   Цена: {product.get('price', 'N/A')}")
        print(f"   Описание: {product.get('description', 'N/A')[:100]}...")
        print(f"   Наличие: {product.get('availability', 'N/A')}")
        print(f"   Изображение: {product.get('image_url', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(test_catalog_content()) 
#!/usr/bin/env python3
"""
Тест реального API каталога с исправленным CatalogService
"""

import asyncio
import os
import sys

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_catalog_api():
    """Тестирует реальный API каталога"""
    print("=== ТЕСТ РЕАЛЬНОГО API КАТАЛОГА ===")
    
    # Проверяем переменные окружения
    print(f"WHATSAPP_CATALOG_ID: {WHATSAPP_CATALOG_ID}")
    print(f"WHATSAPP_TOKEN: {WHATSAPP_TOKEN[:20]}..." if WHATSAPP_TOKEN else "НЕ УСТАНОВЛЕН")
    
    if not WHATSAPP_CATALOG_ID or not WHATSAPP_TOKEN:
        print("❌ ОШИБКА: Не установлены переменные окружения")
        return
    
    # Создаем сервис каталога
    catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
    
    try:
        # Получаем все товары
        print("\n1. Получение всех товаров...")
        all_products = await catalog_service.get_products(force_refresh=True)
        print(f"Всего товаров: {len(all_products)}")
        
        if all_products:
            print("Первые 3 товара:")
            for i, product in enumerate(all_products[:3]):
                print(f"  {i+1}. {product.get('name', 'Без названия')} - {product.get('price', 'Нет цены')}")
                print(f"     ID: {product.get('id')}, Retailer ID: {product.get('retailer_id')}")
                print(f"     Availability: {product.get('availability')}")
                print(f"     Image: {product.get('image_url', 'Нет изображения')[:50]}...")
                print()
        
        # Получаем только доступные товары
        print("\n2. Получение доступных товаров...")
        available_products = await catalog_service.get_available_products()
        print(f"Доступных товаров: {len(available_products)}")
        
        if available_products:
            print("Доступные товары:")
            for i, product in enumerate(available_products):
                print(f"  {i+1}. {product.get('name', 'Без названия')} - {product.get('price', 'Нет цены')}")
                print(f"     Availability: {product.get('availability')}")
        
        # Тестируем фильтрацию
        print("\n3. Тестирование фильтрации...")
        filtered_products = catalog_service.filter_available_products(all_products)
        print(f"Отфильтровано товаров: {len(filtered_products)}")
        
        # Проверяем статистику по availability
        availability_stats = {}
        for product in all_products:
            avail = product.get('availability', 'unknown')
            availability_stats[avail] = availability_stats.get(avail, 0) + 1
        
        print("\n4. Статистика по availability:")
        for avail, count in availability_stats.items():
            print(f"  {avail}: {count} товаров")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_catalog_api()) 
#!/usr/bin/env python3
"""
Тест сервиса каталога
"""

import sys
import os

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_catalog_service():
    """Тест сервиса каталога"""
    print("=== ТЕСТ СЕРВИСА КАТАЛОГА ===")
    
    try:
        # Инициализация каталога
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        
        # Тест 1: Получение товаров (синхронный метод)
        products = catalog_service.get_products()
        if products and len(products) > 0:
            print(f"✅ Каталог загрузка товаров - Загружено {len(products)} товаров")
        else:
            print("❌ Каталог загрузка товаров - Товары не загружены")
            return False
            
        # Тест 2: Получение доступных товаров (синхронный метод)
        available_products = catalog_service.get_available_products()
        if available_products and len(available_products) > 0:
            print(f"✅ Каталог доступные товары - Доступно {len(available_products)} товаров")
        else:
            print("❌ Каталог доступные товары - Нет доступных товаров")
            return False
            
        # Тест 3: Валидация товара (синхронный метод)
        if available_products:
            test_product = available_products[0]
            retailer_id = test_product.get('retailer_id')
            if retailer_id:
                validation = catalog_service.validate_product(retailer_id)
                if validation['valid']:
                    print(f"✅ Каталог валидация товара - Товар {test_product.get('name')} валиден")
                else:
                    print("❌ Каталог валидация товара - Товар не прошел валидацию")
                    return False
                    
        print("✅ Каталог прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Каталог сервис - Ошибка: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_catalog_service())
    if not success:
        sys.exit(1) 
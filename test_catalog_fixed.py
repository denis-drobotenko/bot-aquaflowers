#!/usr/bin/env python3
"""
Тест исправленной логики отправки каталога
"""

import asyncio
import json
from src.services.command_service import CommandService
from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_catalog_command():
    """Тестирует обработку команды send_catalog"""
    print("=== ТЕСТ КОМАНДЫ SEND_CATALOG ===")
    
    # Создаем CommandService
    command_service = CommandService()
    
    # Тестируем команду send_catalog
    command = {
        "type": "send_catalog"
    }
    
    print("Отправляем команду send_catalog...")
    result = await command_service.handle_command("test_user_123", "test_session_123", command)
    
    print(f"Результат: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('status') == 'success':
        print("✅ Команда выполнена успешно!")
    else:
        print(f"❌ Ошибка: {result.get('message')}")

async def test_catalog_service():
    """Тестирует CatalogService напрямую"""
    print("\n=== ТЕСТ CATALOG_SERVICE ===")
    
    catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
    
    print("Получаем все товары...")
    all_products = catalog_service.get_products()
    print(f"Всего товаров: {len(all_products)}")
    
    if all_products:
        print(f"Первый товар: {all_products[0]}")
    
    print("\nПолучаем доступные товары...")
    available_products = catalog_service.get_available_products()
    print(f"Доступных товаров: {len(available_products)}")
    
    if available_products:
        print(f"Первый доступный товар: {available_products[0]}")
    else:
        print("❌ Нет доступных товаров!")

if __name__ == "__main__":
    asyncio.run(test_catalog_service())
    asyncio.run(test_catalog_command()) 
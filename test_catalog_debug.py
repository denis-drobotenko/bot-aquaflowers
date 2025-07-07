#!/usr/bin/env python3
"""
Тест функции get_available_products
"""

from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

def test_get_available_products():
    print("=== ТЕСТ GET_AVAILABLE_PRODUCTS ===")
    catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
    all_products = catalog_service.get_products()
    print(f"Всего товаров: {len(all_products)}")
    if all_products:
        for i, p in enumerate(all_products[:5]):
            print(f"  {i+1}. {p.get('name')} | {p.get('availability')}")
    available = catalog_service.get_available_products()
    print(f"Доступных товаров: {len(available)}")
    if available:
        for i, p in enumerate(available):
            print(f"  {i+1}. {p.get('name')} | {p.get('availability')}")
    else:
        print("❌ Нет доступных товаров!")

if __name__ == "__main__":
    test_get_available_products() 
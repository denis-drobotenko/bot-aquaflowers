#!/usr/bin/env python3
"""
Тест чтения реального каталога цветов
"""

import asyncio
import sys
import os
import pytest

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем src в путь
# Добавляем src в путь
current_dir = os.path.dirname(__file__)
# Всегда добавляем путь к src относительно текущего файла
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

from src import catalog_reader

@pytest.mark.asyncio
async def test_catalog_reading():
    """Тестируем чтение реального каталога"""
    print("=== ТЕСТ ЧТЕНИЯ КАТАЛОГА ===")
    
    # Тест 1: Получение списка товаров
    print("\n1. Получение списка товаров из каталога")
    products = await catalog_reader.get_catalog_products()
    print(f"Найдено товаров: {len(products)}")
    
    if products:
        print("✅ Каталог успешно загружен!")
        for i, product in enumerate(products[:3]):  # Показываем первые 3
            print(f"  {i+1}. {product.get('name', 'Без названия')} (ID: {product.get('retailer_id', 'N/A')})")
    else:
        print("❌ Каталог не загружен")
    
    # Тест 2: Форматирование каталога для AI
    print("\n2. Форматирование каталога для AI")
    catalog_text = catalog_reader.format_catalog_for_ai(products)
    print(f"Длина текста каталога: {len(catalog_text)} символов")
    print("Первые 200 символов:")
    print(catalog_text[:200] + "...")
    
    # Тест 3: Краткая сводка каталога
    print("\n3. Краткая сводка каталога")
    summary = await catalog_reader.get_catalog_summary()
    print("Сводка каталога:")
    print(summary)
    
    # Тест 4: Валидация выбора товара
    if products:
        print("\n4. Валидация выбора товара")
        test_retailer_id = products[0].get('retailer_id')
        if test_retailer_id:
            validation = await catalog_reader.validate_product_selection(test_retailer_id)
            print(f"Валидация товара {test_retailer_id}: {validation['valid']}")
            if validation['valid']:
                print(f"✅ Товар найден: {validation['product'].get('name')}")
            else:
                print(f"❌ Товар не найден")
        
        # Тест с несуществующим товаром
        fake_retailer_id = "fake_product_123"
        validation = await catalog_reader.validate_product_selection(fake_retailer_id)
        print(f"Валидация несуществующего товара {fake_retailer_id}: {validation['valid']}")
        if not validation['valid']:
            print(f"✅ Правильно отклонен несуществующий товар")
        else:
            print(f"❌ Неправильно принят несуществующий товар")

if __name__ == "__main__":
    asyncio.run(test_catalog_reading()) 
#!/usr/bin/env python3
"""
Тест OrderService с реальными данными из каталога
Проверяет интеграцию с CatalogService
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService
from src.services.catalog_service import CatalogService
from src.models.order import OrderStatus
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_order_with_catalog():
    """Тестирует OrderService с реальными товарами из каталога"""
    print("🧪 Начинаем тест OrderService с каталогом...")
    
    order_service = OrderService()
    catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
    
    # Тестовые данные
    test_session_id = f"catalog_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_sender_id = "catalog_test_user"
    
    print(f"📋 Тестовая сессия: {test_session_id}")
    print(f"👤 Тестовый пользователь: {test_sender_id}")
    
    try:
        # 1. Получаем реальные товары из каталога
        print("\n1️⃣ Получение товаров из каталога...")
        products = catalog_service.get_available_products()
        print(f"📦 Найдено товаров: {len(products)}")
        
        if not products:
            print("❌ Нет доступных товаров в каталоге")
            return
        
        # Показываем первые 3 товара
        for i, product in enumerate(products[:3], 1):
            print(f"   {i}. {product.get('name')} - {product.get('price')} (ID: {product.get('retailer_id')})")
        
        # 2. Создаем заказ с реальными товарами
        print("\n2️⃣ Создание заказа с реальными товарами...")
        
        # Берем первый доступный товар
        first_product = products[0]
        retailer_id = first_product.get('retailer_id')
        product_name = first_product.get('name')
        product_price = first_product.get('price')
        
        print(f"🛒 Добавляем товар: {product_name} - {product_price}")
        
        # Создаем заказ
        order_data = {
            'delivery_needed': True,
            'address': 'Phuket, Patong Beach, 123/45',
            'date': '2025-07-10',
            'time': '14:00',
            'card_needed': True,
            'card_text': 'Happy Birthday! 🌸',
            'recipient_name': 'John Doe',
            'recipient_phone': '+66 123 456 789'
        }
        
        order_id = await order_service.update_order_data(test_session_id, test_sender_id, order_data)
        print(f"✅ Заказ создан с ID: {order_id}")
        
        # 3. Добавляем товар из каталога
        print("\n3️⃣ Добавление товара из каталога...")
        item_data = {
            'bouquet': product_name,
            'quantity': 1,
            'price': product_price,
            'product_id': retailer_id,
            'notes': 'Test order from catalog'
        }
        
        order_id = await order_service.add_item(test_session_id, test_sender_id, item_data)
        print(f"✅ Товар добавлен в заказ")
        
        # 4. Проверяем валидацию товара
        print("\n4️⃣ Проверка валидации товара...")
        validation = catalog_service.validate_product(retailer_id)
        print(f"✅ Валидация товара: {validation['valid']}")
        if validation['valid']:
            print(f"   - Название: {validation['product'].get('name')}")
            print(f"   - Цена: {validation['product'].get('price')}")
            print(f"   - Доступность: {validation['product'].get('availability')}")
        
        # 5. Получаем полные данные заказа
        print("\n5️⃣ Получение полных данных заказа...")
        order = await order_service.get_order_data(test_session_id, test_sender_id)
        
        print(f"📦 Данные заказа:")
        print(f"   - Статус: {order.get('status')}")
        print(f"   - Доставка: {order.get('delivery_needed')}")
        print(f"   - Адрес: {order.get('address')}")
        print(f"   - Дата: {order.get('date')}")
        print(f"   - Время: {order.get('time')}")
        print(f"   - Получатель: {order.get('recipient_name')}")
        print(f"   - Телефон: {order.get('recipient_phone')}")
        print(f"   - Открытка: {order.get('card_needed')}")
        print(f"   - Текст открытки: {order.get('card_text')}")
        
        items = order.get('items', [])
        print(f"   - Товаров: {len(items)}")
        for i, item in enumerate(items, 1):
            print(f"     {i}. {item.get('bouquet')} - {item.get('price')} (x{item.get('quantity')})")
        
        # 6. Тест готовности заказа для оператора
        print("\n6️⃣ Проверка готовности заказа для оператора...")
        order_result = await order_service.process_order_for_operator(test_session_id, test_sender_id)
        
        print(f"📋 Результат обработки:")
        print(f"   - Готов для оператора: {order_result.get('is_ready_for_operator')}")
        
        validation = order_result.get('validation', {})
        print(f"   - Полный заказ: {validation.get('is_complete')}")
        print(f"   - Отсутствует: {validation.get('missing_required')}")
        print(f"   - Рекомендуется: {validation.get('missing_optional')}")
        
        # 7. Подтверждаем заказ
        print("\n7️⃣ Подтверждение заказа...")
        await order_service.update_order_status(test_session_id, test_sender_id, OrderStatus.CONFIRMED)
        
        # 8. Финальная проверка
        print("\n8️⃣ Финальная проверка...")
        final_order = await order_service.get_order_data(test_session_id, test_sender_id)
        print(f"📦 Финальный статус: {final_order.get('status')}")
        
        # Проверяем, что все данные сохранились корректно
        assert final_order.get('status') == 'confirmed', "Статус должен быть confirmed"
        assert final_order.get('delivery_needed') == True, "Доставка должна быть True"
        assert final_order.get('address') == 'Phuket, Patong Beach, 123/45', "Адрес должен совпадать"
        assert len(final_order.get('items', [])) == 1, "Должен быть 1 товар"
        
        print("\n🎉 Все тесты с каталогом прошли успешно!")
        print("✅ OrderService корректно работает с реальными данными из каталога")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_with_catalog()) 
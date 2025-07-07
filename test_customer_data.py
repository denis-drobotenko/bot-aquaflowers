#!/usr/bin/env python3
"""
Тест сохранения данных заказчика в заказе
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService

async def test_customer_data():
    """Тестирует сохранение данных заказчика"""
    print("🧪 Тест сохранения данных заказчика...")
    
    order_service = OrderService()
    
    # Тестовые данные
    test_session_id = f"customer_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_sender_id = "customer_test_user"
    test_customer_name = "Иван Петров"  # Исходное имя из WABA
    test_customer_phone = "+79123456789"  # Исходный телефон из WABA
    
    print(f"📋 Тестовая сессия: {test_session_id}")
    print(f"👤 Заказчик: {test_customer_name}")
    print(f"📞 Телефон: {test_customer_phone}")
    
    try:
        # 1. Создаем заказ с данными заказчика
        print("\n1️⃣ Создание заказа с данными заказчика...")
        customer_data = {
            'customer_name': test_customer_name,
            'customer_phone': test_customer_phone
        }
        
        order_id = await order_service.update_order_data(test_session_id, test_sender_id, customer_data)
        print(f"✅ Заказ создан с ID: {order_id}")
        
        # 2. Добавляем товар
        print("\n2️⃣ Добавление товара...")
        item_data = {
            'bouquet': 'Test Bouquet',
            'quantity': 1,
            'price': '1 500,00 ฿',
            'product_id': 'test_product_123'
        }
        
        order_id = await order_service.add_item(test_session_id, test_sender_id, item_data)
        print(f"✅ Товар добавлен")
        
        # 3. Получаем данные заказа
        print("\n3️⃣ Получение данных заказа...")
        order = await order_service.get_order_data(test_session_id, test_sender_id)
        
        print(f"📦 Данные заказа:")
        print(f"   - ID: {order.get('order_id')}")
        print(f"   - Заказчик: {order.get('customer_name')}")
        print(f"   - Телефон заказчика: {order.get('customer_phone')}")
        print(f"   - Товаров: {len(order.get('items', []))}")
        
        # 4. Проверяем, что данные заказчика сохранились корректно
        print("\n4️⃣ Проверка данных заказчика...")
        assert order.get('customer_name') == test_customer_name, f"Имя заказчика не совпадает: {order.get('customer_name')} != {test_customer_name}"
        assert order.get('customer_phone') == test_customer_phone, f"Телефон заказчика не совпадает: {order.get('customer_phone')} != {test_customer_phone}"
        
        print("✅ Данные заказчика сохранены корректно!")
        
        # 5. Тест сводки для AI
        print("\n5️⃣ Тест сводки для AI...")
        summary = order_service.get_order_summary_for_ai(order)
        print(f"📋 Сводка заказа:")
        print(summary)
        
        # Проверяем, что в сводке есть данные заказчика
        assert test_customer_name in summary, "Имя заказчика отсутствует в сводке"
        assert test_customer_phone in summary, "Телефон заказчика отсутствует в сводке"
        
        print("✅ Сводка для AI содержит данные заказчика!")
        
        print("\n🎉 Все тесты прошли успешно!")
        print("✅ Данные заказчика корректно сохраняются в заказе")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_customer_data()) 
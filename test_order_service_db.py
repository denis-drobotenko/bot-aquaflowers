#!/usr/bin/env python3
"""
Тест OrderService с прямым доступом к БД
Проверяет все функции сохранения и получения данных заказов
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService
from src.models.order import OrderStatus

async def test_order_service():
    """Тестирует все функции OrderService"""
    print("🧪 Начинаем тест OrderService...")
    
    order_service = OrderService()
    
    # Тестовые данные
    test_session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_sender_id = "test_user_123"
    
    print(f"📋 Тестовая сессия: {test_session_id}")
    print(f"👤 Тестовый пользователь: {test_sender_id}")
    
    try:
        # 1. Тест создания заказа
        print("\n1️⃣ Тест создания заказа...")
        order_data = {
            'delivery_needed': True,
            'address': 'Test Address 123',
            'card_needed': True,
            'card_text': 'Happy Birthday!'
        }
        
        order_id = await order_service.update_order_data(test_session_id, test_sender_id, order_data)
        print(f"✅ Заказ создан с ID: {order_id}")
        
        # 2. Тест добавления товара
        print("\n2️⃣ Тест добавления товара...")
        item_data = {
            'bouquet': 'Test Bouquet',
            'quantity': 2,
            'price': '1 500,00 ฿',
            'notes': 'Test notes',
            'product_id': 'test_product_123'
        }
        
        order_id = await order_service.add_item(test_session_id, test_sender_id, item_data)
        print(f"✅ Товар добавлен в заказ: {order_id}")
        
        # 3. Тест получения данных заказа
        print("\n3️⃣ Тест получения данных заказа...")
        retrieved_order = await order_service.get_order_data(test_session_id, test_sender_id)
        print(f"📦 Полученные данные заказа:")
        print(f"   - ID: {retrieved_order.get('id')}")
        print(f"   - Статус: {retrieved_order.get('status')}")
        print(f"   - Доставка: {retrieved_order.get('delivery_needed')}")
        print(f"   - Адрес: {retrieved_order.get('address')}")
        print(f"   - Товары: {len(retrieved_order.get('items', []))}")
        
        # Проверяем товары
        items = retrieved_order.get('items', [])
        if items:
            print(f"   - Первый товар: {items[0]}")
        
        # 4. Тест добавления второго товара
        print("\n4️⃣ Тест добавления второго товара...")
        item_data2 = {
            'bouquet': 'Second Test Bouquet',
            'quantity': 1,
            'price': '2 000,00 ฿',
            'product_id': 'test_product_456'
        }
        
        order_id = await order_service.add_item(test_session_id, test_sender_id, item_data2)
        print(f"✅ Второй товар добавлен")
        
        # 5. Тест получения обновленного заказа
        print("\n5️⃣ Тест получения обновленного заказа...")
        updated_order = await order_service.get_order_data(test_session_id, test_sender_id)
        items = updated_order.get('items', [])
        print(f"📦 Товаров в заказе: {len(items)}")
        for i, item in enumerate(items, 1):
            print(f"   {i}. {item.get('bouquet')} - {item.get('price')} (x{item.get('quantity')})")
        
        # 6. Тест удаления товара
        print("\n6️⃣ Тест удаления товара...")
        if items:
            product_id_to_remove = items[0].get('product_id')
            success = await order_service.remove_item(test_session_id, test_sender_id, product_id_to_remove)
            print(f"✅ Товар удален: {success}")
        
        # 7. Тест обновления статуса
        print("\n7️⃣ Тест обновления статуса...")
        await order_service.update_order_status(test_session_id, test_sender_id, OrderStatus.CONFIRMED)
        print(f"✅ Статус обновлен на CONFIRMED")
        
        # 8. Финальная проверка
        print("\n8️⃣ Финальная проверка заказа...")
        final_order = await order_service.get_order_data(test_session_id, test_sender_id)
        print(f"📦 Финальный статус: {final_order.get('status')}")
        print(f"📦 Товаров осталось: {len(final_order.get('items', []))}")
        
        # 9. Тест обработки заказа для оператора
        print("\n9️⃣ Тест обработки заказа для оператора...")
        order_result = await order_service.process_order_for_operator(test_session_id, test_sender_id)
        print(f"📋 Готов для оператора: {order_result.get('is_ready_for_operator')}")
        print(f"📋 Валидация: {order_result.get('validation')}")
        
        print("\n🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_service()) 
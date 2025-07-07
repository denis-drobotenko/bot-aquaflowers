#!/usr/bin/env python3
"""
Тест создания тестового заказа
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService
from src.models.order import Order, OrderItem, OrderStatus
from datetime import datetime

async def test_create_order():
    print("🔍 Тест создания тестового заказа...")
    
    order_service = OrderService()
    
    # Создаем тестовый заказ
    test_session_id = "test_session_001"
    test_sender_id = "79140775712"
    
    try:
        # Создаем заказ
        order = await order_service.get_or_create_order(test_session_id, test_sender_id)
        print(f"✅ Заказ создан: {order.order_id}")
        
        # Добавляем товар
        item_data = {
            "product_id": "test_product_001",
            "bouquet": "Test Bouquet 🌸",
            "quantity": 2,
            "price": "350.00 ฿",
            "notes": "Test item"
        }
        
        result = await order_service.add_item(test_session_id, test_sender_id, item_data)
        print(f"✅ Товар добавлен: {result}")
        
        # Обновляем данные заказа
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": test_sender_id,
            "recipient_name": "Test Recipient",
            "recipient_phone": "1234567890",
            "address": "Test Address, Bangkok",
            "date": "2025-07-08",
            "time": "14:00",
            "card_text": "Test card text",
            "delivery_needed": True
        }
        
        result = await order_service.update_order_data(test_session_id, test_sender_id, order_data)
        print(f"✅ Данные заказа обновлены: {result}")
        
        # Подтверждаем заказ
        result = await order_service.update_order_status(test_session_id, test_sender_id, OrderStatus.CONFIRMED)
        print(f"✅ Заказ подтвержден: {result}")
        
        # Проверяем, что заказ появился в CRM
        print("\n🔍 Проверяем заказ в CRM...")
        all_orders = await order_service.get_all_orders_for_crm()
        print(f"✅ Заказов в CRM: {len(all_orders)}")
        
        if all_orders:
            for order in all_orders:
                print(f"📋 Заказ: {order.get('order_id')} | {order.get('status')} | {order.get('customer_name')}")
        
        # Проверяем сводку по клиентам
        print("\n🔍 Проверяем сводку по клиентам...")
        customer_summary = await order_service.get_customer_orders_summary()
        print(f"✅ Клиентов с заказами: {len(customer_summary['with_orders'])}")
        print(f"✅ Клиентов без заказов: {len(customer_summary['without_orders'])}")
        
        if customer_summary['with_orders']:
            for customer in customer_summary['with_orders']:
                print(f"👤 {customer['name']} ({customer['phone']}) - {customer['total_orders']} заказов")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_create_order()) 
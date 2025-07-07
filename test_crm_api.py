#!/usr/bin/env python3
"""
Тест CRM API
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService

async def test_crm_api():
    print("🔍 Тест CRM API...")
    
    order_service = OrderService()
    
    # 1. Тест get_all_orders_for_crm
    print("\n1. Тест get_all_orders_for_crm:")
    try:
        orders = await order_service.get_all_orders_for_crm()
        print(f"   ✅ Получено заказов: {len(orders)}")
        
        for order in orders:
            print(f"   📋 Заказ: {order.get('order_id')} | {order.get('status')} | {order.get('customer_name')}")
            print(f"      Товары: {order.get('total_items')} | Цена: {order.get('total_price')}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    # 2. Тест get_customer_orders_summary
    print("\n2. Тест get_customer_orders_summary:")
    try:
        summary = await order_service.get_customer_orders_summary()
        print(f"   ✅ Клиентов с заказами: {len(summary['with_orders'])}")
        print(f"   ✅ Клиентов без заказов: {len(summary['without_orders'])}")
        
        for customer in summary['with_orders']:
            print(f"   👤 {customer['name']} ({customer['phone']}) - {customer['total_orders']} заказов")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(test_crm_api()) 
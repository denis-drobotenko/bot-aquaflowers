#!/usr/bin/env python3
"""
Тестовый скрипт для проверки заказов в CRM
"""

import asyncio
from src.services.order_service import OrderService

async def test_crm_orders():
    print("🔍 Проверка заказов для CRM...")
    
    order_service = OrderService()
    
    # Тест 1: Получаем все заказы для CRM
    print("\n1. Тест get_all_orders_for_crm()...")
    try:
        all_orders = await order_service.get_all_orders_for_crm()
        print(f"✅ Получено заказов для CRM: {len(all_orders)}")
        
        if all_orders:
            print("📋 Примеры заказов:")
            for i, order in enumerate(all_orders[:3]):
                print(f"  {i+1}. ID: {order.get('order_id')}, Статус: {order.get('status')}, Клиент: {order.get('sender_id')}")
                print(f"     Создан: {order.get('created_at')}")
                print(f"     Товары: {order.get('total_items', 0)}")
        else:
            print("⚠️ Заказов для CRM нет")
            
    except Exception as e:
        print(f"❌ Ошибка get_all_orders_for_crm: {e}")
        import traceback
        traceback.print_exc()
    
    # Тест 2: Получаем сводку по клиентам
    print("\n2. Тест get_customer_orders_summary()...")
    try:
        customer_summary = await order_service.get_customer_orders_summary()
        print(f"✅ Клиентов с заказами: {len(customer_summary['with_orders'])}")
        print(f"✅ Клиентов без заказов: {len(customer_summary['without_orders'])}")
        
        if customer_summary['with_orders']:
            print("📋 Примеры клиентов с заказами:")
            for i, customer in enumerate(customer_summary['with_orders'][:3]):
                print(f"  {i+1}. {customer['name']} ({customer['phone']}) - {customer['total_orders']} заказов")
        else:
            print("⚠️ Клиентов с заказами нет")
            
    except Exception as e:
        print(f"❌ Ошибка get_customer_orders_summary: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crm_orders()) 
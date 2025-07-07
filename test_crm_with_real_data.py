#!/usr/bin/env python3
"""
Тест CRM с реальными данными
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService

async def test_crm_with_real_data():
    print("🔍 Тест CRM с реальными данными...")
    
    order_service = OrderService()
    
    try:
        # 1. Проверяем все заказы для CRM
        print("\n1. Проверяем get_all_orders_for_crm()...")
        all_orders = await order_service.get_all_orders_for_crm()
        print(f"✅ Заказов для CRM: {len(all_orders)}")
        
        if all_orders:
            print("📋 Примеры заказов:")
            for i, order in enumerate(all_orders[:3]):
                print(f"  {i+1}. ID: {order.get('order_id')}")
                print(f"     Статус: {order.get('status')}")
                print(f"     Клиент: {order.get('customer_name', 'N/A')} ({order.get('sender_id')})")
                print(f"     Создан: {order.get('created_at')}")
                print(f"     Товары: {order.get('total_items', 0)}")
                print(f"     Цена: {order.get('total_price', 0)}")
        else:
            print("⚠️ Заказов для CRM нет")
        
        # 2. Проверяем сводку по клиентам
        print("\n2. Проверяем get_customer_orders_summary()...")
        customer_summary = await order_service.get_customer_orders_summary()
        print(f"✅ Клиентов с заказами: {len(customer_summary['with_orders'])}")
        print(f"✅ Клиентов без заказов: {len(customer_summary['without_orders'])}")
        
        if customer_summary['with_orders']:
            print("📋 Клиенты с заказами:")
            for i, customer in enumerate(customer_summary['with_orders']):
                print(f"  {i+1}. {customer['name']} ({customer['phone']})")
                print(f"     Заказов: {customer['total_orders']}")
                print(f"     Завершённых: {customer['completed_orders']}")
                if customer.get('orders'):
                    print(f"     Заказы: {[order.get('order_id', 'N/A')[-8:] for order in customer['orders'][:3]]}")
        else:
            print("⚠️ Клиентов с заказами нет")
        
        # 3. Проверяем группировку по времени
        print("\n3. Проверяем группировку по времени...")
        from src.routes.crm_routes import group_orders_by_time
        time_grouped = group_orders_by_time(all_orders)
        
        print("📋 Группировка по времени:")
        for period, statuses in time_grouped.items():
            incomplete = len(statuses['incomplete'])
            completed = len(statuses['completed'])
            total = incomplete + completed
            print(f"  {period.capitalize()}: {total} заказов ({incomplete} незавершённых, {completed} завершённых)")
        
        # 4. Проверяем группировку по статусам
        print("\n4. Проверяем группировку по статусам...")
        from src.routes.crm_routes import group_orders_by_status
        status_grouped = group_orders_by_status(all_orders)
        
        print("📋 Группировка по статусам:")
        for status, orders in status_grouped.items():
            print(f"  {status}: {len(orders)} заказов")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_crm_with_real_data()) 
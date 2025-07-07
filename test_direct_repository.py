#!/usr/bin/env python3
"""
Прямая проверка репозитория
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.repositories.order_repository import OrderRepository

async def test_direct_repository():
    print("🔍 Прямая проверка репозитория...")
    
    repo = OrderRepository()
    
    try:
        # Проверяем get_all_orders
        print("\n1. Проверяем get_all_orders()...")
        orders = await repo.get_all_orders()
        print(f"✅ Получено заказов: {len(orders)}")
        
        if orders:
            print("📋 Заказы:")
            for i, order in enumerate(orders[:3]):
                print(f"  {i+1}. ID: {order.order_id}")
                print(f"     Статус: {order.status}")
                print(f"     Клиент: {order.sender_id}")
                print(f"     Сессия: {order.session_id}")
                print(f"     Товары: {len(order.items)}")
        else:
            print("⚠️ Заказов нет")
        
        # Проверяем конкретный заказ
        print("\n2. Проверяем конкретный заказ...")
        specific_order = await repo.get_order_by_session("79140775712", "20250707_015555_233876_286")
        if specific_order:
            print(f"✅ Конкретный заказ найден: {specific_order.order_id}")
            print(f"   Статус: {specific_order.status}")
            print(f"   Товары: {len(specific_order.items)}")
        else:
            print("❌ Конкретный заказ не найден")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_repository()) 
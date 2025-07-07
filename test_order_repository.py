#!/usr/bin/env python3
"""
Тест для проверки OrderRepository.get_all_orders()
"""

import asyncio
from src.repositories.order_repository import OrderRepository

async def test_order_repository():
    print("🔍 Тест OrderRepository.get_all_orders()...")
    repo = OrderRepository()
    orders = await repo.get_all_orders()
    print(f"Найдено заказов: {len(orders)}")
    if not orders:
        print("⚠️ Нет заказов!")
        return
    for i, order in enumerate(orders[:5]):
        print(f"\n{i+1}. order_id: {order.order_id}")
        print(f"   status: {order.status.value}")
        print(f"   sender_id: {order.sender_id}")
        print(f"   customer_name: {getattr(order, 'customer_name', None)}")
        print(f"   items: {len(order.items)}")
        for j, item in enumerate(order.items):
            print(f"      {j+1}. {item.bouquet} | {item.price}")

if __name__ == "__main__":
    asyncio.run(test_order_repository()) 
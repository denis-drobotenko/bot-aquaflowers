#!/usr/bin/env python3
"""
Простой тест подключения к Firestore
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.repositories.order_repository import OrderRepository

async def test_simple():
    print("🔍 Простой тест Firestore...")
    
    repo = OrderRepository()
    
    try:
        orders = await repo.get_all_orders()
        print(f"✅ Получено заказов: {len(orders)}")
        
        if orders:
            for order in orders[:3]:
                print(f"📋 Заказ: {order.order_id} | {order.status} | {order.sender_id}")
        else:
            print("⚠️ Заказов не найдено")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple()) 
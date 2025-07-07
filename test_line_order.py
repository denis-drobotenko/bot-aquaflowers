#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки заказа в LINE.
"""

import asyncio
import sys
import os

# Добавляем src в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.order_service import OrderService
from src.repositories.order_repository import OrderRepository

async def test_line_order():
    """Тестирует отправку заказа в LINE."""
    print("🧪 Тестируем отправку заказа в LINE...")
    
    # Инициализируем сервисы
    order_repo = OrderRepository()
    order_service = OrderService()
    order_service.repo = order_repo
    
    # Тестовые данные
    session_id = "20250706_162943_50861_139"
    sender_id = "79140775712"
    
    try:
        # Получаем данные заказа
        print(f"📋 Получаем данные заказа для сессии: {session_id}")
        order_data = await order_service.get_order_data(session_id, sender_id)
        
        if not order_data:
            print("❌ Заказ не найден!")
            return
        
        print(f"✅ Заказ найден: {order_data.get('order_id')}")
        print(f"📦 Товары: {len(order_data.get('items', []))}")
        
        for i, item in enumerate(order_data.get('items', []), 1):
            print(f"  {i}. {item.get('bouquet')} x{item.get('quantity', 1)}")
        
        # Тестируем отправку в LINE
        print("\n📤 Отправляем заказ в LINE...")
        result = await order_service.send_order_to_line(session_id, sender_id)
        
        if result == "ok":
            print("✅ Заказ успешно отправлен в LINE!")
        else:
            print(f"❌ Ошибка отправки: {result}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
    finally:
        # OrderRepository не требует закрытия
        pass

if __name__ == "__main__":
    asyncio.run(test_line_order()) 
#!/usr/bin/env python3
"""
Тестовый скрипт для проверки данных в БД
"""

import asyncio
from src.repositories.order_repository import OrderRepository
from src.services.order_service import OrderService

async def test_db_data():
    print("🔍 Проверка данных в БД...")
    
    # Тест 1: Проверяем репозиторий
    print("\n1. Тест репозитория...")
    try:
        repo = OrderRepository()
        print(f"✅ Репозиторий создан")
        print(f"✅ Firestore доступен: {repo.db is not None}")
        
        # Пробуем получить все заказы
        orders = await repo.get_all_orders()
        print(f"✅ Получено заказов из БД: {len(orders)}")
        
        if orders:
            print("📋 Примеры заказов:")
            for i, order in enumerate(orders[:3]):
                print(f"  {i+1}. ID: {order.order_id}, Статус: {order.status.value}, Клиент: {order.sender_id}")
        else:
            print("⚠️ Заказов в БД нет")
            
    except Exception as e:
        print(f"❌ Ошибка репозитория: {e}")
    
    # Тест 2: Проверяем сервис
    print("\n2. Тест сервиса...")
    try:
        service = OrderService()
        
        # Получаем все заказы для CRM
        all_orders = await service.get_all_orders_for_crm()
        print(f"✅ Получено заказов для CRM: {len(all_orders)}")
        
        if all_orders:
            print("📋 Примеры заказов для CRM:")
            for i, order in enumerate(all_orders[:3]):
                print(f"  {i+1}. ID: {order['order_id']}, Статус: {order['status']}, Клиент: {order['sender_id']}")
        
        # Получаем сводку по клиентам
        customer_summary = await service.get_customer_orders_summary()
        print(f"✅ Клиентов с заказами: {len(customer_summary['with_orders'])}")
        print(f"✅ Клиентов без заказов: {len(customer_summary['without_orders'])}")
        
        if customer_summary['with_orders']:
            print("📋 Примеры клиентов с заказами:")
            for i, customer in enumerate(customer_summary['with_orders'][:3]):
                print(f"  {i+1}. {customer['name']} ({customer['phone']}) - {customer['total_orders']} заказов")
                
    except Exception as e:
        print(f"❌ Ошибка сервиса: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_data()) 
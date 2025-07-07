#!/usr/bin/env python3
"""
Тестовый скрипт для проверки реальных сессий и создания заказов
"""

import asyncio
from google.cloud import firestore
from src.services.order_service import OrderService
from src.models.order import Order, OrderStatus, OrderItem
from datetime import datetime

async def test_real_orders():
    print("🔍 Проверка реальных сессий и создание заказов...")
    
    db = firestore.Client()
    order_service = OrderService()
    
    # 1. Проверяем, есть ли сессии в conversations
    print("\n1. Проверяем сессии в conversations...")
    conversations_ref = db.collection('conversations')
    conversations = list(conversations_ref.stream())
    print(f"✅ Найдено пользователей: {len(conversations)}")
    
    if not conversations:
        print("⚠️ Нет пользователей в conversations")
        return
    
    # 2. Для каждого пользователя проверяем сессии
    total_sessions = 0
    for conv_doc in conversations:
        sender_id = conv_doc.id
        sessions_ref = conv_doc.reference.collection('sessions')
        sessions = list(sessions_ref.stream())
        print(f"  Пользователь {sender_id}: {len(sessions)} сессий")
        total_sessions += len(sessions)
        
        # 3. Для каждой сессии создаем заказ
        for session_doc in sessions:
            session_id = session_doc.id
            session_data = session_doc.to_dict()
            message_count = session_data.get('message_count', 0)
            
            print(f"    Сессия {session_id}: {message_count} сообщений")
            
            # Создаем заказ для этой сессии
            try:
                order = Order(
                    order_id=session_id,
                    session_id=session_id,
                    sender_id=sender_id,
                    status=OrderStatus.DRAFT,
                    created_at=session_data.get('created_at', datetime.now()),
                    updated_at=datetime.now()
                )
                
                # Добавляем тестовый товар
                item = OrderItem(
                    product_id="test_product_1",
                    bouquet="Тестовый букет",
                    quantity=1,
                    price="฿500",
                    notes="Создан автоматически"
                )
                order.items.append(item)
                
                # Сохраняем заказ
                await order_service.repo.create_order_for_session(order)
                print(f"    ✅ Создан заказ для сессии {session_id}")
                
            except Exception as e:
                print(f"    ❌ Ошибка создания заказа для {session_id}: {e}")
    
    print(f"\n📊 Итого: {total_sessions} сессий обработано")
    
    # 4. Проверяем, что заказы создались
    print("\n2. Проверяем созданные заказы...")
    try:
        all_orders = await order_service.get_all_orders_for_crm()
        print(f"✅ Теперь заказов в CRM: {len(all_orders)}")
        
        if all_orders:
            print("📋 Примеры заказов:")
            for i, order in enumerate(all_orders[:3]):
                print(f"  {i+1}. ID: {order.get('order_id')}, Статус: {order.get('status')}, Клиент: {order.get('sender_id')}")
                print(f"     Товары: {order.get('total_items', 0)}")
    except Exception as e:
        print(f"❌ Ошибка проверки заказов: {e}")

if __name__ == "__main__":
    asyncio.run(test_real_orders()) 
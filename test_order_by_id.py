#!/usr/bin/env python3
"""
Тест для получения заказа по user_id и session_id через OrderRepository
"""

import asyncio
from src.repositories.order_repository import OrderRepository

async def test_order_by_id():
    sender_id = '79140775712'
    session_id = None
    repo = OrderRepository()
    # Получаем все сессии для user_id
    from google.cloud import firestore
    db = firestore.Client()
    sessions_ref = db.collection('orders').document(sender_id).collection('sessions')
    session_docs = list(sessions_ref.stream())
    print(f"Найдено сессий для {sender_id}: {len(session_docs)}")
    if not session_docs:
        print("Нет сессий!")
        return
    for i, session_doc in enumerate(session_docs):
        session_id = session_doc.id
        print(f"\n{i+1}. session_id: {session_id}")
        order = await repo.get_order_by_session(sender_id, session_id)
        if order:
            print(f"  ✅ Заказ найден: {order.order_id}")
            print(f"  Статус: {order.status.value}")
            print(f"  Клиент: {getattr(order, 'customer_name', None)} | {getattr(order, 'customer_phone', None)}")
            print(f"  Товаров: {len(order.items)}")
            for j, item in enumerate(order.items):
                print(f"    {j+1}. {item.bouquet} | {item.price}")
        else:
            print("  ❌ Заказ не найден!")

if __name__ == "__main__":
    asyncio.run(test_order_by_id()) 
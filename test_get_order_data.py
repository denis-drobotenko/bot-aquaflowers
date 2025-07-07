#!/usr/bin/env python3
"""
Тест для вызова get_order_data по sender_id=79140775712 и всем его сессиям
"""

import asyncio
from src.services.order_service import OrderService
from google.cloud import firestore

async def test_get_order_data():
    sender_id = '79140775712'
    db = firestore.Client()
    sessions_ref = db.collection('orders').document(sender_id).collection('sessions')
    session_docs = list(sessions_ref.stream())
    print(f"Найдено сессий для {sender_id}: {len(session_docs)}")
    if not session_docs:
        print("Нет сессий!")
        return
    order_service = OrderService()
    for i, session_doc in enumerate(session_docs):
        session_id = session_doc.id
        print(f"\n{i+1}. session_id: {session_id}")
        order_data = await order_service.get_order_data(session_id, sender_id)
        if order_data:
            print(f"  ✅ Заказ найден: {order_data['order_id']}")
            print(f"  Статус: {order_data['status']}")
            print(f"  Клиент: {order_data.get('customer_name')} | {order_data.get('customer_phone')}")
            print(f"  Товаров: {len(order_data.get('items', []))}")
            for j, item in enumerate(order_data.get('items', [])):
                print(f"    {j+1}. {item.get('bouquet')} | {item.get('price')}")
        else:
            print("  ❌ Заказ не найден!")

if __name__ == "__main__":
    asyncio.run(test_get_order_data()) 
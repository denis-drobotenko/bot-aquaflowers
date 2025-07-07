#!/usr/bin/env python3
"""
Тест для исправления получения заказа по order_id
"""

import asyncio
from src.services.order_service import OrderService

async def test_order_fix():
    order_service = OrderService()
    
    # Тестовые данные
    session_id = "20250706_162943_50861_139"
    sender_id = "79140775712"
    
    print(f"Testing order retrieval:")
    print(f"Session ID: {session_id}")
    print(f"Sender ID: {sender_id}")
    
    # Тест 1: Прямое получение с правильным sender_id
    print("\n1. Testing direct retrieval with correct sender_id:")
    order_data = await order_service.get_order_data(session_id, sender_id)
    if order_data:
        print(f"✅ Order found: {order_data.get('order_id')}")
        print(f"   Status: {order_data.get('status')}")
        print(f"   Items: {len(order_data.get('items', []))}")
    else:
        print("❌ Order not found")
    
    # Тест 2: Получение без sender_id (должно извлечь неправильно)
    print("\n2. Testing retrieval without sender_id:")
    order_data = await order_service.get_order_data(session_id)
    if order_data:
        print(f"✅ Order found: {order_data.get('order_id')}")
    else:
        print("❌ Order not found (expected)")
    
    # Тест 3: Поиск sender_id в базе данных
    print("\n3. Testing sender_id search in database:")
    try:
        from google.cloud import firestore
        db = firestore.Client()
        orders_ref = db.collection('orders')
        users = orders_ref.stream()
        
        found_sender_id = None
        for user_doc in users:
            sessions_ref = user_doc.reference.collection('sessions')
            session_doc = sessions_ref.document(session_id).get()
            if session_doc.exists:
                found_sender_id = user_doc.id
                print(f"✅ Found sender_id: {found_sender_id}")
                break
        
        if found_sender_id:
            # Тест с найденным sender_id
            order_data = await order_service.get_order_data(session_id, found_sender_id)
            if order_data:
                print(f"✅ Order found with searched sender_id: {order_data.get('order_id')}")
            else:
                print("❌ Order not found with searched sender_id")
        else:
            print("❌ Sender_id not found in database")
            
    except Exception as e:
        print(f"❌ Error searching database: {e}")

if __name__ == "__main__":
    asyncio.run(test_order_fix()) 
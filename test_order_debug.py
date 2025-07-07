#!/usr/bin/env python3
"""
Тест для отладки проблемы с заказом
"""

import asyncio
from src.services.order_service import OrderService
from src.repositories.order_repository import OrderRepository
from google.cloud import firestore

async def test_order_debug():
    sender_id = '79140775712'
    session_id = '20250706_162943_50861_139'
    
    print(f"Testing order retrieval for {sender_id}/{session_id}")
    
    # Тест 1: Прямое обращение к Firestore
    print("\n1. Direct Firestore access:")
    try:
        db = firestore.Client()
        doc_ref = db.collection('orders').document(sender_id).collection('sessions').document(session_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            print(f"Raw data from Firestore: {data}")
            print(f"Data keys: {list(data.keys())}")
            
            if 'items' in data:
                print(f"Items type: {type(data['items'])}")
                print(f"Items value: {data['items']}")
        else:
            print("Document not found in Firestore")
    except Exception as e:
        print(f"Firestore error: {e}")
    
    # Тест 2: Через репозиторий
    print("\n2. Through repository:")
    try:
        repo = OrderRepository()
        order = await repo.get_order_by_session(sender_id, session_id)
        
        if order:
            print(f"Order retrieved: {order.order_id}")
            print(f"Order type: {type(order)}")
            print(f"Order attributes: {dir(order)}")
            
            if hasattr(order, 'items'):
                print(f"order.items type: {type(order.items)}")
                print(f"order.items value: {order.items}")
            else:
                print("order.items attribute not found")
        else:
            print("Order not found through repository")
    except Exception as e:
        print(f"Repository error: {e}")
        import traceback
        traceback.print_exc()
    
    # Тест 3: Через сервис
    print("\n3. Through service:")
    try:
        service = OrderService()
        order_data = await service.get_order_data(session_id, sender_id)
        
        if order_data:
            print(f"Order data retrieved: {order_data['order_id']}")
            print(f"Items count: {len(order_data.get('items', []))}")
        else:
            print("Order data not found through service")
    except Exception as e:
        print(f"Service error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_order_debug()) 
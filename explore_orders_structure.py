#!/usr/bin/env python3
"""
Скрипт для вывода структуры orders: user_id -> session_id -> краткая инфа по заказу
"""

from google.cloud import firestore

def explore_orders_structure(user_id_filter=None):
    print("🔍 Структура Firestore: orders/{user_id}/sessions/{session_id}")
    db = firestore.Client()
    orders_ref = db.collection('orders')
    if user_id_filter:
        user_docs = [orders_ref.document(user_id_filter).get()]
    else:
        user_docs = list(orders_ref.stream())
    print(f"Всего user_id в orders: {len(user_docs)}")
    if not user_docs or not user_docs[0].exists:
        print("⚠️ Нет user_id в orders!")
        return
    for i, user_doc in enumerate(user_docs):
        user_id = user_doc.id
        print(f"\n{i+1}. user_id: {user_id}")
        sessions_ref = user_doc.reference.collection('sessions')
        session_docs = list(sessions_ref.stream())
        print(f"   Сессий: {len(session_docs)}")
        if not session_docs:
            print("   ⚠️ Нет сессий!")
            continue
        for j, session_doc in enumerate(session_docs):
            session_id = session_doc.id
            data = session_doc.to_dict()
            print(f"   {j+1}. session_id: {session_id}")
            print(f"      customer_name: {data.get('customer_name')}")
            print(f"      created_at: {data.get('created_at')}")
            print(f"      items: {len(data.get('items', []))}")
            if data.get('items'):
                for k, item in enumerate(data['items']):
                    print(f"         {k+1}. {item.get('bouquet')} | {item.get('price')}")

if __name__ == "__main__":
    explore_orders_structure('79140775712') 
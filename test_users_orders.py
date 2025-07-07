#!/usr/bin/env python3
"""
Проверка заказов в подколлекции orders у пользователей
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_users_orders():
    print("🔍 Проверка заказов в подколлекции orders у пользователей...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем всех пользователей
        users_ref = db.collection('users')
        users = list(users_ref.stream())
        
        print(f"📋 Найдено пользователей: {len(users)}")
        
        total_orders = 0
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            sender_id = user_data.get('sender_id', user_doc.id)
            
            # Проверяем подколлекцию orders у пользователя
            orders_ref = user_doc.reference.collection('orders')
            orders = list(orders_ref.stream())
            
            if orders:
                print(f"\n👤 Пользователь: {user_data.get('name', 'Unknown')} ({sender_id})")
                print(f"   📦 Найдено заказов: {len(orders)}")
                total_orders += len(orders)
                
                for order_doc in orders:
                    order_data = order_doc.to_dict()
                    print(f"   🔍 Заказ: {order_doc.id} | Статус: {order_data.get('status', 'N/A')}")
        
        print(f"\n📊 Итого заказов: {total_orders}")
        
        if total_orders == 0:
            print("\n🔍 Проверяем другие возможные структуры...")
            
            # Проверяем, есть ли заказы в подколлекции sessions у пользователей
            for user_doc in users:
                user_data = user_doc.to_dict()
                sender_id = user_data.get('sender_id', user_doc.id)
                
                sessions_ref = user_doc.reference.collection('sessions')
                sessions = list(sessions_ref.stream())
                
                if sessions:
                    print(f"\n👤 Пользователь: {user_data.get('name', 'Unknown')} ({sender_id})")
                    print(f"   📦 Найдено сессий: {len(sessions)}")
                    
                    for session_doc in sessions:
                        session_data = session_doc.to_dict()
                        if 'order_id' in session_data or 'items' in session_data:
                            print(f"   🔍 Сессия с заказом: {session_doc.id} | Статус: {session_data.get('status', 'N/A')}")
                            total_orders += 1
            
            print(f"\n📊 Итого заказов в сессиях: {total_orders}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_users_orders()) 
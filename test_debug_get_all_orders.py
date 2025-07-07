#!/usr/bin/env python3
"""
Отладка метода get_all_orders
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_debug_get_all_orders():
    print("🔍 Отладка метода get_all_orders...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем все документы из коллекции orders
        orders_collection = db.collection('orders')
        user_docs = list(orders_collection.stream())
        
        print(f"📋 Найдено документов в orders: {len(user_docs)}")
        
        for user_doc in user_docs:
            sender_id = user_doc.id
            print(f"\n👤 Пользователь: {sender_id}")
            
            try:
                # Получаем подколлекцию sessions для каждого пользователя
                sessions_ref = user_doc.reference.collection('sessions')
                session_docs = list(sessions_ref.stream())
                
                print(f"   📦 Найдено сессий: {len(session_docs)}")
                
                for session_doc in session_docs:
                    data = session_doc.to_dict()
                    print(f"   🔍 Сессия: {session_doc.id} | Статус: {data.get('status', 'N/A')}")
                    
            except Exception as e:
                print(f"   ❌ Ошибка для {sender_id}: {e}")
        
        # Проверяем конкретно нашего тестового пользователя
        print(f"\n🔍 Проверяем тестового пользователя: 79140775712")
        test_user_ref = db.collection('orders').document('79140775712')
        test_user_doc = test_user_ref.get()
        
        if test_user_doc.exists:
            print("   ✅ Документ пользователя существует")
            
            # Проверяем подколлекцию sessions
            test_sessions_ref = test_user_ref.collection('sessions')
            test_sessions = list(test_sessions_ref.stream())
            
            print(f"   📦 Найдено сессий: {len(test_sessions)}")
            
            for session_doc in test_sessions:
                data = session_doc.to_dict()
                print(f"   🔍 Сессия: {session_doc.id} | Статус: {data.get('status', 'N/A')}")
        else:
            print("   ❌ Документ пользователя не существует")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_debug_get_all_orders()) 
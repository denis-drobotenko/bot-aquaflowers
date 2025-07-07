#!/usr/bin/env python3
"""
Тест с известными sender_id
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_known_sender_ids():
    print("🔍 Тест с известными sender_id...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    # Известные sender_id
    known_sender_ids = ["79140775712", "79140775713", "79140775714", "79140775715"]
    
    total_orders = 0
    
    for sender_id in known_sender_ids:
        try:
            print(f"\n📋 Проверяем пользователя: {sender_id}")
            
            # Проверяем, есть ли документ пользователя
            user_ref = db.collection('orders').document(sender_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                print(f"   ✅ Документ пользователя существует")
                
                # Проверяем подколлекцию sessions
                sessions_ref = user_ref.collection('sessions')
                sessions = list(sessions_ref.stream())
                
                print(f"   📦 Найдено сессий: {len(sessions)}")
                
                for session_doc in sessions:
                    data = session_doc.to_dict()
                    print(f"   🔍 Сессия: {session_doc.id} | Статус: {data.get('status', 'N/A')}")
                    total_orders += 1
            else:
                print(f"   ❌ Документ пользователя не существует")
                
        except Exception as e:
            print(f"   ❌ Ошибка для {sender_id}: {e}")
    
    print(f"\n📊 Итого заказов: {total_orders}")

if __name__ == "__main__":
    asyncio.run(test_known_sender_ids()) 
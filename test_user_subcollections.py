#!/usr/bin/env python3
"""
Тест подколлекций у пользователей с sender_id
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_user_subcollections():
    print("🔍 Проверка подколлекций у пользователей с sender_id...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    # Проверяем пользователей с sender_id как ID
    sender_ids = ["79140775712", "79140775713", "79140775714", "79084634603"]
    
    for sender_id in sender_ids:
        try:
            print(f"\n📋 Проверяем пользователя: {sender_id}")
            
            # Проверяем документ пользователя
            user_ref = db.collection('users').document(sender_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                print(f"   ✅ Пользователь найден: {user_data.get('name', 'Unknown')}")
                
                # Проверяем подколлекции
                subcollections = user_ref.collections()
                for subcollection in subcollections:
                    print(f"   📂 Подколлекция: {subcollection.id}")
                    subdocs = list(subcollection.stream())
                    print(f"      Документов: {len(subdocs)}")
                    
                    for subdoc in subdocs:
                        subdata = subdoc.to_dict()
                        print(f"      📄 {subdoc.id}: {subdata}")
            else:
                print(f"   ❌ Пользователь не найден")
                
        except Exception as e:
            print(f"   ❌ Ошибка для {sender_id}: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_subcollections()) 
#!/usr/bin/env python3
"""
Тест структуры коллекции users
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_users_structure():
    print("🔍 Проверка структуры коллекции users...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем все документы из коллекции users
        users_ref = db.collection('users')
        users = list(users_ref.stream())
        
        print(f"📋 Найдено пользователей: {len(users)}")
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            print(f"\n👤 Пользователь: {user_doc.id}")
            print(f"   Данные: {user_data}")
            
            # Проверяем подколлекции пользователя
            subcollections = user_doc.reference.collections()
            for subcollection in subcollections:
                print(f"   📂 Подколлекция: {subcollection.id}")
                subdocs = list(subcollection.stream())
                print(f"      Документов: {len(subdocs)}")
                
                for subdoc in subdocs:
                    subdata = subdoc.to_dict()
                    print(f"      📄 {subdoc.id}: {subdata}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_users_structure()) 
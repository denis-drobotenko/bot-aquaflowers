#!/usr/bin/env python3
"""
Проверка всех подколлекций у всех пользователей
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_all_subcollections():
    print("🔍 Проверка всех подколлекций у всех пользователей...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем всех пользователей
        users_ref = db.collection('users')
        users = list(users_ref.stream())
        
        print(f"📋 Найдено пользователей: {len(users)}")
        
        total_subcollections = 0
        
        for user_doc in users:
            user_data = user_doc.to_dict()
            sender_id = user_data.get('sender_id', user_doc.id)
            
            # Проверяем подколлекции
            subcollections = user_doc.reference.collections()
            subcollections_list = list(subcollections)
            
            if subcollections_list:
                print(f"\n👤 Пользователь: {user_data.get('name', 'Unknown')} ({sender_id})")
                print(f"   ID документа: {user_doc.id}")
                
                for subcollection in subcollections_list:
                    print(f"   📂 Подколлекция: {subcollection.id}")
                    subdocs = list(subcollection.stream())
                    print(f"      Документов: {len(subdocs)}")
                    total_subcollections += len(subdocs)
                    
                    for subdoc in subdocs:
                        subdata = subdoc.to_dict()
                        print(f"      📄 {subdoc.id}: {subdata}")
        
        print(f"\n📊 Итого документов в подколлекциях: {total_subcollections}")
        
        if total_subcollections == 0:
            print("\n🔍 Проверяем коллекцию conversations...")
            conversations_ref = db.collection('conversations')
            conversations = list(conversations_ref.stream())
            print(f"📋 Найдено документов в conversations: {len(conversations)}")
            
            if conversations:
                for conv_doc in conversations:
                    conv_data = conv_doc.to_dict()
                    print(f"📄 {conv_doc.id}: {conv_data}")
                    
                    # Проверяем подколлекции conversations
                    conv_subcollections = conv_doc.reference.collections()
                    for subcollection in conv_subcollections:
                        print(f"   📂 Подколлекция: {subcollection.id}")
                        subdocs = list(subcollection.stream())
                        print(f"      Документов: {len(subdocs)}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_all_subcollections()) 
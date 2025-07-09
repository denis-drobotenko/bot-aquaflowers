#!/usr/bin/env python3
"""
Скрипт для удаления странного пользователя
"""

import asyncio
from google.cloud import firestore

async def cleanup_strange_user():
    """Удаляет странного пользователя без sender_id"""
    
    # Инициализируем Firestore
    db = firestore.Client()
    users_ref = db.collection('users')
    
    print("🧹 Удаление странного пользователя...")
    print("=" * 60)
    
    # Получаем все документы
    docs = users_ref.stream()
    
    for doc in docs:
        user_data = doc.to_dict()
        doc_id = doc.id
        
        # Проверяем, есть ли sender_id
        if 'sender_id' not in user_data or not user_data['sender_id']:
            print(f"🔍 Найден странный пользователь:")
            print(f"   Doc ID: {doc_id}")
            print(f"   Data: {user_data}")
            
            try:
                doc_ref = users_ref.document(doc_id)
                doc_ref.delete()
                print(f"   ✅ Удален")
            except Exception as e:
                print(f"   ❌ Ошибка удаления: {e}")
        else:
            print(f"✅ Нормальный пользователь: {doc_id} -> {user_data.get('sender_id')}")
    
    print("=" * 60)
    print("✅ Очистка завершена!")

if __name__ == "__main__":
    asyncio.run(cleanup_strange_user()) 
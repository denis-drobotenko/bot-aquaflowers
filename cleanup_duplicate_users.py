#!/usr/bin/env python3
"""
Скрипт для очистки дубликатов пользователей
"""

import asyncio
from datetime import datetime
from google.cloud import firestore

async def cleanup_duplicate_users():
    """Очищает дубликаты пользователей, оставляя только самый старый"""
    
    # Инициализируем Firestore
    db = firestore.Client()
    users_ref = db.collection('users')
    
    print("🧹 Очистка дубликатов пользователей...")
    print("=" * 60)
    
    # Получаем все документы
    docs = users_ref.stream()
    
    users = []
    for doc in docs:
        user_data = doc.to_dict()
        user_data['doc_id'] = doc.id
        users.append(user_data)
    
    print(f"📊 Всего пользователей: {len(users)}")
    
    # Группируем по sender_id
    sender_groups = {}
    for user in users:
        sender_id = user.get('sender_id', 'unknown')
        if sender_id not in sender_groups:
            sender_groups[sender_id] = []
        sender_groups[sender_id].append(user)
    
    # Находим дубликаты
    duplicates = {}
    for sender_id, user_list in sender_groups.items():
        if len(user_list) > 1:
            duplicates[sender_id] = user_list
    
    print(f"🔍 Найдено {len(duplicates)} пользователей с дубликатами")
    
    total_deleted = 0
    
    for sender_id, user_list in duplicates.items():
        print(f"\n📱 Обрабатываем {sender_id}:")
        
        # Сортируем по времени создания (самый старый первый)
        sorted_users = sorted(user_list, key=lambda x: x.get('created_at', ''))
        
        # Оставляем самый старый, удаляем остальные
        keep_user = sorted_users[0]
        users_to_delete = sorted_users[1:]
        
        print(f"   Оставляем: {keep_user['doc_id']} (создан: {keep_user.get('created_at', 'N/A')})")
        print(f"   Удаляем: {len(users_to_delete)} дубликатов")
        
        for user_to_delete in users_to_delete:
            try:
                doc_ref = users_ref.document(user_to_delete['doc_id'])
                doc_ref.delete()
                print(f"     ✅ Удален: {user_to_delete['doc_id']}")
                total_deleted += 1
            except Exception as e:
                print(f"     ❌ Ошибка удаления {user_to_delete['doc_id']}: {e}")
    
    print(f"\n✅ Очистка завершена!")
    print(f"📊 Удалено дубликатов: {total_deleted}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_users()) 
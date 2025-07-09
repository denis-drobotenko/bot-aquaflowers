#!/usr/bin/env python3
"""
Скрипт для анализа коллекции Users
"""

import asyncio
import json
from datetime import datetime
from google.cloud import firestore

async def analyze_users_collection():
    """Анализирует коллекцию Users"""
    
    # Инициализируем Firestore
    db = firestore.Client()
    users_ref = db.collection('users')
    
    print("🔍 Анализ коллекции Users...")
    print("=" * 60)
    
    # Получаем все документы
    docs = users_ref.stream()
    
    users = []
    for doc in docs:
        user_data = doc.to_dict()
        user_data['doc_id'] = doc.id
        users.append(user_data)
    
    print(f"📊 Всего пользователей: {len(users)}")
    print()
    
    # Группируем по sender_id
    sender_groups = {}
    for user in users:
        sender_id = user.get('sender_id', 'unknown')
        if sender_id not in sender_groups:
            sender_groups[sender_id] = []
        sender_groups[sender_id].append(user)
    
    # Анализируем дубликаты
    duplicates = {}
    for sender_id, user_list in sender_groups.items():
        if len(user_list) > 1:
            duplicates[sender_id] = user_list
    
    print(f"🔍 Найдено {len(duplicates)} пользователей с дубликатами:")
    print()
    
    for sender_id, user_list in duplicates.items():
        print(f"📱 Sender ID: {sender_id}")
        print(f"   Количество документов: {len(user_list)}")
        
        for i, user in enumerate(user_list, 1):
            created_at = user.get('created_at')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = "Invalid date"
            
            updated_at = user.get('updated_at')
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                except:
                    updated_at = "Invalid date"
            
            print(f"   {i}. Doc ID: {user.get('doc_id')}")
            print(f"      Name: {user.get('name', 'N/A')}")
            print(f"      Language: {user.get('language', 'N/A')}")
            print(f"      Status: {user.get('status', 'N/A')}")
            print(f"      Created: {created_at}")
            print(f"      Updated: {updated_at}")
            print()
    
    # Анализируем системные ключи
    print("🔧 Анализ системных ключей:")
    print()
    
    system_keys = set()
    for user in users:
        for key in user.keys():
            if key.startswith('_') or key in ['doc_id', 'created_at', 'updated_at']:
                system_keys.add(key)
    
    print(f"Системные ключи: {sorted(system_keys)}")
    print()
    
    # Проверяем, кто создает документы с системными ключами
    print("🔍 Документы с системными ключами:")
    print()
    
    for user in users:
        has_system_keys = False
        system_key_values = {}
        
        for key, value in user.items():
            if key.startswith('_') or key in ['created_at', 'updated_at']:
                has_system_keys = True
                system_key_values[key] = value
        
        if has_system_keys:
            print(f"📱 Sender ID: {user.get('sender_id', 'N/A')}")
            print(f"   Doc ID: {user.get('doc_id', 'N/A')}")
            print(f"   Name: {user.get('name', 'N/A')}")
            print(f"   Системные ключи: {system_key_values}")
            print()
    
    # Статистика по языкам
    print("🌍 Статистика по языкам:")
    print()
    
    language_stats = {}
    for user in users:
        lang = user.get('language', 'unknown')
        language_stats[lang] = language_stats.get(lang, 0) + 1
    
    for lang, count in sorted(language_stats.items()):
        print(f"   {lang}: {count}")
    
    print()
    
    # Статистика по статусам
    print("📊 Статистика по статусам:")
    print()
    
    status_stats = {}
    for user in users:
        status = user.get('status', 'unknown')
        status_stats[status] = status_stats.get(status, 0) + 1
    
    for status, count in sorted(status_stats.items()):
        print(f"   {status}: {count}")
    
    print()
    print("=" * 60)
    print("✅ Анализ завершен")

if __name__ == "__main__":
    asyncio.run(analyze_users_collection()) 
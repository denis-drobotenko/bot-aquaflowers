#!/usr/bin/env python3
"""
Тест для просмотра всех коллекций в Firestore
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_list_collections():
    print("🔍 Просмотр всех коллекций в Firestore...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем все коллекции верхнего уровня
        collections = db.collections()
        
        print("📋 Коллекции верхнего уровня:")
        for collection in collections:
            print(f"   📁 {collection.id}")
            
            # Показываем первые несколько документов в каждой коллекции
            docs = list(collection.limit(3).stream())
            print(f"      Документов: {len(docs)}")
            
            for doc in docs:
                print(f"      📄 {doc.id}")
                
                # Если это коллекция orders, проверяем подколлекции
                if collection.id == 'orders':
                    subcollections = doc.reference.collections()
                    for subcollection in subcollections:
                        print(f"         📂 Подколлекция: {subcollection.id}")
                        subdocs = list(subcollection.limit(2).stream())
                        print(f"            Документов: {len(subdocs)}")
                        for subdoc in subdocs:
                            print(f"            📄 {subdoc.id}")
            
            print()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_collections()) 
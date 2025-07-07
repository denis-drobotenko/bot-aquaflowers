#!/usr/bin/env python3
"""
Проверка проекта Firestore
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_firestore_project():
    print("🔍 Проверка проекта Firestore...")
    
    try:
        # Инициализируем Firestore
        db = firestore.Client()
        
        # Получаем информацию о проекте
        project_id = db.project
        print(f"📋 Проект: {project_id}")
        
        # Проверяем переменные окружения
        print(f"📋 GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Не установлено')}")
        print(f"📋 GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Не установлено')}")
        
        # Проверяем все коллекции
        collections = list(db.collections())
        print(f"📋 Коллекций в проекте: {len(collections)}")
        
        for collection in collections:
            docs = list(collection.limit(1).stream())
            print(f"   📁 {collection.id}: {len(docs)} документов")
        
        # Проверяем, есть ли заказы в других коллекциях
        print(f"\n🔍 Проверяем все коллекции на наличие заказов...")
        
        for collection in collections:
            if 'order' in collection.id.lower():
                print(f"   🔍 Проверяем коллекцию: {collection.id}")
                docs = list(collection.stream())
                print(f"      Документов: {len(docs)}")
                
                for doc in docs:
                    data = doc.to_dict()
                    print(f"      📄 {doc.id}: {data}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_firestore_project()) 
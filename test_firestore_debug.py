#!/usr/bin/env python3
"""
Тест настроек Firestore
"""

import os
import sys
from google.cloud import firestore

def debug_firestore_settings():
    print("🔍 Проверка настроек Firestore...")
    
    # 1. Проверяем переменные окружения
    print("\n1. Переменные окружения:")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'НЕ УСТАНОВЛЕНА')}")
    print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'НЕ УСТАНОВЛЕН')}")
    
    # 2. Создаем клиент и проверяем project_id
    try:
        client = firestore.Client()
        print(f"\n2. Firestore клиент:")
        print(f"   Project ID: {client.project}")
        print(f"   Database: {client._database}")
        
        # 3. Проверяем доступ к коллекции orders
        print(f"\n3. Проверка доступа к коллекции orders:")
        orders_ref = client.collection('orders')
        
        # Пробуем получить документы
        docs = list(orders_ref.limit(1).stream())
        print(f"   Документов в orders (limit 1): {len(docs)}")
        
        if docs:
            doc = docs[0]
            print(f"   Первый документ ID: {doc.id}")
            print(f"   Данные: {list(doc.to_dict().keys())}")
        else:
            print("   ⚠️ Документов не найдено")
        
        # 4. Проверяем конкретный путь
        print(f"\n4. Проверка конкретного пути:")
        specific_doc = client.collection('orders').document('79140775712').collection('sessions').document('20250706_162943_50861_139')
        doc_snapshot = specific_doc.get()
        
        if doc_snapshot.exists:
            print(f"   ✅ Конкретный документ найден: {doc_snapshot.id}")
            data = doc_snapshot.to_dict()
            print(f"   📄 Поля: {list(data.keys())}")
        else:
            print("   ❌ Конкретный документ не найден")
        
        # 5. Проверяем родительский документ
        print(f"\n5. Проверка родительского документа:")
        parent_doc = client.collection('orders').document('79140775712')
        parent_snapshot = parent_doc.get()
        
        if parent_snapshot.exists:
            print(f"   ✅ Родительский документ найден: {parent_snapshot.id}")
        else:
            print("   ❌ Родительский документ не найден")
            
        # 6. Проверяем подколлекции
        print(f"\n6. Проверка подколлекций:")
        subcollections = list(parent_doc.collections())
        print(f"   Подколлекций: {len(subcollections)}")
        
        for subcol in subcollections:
            print(f"     📁 Подколлекция: {subcol.id}")
            subcol_docs = list(subcol.limit(5).stream())
            print(f"       Документов: {len(subcol_docs)}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_firestore_settings() 
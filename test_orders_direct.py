#!/usr/bin/env python3
"""
Прямая проверка коллекции orders
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from google.cloud import firestore

async def test_orders_direct():
    print("🔍 Прямая проверка коллекции orders...")
    
    # Инициализируем Firestore
    db = firestore.Client()
    
    try:
        # Получаем все документы из коллекции orders
        orders_ref = db.collection('orders')
        orders = list(orders_ref.stream())
        
        print(f"📋 Найдено документов в orders: {len(orders)}")
        
        if orders:
            for order_doc in orders:
                order_data = order_doc.to_dict()
                print(f"\n📄 Документ: {order_doc.id}")
                print(f"   Данные: {order_data}")
                
                # Проверяем подколлекции
                subcollections = order_doc.reference.collections()
                for subcollection in subcollections:
                    print(f"   📂 Подколлекция: {subcollection.id}")
                    subdocs = list(subcollection.stream())
                    print(f"      Документов: {len(subdocs)}")
                    
                    for subdoc in subdocs:
                        subdata = subdoc.to_dict()
                        print(f"      📄 {subdoc.id}: {subdata}")
        else:
            print("⚠️ В коллекции orders нет документов")
            
            # Проверяем, может быть есть подколлекции у корневого документа
            print("\n🔍 Проверяем подколлекции корневого документа...")
            root_ref = db.collection('orders').document('root')
            root_doc = root_ref.get()
            
            if root_doc.exists:
                print("   ✅ Корневой документ существует")
                subcollections = root_ref.collections()
                for subcollection in subcollections:
                    print(f"   📂 Подколлекция: {subcollection.id}")
            else:
                print("   ❌ Корневой документ не существует")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_orders_direct()) 
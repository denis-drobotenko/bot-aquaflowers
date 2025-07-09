#!/usr/bin/env python3
"""
Отладочный скрипт для проверки подключения к Firestore
"""
import os
from google.cloud import firestore

def debug_firestore():
    print("🔍 Отладка подключения к Firestore")
    
    # Проверяем переменные окружения
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
    print(f"GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    
    try:
        # Создаем клиент
        print("📡 Создаем Firestore клиент...")
        db = firestore.Client()
        print("✅ Firestore клиент создан успешно")
        
        # Проверяем заказы через collection_group (как в CRM)
        print("\n📦 Проверяем заказы через collection_group('sessions')...")
        order_sessions = db.collection_group('sessions').stream()
        order_sess_list = list(order_sessions)
        print(f"📊 Найдено сессий заказов: {len(order_sess_list)}")
        
        if order_sess_list:
            print("📋 Первые 3 заказа:")
            for i, session_doc in enumerate(order_sess_list[:3]):
                data = session_doc.to_dict()
                print(f"  {i+1}. {session_doc.reference.path}: {data}")
        
        # Проверяем сообщения через collection_group
        print("\n💬 Проверяем сообщения через collection_group('messages')...")
        messages = db.collection_group('messages').stream()
        msg_list = list(messages)
        print(f"📊 Найдено сообщений: {len(msg_list)}")
        
        if msg_list:
            print("💬 Первые 5 сообщений:")
            for i, msg_doc in enumerate(msg_list[:5]):
                msg_data = msg_doc.to_dict()
                role = msg_data.get('role', 'unknown')
                content = msg_data.get('content', '')[:50]
                image_url = msg_data.get('image_url')
                print(f"  {i+1}. [{role}] {content}...")
                if image_url:
                    print(f"      🖼️  image_url: {image_url}")
                print(f"      📍 Путь: {msg_doc.reference.path}")
        else:
            print("❌ Сообщения не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка подключения к Firestore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_firestore() 
#!/usr/bin/env python3
"""
Скрипт для вывода примеров сообщений из Firestore (расширенный)
"""
from google.cloud import firestore

if __name__ == "__main__":
    db = firestore.Client()
    conversations = db.collection('conversations').limit(5).stream()
    for conv in conversations:
        sender_id = conv.id
        print(f"\n=== Диалоги пользователя: {sender_id} ===")
        sessions = db.collection('conversations').document(sender_id).collection('sessions').limit(5).stream()
        for sess in sessions:
            session_id = sess.id
            print(f"  --- Сессия: {session_id} ---")
            messages = db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages').order_by('timestamp').limit(20).stream()
            for msg in messages:
                msg_data = msg.to_dict()
                print(f"    [{msg_data.get('role')}] id={msg.id}")
                print(f"      content: {msg_data.get('content')}")
                if msg_data.get('image_url'):
                    print(f"      image_url: {msg_data.get('image_url')}") 
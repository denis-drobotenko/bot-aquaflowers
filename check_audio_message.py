#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, firestore
import json

def check_audio_message():
    """Проверяет данные аудиосообщения в базе"""
    try:
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("src/aquaf.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Проверяем сообщение с аудио
        session_id = "test_audio_session_20250708"
        sender_id = "79037286228"
        
        # Получаем все сообщения
        messages_ref = db.collection('users').document(sender_id).collection('sessions').document(session_id).collection('messages')
        messages = messages_ref.stream()
        
        print(f"🔍 Проверяем сообщения для {sender_id}/{session_id}")
        print("=" * 50)
        
        for message in messages:
            message_data = message.to_dict()
            print(f"📝 Сообщение ID: {message.id}")
            print(f"   Роль: {message_data.get('role')}")
            print(f"   Контент: {message_data.get('content', '')[:100]}...")
            print(f"   Тип: {message_data.get('type')}")
            print(f"   Audio URL: {message_data.get('audio_url')}")
            print(f"   Audio Duration: {message_data.get('audio_duration')}")
            print(f"   Transcription: {message_data.get('transcription')}")
            print("-" * 30)
        
    except Exception as e:
        print(f"Ошибка при проверке: {e}")

if __name__ == "__main__":
    check_audio_message() 
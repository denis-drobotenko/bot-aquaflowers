#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import json

def create_test_audio_history():
    """Создает тестовую историю с аудиосообщением в правильной структуре"""
    try:
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("src/aquaf.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Тестовые данные
        sender_id = "79037286228"
        session_id = "test_audio_session_20250708"
        
        # URL аудиофайла с речью
        audio_url = "https://storage.googleapis.com/aquaflowers-bot-audio/voice_message_real_speech.wav"
        
        # Создаем сообщения
        messages = [
            {
                "role": "user",
                "content": "Привет! Хочу заказать букет",
                "content_en": "Hello! I want to order a bouquet",
                "content_thai": "สวัสดี! ฉันต้องการสั่งช่อดอกไม้",
                "timestamp": datetime.now(timezone.utc),
                "wa_message_id": "test_wa_msg_1"
            },
            {
                "role": "assistant",
                "content": "Здравствуйте! Конечно, я помогу вам выбрать букет. Вот наш каталог:",
                "content_en": "Hello! Of course, I'll help you choose a bouquet. Here's our catalog:",
                "content_thai": "สวัสดี! แน่นอน ฉันจะช่วยคุณเลือกช่อดอกไม้ นี่คือแคตตาล็อกของเรา:",
                "timestamp": datetime.now(timezone.utc),
                "wa_message_id": "test_wa_msg_2"
            },
            {
                "role": "user",
                "content": "[AUDIO] Привет! Это тестовое аудиосообщение",
                "content_en": "[AUDIO] Hello! This is a test audio message",
                "content_thai": "[AUDIO] สวัสดี! นี่คือข้อความเสียงทดสอบ",
                "timestamp": datetime.now(timezone.utc),
                "wa_message_id": "test_wa_msg_3",
                "audio_url": audio_url,
                "audio_duration": "1.1",
                "transcription": "rant"
            },
            {
                "role": "assistant",
                "content": "Понял ваше аудиосообщение! Вы сказали: 'rant'. Какой букет вас интересует?",
                "content_en": "I understood your audio message! You said: 'rant'. What bouquet interests you?",
                "content_thai": "ฉันเข้าใจข้อความเสียงของคุณ! คุณพูดว่า: 'rant' ช่อดอกไม้ไหนที่คุณสนใจ?",
                "timestamp": datetime.now(timezone.utc),
                "wa_message_id": "test_wa_msg_4"
            },
            {
                "role": "user",
                "content": "Спасибо! Хочу букет роз",
                "content_en": "Thank you! I want a rose bouquet",
                "content_thai": "ขอบคุณ! ฉันต้องการช่อดอกกุหลาบ",
                "timestamp": datetime.now(timezone.utc),
                "wa_message_id": "test_wa_msg_5"
            }
        ]
        
        # Создаем сессию в правильной структуре (conversations)
        session_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
        session_ref.set({
            'session_id': session_id,
            'sender_id': sender_id,
            'created_at': datetime.now(timezone.utc),
            'status': 'active'
        })
        
        # Добавляем сообщения
        messages_ref = session_ref.collection('messages')
        
        for i, msg_data in enumerate(messages):
            message_id = f"test_msg_{i+1}"
            messages_ref.document(message_id).set(msg_data)
            print(f"✅ Добавлено сообщение {i+1}: {msg_data['role']}")
        
        print(f"🎉 Тестовая история создана в правильной структуре!")
        print(f"📱 Sender ID: {sender_id}")
        print(f"💬 Session ID: {session_id}")
        print(f"🎵 Audio URL: {audio_url}")
        print(f"🔗 Ссылка: http://localhost:8080/chat/history/{sender_id}/{session_id}")
        
    except Exception as e:
        print(f"Ошибка при создании: {e}")

if __name__ == "__main__":
    create_test_audio_history() 
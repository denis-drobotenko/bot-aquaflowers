#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import json

def update_test_audio_history():
    """Обновляет тестовую историю с новым аудиофайлом с речью"""
    try:
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("src/aquaf.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Новый URL аудиофайла с речью
        audio_url = "https://storage.googleapis.com/aquaflowers-bot-audio/voice_message_real_speech.wav"
        
        # Обновляем сообщение с аудио
        session_id = "test_audio_session_20250708"
        sender_id = "79037286228"
        
        # Находим сообщение с аудио и обновляем его
        messages_ref = db.collection('users').document(sender_id).collection('sessions').document(session_id).collection('messages')
        
        # Получаем все сообщения
        messages = messages_ref.stream()
        
        for message in messages:
            message_data = message.to_dict()
            if message_data.get('type') == 'audio':
                print(f"Обновляем сообщение {message.id} с аудио")
                
                # Обновляем поля аудио
                message_data.update({
                    'audio_url': audio_url,
                    'audio_duration': 1.1,  # Примерная длительность
                    'transcription': 'rant',
                    'updated_at': datetime.now(timezone.utc)
                })
                
                # Сохраняем обновленное сообщение
                messages_ref.document(message.id).set(message_data)
                print(f"Сообщение обновлено с новым URL: {audio_url}")
                break
        
        print("Тестовая история обновлена!")
        
    except Exception as e:
        print(f"Ошибка при обновлении: {e}")

if __name__ == "__main__":
    update_test_audio_history() 
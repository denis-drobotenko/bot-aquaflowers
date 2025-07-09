#!/usr/bin/env python3
import json
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

def log_webhook_structure():
    """Логирует структуру входящих webhook'ов для отладки"""
    try:
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("src/aquaf.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Создаем коллекцию для логирования webhook'ов
        webhook_logs_ref = db.collection('debug_webhook_logs')
        
        # Пример структуры webhook'а от WhatsApp для аудио
        sample_audio_webhook = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123456789",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "display_phone_number": "1234567890",
                                    "phone_number_id": "123456789"
                                },
                                "contacts": [
                                    {
                                        "profile": {
                                            "name": "Test User"
                                        },
                                        "wa_id": "79140775712"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "79140775712",
                                        "id": "wamid.test123",
                                        "timestamp": "1234567890",
                                        "type": "audio",
                                        "audio": {
                                            "id": "audio_id_123",
                                            "mime_type": "audio/ogg; codecs=opus",
                                            "sha256": "audio_sha256",
                                            "filename": "audio.ogg",
                                            "url": "https://example.com/audio.ogg"
                                        }
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        
        # Логируем пример структуры
        webhook_logs_ref.document('sample_audio_webhook').set({
            'timestamp': datetime.now(timezone.utc),
            'webhook_data': sample_audio_webhook,
            'description': 'Пример структуры webhook\'а для аудиосообщения'
        })
        
        print("✅ Пример структуры webhook'а записан в базу")
        print("📋 Структура аудиосообщения:")
        print(json.dumps(sample_audio_webhook, indent=2))
        
        # Проверяем функцию извлечения
        from src.handlers.webhook_extractors import extract_audio_url, extract_audio_duration
        
        audio_url = extract_audio_url(sample_audio_webhook)
        audio_duration = extract_audio_duration(sample_audio_webhook)
        
        print(f"\n🔍 Тест извлечения:")
        print(f"   Audio URL: {audio_url}")
        print(f"   Audio Duration: {audio_duration}")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    log_webhook_structure() 
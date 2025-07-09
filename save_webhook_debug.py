#!/usr/bin/env python3
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import json

def save_webhook_debug():
    """Сохраняет пример webhook'а для отладки"""
    try:
        # Инициализация Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("src/aquaf.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Создаем коллекцию для отладки webhook'ов
        debug_ref = db.collection('debug_webhooks')
        
        # Пример реального webhook'а от WhatsApp (на основе логов)
        real_webhook = {
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
                                            "name": "Denis"
                                        },
                                        "wa_id": "79140775712"
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "79140775712",
                                        "id": "wamid.HBgLNzkxNDA3NzU3MTIVAgASGBQzQUNBMjZGRDA1RUQyNDY0MDIzNAA=",
                                        "timestamp": "1752045728",
                                        "type": "audio",
                                        "audio": {
                                            "id": "audio_id_123",
                                            "mime_type": "audio/ogg; codecs=opus",
                                            "sha256": "audio_sha256",
                                            "filename": "audio.ogg"
                                            # Обратите внимание: здесь НЕТ поля "url"!
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
        
        # Сохраняем в базу
        debug_ref.document('audio_webhook_no_url').set({
            'timestamp': datetime.now(timezone.utc),
            'webhook_data': real_webhook,
            'description': 'Webhook от WhatsApp без поля url в audio',
            'problem': 'WhatsApp не отправляет URL аудиофайла в webhook\'е'
        })
        
        print("✅ Webhook сохранен в базу для отладки")
        print("🔍 Проблема: WhatsApp не отправляет URL аудиофайла в webhook'е!")
        print("📋 Структура audio объекта:")
        print(json.dumps(real_webhook['entry'][0]['changes'][0]['value']['messages'][0]['audio'], indent=2))
        
        # Тестируем извлечение
        from src.handlers.webhook_extractors import extract_audio_url, extract_audio_duration
        
        audio_url = extract_audio_url(real_webhook)
        audio_duration = extract_audio_duration(real_webhook)
        
        print(f"\n🔍 Результат извлечения:")
        print(f"   Audio URL: {audio_url}")
        print(f"   Audio Duration: {audio_duration}")
        
        if not audio_url:
            print("❌ URL не найден - нужно использовать WhatsApp Media API!")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    save_webhook_debug() 
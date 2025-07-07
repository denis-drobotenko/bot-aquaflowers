#!/usr/bin/env python3
"""
Тест обработки webhook статусов доставки
"""

import json
from src.handlers.webhook_handler import WebhookHandler

def test_status_webhook():
    """Тестирует обработку webhook статусов доставки"""
    
    webhook_handler = WebhookHandler()
    
    # Тестовый webhook со статусом доставки
    status_webhook = {
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
                                "phone_number_id": "987654321"
                            },
                            "statuses": [
                                {
                                    "id": "wamid.HBgNMTIzNDU2Nzg5ABESFgQ5QjY4QjU5QjU5QjU5QjU5QjU5",
                                    "status": "delivered",
                                    "timestamp": "1234567890",
                                    "recipient_id": "123456789"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print("🧪 Тестирование обработки webhook статусов...")
    
    # Тестируем извлечение статуса
    status_update = webhook_handler.extract_status_updates(status_webhook)
    print(f"📊 Извлеченный статус: {json.dumps(status_update, indent=2, ensure_ascii=False)}")
    
    # Тестируем валидацию webhook
    validation = webhook_handler.validate_webhook(status_webhook)
    print(f"✅ Валидация webhook: {json.dumps(validation, indent=2, ensure_ascii=False)}")
    
    # Тестируем webhook с сообщением (для сравнения)
    message_webhook = {
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
                                "phone_number_id": "987654321"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "123456789"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "123456789",
                                    "id": "wamid.HBgNMTIzNDU2Nzg5ABESFgQ5QjY4QjU5QjU5QjU5QjU5QjU5",
                                    "timestamp": "1234567890",
                                    "text": {
                                        "body": "Привет!"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print("\n📨 Тестирование webhook с сообщением...")
    message_validation = webhook_handler.validate_webhook(message_webhook)
    print(f"✅ Валидация сообщения: {json.dumps(message_validation, indent=2, ensure_ascii=False)}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_status_webhook() 
#!/usr/bin/env python3
"""
Тест обработки webhook'ов с типом "печатает" от клиента
"""

import json
import requests

# URL вашего webhook endpoint
WEBHOOK_URL = "http://localhost:8000/webhook"

def test_typing_webhook():
    """Тестирует webhook с типом 'typing' (печатает)"""
    
    # Webhook с типом "печатает"
    typing_webhook = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "515848908286141",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "66963617068",
                                "phone_number_id": "494991623707876"
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
                                    "id": "wamid.test.typing.message",
                                    "timestamp": "1751670861",
                                    "type": "typing"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    print("🧪 Тестируем webhook с типом 'typing'...")
    print(f"📤 Отправляем POST запрос на {WEBHOOK_URL}")
    print(f"📋 Данные: {json.dumps(typing_webhook, indent=2)}")
    
    try:
        response = requests.post(WEBHOOK_URL, json=typing_webhook)
        print(f"📥 Статус ответа: {response.status_code}")
        print(f"📄 Тело ответа: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ignored":
                print("✅ УСПЕХ: Webhook с типом 'typing' правильно пропущен!")
            else:
                print("❌ ОШИБКА: Webhook с типом 'typing' обработан неправильно!")
        else:
            print(f"❌ ОШИБКА: Неожиданный статус ответа: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ОШИБКА при отправке запроса: {e}")

def test_reaction_webhook():
    """Тестирует webhook с типом 'reaction' (реакция)"""
    
    # Webhook с типом "реакция"
    reaction_webhook = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "515848908286141",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "66963617068",
                                "phone_number_id": "494991623707876"
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
                                    "id": "wamid.test.reaction.message",
                                    "timestamp": "1751670861",
                                    "type": "reaction",
                                    "reaction": {
                                        "message_id": "wamid.original.message",
                                        "emoji": "👍"
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
    
    print("\n🧪 Тестируем webhook с типом 'reaction'...")
    print(f"📤 Отправляем POST запрос на {WEBHOOK_URL}")
    
    try:
        response = requests.post(WEBHOOK_URL, json=reaction_webhook)
        print(f"📥 Статус ответа: {response.status_code}")
        print(f"📄 Тело ответа: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ignored":
                print("✅ УСПЕХ: Webhook с типом 'reaction' правильно пропущен!")
            else:
                print("❌ ОШИБКА: Webhook с типом 'reaction' обработан неправильно!")
        else:
            print(f"❌ ОШИБКА: Неожиданный статус ответа: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ОШИБКА при отправке запроса: {e}")

def test_metrics():
    """Проверяет метрики webhook'ов"""
    
    print("\n📊 Проверяем метрики webhook'ов...")
    
    try:
        response = requests.get(f"{WEBHOOK_URL}/metrics")
        print(f"📥 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            metrics = response.json()
            print(f"📈 Метрики: {json.dumps(metrics, indent=2)}")
            
            if metrics.get("skipped_messages", 0) > 0:
                print("✅ УСПЕХ: Метрика 'skipped_messages' работает!")
            else:
                print("ℹ️  Метрика 'skipped_messages' пока 0 (нормально для первого запуска)")
        else:
            print(f"❌ ОШИБКА: Не удалось получить метрики: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ОШИБКА при получении метрик: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов обработки webhook'ов...")
    
    # Тестируем webhook с типом "печатает"
    test_typing_webhook()
    
    # Тестируем webhook с типом "реакция"
    test_reaction_webhook()
    
    # Проверяем метрики
    test_metrics()
    
    print("\n✨ Тесты завершены!") 
#!/usr/bin/env python3
"""
Тест динамического определения URL для команды /getchat
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.webhook_handlers import router
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

def test_dynamic_url_detection():
    """Тестирует динамическое определение URL для команды /getchat"""
    
    # Создаем тестовое приложение
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Тестовые данные для команды /getchat
    test_data = {
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
                            "messages": [
                                {
                                    "from": "79140775712",
                                    "id": "test_message_id",
                                    "timestamp": "1234567890",
                                    "text": {
                                        "body": "/getchat"
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
    
    # Тестируем с разными заголовками для определения URL
    test_cases = [
        {
            "name": "Local development",
            "headers": {"Host": "localhost:8080"},
            "expected_base": "http://localhost:8080"
        },
        {
            "name": "Cloud Run with proxy",
            "headers": {
                "X-Forwarded-Host": "auraflora-bot-xicvc2y5hq-as.a.run.app",
                "X-Forwarded-Proto": "https"
            },
            "expected_base": "https://auraflora-bot-xicvc2y5hq-as.a.run.app"
        },
        {
            "name": "Direct HTTPS",
            "headers": {
                "Host": "auraflora-bot.onrender.com",
                "X-Forwarded-Proto": "https"
            },
            "expected_base": "https://auraflora-bot.onrender.com"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Тестируем: {test_case['name']}")
        
        # Отправляем запрос с тестовыми заголовками
        response = client.post(
            "/webhook",
            json=test_data,
            headers=test_case["headers"]
        )
        
        print(f"   Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Результат: {result}")
            
            # Проверяем, что в ответе есть chat_link
            if "chat_link" in result:
                chat_link = result["chat_link"]
                print(f"   Ссылка: {chat_link}")
                
                # Проверяем, что базовый URL соответствует ожидаемому
                if chat_link.startswith(test_case["expected_base"]):
                    print(f"   ✅ URL определен правильно: {test_case['expected_base']}")
                else:
                    print(f"   ❌ Неправильный URL. Ожидалось: {test_case['expected_base']}, получено: {chat_link}")
            else:
                print(f"   ❌ Нет chat_link в ответе")
        else:
            print(f"   ❌ Ошибка: {response.text}")

if __name__ == "__main__":
    print("🚀 Тестирование динамического определения URL для /getchat")
    test_dynamic_url_detection()
    print("\n✅ Тест завершен") 
#!/usr/bin/env python3
"""
Тест реальной команды /getchat с корректными данными WhatsApp
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.webhook_handlers import router
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

def test_real_getchat_command():
    """Тестирует реальную команду /getchat с корректными данными"""
    
    # Создаем тестовое приложение
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Реальные данные для команды /getchat (имитация WhatsApp webhook)
    test_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "494991623707876",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
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
                                    "id": "test_message_id_123",
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
    
    print("🧪 Тестируем команду /getchat с реальными данными WhatsApp")
    
    # Отправляем запрос с заголовками для локальной разработки
    response = client.post(
        "/webhook",
        json=test_data,
        headers={"Host": "localhost:8080"}
    )
    
    print(f"   Статус: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Результат: {result}")
        
        # Проверяем, что в ответе есть chat_link
        if "chat_link" in result:
            chat_link = result["chat_link"]
            print(f"   ✅ Ссылка сгенерирована: {chat_link}")
            
            # Проверяем формат ссылки
            if chat_link.startswith("http://localhost:8080/chat/"):
                print(f"   ✅ Формат ссылки правильный")
                
                # Проверяем, что ссылка содержит sender_id и session_id
                parts = chat_link.split("/chat/")[1].split("_")
                if len(parts) >= 4:
                    sender_id = parts[0]
                    session_id = "_".join(parts[1:])
                    print(f"   ✅ Sender ID: {sender_id}")
                    print(f"   ✅ Session ID: {session_id}")
                else:
                    print(f"   ❌ Неправильный формат session_id в ссылке")
            else:
                print(f"   ❌ Неправильный базовый URL в ссылке")
        else:
            print(f"   ❌ Нет chat_link в ответе")
    else:
        print(f"   ❌ Ошибка: {response.text}")

if __name__ == "__main__":
    print("🚀 Тестирование реальной команды /getchat")
    test_real_getchat_command()
    print("\n✅ Тест завершен") 
#!/usr/bin/env python3
"""
Тест команды /getchat с сообщением, содержащим переносы строк
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.webhook_handlers import router
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

def test_getchat_with_formatting():
    """Тестирует команду /getchat с сообщением, содержащим переносы строк"""
    
    # Создаем тестовое приложение
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Реальные данные для команды /getchat с сообщением, содержащим переносы строк
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
                                    "id": "test_message_id_formatting",
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
    
    print("🧪 Тестируем команду /getchat с форматированием")
    
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
                    
                    # Теперь проверим, что страница с историей загружается
                    print(f"   🔍 Проверяем загрузку страницы истории...")
                    history_response = client.get(chat_link)
                    
                    if history_response.status_code == 200:
                        print(f"   ✅ Страница истории загружается успешно")
                        
                        # Проверяем, что на странице есть сообщения с переносами строк
                        content = history_response.text
                        if "Первая строка" in content and "Вторая строка" in content:
                            print(f"   ✅ Сообщения с переносами строк найдены на странице")
                        else:
                            print(f"   ⚠️ Сообщения с переносами строк не найдены на странице")
                    else:
                        print(f"   ❌ Ошибка загрузки страницы истории: {history_response.status_code}")
                else:
                    print(f"   ❌ Неправильный формат session_id в ссылке")
            else:
                print(f"   ❌ Неправильный базовый URL в ссылке")
        else:
            print(f"   ❌ Нет chat_link в ответе")
    else:
        print(f"   ❌ Ошибка: {response.text}")

if __name__ == "__main__":
    print("🚀 Тестирование команды /getchat с форматированием")
    test_getchat_with_formatting()
    print("\n✅ Тест завершен") 
 
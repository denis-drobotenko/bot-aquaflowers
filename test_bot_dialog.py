#!/usr/bin/env python3
"""
Тестовый скрипт для симуляции диалога с ботом
"""

import asyncio
import sys
import os
import json
import httpx

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def simulate_user_message(message_text: str, sender_id: str = "79140775712", sender_name: str = "Denis"):
    """Симулирует отправку сообщения от пользователя боту"""
    
    # Данные webhook'а, которые отправляет WhatsApp
    webhook_data = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "742818811434193",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "494991623707876",
                        "phone_number_id": "494991623707876"
                    },
                    "contacts": [{
                        "profile": {
                            "name": sender_name
                        },
                        "wa_id": sender_id
                    }],
                    "messages": [{
                        "from": sender_id,
                        "id": f"wamid.test.{asyncio.get_event_loop().time()}",
                        "timestamp": str(int(asyncio.get_event_loop().time())),
                        "text": {
                            "body": message_text
                        },
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    # Отправляем webhook на локальный сервер
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8080/webhook",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Сообщение '{message_text}' отправлено успешно")
                return True
            else:
                print(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка соединения: {e}")
            return False

async def test_bot_dialog():
    """Тестирует полный диалог с ботом"""
    
    print("🤖 Тестируем диалог с AuraFlora Bot")
    print("=" * 50)
    
    # Тестовые сценарии
    test_scenarios = [
        {
            "name": "Приветствие",
            "message": "Привет!",
            "expected": "Бот должен поздороваться и предложить каталог"
        },
        {
            "name": "Согласие на каталог",
            "message": "Да, покажите",
            "expected": "Бот должен отправить каталог с фото"
        },
        {
            "name": "Выбор букета",
            "message": "Хочу букет Love is on the air",
            "expected": "Бот должен сохранить выбор и спросить про доставку"
        },
        {
            "name": "Новая сессия",
            "message": "/newses",
            "expected": "Бот должен создать новую сессию"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Тест {i}: {scenario['name']}")
        print(f"💬 Сообщение: '{scenario['message']}'")
        print(f"🎯 Ожидаем: {scenario['expected']}")
        
        # Отправляем сообщение
        success = await simulate_user_message(scenario['message'])
        
        if success:
            print("⏳ Ждем ответа бота...")
            # Ждем немного, чтобы бот обработал сообщение
            await asyncio.sleep(3)
        else:
            print("❌ Не удалось отправить сообщение")
        
        print("-" * 30)

async def test_simple_greeting():
    """Простой тест приветствия"""
    print("👋 Тестируем простое приветствие...")
    
    success = await simulate_user_message("Привет!")
    
    if success:
        print("✅ Приветствие отправлено, проверьте WhatsApp")
        print("💡 Бот должен ответить приветствием и предложить каталог")
    else:
        print("❌ Ошибка отправки приветствия")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тестирование диалога с ботом")
    parser.add_argument("--simple", action="store_true", help="Простой тест приветствия")
    parser.add_argument("--full", action="store_true", help="Полный тест диалога")
    
    args = parser.parse_args()
    
    if args.simple:
        asyncio.run(test_simple_greeting())
    elif args.full:
        asyncio.run(test_bot_dialog())
    else:
        # По умолчанию простой тест
        asyncio.run(test_simple_greeting()) 
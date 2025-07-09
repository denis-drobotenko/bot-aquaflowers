#!/usr/bin/env python3
"""
Локальный тест AI сервиса
"""

import asyncio
import os
import sys
from datetime import datetime
import pytz

# Добавляем путь к src
sys.path.append('src')

from src.services.ai_service import AIService
from src.models.message import Message, MessageRole

async def test_ai_service():
    """Тестирует AI сервис с реальными запросами"""
    
    # Получаем API ключ из переменных окружения
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден в переменных окружения")
        return
    
    print("🔧 Инициализация AI сервиса...")
    ai_service = AIService(api_key)
    
    # Тестовые сообщения
    test_cases = [
        {
            "name": "Первое приветствие",
            "messages": [
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Привет",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="Hello",
                    content_thai="สวัสดี"
                )
            ],
            "user_lang": "ru",
            "sender_name": "Test User",
            "is_first_message": True
        },
        {
            "name": "Запрос каталога",
            "messages": [
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Добрый день, хочу заказать букет",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="Good day, I'd like to order a bouquet",
                    content_thai="สวัสดีครับ อยากจะสั่งช่อดอกไม้"
                ),
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Привет",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="Hello",
                    content_thai="สวัสดี"
                )
            ],
            "user_lang": "ru",
            "sender_name": "Test User",
            "is_first_message": False
        },
        {
            "name": "Выбор букета",
            "messages": [
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Мне нравится букет Pink peony 15",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="I like the Pink peony 15 bouquet",
                    content_thai="ฉันชอบช่อดอกไม้ Pink peony 15"
                ),
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Добрый день, хочу заказать букет",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="Good day, I'd like to order a bouquet",
                    content_thai="สวัสดีครับ อยากจะสั่งช่อดอกไม้"
                ),
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Привет",
                    timestamp=datetime.now(pytz.UTC),
                    content_en="Hello",
                    content_thai="สวัสดี"
                )
            ],
            "user_lang": "ru",
            "sender_name": "Test User",
            "is_first_message": False
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        try:
            print(f"📤 Отправка запроса к AI...")
            print(f"   Сообщений: {len(test_case['messages'])}")
            print(f"   Язык: {test_case['user_lang']}")
            print(f"   Имя: {test_case['sender_name']}")
            print(f"   Первое сообщение: {test_case['is_first_message']}")
            
            # Вызываем AI сервис
            start_time = datetime.now()
            result = await ai_service.generate_response(
                messages=test_case['messages'],
                user_lang=test_case['user_lang'],
                sender_name=test_case['sender_name'],
                is_first_message=test_case['is_first_message']
            )
            end_time = datetime.now()
            
            # Анализируем результат
            text, text_en, text_thai, command = result
            
            print(f"\n⏱️  Время выполнения: {(end_time - start_time).total_seconds():.2f} сек")
            print(f"\n📥 РЕЗУЛЬТАТ:")
            print(f"   text: '{text}'")
            print(f"   text_en: '{text_en}'")
            print(f"   text_thai: '{text_thai}'")
            print(f"   command: {command}")
            
            # Проверяем валидность
            if not text:
                print("❌ ОШИБКА: Пустой текст в ответе")
            elif command is None:
                print("⚠️  ПРЕДУПРЕЖДЕНИЕ: Команда отсутствует (может быть нормально)")
            else:
                print("✅ УСПЕХ: Получен валидный ответ с текстом и командой")
                
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск локального теста AI сервиса...")
    asyncio.run(test_ai_service())
    print("\n�� Тест завершен!") 
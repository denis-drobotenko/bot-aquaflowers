#!/usr/bin/env python3
"""
Тест для проверки JSON ответов AI
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_ai_json():
    """Тестирует JSON ответы AI"""
    print("=== ТЕСТ JSON ОТВЕТОВ AI ===")
    
    try:
        # Инициализация AI сервиса
        ai_service = AIService(GEMINI_API_KEY)
        
        # Тест 1: Простое приветствие
        print("1. Тестируем простое приветствие...")
        test_messages = [
            Message(
                sender_id="test",
                session_id="test",
                role=MessageRole.USER,
                content="Привет!"
            )
        ]
        
        ai_response = await ai_service.generate_response(test_messages, user_lang='ru')
        print(f"   ✅ Ответ AI получен: {len(ai_response)} символов")
        print(f"   📝 Полный ответ:")
        print(f"   {ai_response}")
        print()
        
        # Тест 2: Парсинг JSON
        print("2. Тестируем парсинг JSON...")
        ai_text, ai_text_en, ai_text_thai, ai_command = ai_service.parse_ai_response(ai_response)
        
        print(f"   ✅ Парсинг выполнен:")
        print(f"   📝 text: {ai_text}")
        print(f"   📝 text_en: {ai_text_en}")
        print(f"   📝 text_thai: {ai_text_thai}")
        print(f"   📝 command: {ai_command}")
        print()
        
        # Тест 3: Запрос каталога
        print("3. Тестируем запрос каталога...")
        test_messages = [
            Message(
                sender_id="test",
                session_id="test",
                role=MessageRole.USER,
                content="Покажите каталог цветов"
            )
        ]
        
        ai_response = await ai_service.generate_response(test_messages, user_lang='ru')
        print(f"   ✅ Ответ AI получен: {len(ai_response)} символов")
        print(f"   📝 Полный ответ:")
        print(f"   {ai_response}")
        print()
        
        # Тест 4: Парсинг команды
        print("4. Тестируем парсинг команды...")
        ai_text, ai_text_en, ai_text_thai, ai_command = ai_service.parse_ai_response(ai_response)
        
        print(f"   ✅ Парсинг выполнен:")
        print(f"   📝 text: {ai_text}")
        print(f"   📝 command: {ai_command}")
        print()
        
        print("✅ Все тесты прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_json())
    if not success:
        sys.exit(1) 
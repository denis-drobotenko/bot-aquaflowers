#!/usr/bin/env python3
"""
Тест AI сервиса
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_ai():
    """Тестирует AI сервис"""
    print("=== ТЕСТ AI СЕРВИСА ===")
    
    # Инициализируем AI сервис
    ai_service = AIService(GEMINI_API_KEY)
    print("✅ AI сервис инициализирован")
    
    # Создаем тестовое сообщение
    test_message = Message(
        sender_id="test_user",
        session_id="test_session",
        role=MessageRole.USER,
        content="Привет! Хочу посмотреть каталог цветов"
    )
    
    print("✅ Тестовое сообщение создано")
    
    try:
        # Генерируем ответ
        print("🔄 Генерируем ответ AI...")
        response = await ai_service.generate_response([test_message], user_lang='ru')
        
        print(f"✅ Ответ получен: {response[:100]}...")
        
        # Парсим ответ
        print("🔄 Парсим ответ...")
        text, text_en, text_thai, command = ai_service.parse_ai_response(response)
        
        print(f"✅ Парсинг успешен:")
        print(f"   Текст: {text[:50]}...")
        print(f"   Команда: {command}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ai()) 
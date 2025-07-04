#!/usr/bin/env python3
"""
Тест AI сервиса (Gemini)
"""

import sys
import os

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config import GEMINI_API_KEY

async def test_ai_service():
    """Тест AI сервиса (Gemini)"""
    print("=== ТЕСТ AI СЕРВИСА (GEMINI) ===")
    
    try:
        # Инициализация AI сервиса
        ai_service = AIService(GEMINI_API_KEY)
        
        # Тест 1: Простой ответ
        test_messages = [
            Message(
                sender_id="test_user",
                session_id="test_session",
                role=MessageRole.USER,
                content="Привет"
            )
        ]
        
        response = await ai_service.generate_response(test_messages)
        if response and len(response) > 10:
            print(f"✅ AI простой ответ - Получен ответ длиной {len(response)} символов")
        else:
            print("❌ AI простой ответ - Ответ слишком короткий или пустой")
            return False
            
        # Тест 2: Определение языка
        lang_ru = ai_service.detect_language("Привет, как дела?")
        lang_en = ai_service.detect_language("Hello, how are you?")
        
        if lang_ru == 'ru' and lang_en == 'en':
            print(f"✅ AI определение языка - RU: {lang_ru}, EN: {lang_en}")
        else:
            print(f"❌ AI определение языка - RU: {lang_ru}, EN: {lang_en}")
            return False
            
        print("✅ AI сервис прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ AI сервис - Ошибка: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_ai_service())
    if not success:
        sys.exit(1) 
#!/usr/bin/env python3
"""
Тест исправления перевода сообщений пользователя
"""

import asyncio
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.ai_service import AIService
from src.config.settings import GEMINI_API_KEY

async def test_translation_fix():
    """Тестирует исправление перевода сообщений пользователя"""
    print("🧪 Тестирование исправления перевода сообщений пользователя")
    print("=" * 70)
    
    ai_service = AIService(GEMINI_API_KEY)
    
    # Тестовые сообщения на разных языках
    test_cases = [
        ("Questo bouquet (reply to: Good vibes🌸 2 350,00 ฿ 🌸)", "it", "Italian message"),
        ("This bouquet (reply to: Good vibes🌸 2 350.00 ฿ 🌸)", "en", "English message"),
        ("Этот букет (ответ на: Good vibes🌸 2 350,00 ฿ 🌸)", "ru", "Russian message"),
        ("ช่อดอกไม้นี้ (ตอบกลับถึง: Good vibes🌸 2 350,00 ฿ 🌸)", "th", "Thai message"),
    ]
    
    for text, expected_lang, description in test_cases:
        print(f"\n📝 Тест: {description}")
        print(f"Текст: {text}")
        print(f"Ожидаемый язык: {expected_lang}")
        
        # Тестируем перевод
        content, content_en, content_thai = ai_service.translate_user_message(text, expected_lang)
        
        print(f"✅ Результат:")
        print(f"  content (оригинал): {content}")
        print(f"  content_en (англ.): {content_en}")
        print(f"  content_thai (тайск.): {content_thai}")
        
        # Проверяем, что оригинал сохранен правильно
        if content == text:
            print(f"✅ Оригинал сохранен правильно")
        else:
            print(f"❌ ОШИБКА: Оригинал не сохранен!")
            print(f"   Ожидалось: {text}")
            print(f"   Получено: {content}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_translation_fix()) 
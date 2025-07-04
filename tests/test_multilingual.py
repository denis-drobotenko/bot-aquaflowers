#!/usr/bin/env python3
"""
Тест многоязычной функциональности
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.ai_service import AIService
from src.config import GEMINI_API_KEY
from src.models.message import Message

def test_multilingual_response():
    """Тестирует генерацию ответа на трех языках"""
    print("=== ТЕСТ МНОГОЯЗЫЧНОСТИ ===")
    
    ai_service = AIService(GEMINI_API_KEY)
    
    # Тест 1: Русский язык
    print("\n1. Тест русского языка:")
    response = ai_service.generate_response_sync([], user_lang='ru')
    print(f"Ответ: {response[:100]}...")
    
    # Тест 2: Английский язык
    print("\n2. Тест английского языка:")
    response = ai_service.generate_response_sync([], user_lang='en')
    print(f"Ответ: {response[:100]}...")
    
    # Тест 3: Тайский язык
    print("\n3. Тест тайского языка:")
    response = ai_service.generate_response_sync([], user_lang='th')
    print(f"Ответ: {response[:100]}...")
    
    # Тест 4: Определение языка
    print("\n4. Тест определения языка:")
    russian_text = "Привет, как дела?"
    english_text = "Hello, how are you?"
    thai_text = "สวัสดี คุณเป็นอย่างไรบ้าง?"
    
    lang_ru = ai_service.detect_language(russian_text)
    lang_en = ai_service.detect_language(english_text)
    lang_th = ai_service.detect_language(thai_text)
    
    print(f"Русский текст: {lang_ru}")
    print(f"Английский текст: {lang_en}")
    print(f"Тайский текст: {lang_th}")
    
    # Тест 5: Перевод сообщения
    print("\n5. Тест перевода:")
    test_text = "Привет! Хочу посмотреть каталог цветов."
    text, text_en, text_thai = ai_service.translate_user_message(test_text, 'ru')
    
    print(f"Исходный: {text}")
    print(f"Английский: {text_en}")
    print(f"Тайский: {text_thai}")
    
    print("\n✅ Тест многоязычности завершен!")

if __name__ == "__main__":
    test_multilingual_response() 
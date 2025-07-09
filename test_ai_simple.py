#!/usr/bin/env python3
"""
Упрощенный тест AI сервиса с минимальным промптом
"""

import asyncio
import os
import sys
import google.generativeai as genai
from google.generativeai import GenerationConfig
from google.generativeai.types import HarmCategory, HarmBlockThreshold

async def test_simple_ai():
    """Тестирует AI с минимальным промптом"""
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY не найден")
        return
    
    print("🔧 Инициализация AI...")
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            max_output_tokens=8192
        ),
        safety_settings={
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    )
    
    # Минимальный промпт
    simple_prompt = """You are a flower shop assistant. Respond in JSON format:

{
  "text": "your response in Russian",
  "text_en": "your response in English", 
  "text_thai": "your response in Thai",
  "command": null
}

User says: "Привет"

Response:"""
    
    print("📤 Отправка простого запроса...")
    print(f"Промпт длиной: {len(simple_prompt)} символов")
    
    try:
        response = model.generate_content(simple_prompt)
        response_text = response.text.strip()
        
        print(f"\n📥 РЕЗУЛЬТАТ:")
        print(f"Длина ответа: {len(response_text)} символов")
        print(f"Ответ (repr): {repr(response_text)}")
        print(f"Ответ (display): {response_text}")
        
        # Пробуем парсить JSON
        import json
        try:
            # Ищем JSON в ответе
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                print(f"\n✅ JSON успешно распарсен:")
                print(f"   text: '{parsed.get('text', '')}'")
                print(f"   text_en: '{parsed.get('text_en', '')}'")
                print(f"   text_thai: '{parsed.get('text_thai', '')}'")
                print(f"   command: {parsed.get('command')}")
            else:
                print("❌ JSON не найден в ответе")
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print(f"JSON строка: {json_str}")
            
    except Exception as e:
        print(f"❌ Ошибка AI: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Запуск упрощенного теста AI...")
    asyncio.run(test_simple_ai())
    print("\n�� Тест завершен!") 
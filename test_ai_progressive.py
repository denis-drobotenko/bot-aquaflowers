#!/usr/bin/env python3
"""
Тест с постепенным увеличением сложности промпта
"""

import asyncio
import os
import sys
import google.generativeai as genai
from google.generativeai import GenerationConfig
from google.generativeai.types import HarmCategory, HarmBlockThreshold

async def test_progressive_ai():
    """Тестирует AI с постепенным увеличением сложности промпта"""
    
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
    
    # Тестовые промпты с увеличением сложности
    test_prompts = [
        {
            "name": "Базовый JSON",
            "prompt": """Respond in JSON format:
{
  "text": "Hello in Russian",
  "text_en": "Hello in English", 
  "text_thai": "Hello in Thai",
  "command": null
}

User: "Привет"
Response:"""
        },
        {
            "name": "С каталогом товаров",
            "prompt": """You are a flower shop assistant. Respond in JSON format.

CATALOG:
- Pink peony 15 (4500 baht)
- White roses (3800 baht)
- Red tulips (3200 baht)

{
  "text": "your response in Russian",
  "text_en": "your response in English", 
  "text_thai": "your response in Thai",
  "command": null
}

User: "Привет"
Response:"""
        },
        {
            "name": "С командами",
            "prompt": """You are a flower shop assistant. Respond in JSON format.

AVAILABLE COMMANDS:
- send_catalog: send flower catalog
- save_order_info: save order data

{
  "text": "your response in Russian",
  "text_en": "your response in English", 
  "text_thai": "your response in Thai",
  "command": {"type": "command_name"} or null
}

User: "Хочу заказать букет"
Response:"""
        },
        {
            "name": "С историей диалога",
            "prompt": """You are a flower shop assistant. Respond in JSON format.

CONVERSATION HISTORY:
[{"role": "user", "content": "Привет"}]

AVAILABLE COMMANDS:
- send_catalog: send flower catalog
- save_order_info: save order data

{
  "text": "your response in Russian",
  "text_en": "your response in English", 
  "text_thai": "your response in Thai",
  "command": {"type": "command_name"} or null
}

User: "Хочу заказать букет"
Response:"""
        }
    ]
    
    for i, test_case in enumerate(test_prompts, 1):
        print(f"\n{'='*60}")
        print(f"🧪 ТЕСТ {i}: {test_case['name']}")
        print(f"{'='*60}")
        
        prompt = test_case['prompt']
        print(f"📤 Промпт длиной: {len(prompt)} символов")
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            print(f"📥 Длина ответа: {len(response_text)} символов")
            print(f"📥 Ответ (repr): {repr(response_text)}")
            
            # Пробуем парсить JSON
            import json
            import re
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    print(f"✅ JSON успешно распарсен:")
                    print(f"   text: '{parsed.get('text', '')}'")
                    print(f"   command: {parsed.get('command')}")
                else:
                    print("❌ JSON не найден в ответе")
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                print(f"JSON строка: {json_str}")
                
        except Exception as e:
            print(f"❌ Ошибка AI: {e}")

if __name__ == "__main__":
    print("🚀 Запуск прогрессивного теста AI...")
    asyncio.run(test_progressive_ai())
    print("\n�� Тест завершен!") 
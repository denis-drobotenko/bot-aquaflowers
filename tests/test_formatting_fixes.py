#!/usr/bin/env python3
"""
Тест для проверки исправлений форматирования сообщений AI
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.json_processor import parse_ai_response, extract_and_fix_json

def test_formatting_preservation():
    """Тестирует сохранение форматирования в функциях обработки текста"""
    print("=== Тест сохранения форматирования ===")
    
    # Тест 1: Многострочный текст с переносами
    test_json_1 = '''```json
{
  "text": "Привет! 

Это многострочное сообщение
с переносами строк.

Надеюсь, форматирование сохранится!",
  "command": null
}
```'''
    
    print(f"1. Тест многострочного JSON:")
    print(f"   Входной JSON:\\n{repr(test_json_1)}")
    
    json_data, user_text = extract_and_fix_json(test_json_1)
    print(f"   Извлеченный текст:\\n{repr(user_text)}")
    
    # Проверяем, что переносы строк сохранены
    if user_text and '\\n' in user_text:
        print("   ✅ Переносы строк сохранены")
    else:
        print("   ❌ Переносы строк потеряны")
    
    # Тест 2: JSON с абзацами
    test_json_2 = '''```json
{
  "text": "Отлично! Записал ваш выбор букета 'Spirit 🌸'.

Нужна ли доставка? Если да, то куда?

Доставка работает с 8:00 до 21:00.",
  "command": {
    "type": "save_order_info",
    "bouquet": "Spirit 🌸",
    "retailer_id": "rl7vdxcifo"
  }
}
```'''
    
    print(f"\\n2. Тест JSON с абзацами:")
    print(f"   Входной JSON:\\n{repr(test_json_2)}")
    
    json_data, user_text = extract_and_fix_json(test_json_2)
    print(f"   Извлеченный текст:\\n{repr(user_text)}")
    
    # Проверяем, что абзацы сохранены
    if user_text and user_text.count('\\n\\n') >= 2:
        print("   ✅ Абзацы сохранены")
    else:
        print("   ❌ Абзацы потеряны")
    
    # Тест 3: Простой JSON без markdown
    test_json_3 = '''{
  "text": "Здравствуйте! Хотите посмотреть наш каталог цветов? 🌸",
  "command": null
}'''
    
    print(f"\\n3. Тест простого JSON:")
    print(f"   Входной JSON:\\n{repr(test_json_3)}")
    
    json_data, user_text = extract_and_fix_json(test_json_3)
    print(f"   Извлеченный текст:\\n{repr(user_text)}")
    
    # Проверяем, что текст сохранен
    if user_text and "Здравствуйте" in user_text:
        print("   ✅ Текст сохранен")
    else:
        print("   ❌ Текст потерян")
    
    print("\\n=== Тест завершен ===")

def test_parse_ai_response():
    """Тестирует функцию parse_ai_response"""
    print("\\n=== Тест parse_ai_response ===")
    
    # Создаем mock объект response
    class MockResponse:
        def __init__(self, text):
            self.text = text
            self.candidates = [MockCandidate(text)]
    
    class MockCandidate:
        def __init__(self, text):
            self.content = MockContent(text)
    
    class MockContent:
        def __init__(self, text):
            self.parts = [MockPart(text)]
    
    class MockPart:
        def __init__(self, text):
            self.text = text
    
    # Тест 1: Корректный JSON
    mock_response_1 = MockResponse('''```json
{
  "text": "Привет! 

Это тестовое сообщение
с переносами строк.",
  "command": null
}
```''')
    
    print(f"1. Тест корректного JSON:")
    ai_text, ai_command = parse_ai_response(mock_response_1)
    print(f"   Текст: {repr(ai_text)}")
    print(f"   Команда: {ai_command}")
    
    if ai_text and '\\n' in ai_text:
        print("   ✅ Форматирование сохранено")
    else:
        print("   ❌ Форматирование потеряно")
    
    # Тест 2: Некорректный JSON (должен вернуть None)
    mock_response_2 = MockResponse("Просто текст без JSON")
    
    print(f"\\n2. Тест некорректного JSON:")
    ai_text, ai_command = parse_ai_response(mock_response_2)
    print(f"   Текст: {ai_text}")
    print(f"   Команда: {ai_command}")
    
    if ai_text is None and ai_command is None:
        print("   ✅ Правильно обработан некорректный JSON")
    else:
        print("   ❌ Неправильно обработан некорректный JSON")
    
    print("\\n=== Тест завершен ===")

if __name__ == "__main__":
    test_formatting_preservation()
    test_parse_ai_response() 
 
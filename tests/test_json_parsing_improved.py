#!/usr/bin/env python3
"""
Тест улучшенной функции парсинга JSON с подстраховкой
"""

import json
import re
import sys
import os

# Добавляем src в путь
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, 'src')
sys.path.insert(0, src_path)

from src import ai_manager

def test_parse_response_improved():
    """Тестируем улучшенную функцию parse_response"""
    print("=== ТЕСТ УЛУЧШЕННОГО ПАРСИНГА JSON ===\n")
    
    # Создаем mock объект response
    class MockResponse:
        def __init__(self, text):
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
    print("1. Тест: Корректный JSON")
    test_response = MockResponse('{"text": "Привет! Как дела?", "command": null}')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text == "Привет! Как дела?"
    print("✅ Успешно")
    
    # Тест 2: Неполный JSON (сломанный)
    print("\n2. Тест: Неполный JSON")
    test_response = MockResponse('{"text": "Привет! Как дела?", "command": {')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text is not None and len(text) > 0
    print("✅ Успешно (fallback сработал)")
    
    # Тест 3: JSON с двойными скобками
    print("\n3. Тест: JSON с двойными скобками")
    test_response = MockResponse('{{"text": "Привет! Как дела?", "command": null}}')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text == "Привет! Как дела?"
    print("✅ Успешно")
    
    # Тест 4: Markdown JSON блок
    print("\n4. Тест: Markdown JSON блок")
    test_response = MockResponse('```json\n{"text": "Привет! Как дела?", "command": null}\n```')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text == "Привет! Как дела?"
    print("✅ Успешно")
    
    # Тест 5: Обычный текст без JSON
    print("\n5. Тест: Обычный текст без JSON")
    test_response = MockResponse('Привет! Как дела?')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text == "Привет! Как дела?"
    print("✅ Успешно")
    
    # Тест 6: Пустой ответ
    print("\n6. Тест: Пустой ответ")
    test_response = MockResponse('')
    text, command = ai_manager.parse_response(test_response)
    print(f"Результат: text='{text}', command={command}")
    assert text is None
    print("✅ Успешно")
    
    print("\n=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО ===")

if __name__ == "__main__":
    test_parse_response_improved() 
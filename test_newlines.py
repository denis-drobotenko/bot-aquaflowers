#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.ai_utils import parse_ai_response

def test_newlines():
    # Тест 1: Обычный текст с \n
    test1 = 'Добрый вечер, Денис!\n\nХотели бы Вы посмотреть наш каталог цветов? 🌸'
    print("Test 1 - Plain text with \\n:")
    print("Input:", repr(test1))
    result1 = parse_ai_response(test1)
    print("Output:", repr(result1))
    print()
    
    # Тест 2: JSON с обычными \n
    test2 = '''```json
{
  "text": "Добрый вечер, Денис!\n\nХотели бы Вы посмотреть наш каталог цветов? 🌸",
  "text_en": "Good evening, Denis!\n\nWould you like to see our flower catalog? 🌸",
  "text_thai": "สวัสดีตอนเย็น เดนิส!\n\nคุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม? 🌸"
}
```'''
    print("Test 2 - JSON with \\n:")
    print("Input:", repr(test2))
    result2 = parse_ai_response(test2)
    print("Output:", repr(result2))
    print()
    
    # Тест 3: JSON с \\n (правильный формат)
    test3 = '''```json
{
  "text": "Добрый вечер, Денис!\\n\\nХотели бы Вы посмотреть наш каталог цветов? 🌸",
  "text_en": "Good evening, Denis!\\n\\nWould you like to see our flower catalog? 🌸",
  "text_thai": "สวัสดีตอนเย็น เดนิส!\\n\\nคุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม? 🌸"
}
```'''
    print("Test 3 - JSON with \\\\n:")
    print("Input:", repr(test3))
    result3 = parse_ai_response(test3)
    print("Output:", repr(result3))
    print()

if __name__ == "__main__":
    test_newlines() 
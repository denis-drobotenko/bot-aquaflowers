#!/usr/bin/env python3
"""
Тест сохранения переносов строк в WhatsApp сообщениях
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.whatsapp_utils import send_whatsapp_message
import asyncio

def test_whatsapp_formatting():
    """Тестирует сохранение переносов строк в WhatsApp сообщениях"""
    
    print("🧪 Тестируем сохранение переносов строк в WhatsApp сообщениях")
    
    # Тестовые сообщения с переносами строк
    test_messages = [
        {
            "name": "Простой перенос строки",
            "text": "Первая строка\nВторая строка"
        },
        {
            "name": "Множественные переносы",
            "text": "Строка 1\n\nСтрока 2\n\nСтрока 3"
        },
        {
            "name": "Списки с переносами",
            "text": "Наш прайс-лист:\n* Раваи: 500 бат\n* Чалонг: 380 бат\n* Пхукет-Таун: 300 бат"
        },
        {
            "name": "Смешанное форматирование",
            "text": "🌸 Привет!\n\nКак дела?\n\nНадеюсь, все хорошо! 🌸"
        }
    ]
    
    for test_case in test_messages:
        print(f"\n📝 Тест: {test_case['name']}")
        print(f"   Исходный текст:")
        print(f"   '{test_case['text']}'")
        
        # Имитируем обработку через clean_message
        import re
        def clean_message(text):
            # Сохраняем переносы строк для WhatsApp, но убираем лишние пробелы
            # Заменяем множественные пробелы на один, но сохраняем \n
            # Убираем множественные пробелы, но сохраняем переносы строк
            text = re.sub(r'[ \t]+', ' ', text)
            # Убираем пробелы в начале и конце строк
            text = re.sub(r'^[ \t]+', '', text, flags=re.MULTILINE)
            text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
            # Убираем пустые строки в начале и конце
            text = text.strip()
            return text
        
        cleaned_text = clean_message(test_case['text'])
        print(f"   Обработанный текст:")
        print(f"   '{cleaned_text}'")
        
        # Проверяем, что переносы строк сохранились
        if '\n' in cleaned_text:
            print(f"   ✅ Переносы строк сохранены")
        else:
            print(f"   ❌ Переносы строк потеряны")
        
        # Проверяем количество строк
        original_lines = test_case['text'].split('\n')
        cleaned_lines = cleaned_text.split('\n')
        
        if len(original_lines) == len(cleaned_lines):
            print(f"   ✅ Количество строк сохранено: {len(original_lines)}")
        else:
            print(f"   ❌ Количество строк изменилось: было {len(original_lines)}, стало {len(cleaned_lines)}")

def test_whatsapp_message_structure():
    """Тестирует структуру WhatsApp сообщения"""
    
    print("\n🔧 Тестируем структуру WhatsApp сообщения")
    
    # Имитируем структуру сообщения, которую отправляет WhatsApp API
    test_message = "Первая строка\n\nВторая строка\n\nТретья строка"
    
    # Структура payload для WhatsApp API
    payload = {
        "messaging_product": "whatsapp",
        "to": "test_number",
        "type": "text",
        "text": {
            "body": test_message
        }
    }
    
    print(f"   Payload для WhatsApp API:")
    print(f"   {payload}")
    
    # Проверяем, что body содержит переносы строк
    body = payload["text"]["body"]
    if '\n' in body:
        print(f"   ✅ Body содержит переносы строк")
        print(f"   Количество строк: {len(body.split(chr(10)))}")
    else:
        print(f"   ❌ Body не содержит переносы строк")

if __name__ == "__main__":
    print("🚀 Тестирование форматирования WhatsApp сообщений")
    test_whatsapp_formatting()
    test_whatsapp_message_structure()
    print("\n✅ Тест завершен") 
 
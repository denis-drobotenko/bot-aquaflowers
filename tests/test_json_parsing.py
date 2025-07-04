#!/usr/bin/env python3
"""
Тест функции парсинга JSON из AI ответов
"""

import json
import re

def parse_response_test(response_text):
    """Тестовая версия функции parse_response"""
    text = None
    command = None
    
    try:
        # Имитируем структуру ответа AI
        full_text = response_text
        
        # Пытаемся найти JSON в ответе
        try:
            # Ищем JSON блок (может быть обернут в ```json или просто JSON)
            if '```json' in full_text:
                json_start = full_text.find('```json') + 7
                json_end = full_text.find('```', json_start)
                json_str = full_text[json_start:json_end].strip()
            elif full_text.strip().startswith('{'):
                json_str = full_text.strip()
            else:
                # Пытаемся найти JSON с помощью регулярного выражения
                # Сначала ищем JSON с двойными скобками (из f-string)
                json_match = re.search(r'\{\{.*\}\}', full_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # Заменяем двойные скобки на одинарные
                    json_str = json_str.replace('{{', '{').replace('}}', '}')
                else:
                    # Ищем обычный JSON
                    json_match = re.search(r'\{.*\}', full_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                    else:
                        # Если нет JSON, используем весь текст как ответ
                        text = full_text
                        return text, None
            
            print(f"Найденный JSON (до замены): {json_str}")
            if '{{' in json_str:
                json_str = json_str.replace('{{', '{').replace('}}', '}')
                print(f"Найденный JSON (после замены): {json_str}")
            
            # Парсим JSON
            response_data = json.loads(json_str)
            
            # Извлекаем текст и команду
            text = response_data.get('text', '')
            command = response_data.get('command', None)
            
            print(f"[JSON_PARSE] Parsed JSON: text='{text}', command={command}")
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Если JSON сломан, используем весь текст как ответ
            text = full_text
            command = None
            
    except Exception as e:
        print(f"Error parsing response: {e}")
        text = None
        command = None
        
    return text, command

# Тестовые случаи из логов
test_cases = [
    # Случай 1: Правильный JSON с двойными скобками
    """{{
  "text": "Отлично! Ваш заказ подтвержден и передан в обработку. Мы свяжемся с вами в ближайшее время! 🌹",
  "command": {{
    "type": "confirm_order",
    "order_summary": {{
      "bouquet": "Candy's",
      "delivery_needed": true,
      "address": "Centrio condo",
      "date": "2 July 2025",
      "time": "09:00",
      "card_needed": true,
      "card_text": "Я тебя люблю!",
      "recipient_name": "Саша",
      "recipient_phone": "3578368646774"
    }}
  }}
}}""",
    
    # Случай 2: JSON с экранированными кавычками
    """{{\n  "text": "Отлично, номер телефона получателя записан. Вот сводка вашего заказа:\\n\\nБукет: Candy's\\nДоставка: Да, по адресу Centrio condo\\nДата и время доставки: 2 июля 2025 года, 09:00\\nОткрытка: Да, с текстом 'Я тебя люблю!'\\nПолучатель: Саша\\nТелефон получателя: 3578368646774\\n\\nВсе верно? Подтверждаете заказ?",\n  "command": {\n    "type": "save_order_info",\n    "recipient_name": "Саша",\n    "recipient_phone": "3578368646774"\n  }\n}}""",
    
    # Случай 3: Обычный текст без JSON
    "Здравствуйте! Хотите посмотреть наш каталог цветов? 🌸",
    
    # Случай 4: JSON в markdown блоке
    """```json
{
  "text": "Сейчас покажу вам каждый букет отдельно с фотографией и описанием!",
  "command": {
    "type": "send_catalog"
  }
}
```""",
]

print("=== ТЕСТИРОВАНИЕ ФУНКЦИИ ПАРСИНГА JSON ===\n")

for i, test_case in enumerate(test_cases, 1):
    print(f"--- Тест {i} ---")
    print(f"Входные данные:\n{test_case}\n")
    
    text, command = parse_response_test(test_case)
    
    print(f"Результат:")
    print(f"Text: {text}")
    print(f"Command: {command}")
    print("-" * 50)
    print() 
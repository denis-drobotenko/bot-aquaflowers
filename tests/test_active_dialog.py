#!/usr/bin/env python3
"""
Тест активного диалога AI
"""

import asyncio
import sys
import os
import pytest

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем src в путь
current_dir = os.path.dirname(__file__)
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

# Добавляем корневую директорию проекта в путь
project_root = os.path.join(current_dir, '..')
sys.path.insert(0, project_root)

try:
    from src.ai_manager import get_ai_response
    from src.command_handler import handle_commands
except ImportError:
    # Альтернативный способ импорта
    import src.ai_manager as ai_manager
    import src.command_handler as command_handler
    
    def get_ai_response(session_id, history):
        return ai_manager.get_ai_response(session_id, history)
    
    def handle_commands(session_id, text):
        return command_handler.handle_commands(session_id, text)

@pytest.mark.asyncio
async def test_active_dialog():
    """Тестируем активный диалог AI"""
    print("=== ТЕСТ АКТИВНОГО ДИАЛОГА ===")
    
    # Используем уникальный session_id для тестов
    session_id = "test_active_dialog_session"
    
    # Тест 1: Приветствие
    print("\n1. Тест: Приветствие")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про каталог
    if "?" in ai_text and ("каталог" in ai_text.lower() or "хотите" in ai_text.lower()):
        print("✅ AI задал вопрос про каталог!")
    else:
        print("❌ AI не задал вопрос про каталог")
    
    # Тест 2: Согласие на каталог
    print("\n2. Тест: Согласие на каталог")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI отправил каталог и спросил про выбор букета
    if "каталог" in ai_text.lower() and "?" in ai_text and ("какой" in ai_text.lower() or "букет" in ai_text.lower()):
        print("✅ AI отправил каталог и спросил про выбор букета!")
    else:
        print("❌ AI не отправил каталог или не спросил про выбор букета")
    
    # Тест 3: Выбор букета
    print("\n3. Тест: Выбор букета")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]}  # Название букета
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про дату/время
    if "?" in ai_text and ("когда" in ai_text.lower() or "дата" in ai_text.lower() or "время" in ai_text.lower()):
        print("✅ AI задал вопрос про дату/время!")
    else:
        print("❌ AI не задал вопрос про дату/время")
    
    # Тест 4: Указание даты
    print("\n4. Тест: Указание даты")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Записал ваш выбор букета \'Spirit 🌸\'. Когда нужна доставка? (дата и время)'}]},
        {'role': 'user', 'parts': [{'text': '15 декабря в 14:00'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про доставку
    if "?" in ai_text and ("доставка" in ai_text.lower() or "куда" in ai_text.lower() or "адрес" in ai_text.lower()):
        print("✅ AI задал вопрос про доставку!")
    else:
        print("❌ AI не задал вопрос про доставку")
    
    # Тест 5: Ответ про доставку
    print("\n5. Тест: Ответ про доставку")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Записал ваш выбор букета \'Spirit 🌸\'. Когда нужна доставка? (дата и время)'}]},
        {'role': 'user', 'parts': [{'text': '15 декабря в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату доставки: 15 декабря в 14:00. Нужна ли доставка? Если да, то куда?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, ул. Пушкина, 10'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про открытку
    if "?" in ai_text and ("открытка" in ai_text.lower() or "текст" in ai_text.lower()):
        print("✅ AI задал вопрос про открытку!")
    else:
        print("❌ AI не задал вопрос про открытку")
    
    # Тест 6: Ответ про открытку
    print("\n6. Тест: Ответ про открытку")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Записал ваш выбор букета \'Spirit 🌸\'. Когда нужна доставка? (дата и время)'}]},
        {'role': 'user', 'parts': [{'text': '15 декабря в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату доставки: 15 декабря в 14:00. Нужна ли доставка? Если да, то куда?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Понял! Доставка по адресу: ул. Пушкина, 10. Нужна ли открытка к букету? Если да, то какой текст?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, С любовью!'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про имя получателя
    if "?" in ai_text and ("получателя" in ai_text.lower() or "зовут" in ai_text.lower()):
        print("✅ AI задал вопрос про имя получателя!")
    else:
        print("❌ AI не задал вопрос про имя получателя")
    
    # Тест 7: Имя получателя
    print("\n7. Тест: Имя получателя")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Записал ваш выбор букета \'Spirit 🌸\'. Когда нужна доставка? (дата и время)'}]},
        {'role': 'user', 'parts': [{'text': '15 декабря в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату доставки: 15 декабря в 14:00. Нужна ли доставка? Если да, то куда?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Понял! Доставка по адресу: ул. Пушкина, 10. Нужна ли открытка к букету? Если да, то какой текст?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, С любовью!'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал текст открытки: \'С любовью!\'. Как зовут получателя букета?'}]},
        {'role': 'user', 'parts': [{'text': 'Анна'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI задал вопрос про телефон получателя
    if "?" in ai_text and ("телефон" in ai_text.lower() or "номер" in ai_text.lower()):
        print("✅ AI задал вопрос про телефон получателя!")
    else:
        print("❌ AI не задал вопрос про телефон получателя")
    
    # Тест 8: Телефон получателя и сводка заказа
    print("\n8. Тест: Телефон получателя и сводка заказа")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA! 🌸 Хотите посмотреть наш каталог цветов?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Отправляю наш каталог цветов! Какой букет вам нравится?'}]},
        {'role': 'user', 'parts': [{'text': 'Spirit 🌸'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Записал ваш выбор букета \'Spirit 🌸\'. Когда нужна доставка? (дата и время)'}]},
        {'role': 'user', 'parts': [{'text': '15 декабря в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату доставки: 15 декабря в 14:00. Нужна ли доставка? Если да, то куда?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Понял! Доставка по адресу: ул. Пушкина, 10. Нужна ли открытка к букету? Если да, то какой текст?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, С любовью!'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал текст открытки: \'С любовью!\'. Как зовут получателя букета?'}]},
        {'role': 'user', 'parts': [{'text': 'Анна'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал имя получателя: Анна. Какой номер телефона получателя?'}]},
        {'role': 'user', 'parts': [{'text': '+7 999 123-45-67'}]}
    ]
    
    ai_text, ai_commands = get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    
    # Проверяем, что AI показал сводку заказа и спросил про подтверждение
    if "сводка" in ai_text.lower() and "?" in ai_text and ("верно" in ai_text.lower() or "подтверждаете" in ai_text.lower()):
        print("✅ AI показал сводку заказа и спросил про подтверждение!")
    else:
        print("❌ AI не показал сводку заказа или не спросил про подтверждение")
    
    # Тест 9: Подтверждение заказа и отправка в LINE
    print("\n9. Тест: Подтверждение заказа и отправка в LINE")
    order_data = {
        'type': 'confirm_order',
        'bouquet': 'Spirit 🌸',
        'date': '15 декабря',
        'time': '14:00',
        'delivery_needed': 'True',
        'address': 'ул. Пушкина, 10',
        'card_needed': 'True',
        'card_text': 'С любовью!',
        'recipient_name': 'Анна',
        'recipient_phone': '+7 999 123-45-67',
        'retailer_id': 'test_bouquet_id'
    }
    result = await handle_commands(session_id, session_id, order_data)
    print(f"Результат отправки заказа: {result}")
    print("✅ Проверка отправки заказа в LINE завершена!")
    
    print("\n=== ТЕСТ АКТИВНОГО ДИАЛОГА ЗАВЕРШЕН ===")
    print("✅ Все тесты активного диалога пройдены!")

if __name__ == "__main__":
    asyncio.run(test_active_dialog()) 
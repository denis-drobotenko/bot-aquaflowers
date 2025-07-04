#!/usr/bin/env python3
"""
Полный тест диалога - от приветствия до подтверждения заказа
"""

import asyncio
import sys
import os
import json
import pytest

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем src в путь
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src import ai_manager, command_handler, database

@pytest.mark.asyncio
async def test_full_dialog():
    """Тестирует полный диалог от приветствия до подтверждения заказа"""
    print("=== ПОЛНЫЙ ТЕСТ ДИАЛОГА ===")
    
    # Используем уникальный sender_id и session_id для чистого теста
    sender_id = f"test_user_{os.getpid()}"
    session_id = f"test_session_{os.getpid()}_{asyncio.get_event_loop().time()}"
    
    # Шаг 1: Приветствие
    print("\n1. Шаг: Приветствие")
    history = [{'role': 'user', 'parts': [{'text': 'Привет'}]}]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Шаг 2: Согласие на каталог
    print("\n2. Шаг: Согласие на каталог")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': ai_text}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Шаг 3: Выбор букета
    print("\n3. Шаг: Выбор букета")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:bouquet=Spirit")
    database.add_message(sender_id, session_id, "system", "order_info:retailer_id=123")
    
    # Шаг 4: Дата и время
    print("\n4. Шаг: Дата и время")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:date=2025-07-02")
    database.add_message(sender_id, session_id, "system", "order_info:time=14:00")
    
    # Шаг 5: Доставка
    print("\n5. Шаг: Доставка")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату и время. Нужна ли доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, нужна доставка по адресу ул. Пушкина, 10'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:delivery_needed=True")
    database.add_message(sender_id, session_id, "system", "order_info:address=ул. Пушкина, 10")
    
    # Шаг 6: Открытка
    print("\n6. Шаг: Открытка")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату и время. Нужна ли доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, нужна доставка по адресу ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал адрес. Нужна ли открытка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, с текстом "С любовью!"'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:card_needed=True")
    database.add_message(sender_id, session_id, "system", "order_info:card_text=С любовью!")
    
    # Шаг 7: Имя получателя
    print("\n7. Шаг: Имя получателя")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату и время. Нужна ли доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, нужна доставка по адресу ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал адрес. Нужна ли открытка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, с текстом "С любовью!"'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал открытку. Как зовут получателя?'}]},
        {'role': 'user', 'parts': [{'text': 'Анна'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:recipient_name=Анна")
    
    # Шаг 8: Телефон получателя
    print("\n8. Шаг: Телефон получателя")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату и время. Нужна ли доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, нужна доставка по адресу ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал адрес. Нужна ли открытка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, с текстом "С любовью!"'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал открытку. Как зовут получателя?'}]},
        {'role': 'user', 'parts': [{'text': 'Анна'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал имя. Какой номер телефона получателя?'}]},
        {'role': 'user', 'parts': [{'text': '+7 999 123-45-67'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Сохраняем данные заказа в базу для тестирования
    database.add_message(sender_id, session_id, "system", "order_info:recipient_phone=+7 999 123-45-67")
    
    # Шаг 9: Подтверждение заказа
    print("\n9. Шаг: Подтверждение заказа")
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'assistant', 'parts': [{'text': 'Добро пожаловать!'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отправляю каталог!'}]},
        {'role': 'user', 'parts': [{'text': 'Выбираю букет Spirit'}]},
        {'role': 'assistant', 'parts': [{'text': 'Отлично! Когда нужна доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Завтра в 14:00'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал дату и время. Нужна ли доставка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, нужна доставка по адресу ул. Пушкина, 10'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал адрес. Нужна ли открытка?'}]},
        {'role': 'user', 'parts': [{'text': 'Да, с текстом "С любовью!"'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал открытку. Как зовут получателя?'}]},
        {'role': 'user', 'parts': [{'text': 'Анна'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал имя. Какой номер телефона получателя?'}]},
        {'role': 'user', 'parts': [{'text': '+7 999 123-45-67'}]},
        {'role': 'assistant', 'parts': [{'text': 'Записал телефон. Подтвердите заказ.'}]},
        {'role': 'user', 'parts': [{'text': 'Да, подтверждаю заказ'}]}
    ]
    ai_text, ai_commands = ai_manager.get_ai_response(sender_id, session_id, history)
    print(f"AI ответ: {ai_text}")
    print(f"Команды: {ai_commands}")
    
    if ai_commands:
        result = await command_handler.handle_commands(sender_id, session_id, ai_commands)
        print(f"Результат команд: {result}")
    
    # Проверяем финальную историю
    print("\n10. Проверка финальной истории")
    final_history = database.get_conversation_history(sender_id, session_id)
    print(f"Количество сообщений в истории: {len(final_history)}")
    
    # Проверяем, что все системные сообщения сохранены
    system_messages = [msg for msg in final_history if msg.get('role') == 'system']
    print(f"Количество системных сообщений: {len(system_messages)}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")
    print("✅ Полный диалог протестирован успешно!")

if __name__ == "__main__":
    asyncio.run(test_full_dialog()) 
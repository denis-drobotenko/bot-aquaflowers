#!/usr/bin/env python3
"""
Тест нового JSON-подхода AI
"""

import asyncio
import sys
import os
import pytest

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем src в путь
# Добавляем src в путь
current_dir = os.path.dirname(__file__)
# Всегда добавляем путь к src относительно текущего файла
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

from src import ai_manager, command_handler

@pytest.mark.asyncio
async def test_json_ai():
    """Тестируем новый JSON-подход AI"""
    print("=== ТЕСТ JSON AI ===")
    
    # Используем уникальный sender_id для тестов
    sender_id = "test_user_json_ai"
    
    # Тест 1: Приветствие
    print("\n1. Тест: 'Привет'")
    
    # Симулируем историю
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]}
    ]
    
    # Получаем ответ от AI
    ai_text, ai_commands = ai_manager.get_ai_response("test_session1", history)
    print(f"AI ответ: text='{ai_text}', commands={ai_commands}")
    
    if ai_commands:
        print("→ Выполняем команды...")
        command_results = await command_handler.handle_commands(sender_id, "test_session1", ai_commands)
        print(f"→ Результат выполнения команд: {command_results}")
    
    # Проверяем результат
    if ai_text and ("Добро пожаловать" in ai_text or "AURAFLORA" in ai_text):
        print("✅ AI дал правильный текстовый ответ!")
    else:
        print("❌ AI не дал правильный текстовый ответ")
    
    if ai_commands and len(ai_commands) > 0:
        print("✅ AI дал команды!")
    else:
        print("❌ AI не дал команды")
    
    # Тест 2: Запрос каталога
    print("\n2. Тест: 'Покажи каталог'")
    
    # Симулируем историю
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'model', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA!'}]},
        {'role': 'user', 'parts': [{'text': 'Покажи каталог'}]}
    ]
    
    # Получаем ответ от AI
    ai_text, ai_commands = ai_manager.get_ai_response("test_session2", history)
    print(f"AI ответ: text='{ai_text}', commands={ai_commands}")
    
    if ai_commands:
        print("→ Выполняем команды...")
        command_results = await command_handler.handle_commands(sender_id, "test_session2", ai_commands)
        print(f"→ Результат выполнения команд: {command_results}")
    
    # Проверяем результат
    if ai_text and ("каталог" in ai_text.lower() or "цвет" in ai_text.lower()):
        print("✅ AI дал правильный текстовый ответ!")
    else:
        print("❌ AI не дал правильный текстовый ответ")
    
    if ai_commands and len(ai_commands) > 0:
        print("✅ AI дал команды!")
    else:
        print("❌ AI не дал команды")
    
    # Тест 3: Сохранение заказа
    print("\n3. Тест: 'Хочу розовые розы'")
    
    # Симулируем историю
    history = [
        {'role': 'user', 'parts': [{'text': 'Привет'}]},
        {'role': 'model', 'parts': [{'text': 'Привет! Добро пожаловать в AURAFLORA!'}]},
        {'role': 'user', 'parts': [{'text': 'Хочу розовые розы'}]}
    ]
    
    # Получаем ответ от AI
    ai_text, ai_commands = ai_manager.get_ai_response("test_session3", history)
    print(f"AI ответ: text='{ai_text}', commands={ai_commands}")
    
    if ai_commands:
        print("→ Выполняем команды...")
        command_results = await command_handler.handle_commands(sender_id, "test_session3", ai_commands)
        print(f"→ Результат выполнения команд: {command_results}")
    
    # Проверяем результат
    if ai_text and ("записал" in ai_text.lower() or "выбор" in ai_text.lower()):
        print("✅ AI дал правильный текстовый ответ!")
    else:
        print("❌ AI не дал правильный текстовый ответ")
    
    if ai_commands and len(ai_commands) > 0:
        print("✅ AI дал команды!")
    else:
        print("❌ AI не дал команды")

    # Тест 4: Чистая история без технических сообщений
    print("\n4. Тест: Чистая история для AI (без order_info, user_info)")
    history = [
        {'role': 'user', 'parts': [{'text': 'Здравствуйте!'}]},
        {'role': 'model', 'parts': [{'text': 'Здравствуйте! Хотите посмотреть наш каталог цветов? 🌸'}]},
        {'role': 'user', 'parts': [{'text': 'Да, покажите каталог'}]},
        {'role': 'model', 'parts': [{'text': 'Сейчас покажу вам каждый букет отдельно с фотографией и описанием!'}]},
        {'role': 'user', 'parts': [{'text': 'Мне нравится букет Spirit 🌸'}]},
    ]
    ai_text, ai_commands = ai_manager.get_ai_response("test_session_clean", history)
    print(f"AI ответ: text='{ai_text}', commands={ai_commands}")
    if ai_commands:
        print("→ Выполняем команды...")
        command_results = await command_handler.handle_commands(sender_id, "test_session_clean", ai_commands)
        print(f"→ Результат выполнения команд: {command_results}")
    if ai_text:
        print("✅ AI дал текстовый ответ!")
    else:
        print("❌ AI не дал текстовый ответ")
    if ai_commands:
        print("✅ AI дал команды!")
    else:
        print("❌ AI не дал команды")

if __name__ == "__main__":
    asyncio.run(test_json_ai()) 
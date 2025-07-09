#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_prompt_loading():
    """Тестирует загрузку промпта без AI"""
    print("🔍 Тестирую загрузку промпта...")
    
    try:
        # Загружаем промпт напрямую
        prompt_path = os.path.join("src", "services", "prompts", "ai_system_prompt.prompt")
        
        with open(prompt_path, encoding="utf-8") as f:
            prompt_template = f.read()
        
        print(f"✅ Промпт загружен из: {prompt_path}")
        print(f"📏 Длина шаблона: {len(prompt_template)} символов")
        
        # Подготавливаем переменные для подстановки
        user_lang = 'ru'
        sender_name = 'Test User'
        phuket_time_str = '08 July 2025, 12:00'
        name_context = f"User name: {sender_name}"
        name_instruction = f"""
GREETING WITH NAME: This is the first message in conversation, use the user's name '{sender_name}' in greeting.
IMPORTANT: The name '{sender_name}' is from WhatsApp profile. If the user writes in Russian, use Russian name format.
If the user writes in English, use English name format. If the user writes in Thai, use Thai name format.
Example: 'Hello {sender_name}! Would you like to see our flower catalog?'"""
        language_instruction = f"IMPORTANT: Respond in user's language! User writes in language code '{user_lang}'. Respond in the same language."
        
        try:
            # Выполняем подстановку
            final_prompt = prompt_template.format(
                user_lang=user_lang,
                sender_name=sender_name or "",
                phuket_time_str=phuket_time_str,
                name_context=name_context,
                name_instruction=name_instruction,
                language_instruction=language_instruction
            )
        except KeyError as e:
            print(f"❌ ОШИБКА KeyError: {e}")
            print("--- Фрагмент шаблона (первые 1000 символов) ---")
            print(prompt_template[:1000])
            print("--- КОНЕЦ ФРАГМЕНТА ---")
            raise
        
        print(f"✅ Подстановка выполнена!")
        print(f"📏 Длина финального промпта: {len(final_prompt)} символов")
        
        # Проверяем, что нет двойных скобок
        if '{{' in final_prompt or '}}' in final_prompt:
            print("❌ ОШИБКА: В промпте остались двойные скобки!")
            # Показываем где именно
            lines = final_prompt.split('\n')
            for i, line in enumerate(lines):
                if '{{' in line or '}}' in line:
                    print(f"   Строка {i+1}: {line}")
            return False
        
        # Проверяем, что есть правильные JSON примеры
        if '"text":' in final_prompt and '"command":' in final_prompt:
            print("✅ JSON примеры присутствуют")
        else:
            print("❌ ОШИБКА: JSON примеры отсутствуют!")
            return False
        
        # Проверяем подстановку переменных
        if 'Test User' in final_prompt:
            print("✅ Переменные подставляются корректно")
        else:
            print("❌ ОШИБКА: Переменные не подставляются!")
            return False
        
        # Показываем небольшой фрагмент промпта
        print("\n📄 Фрагмент промпта (первые 500 символов):")
        print("=" * 50)
        print(final_prompt[:500])
        print("=" * 50)
        
        print("✅ Все проверки пройдены!")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Тест отладки промпта...")
    success = test_prompt_loading()
    print(f"🎯 Результат: {'УСПЕХ' if success else 'ОШИБКА'}") 
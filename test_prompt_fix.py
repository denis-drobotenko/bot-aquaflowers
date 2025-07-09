#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.ai_service import AIService

def test_prompt_loading():
    """Тестирует загрузку промпта"""
    print("🔍 Тестирую загрузку промпта...")
    
    try:
        # Создаем экземпляр AI сервиса (без API ключа)
        ai_service = AIService("dummy_key")
        
        # Тестируем загрузку промпта
        prompt = ai_service.get_system_prompt(
            user_lang='ru',
            sender_name='Test User',
            is_first_message=True
        )
        
        print(f"✅ Промпт успешно загружен!")
        print(f"📏 Длина промпта: {len(prompt)} символов")
        
        # Проверяем, что нет двойных скобок
        if '{{' in prompt or '}}' in prompt:
            print("❌ ОШИБКА: В промпте остались двойные скобки!")
            return False
        
        # Проверяем, что есть правильные JSON примеры
        if '"text":' in prompt and '"command":' in prompt:
            print("✅ JSON примеры присутствуют")
        else:
            print("❌ ОШИБКА: JSON примеры отсутствуют!")
            return False
        
        # Проверяем подстановку переменных
        if 'Test User' in prompt:
            print("✅ Переменные подставляются корректно")
        else:
            print("❌ ОШИБКА: Переменные не подставляются!")
            return False
        
        print("✅ Все проверки пройдены!")
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Тест исправления промпта...")
    success = test_prompt_loading()
    print(f"🎯 Результат: {'УСПЕХ' if success else 'ОШИБКА'}") 
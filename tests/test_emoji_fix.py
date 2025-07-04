#!/usr/bin/env python3
"""
Тест исправления эмодзи
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.whatsapp_utils import add_flower_emoji

def test_emoji_fix():
    """Тестирует, что эмодзи добавляется правильно"""
    print("=== ТЕСТ ИСПРАВЛЕНИЯ ЭМОДЗИ ===")
    
    # Тест 1: Добавление эмодзи к тексту без эмодзи
    text1 = "Отлично! Я учла, что доставка не нужна."
    result1 = add_flower_emoji(text1)
    print(f"1. Исходный: '{text1}'")
    print(f"   Результат: '{result1}'")
    print(f"   Эмодзи добавлено: {'✅' if result1.endswith('🌸') else '❌'}")
    
    # Тест 2: Текст уже с эмодзи
    text2 = "Добрый день, Петр! 🌸"
    result2 = add_flower_emoji(text2)
    print(f"2. Исходный: '{text2}'")
    print(f"   Результат: '{result2}'")
    print(f"   Эмодзи НЕ дублировано: {'✅' if result2 == text2 else '❌'}")
    
    # Тест 3: Пустой текст
    text3 = ""
    result3 = add_flower_emoji(text3)
    print(f"3. Исходный: '{text3}'")
    print(f"   Результат: '{result3}'")
    print(f"   Правильная обработка: {'✅' if result3 == ' 🌸' else '❌'}")
    
    # Тест 4: Проверяем, что эмодзи именно 🌸, а не ��
    print(f"4. Символ эмодзи: '{result1[-1]}'")
    print(f"   Корректный символ: {'✅' if '🌸' in result1 and '��' not in result1 else '❌'}")
    
    print("\n=== РЕЗУЛЬТАТ ===")
    all_tests_passed = (
        result1.endswith('🌸') and
        result2 == text2 and
        '🌸' in result1 and
        '��' not in result1
    )
    print(f"Все тесты пройдены: {'✅' if all_tests_passed else '❌'}")
    
    return all_tests_passed

if __name__ == "__main__":
    test_emoji_fix() 
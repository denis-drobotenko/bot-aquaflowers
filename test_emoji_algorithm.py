#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест алгоритма добавления эмоджи 🌸 к сообщениям бота
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.whatsapp_client import WhatsAppClient

def test_emoji_algorithm():
    """Тестирует алгоритм добавления эмоджи 🌸"""
    client = WhatsAppClient()
    
    # Тест 1: Обычный текст без эмоджи
    text1 = "Здравствуйте! Чем могу помочь?"
    result1 = client._add_flower_emoji(text1)
    expected1 = "Здравствуйте! Чем могу помочь? 🌸"
    print(f"Тест 1: {text1}")
    print(f"Результат: {result1}")
    print(f"Ожидалось: {expected1}")
    print(f"✅ {'ПРОШЕЛ' if result1 == expected1 else 'НЕ ПРОШЕЛ'}")
    print()
    
    # Тест 2: Текст уже с эмоджи 🌸
    text2 = "Привет! 🌸"
    result2 = client._add_flower_emoji(text2)
    expected2 = "Привет! 🌸"
    print(f"Тест 2: {text2}")
    print(f"Результат: {result2}")
    print(f"Ожидалось: {expected2}")
    print(f"✅ {'ПРОШЕЛ' if result2 == expected2 else 'НЕ ПРОШЕЛ'}")
    print()
    
    # Тест 3: Текст с пробелами в конце
    text3 = "Добрый день!   "
    result3 = client._add_flower_emoji(text3)
    expected3 = "Добрый день! 🌸"
    print(f"Тест 3: {text3}")
    print(f"Результат: {result3}")
    print(f"Ожидалось: {expected3}")
    print(f"✅ {'ПРОШЕЛ' if result3 == expected3 else 'НЕ ПРОШЕЛ'}")
    print()
    
    # Тест 4: Пустой текст
    text4 = ""
    result4 = client._add_flower_emoji(text4)
    expected4 = "🌸"
    print(f"Тест 4: {text4}")
    print(f"Результат: {result4}")
    print(f"Ожидалось: {expected4}")
    print(f"✅ {'ПРОШЕЛ' if result4 == expected4 else 'НЕ ПРОШЕЛ'}")
    print()
    
    # Тест 5: Текст с другими эмоджи
    text5 = "Спасибо! 😊"
    result5 = client._add_flower_emoji(text5)
    expected5 = "Спасибо! 😊 🌸"
    print(f"Тест 5: {text5}")
    print(f"Результат: {result5}")
    print(f"Ожидалось: {expected5}")
    print(f"✅ {'ПРОШЕЛ' if result5 == expected5 else 'НЕ ПРОШЕЛ'}")
    print()

if __name__ == "__main__":
    print("🧪 Тестирование алгоритма добавления эмоджи 🌸")
    print("=" * 50)
    test_emoji_algorithm()
    print("=" * 50)
    print("✅ Тестирование завершено!") 
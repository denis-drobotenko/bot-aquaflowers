#!/usr/bin/env python3
"""
Тест конфигурации системы
"""

import sys
import os

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.config.settings import GEMINI_API_KEY, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, PROJECT_ID

def test_configuration():
    """Тест конфигурации системы"""
    print("=== ТЕСТ КОНФИГУРАЦИИ ===")
    
    # Тест 1: Критические переменные окружения
    critical_vars = {
        'GEMINI_API_KEY': GEMINI_API_KEY,
        'WHATSAPP_TOKEN': WHATSAPP_TOKEN,
        'WHATSAPP_PHONE_ID': WHATSAPP_PHONE_ID,
        'PROJECT_ID': PROJECT_ID
    }
    
    missing_vars = []
    for var_name, var_value in critical_vars.items():
        if not var_value:
            missing_vars.append(var_name)
            
    if not missing_vars:
        print("✅ Критические переменные - Все критические переменные настроены")
    else:
        print(f"❌ Критические переменные - Отсутствуют: {', '.join(missing_vars)}")
        return False
        
    # Тест 2: Проверка API ключей
    if len(GEMINI_API_KEY) > 20:
        print("✅ Gemini API ключ - API ключ корректной длины")
    else:
        print("❌ Gemini API ключ - API ключ слишком короткий")
        return False
        
    if len(WHATSAPP_TOKEN) > 50:
        print("✅ WhatsApp токен - Токен корректной длины")
    else:
        print("❌ WhatsApp токен - Токен слишком короткий")
        return False
        
    print("✅ Конфигурация прошла успешно!")
    return True

if __name__ == "__main__":
    success = test_configuration()
    if not success:
        sys.exit(1) 
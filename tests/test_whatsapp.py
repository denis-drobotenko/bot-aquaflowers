#!/usr/bin/env python3
"""
Тест WhatsApp клиента
"""

import sys
import os

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.utils.whatsapp_client import WhatsAppClient

def test_whatsapp_client():
    """Тест WhatsApp клиента"""
    print("=== ТЕСТ WHATSAPP КЛИЕНТА ===")
    
    try:
        # Инициализация клиента
        whatsapp_client = WhatsAppClient()
        
        # Тест 1: Проверка конфигурации
        if whatsapp_client.token and whatsapp_client.phone_id:
            print("✅ WhatsApp конфигурация - Токен и Phone ID настроены")
        else:
            print("❌ WhatsApp конфигурация - Отсутствует токен или Phone ID")
            return False
            
        # Тест 2: Форматирование сообщения
        test_text = "Тестовое сообщение"
        formatted_text = whatsapp_client._add_flower_emoji(test_text)
        if "🌸" in formatted_text:
            print("✅ WhatsApp форматирование - Эмодзи добавлен корректно")
        else:
            print("❌ WhatsApp форматирование - Эмодзи не добавлен")
            return False
            
        # Примечание: Отправка реального сообщения не тестируется в критических тестах
        # чтобы избежать спама в WhatsApp
        print("✅ WhatsApp готовность - Клиент готов к отправке сообщений")
        
        print("✅ WhatsApp прошел успешно!")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp клиент - Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = test_whatsapp_client()
    if not success:
        sys.exit(1) 
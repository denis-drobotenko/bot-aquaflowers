#!/usr/bin/env python3
"""
Простой тест LINE API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import config
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

def test_line_api():
    """Тестирует подключение к LINE API"""
    print("=== ТЕСТ LINE API ===")
    
    try:
        # Проверяем конфигурацию
        print(f"1. LINE_ACCESS_TOKEN: {'Есть' if config.LINE_ACCESS_TOKEN else 'НЕТ!'}")
        print(f"2. LINE_GROUP_ID: {config.LINE_GROUP_ID}")
        
        if not config.LINE_ACCESS_TOKEN:
            print("❌ LINE_ACCESS_TOKEN не настроен!")
            return False
            
        if not config.LINE_GROUP_ID:
            print("❌ LINE_GROUP_ID не настроен!")
            return False
        
        # Создаем API клиент
        line_bot_api = LineBotApi(config.LINE_ACCESS_TOKEN)
        print("3. LINE API клиент создан")
        
        # Пробуем отправить тестовое сообщение
        test_message = "🧪 Тестовое сообщение от AuraFlora Bot\nВремя: " + str(__import__('datetime').datetime.now())
        
        print("4. Отправляем тестовое сообщение...")
        line_bot_api.push_message(config.LINE_GROUP_ID, TextSendMessage(text=test_message))
        
        print("✅ Тестовое сообщение отправлено успешно!")
        return True
        
    except LineBotApiError as e:
        print(f"❌ LINE API ошибка: {e}")
        print(f"❌ Код ошибки: {e.status_code}")
        print(f"❌ Детали: {e.error.message}")
        return False
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_line_api() 
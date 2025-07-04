#!/usr/bin/env python3
"""
Отладочный тест отправки заказа в LINE
"""

import sys
import os
import pytest
import asyncio
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Включаем подробное логирование
logging.basicConfig(level=logging.DEBUG)

from src import database, session_manager, order_utils, config
from linebot import LineBotApi
from linebot.models import TextSendMessage

@pytest.mark.asyncio
async def test_line_sending_debug():
    """Тестирует отправку заказа в LINE с отладкой"""
    print("=== ОТЛАДОЧНЫЙ ТЕСТ ОТПРАВКИ В LINE ===")
    
    sender_id = "test_user_line_debug"
    
    # Тест 1: Создаем сессию и добавляем сообщения
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Сессия: {session_id}")
    
    # Добавляем несколько сообщений в историю
    database.add_message(sender_id, session_id, "user", "Привет!")
    database.add_message(sender_id, session_id, "model", "Здравствуйте! Чем могу помочь?")
    database.add_message(sender_id, session_id, "user", "Хочу заказать букет Good vibes")
    database.add_message(sender_id, session_id, "model", "Отлично! Выберите дату доставки")
    
    # Тест 2: Создаем данные заказа
    order_data = {
        'bouquet': 'Good vibes 🌸',
        'date': '05 July 2025',
        'time': '10:00',
        'delivery_needed': False,
        'address': None,
        'card_needed': False,
        'card_text': None,
        'recipient_name': 'Петр',
        'recipient_phone': '3543585834',
        'retailer_id': 'rldxcifo_goodvibes'
    }
    
    print(f"2. Данные заказа: {order_data}")
    
    # Тест 3: Проверяем конфигурацию LINE
    print("3. Проверяем конфигурацию LINE...")
    print(f"   LINE_ACCESS_TOKEN: {'Есть' if config.LINE_ACCESS_TOKEN else 'НЕТ!'}")
    print(f"   LINE_GROUP_ID: {config.LINE_GROUP_ID}")
    
    # Тест 4: Пробуем отправить напрямую через LINE API
    print("4. Тестируем прямое подключение к LINE API...")
    try:
        line_bot_api = LineBotApi(config.LINE_ACCESS_TOKEN)
        test_message = "🔍 Отладочное сообщение от AuraFlora Bot\nТест прямой отправки"
        line_bot_api.push_message(config.LINE_GROUP_ID, TextSendMessage(text=test_message))
        print("   ✅ Прямая отправка работает!")
    except Exception as e:
        print(f"   ❌ Ошибка прямой отправки: {e}")
        return False
    
    # Тест 5: Отправляем заказ в LINE через функцию
    print("5. Отправляем заказ в LINE через функцию...")
    try:
        result = await order_utils.send_order_to_line(sender_id, session_id, order_data)
        print(f"   ✅ Результат отправки: {result}")
        
        if "Ошибка" in result:
            print(f"   ❌ Ошибка отправки: {result}")
            return False
        else:
            print(f"   ✅ Заказ успешно отправлен в LINE!")
            return True
            
    except Exception as e:
        print(f"   ❌ Исключение при отправке: {e}")
        import traceback
        print(f"   ❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_line_sending_debug()) 
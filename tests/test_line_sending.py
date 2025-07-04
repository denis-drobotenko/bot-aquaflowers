#!/usr/bin/env python3
"""
Тест отправки заказа в LINE
"""

import sys
import os
import pytest
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, order_utils

@pytest.mark.asyncio
async def test_line_sending():
    """Тестирует отправку заказа в LINE"""
    print("=== ТЕСТ ОТПРАВКИ В LINE ===")
    
    sender_id = "test_user_line_sending"
    
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
    
    # Тест 3: Отправляем заказ в LINE
    print("3. Отправляем заказ в LINE...")
    try:
        result = await order_utils.send_order_to_line(sender_id, session_id, order_data)
        print(f"✅ Результат отправки: {result}")
        
        if "Ошибка" in result:
            print(f"❌ Ошибка отправки: {result}")
            return False
        else:
            print(f"✅ Заказ успешно отправлен в LINE!")
            return True
            
    except Exception as e:
        print(f"❌ Исключение при отправке: {e}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_line_sending()) 
#!/usr/bin/env python3
"""
Тест исправления дублирования сообщений при подтверждении заказа
"""

import sys
import os
import pytest
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, command_handler, order_utils

@pytest.mark.asyncio
async def test_order_duplication_fix():
    """Тестирует исправление дублирования сообщений при подтверждении заказа"""
    print("=== ТЕСТ ИСПРАВЛЕНИЯ ДУБЛИРОВАНИЯ ===")
    
    sender_id = "test_user_duplication_fix"
    
    # Тест 1: Создаем сессию и добавляем данные заказа
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Сессия: {session_id}")
    
    # Добавляем данные заказа в историю
    order_data = {
        'bouquet': 'Test Bouquet 🌸',
        'date': '2025-07-05',
        'time': '14:00',
        'delivery_needed': True,
        'address': 'Test Address, Phuket',
        'card_needed': True,
        'card_text': 'Test card text',
        'recipient_name': 'Test Recipient',
        'recipient_phone': '+79123456789',
        'retailer_id': 'test_retailer_id'
    }
    
    # Сохраняем данные заказа в истории
    for key, value in order_data.items():
        database.add_message(sender_id, session_id, "system", f"[SAVED: {key}={value}]")
    
    print("✅ Данные заказа добавлены в историю")
    
    # Тест 2: Мокаем отправку сообщений WhatsApp и LINE
    sent_messages = []
    sent_line = []
    
    async def fake_send_message(to, msg, sender_id=None, session_id=None):
        sent_messages.append({
            'to': to,
            'message': msg,
            'sender_id': sender_id,
            'session_id': session_id
        })
        return True
    
    class FakeLineBotApi:
        def push_message(self, group_id, text_message):
            sent_line.append({'group_id': group_id, 'text': text_message.text})
    
    # Подменяем функции
    import src.order_utils as order_utils
    import src.whatsapp_utils as whatsapp_utils
    original_send = whatsapp_utils.send_whatsapp_message
    original_line_api = order_utils.line_bot_api
    whatsapp_utils.send_whatsapp_message = fake_send_message
    order_utils.line_bot_api = FakeLineBotApi()
    
    try:
        # Тест 3: Имитируем команду confirm_order с данными
        print("3. Имитируем команду confirm_order с данными")
        command = {
            'type': 'confirm_order',
            'bouquet': 'Test Bouquet 🌸',
            'date': '2025-07-05',
            'time': '14:00',
            'delivery_needed': True,
            'address': 'Test Address, Phuket',
            'card_needed': True,
            'card_text': 'Test card text',
            'recipient_name': 'Test Recipient',
            'recipient_phone': '+79123456789',
            'retailer_id': 'test_retailer_id'
        }
        
        # Выполняем команду подтверждения заказа
        result = await command_handler.handle_confirm_order(sender_id, session_id, command)
        
        # Проверяем результаты
        print(f"4. Результат выполнения команды: {result}")
        
        # Проверяем, что команда выполнилась успешно
        assert result['status'] == 'success', f"Команда должна выполниться успешно, но получили: {result['status']}"
        assert result['action'] == 'order_confirmed', f"Действие должно быть 'order_confirmed', но получили: {result['action']}"
        
        # Проверяем, что пользователю отправлено РОВНО ОДНО сообщение
        assert len(sent_messages) == 1, f"Должно быть отправлено 1 сообщение пользователю, а не {len(sent_messages)}"
        assert sent_messages[0]['message'].strip().endswith('🌸'), "Сообщение пользователю должно заканчиваться на 🌸"
        assert "Ваш заказ отправлен!" in sent_messages[0]['message'], "Сообщение должно содержать текст о том, что заказ отправлен"
        
        # Проверяем, что в LINE отправлено РОВНО ОДНО сообщение
        assert len(sent_line) == 1, f"В LINE должно быть отправлено 1 сообщение, а не {len(sent_line)}"
        assert 'NEW ORDER CONFIRMED!' in sent_line[0]['text'], "Должно быть сообщение на английском"
        assert 'คำสั่งซื้อใหม่ได้รับการยืนยัน!' in sent_line[0]['text'], "Должно быть сообщение на тайском"
        assert '🌸' not in sent_line[0]['text'], "В сообщении для LINE не должно быть эмодзи 🌸"
        
        # Проверяем, что создалась новая сессия
        new_session_id = result.get('new_session_id')
        assert new_session_id, "Должна создаться новая сессия"
        assert new_session_id != session_id, "Новая сессия должна отличаться от старой"
        
        print("✅ Все проверки пройдены успешно!")
        
    finally:
        # Восстанавливаем оригинальные функции
        whatsapp_utils.send_whatsapp_message = original_send
        order_utils.line_bot_api = original_line_api
    
    print("\n=== ТЕСТ ИСПРАВЛЕНИЯ ДУБЛИРОВАНИЯ ЗАВЕРШЕН ===")

if __name__ == "__main__":
    asyncio.run(test_order_duplication_fix()) 
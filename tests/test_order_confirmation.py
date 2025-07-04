#!/usr/bin/env python3
"""
Тест процесса подтверждения заказа
"""

import sys
import os
import pytest
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager, command_handler, whatsapp_utils

@pytest.mark.asyncio
async def test_order_confirmation():
    """Тестирует процесс подтверждения заказа"""
    print("=== ТЕСТ ПОДТВЕРЖДЕНИЯ ЗАКАЗА ===")
    
    sender_id = "test_user_order_confirmation"
    
    # Тест 1: Создаем сессию и добавляем данные заказа
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"1. Сессия: {session_id}")
    
    # Добавляем данные заказа в историю
    order_data = {
        'bouquet': 'Spirit 🌸',
        'date': '2025-07-05',
        'time': '14:00',
        'delivery_needed': True,
        'address': 'Test Address, Phuket',
        'card_needed': True,
        'card_text': 'С любовью!',
        'recipient_name': 'Test Recipient',
        'recipient_phone': '+79123456789',
        'retailer_id': 'test_retailer_id'
    }
    
    # Сохраняем данные заказа в истории
    for key, value in order_data.items():
        database.add_message(sender_id, session_id, "system", f"[SAVED: {key}={value}]")
    
    print("✅ Данные заказа добавлены в историю")
    
    # Тест 2: Имитируем команду подтверждения заказа
    print("2. Имитируем команду подтверждения заказа")
    
    # Мокаем отправку сообщений WhatsApp и LINE
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
        # Имитируем команду confirm_order
        command = {
            'type': 'confirm_order',
            'order_summary': 'Заказ подтвержден и передан в обработку! 🌸'
        }
        # Выполняем команду подтверждения заказа
        result = await command_handler.handle_confirm_order(sender_id, session_id, command)
        # Проверяем, что команда выполнилась успешно
        assert result['status'] == 'success', f"Команда должна выполниться успешно, но получили: {result['status']}"
        assert result['action'] == 'order_confirmed', f"Действие должно быть 'order_confirmed', но получили: {result['action']}"
        # Проверяем, что создалась новая сессия
        new_session_id = result.get('new_session_id')
        assert new_session_id, "Должна создаться новая сессия"
        assert new_session_id != session_id, "Новая сессия должна отличаться от старой"
        # Проверяем, что новая сессия пустая
        new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
        assert len(new_history) == 0, f"Новая сессия должна быть пустой, но содержит {len(new_history)} сообщений"
        # Проверяем, что новая сессия стала активной
        current_session = session_manager.get_or_create_session_id(sender_id)
        assert current_session == new_session_id, f"Новая сессия должна стать активной, но активна {current_session}"
        # Проверяем, что старая сессия осталась нетронутой
        old_history = database.get_conversation_history_for_ai(sender_id, session_id)
        assert len(old_history) >= len(order_data), f"Старая сессия должна сохраниться, но содержит {len(old_history)} сообщений"
        # Проверяем, что пользователю отправлено ОДНО сообщение с 🌸
        assert len(sent_messages) == 1, f"Должно быть отправлено 1 сообщение пользователю, а не {len(sent_messages)}"
        assert sent_messages[0]['message'].strip().endswith('🌸'), "Сообщение пользователю должно заканчиваться на 🌸"
        # Проверяем, что в LINE отправлено одно сообщение с данными заказа
        assert len(sent_line) == 1, f"В LINE должно быть отправлено 1 сообщение, а не {len(sent_line)}"
        assert '🌸' not in sent_line[0]['text'], "В сообщении для LINE не должно быть эмодзи 🌸"
        assert 'NEW ORDER CONFIRMED!' in sent_line[0]['text'], "Должно быть сообщение на английском"
        assert 'คำสั่งซื้อใหม่ได้รับการยืนยัน!' in sent_line[0]['text'], "Должно быть сообщение на тайском"
    finally:
        whatsapp_utils.send_whatsapp_message = original_send
        order_utils.line_bot_api = original_line_api
    
    print("\n=== ВСЕ ТЕСТЫ ПОДТВЕРЖДЕНИЯ ЗАКАЗА ПРОЙДЕНЫ ===")

if __name__ == "__main__":
    asyncio.run(test_order_confirmation()) 
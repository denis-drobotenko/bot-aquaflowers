#!/usr/bin/env python3
"""
Простой тест: добавить сообщение через транзакцию, потом получить историю обычным чтением.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.repositories.message_repository import MessageRepository
from src.models.message import Message, MessageRole
from datetime import datetime
import time

def test_add_and_read():
    print("🧪 ПРОСТОЙ ТЕСТ: добавить и сразу прочитать историю...")
    repo = MessageRepository()
    sender_id = "79140775712"
    session_id = "test_session_simple_123"
    msg = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.USER,
        content="Проверка простого теста",
        timestamp=datetime.now().isoformat(),
        content_en="Simple test message",
        content_thai="ข้อความทดสอบง่ายๆ",
        wa_message_id="wamid.test_simple_1"
    )
    print(f"➡️ Добавляем: {msg.content}")
    success, _ = repo.add_message_with_transaction_sync(msg, limit=10)
    if not success:
        print("❌ Ошибка при добавлении!")
        return
    print("✅ Сообщение добавлено через транзакцию!")
    time.sleep(1)  # Firestore может быть не мгновенным
    print("🔎 Читаем историю обычным способом...")
    history = repo.get_conversation_history_by_sender(sender_id, session_id, limit=10)
    if hasattr(history, '__await__'):
        # если это корутина (async def), то нужно запустить через event loop
        import asyncio
        history = asyncio.get_event_loop().run_until_complete(history)
    print(f"📋 История сообщений: {len(history)}")
    for i, h in enumerate(history, 1):
        print(f"  {i}. [{h.get('role', 'unknown')}] {h.get('content', '')}")
    if any(h.get('content') == msg.content for h in history):
        print("🎉 Новый месседж есть в истории!")
    else:
        print("❌ Новый месседж НЕ найден в истории!")

if __name__ == "__main__":
    test_add_and_read() 
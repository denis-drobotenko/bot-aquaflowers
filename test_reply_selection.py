#!/usr/bin/env python3
"""
Тест обработки reply с выбором букета
"""

import asyncio
import sys
import os
sys.path.append('.')

from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_reply_selection():
    """Тестирует обработку reply с выбором букета"""
    
    # Инициализируем AI сервис
    ai_service = AIService(GEMINI_API_KEY)
    
    # Создаем историю диалога с reply
    messages = [
        Message(
            role=MessageRole.ASSISTANT,
            content="Отлично! Сейчас покажу вам каждый букет с фото! Подождите немного...",
            timestamp="2025-07-05T04:31:40"
        ),
        Message(
            role=MessageRole.ASSISTANT,
            content="Pretty 😍 - 2 600,00 ฿",
            timestamp="2025-07-05T04:31:45"
        ),
        Message(
            role=MessageRole.USER,
            content="да (ответ на: Pretty 😍 - 2 600,00 ฿)",
            timestamp="2025-07-05T04:32:00"
        )
    ]
    
    print("=== Тест обработки reply с выбором букета ===")
    print(f"История диалога:")
    for i, msg in enumerate(messages):
        print(f"{i+1}. [{msg.role.value}] {msg.content}")
    
    print("\n=== Ответ AI ===")
    
    # Генерируем ответ
    response, response_en, response_thai, command = await ai_service.generate_response(
        messages, user_lang='ru', sender_name="Test User"
    )
    
    print(f"Ответ: {response}")
    print(f"Команда: {command}")
    
    if command and command.get('type') == 'save_order_info':
        print(f"✅ Букет сохранен: {command.get('bouquet')}")
        print(f"✅ Retailer ID: {command.get('retailer_id')}")
    else:
        print("❌ Букет НЕ был сохранен")

if __name__ == "__main__":
    asyncio.run(test_reply_selection()) 
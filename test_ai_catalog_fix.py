#!/usr/bin/env python3
"""
Тест исправления AI - проверяем, что AI отдает команду send_catalog
"""

import asyncio
import json
from src.services.ai_service import AIService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

async def test_ai_catalog_command():
    """Тестирует, что AI отдает команду send_catalog при запросе каталога"""
    print("=== ТЕСТ AI КОМАНДЫ SEND_CATALOG ===")
    
    # Создаем AI сервис
    ai_service = AIService(GEMINI_API_KEY)
    
    # Создаем историю диалога с запросом каталога
    messages = [
        Message(
            role=MessageRole.USER,
            content="Отправь каталог",
            timestamp="2025-01-05T18:45:00Z",
            sender_id="test_user_123",
            session_id="test_session_123"
        )
    ]
    
    print("Отправляем запрос каталога в AI...")
    text, text_en, text_thai, command = await ai_service.generate_response(
        messages, user_lang='ru', sender_name='Test User'
    )
    
    print(f"Ответ AI: {text}")
    print(f"Команда: {json.dumps(command, indent=2, ensure_ascii=False) if command else 'None'}")
    
    if command and command.get('type') == 'send_catalog':
        print("✅ AI правильно отдал команду send_catalog!")
    else:
        print("❌ AI НЕ отдал команду send_catalog!")
        print(f"Ожидалось: {{'type': 'send_catalog'}}")
        print(f"Получено: {command}")

if __name__ == "__main__":
    asyncio.run(test_ai_catalog_command()) 
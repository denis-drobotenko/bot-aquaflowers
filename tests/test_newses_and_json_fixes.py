#!/usr/bin/env python3
"""
Тест команды /newses и исправлений парсинга JSON
"""

import sys
import os
import pytest
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.ai_service import AIService
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY

@pytest.mark.asyncio
async def test_newses_command():
    """Тестирует команду /newses"""
    print("=== ТЕСТ КОМАНДЫ /NEWSES ===")
    
    session_service = SessionService()
    message_service = MessageService()
    
    sender_id = "test_user_newses_fix"
    
    # Тест 1: Создаем начальную сессию
    initial_session_id = await session_service.get_or_create_session_id(sender_id)
    print(f"1. Начальная сессия: {initial_session_id}")
    
    # Тест 2: Добавляем сообщения в начальную сессию
    print("2. Добавляем сообщения в начальную сессию")
    
    user_message = Message(
        sender_id=sender_id,
        session_id=initial_session_id,
        role=MessageRole.USER,
        content="Привет! Хочу заказать букет."
    )
    await message_service.add_message_to_conversation(user_message)
    
    ai_message = Message(
        sender_id=sender_id,
        session_id=initial_session_id,
        role=MessageRole.ASSISTANT,
        content="Здравствуйте! Чем могу помочь?"
    )
    await message_service.add_message_to_conversation(ai_message)
    
    # Проверяем, что сообщения сохранились
    history = await message_service.get_conversation_history_for_ai(initial_session_id, limit=10)
    assert len(history) >= 2, f"Ожидалось минимум 2 сообщения, получено {len(history)}"
    print(f"✅ В начальной сессии {len(history)} сообщений")
    
    # Тест 3: Создаем новую сессию через команду /newses
    print("3. Создаем новую сессию через команду /newses")
    new_session_id = await session_service.create_new_session_after_order(sender_id)
    print(f"Новая сессия: {new_session_id}")
    
    # Проверяем, что новая сессия отличается от старой
    assert new_session_id != initial_session_id, "Новая сессия должна отличаться от старой"
    print("✅ Новая сессия отличается от старой")
    
    # Тест 4: Проверяем, что в новой сессии нет сообщений
    new_history = await message_service.get_conversation_history_for_ai(new_session_id, limit=10)
    assert len(new_history) == 0, f"Новая сессия должна быть пустой, но содержит {len(new_history)} сообщений"
    print("✅ Новая сессия пустая")
    
    # Тест 5: Проверяем, что старая сессия осталась нетронутой
    old_history = await message_service.get_conversation_history_for_ai(initial_session_id, limit=10)
    assert len(old_history) >= 2, f"Старая сессия должна содержать минимум 2 сообщения, но содержит {len(old_history)}"
    print("✅ Старая сессия осталась нетронутой")
    
    # Тест 6: Проверяем, что новая сессия стала активной
    current_session_id = await session_service.get_or_create_session_id(sender_id)
    assert current_session_id == new_session_id, f"Новая сессия должна быть активной, но активна {current_session_id}"
    print("✅ Новая сессия стала активной")
    
    # Тест 7: Проверяем, что команда /newses не сохраняет ответ AI в БД
    print("4. Проверяем, что команда /newses не сохраняет ответ AI в БД")
    
    # Имитируем обработку команды /newses
    from src.main import process_text_message
    
    # Мокаем отправку сообщений
    sent_messages = []
    async def fake_send_message(to, msg):
        sent_messages.append({'to': to, 'message': msg})
        return "fake_message_id"
    
    # Подменяем функцию отправки
    import src.utils.whatsapp_client as whatsapp_client
    original_send = whatsapp_client.send_text_message
    whatsapp_client.send_text_message = fake_send_message
    
    try:
        # Обрабатываем команду /newses
        response = await process_text_message(sender_id, "/newses", "TestUser")
        
        # Проверяем, что ответ содержит информацию о новой сессии
        assert "Новая сессия создана" in response, f"Ответ должен содержать информацию о новой сессии: {response}"
        assert "🌸" in response, f"Ответ должен содержать эмодзи: {response}"
        
        # Проверяем, что в новой сессии нет сообщений от AI
        current_session = await session_service.get_or_create_session_id(sender_id)
        new_history_after = await message_service.get_conversation_history_for_ai(current_session, limit=10)
        assert len(new_history_after) == 0, f"Новая сессия должна быть пустой после команды /newses, но содержит {len(new_history_after)} сообщений"
        
        print("✅ Команда /newses работает правильно - ответ AI не сохраняется в БД")
        
    finally:
        # Восстанавливаем оригинальную функцию
        whatsapp_client.send_text_message = original_send
    
    print("\n=== ТЕСТ КОМАНДЫ /NEWSES ПРОЙДЕН ===")

@pytest.mark.asyncio
async def test_json_parsing_fixes():
    """Тестирует исправления парсинга JSON от AI"""
    print("=== ТЕСТ ИСПРАВЛЕНИЙ ПАРСИНГА JSON ===")
    
    ai_service = AIService(GEMINI_API_KEY)
    
    # Тест 1: Корректный JSON
    print("1. Тестируем корректный JSON")
    correct_json = '''```json
{
  "text": "Здравствуйте! Хотите посмотреть наш каталог цветов?",
  "text_en": "Hello! Would you like to see our flower catalog?",
  "text_thai": "สวัสดี! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?",
  "command": null
}
```'''
    
    text, text_en, text_thai, command = ai_service.parse_ai_response(correct_json)
    
    assert text == "Здравствуйте! Хотите посмотреть наш каталог цветов?", f"Неверный text: {text}"
    assert text_en == "Hello! Would you like to see our flower catalog?", f"Неверный text_en: {text_en}"
    assert text_thai == "สวัสดี! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?", f"Неверный text_thai: {text_thai}"
    assert command is None, f"Неверный command: {command}"
    print("✅ Корректный JSON обработан правильно")
    
    # Тест 2: JSON с командой
    print("2. Тестируем JSON с командой")
    json_with_command = '''```json
{
  "text": "Отправляю каталог!",
  "text_en": "Sending catalog!",
  "text_thai": "ส่งแคตตาล็อก!",
  "command": {
    "type": "send_catalog"
  }
}
```'''
    
    text, text_en, text_thai, command = ai_service.parse_ai_response(json_with_command)
    
    assert text == "Отправляю каталог!", f"Неверный text: {text}"
    assert command is not None, "Command должен быть не None"
    assert command.get('type') == 'send_catalog', f"Неверный тип команды: {command}"
    print("✅ JSON с командой обработан правильно")
    
    # Тест 3: JSON без markdown
    print("3. Тестируем JSON без markdown")
    json_without_markdown = '''{
  "text": "Простой ответ",
  "text_en": "Simple answer",
  "text_thai": "คำตอบง่ายๆ"
}'''
    
    text, text_en, text_thai, command = ai_service.parse_ai_response(json_without_markdown)
    
    assert text == "Простой ответ", f"Неверный text: {text}"
    assert text_en == "Simple answer", f"Неверный text_en: {text_en}"
    assert text_thai == "คำตอบง่ายๆ", f"Неверный text_thai: {text_thai}"
    print("✅ JSON без markdown обработан правильно")
    
    # Тест 4: Некорректный JSON
    print("4. Тестируем некорректный JSON")
    invalid_json = "Это не JSON"
    
    text, text_en, text_thai, command = ai_service.parse_ai_response(invalid_json)
    
    assert text == invalid_json, f"При некорректном JSON должен возвращаться исходный текст: {text}"
    assert text_en == invalid_json, f"При некорректном JSON должен возвращаться исходный текст: {text_en}"
    assert text_thai == invalid_json, f"При некорректном JSON должен возвращаться исходный текст: {text_thai}"
    assert command is None, f"При некорректном JSON command должен быть None: {command}"
    print("✅ Некорректный JSON обработан правильно")
    
    # Тест 5: Пустой JSON
    print("5. Тестируем пустой JSON")
    empty_json = '''```json
{
  "text": "",
  "text_en": "",
  "text_thai": ""
}
```'''
    
    text, text_en, text_thai, command = ai_service.parse_ai_response(empty_json)
    
    assert text == empty_json, f"При пустом text должен возвращаться исходный текст: {text}"
    print("✅ Пустой JSON обработан правильно")
    
    print("\n=== ТЕСТ ИСПРАВЛЕНИЙ ПАРСИНГА JSON ПРОЙДЕН ===")

@pytest.mark.asyncio
async def test_conversation_structure():
    """Тестирует правильную структуру conversations"""
    print("=== ТЕСТ СТРУКТУРЫ CONVERSATIONS ===")
    
    message_service = MessageService()
    session_service = SessionService()
    
    sender_id = "test_user_conversation_structure"
    
    # Создаем сессию
    session_id = await session_service.get_or_create_session_id(sender_id)
    print(f"1. Создана сессия: {session_id}")
    
    # Добавляем сообщения в правильную структуру
    print("2. Добавляем сообщения в conversations")
    
    user_message = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.USER,
        content="Тестовое сообщение пользователя",
        content_en="Test user message",
        content_thai="ข้อความทดสอบของผู้ใช้"
    )
    
    result = await message_service.add_message_to_conversation(user_message)
    assert result == "success", f"Ошибка добавления сообщения: {result}"
    print("✅ Сообщение пользователя добавлено")
    
    ai_message = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content="Тестовый ответ AI",
        content_en="Test AI response",
        content_thai="การตอบสนอง AI ทดสอบ"
    )
    
    result = await message_service.add_message_to_conversation(ai_message)
    assert result == "success", f"Ошибка добавления сообщения AI: {result}"
    print("✅ Сообщение AI добавлено")
    
    # Получаем историю
    history = await message_service.get_conversation_history_for_ai(session_id, limit=10)
    assert len(history) == 2, f"Ожидалось 2 сообщения, получено {len(history)}"
    
    # Проверяем структуру истории
    assert history[0]['role'] == 'user', f"Первое сообщение должно быть от пользователя: {history[0]}"
    assert history[0]['content'] == "Тестовое сообщение пользователя", f"Неверное содержимое первого сообщения: {history[0]}"
    
    assert history[1]['role'] == 'assistant', f"Второе сообщение должно быть от AI: {history[1]}"
    assert history[1]['content'] == "Тестовый ответ AI", f"Неверное содержимое второго сообщения: {history[1]}"
    
    print("✅ Структура conversations работает правильно")
    print("\n=== ТЕСТ СТРУКТУРЫ CONVERSATIONS ПРОЙДЕН ===")

if __name__ == "__main__":
    asyncio.run(test_newses_command())
    asyncio.run(test_json_parsing_fixes())
    asyncio.run(test_conversation_structure()) 
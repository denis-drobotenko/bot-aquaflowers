#!/usr/bin/env python3
"""
Тест объединенной коллекции users
"""

import sys
import os
import pytest
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.session_service import SessionService
from src.services.message_service import MessageService
from src.models.message import Message, MessageRole

@pytest.mark.asyncio
async def test_unified_users_collection():
    """Тестирует объединенную коллекцию users"""
    print("=== ТЕСТ ОБЪЕДИНЕННОЙ КОЛЛЕКЦИИ USERS ===")
    
    session_service = SessionService()
    message_service = MessageService()
    
    sender_id = "test_user_unified"
    user_name = "Тестовый Пользователь"
    
    # Тест 1: Создаем сессию и сохраняем имя пользователя
    print("1. Создаем сессию и сохраняем имя пользователя")
    
    session_id = await session_service.get_or_create_session_id(sender_id)
    print(f"   Создана сессия: {session_id}")
    
    # Сохраняем имя пользователя
    await session_service.save_user_info(sender_id, user_name)
    print(f"   Сохранено имя: {user_name}")
    
    # Тест 2: Получаем информацию о пользователе
    print("2. Получаем информацию о пользователе")
    
    user_info = await session_service.get_user_info(sender_id)
    print(f"   Получена информация: {user_info}")
    
    assert user_info.get('name') == user_name, f"Имя пользователя не совпадает: {user_info}"
    assert user_info.get('session_id') == session_id, f"ID сессии не совпадает: {user_info}"
    print("✅ Информация о пользователе получена правильно")
    
    # Тест 3: Создаем новую сессию и проверяем обновление
    print("3. Создаем новую сессию и проверяем обновление")
    
    new_session_id = await session_service.create_new_session_after_order(sender_id)
    print(f"   Новая сессия: {new_session_id}")
    
    # Проверяем, что информация обновилась
    updated_user_info = await session_service.get_user_info(sender_id)
    print(f"   Обновленная информация: {updated_user_info}")
    
    assert updated_user_info.get('name') == user_name, f"Имя пользователя должно сохраниться: {updated_user_info}"
    assert updated_user_info.get('session_id') == new_session_id, f"ID сессии должен обновиться: {updated_user_info}"
    print("✅ Информация о пользователе обновилась правильно")
    
    # Тест 4: Проверяем, что имя сохраняется при создании сессии
    print("4. Проверяем сохранение имени при создании сессии")
    
    another_sender_id = "test_user_unified_2"
    another_user_name = "Другой Пользователь"
    
    # Создаем сессию с именем
    await session_service._save_to_users(another_sender_id, "test_session", another_user_name)
    
    # Получаем информацию
    another_user_info = await session_service.get_user_info(another_sender_id)
    print(f"   Информация о другом пользователе: {another_user_info}")
    
    assert another_user_info.get('name') == another_user_name, f"Имя должно сохраниться: {another_user_info}"
    assert another_user_info.get('session_id') == "test_session", f"ID сессии должен сохраниться: {another_user_info}"
    print("✅ Имя сохраняется при создании сессии")
    
    # Тест 5: Проверяем работу с сообщениями
    print("5. Проверяем работу с сообщениями")
    
    # Добавляем сообщение
    message = Message(
        sender_id=sender_id,
        session_id=new_session_id,
        role=MessageRole.USER,
        content="Тестовое сообщение"
    )
    
    result = await message_service.add_message_to_conversation(message)
    assert result == "success", f"Ошибка добавления сообщения: {result}"
    print("✅ Сообщение добавлено")
    
    # Получаем историю
    history = await message_service.get_conversation_history_for_ai_by_sender(sender_id, new_session_id, limit=10)
    assert len(history) == 1, f"Ожидалось 1 сообщение, получено {len(history)}"
    print("✅ История получена правильно")
    
    print("\n=== ТЕСТ ОБЪЕДИНЕННОЙ КОЛЛЕКЦИИ USERS ПРОЙДЕН ===")

@pytest.mark.asyncio
async def test_user_info_persistence():
    """Тестирует сохранение информации о пользователе"""
    print("=== ТЕСТ СОХРАНЕНИЯ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ ===")
    
    session_service = SessionService()
    
    sender_id = "test_user_persistence"
    user_name = "Постоянный Пользователь"
    
    # Тест 1: Сохраняем только имя
    print("1. Сохраняем только имя пользователя")
    
    await session_service.save_user_info(sender_id, user_name)
    
    user_info = await session_service.get_user_info(sender_id)
    assert user_info.get('name') == user_name, f"Имя не сохранилось: {user_info}"
    assert 'session_id' not in user_info, f"ID сессии не должен быть: {user_info}"
    print("✅ Имя сохранено без ID сессии")
    
    # Тест 2: Создаем сессию
    print("2. Создаем сессию")
    
    session_id = await session_service.get_or_create_session_id(sender_id)
    
    user_info_after = await session_service.get_user_info(sender_id)
    assert user_info_after.get('name') == user_name, f"Имя должно сохраниться: {user_info_after}"
    assert user_info_after.get('session_id') == session_id, f"ID сессии должен добавиться: {user_info_after}"
    print("✅ ID сессии добавлен, имя сохранено")
    
    # Тест 3: Обновляем имя
    print("3. Обновляем имя пользователя")
    
    new_name = "Обновленный Пользователь"
    await session_service.save_user_info(sender_id, new_name)
    
    user_info_updated = await session_service.get_user_info(sender_id)
    assert user_info_updated.get('name') == new_name, f"Имя должно обновиться: {user_info_updated}"
    assert user_info_updated.get('session_id') == session_id, f"ID сессии должен сохраниться: {user_info_updated}"
    print("✅ Имя обновлено, ID сессии сохранен")
    
    print("\n=== ТЕСТ СОХРАНЕНИЯ ИНФОРМАЦИИ О ПОЛЬЗОВАТЕЛЕ ПРОЙДЕН ===")

if __name__ == "__main__":
    asyncio.run(test_unified_users_collection())
    asyncio.run(test_user_info_persistence()) 
#!/usr/bin/env python3
"""
Тест базы данных
"""

import sys
import os
import time

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.models.message import Message, MessageRole

async def test_database_operations():
    """Тест операций с базой данных"""
    print("=== ТЕСТ БАЗЫ ДАННЫХ ===")
    
    try:
        # Инициализация сервисов
        message_service = MessageService()
        session_service = SessionService()
        
        # Тест 1: Создание сессии
        test_sender_id = f"test_user_{int(time.time())}"
        session_id = await session_service.get_or_create_session_id(test_sender_id)
        
        if session_id:
            print(f"✅ БД создание сессии - Создана сессия: {session_id}")
        else:
            print("❌ БД создание сессии - Сессия не создана")
            return False
            
        # Тест 2: Сохранение сообщения
        test_message = Message(
            sender_id=test_sender_id,
            session_id=session_id,
            role=MessageRole.USER,
            content="Тестовое сообщение"
        )
        
        message_id = await message_service.add_message(test_message)
        if message_id:
            print(f"✅ БД сохранение сообщения - Сообщение сохранено с ID: {message_id}")
        else:
            print("❌ БД сохранение сообщения - Сообщение не сохранено")
            return False
            
        # Тест 3: Получение истории
        history = await message_service.get_conversation_history(session_id, limit=10)
        if history and len(history) > 0:
            print(f"✅ БД получение истории - Получено {len(history)} сообщений")
        else:
            print("❌ БД получение истории - История не получена")
            return False
            
        print("✅ База данных прошла успешно!")
        return True
        
    except Exception as e:
        print(f"❌ БД операции - Ошибка: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_database_operations())
    if not success:
        sys.exit(1) 
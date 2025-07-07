#!/usr/bin/env python3
"""
Тестовый скрипт для проверки пользователей в БД
"""

import asyncio
from src.repositories.user_repository import UserRepository
from src.repositories.message_repository import MessageRepository

async def test_users():
    print("🔍 Проверка пользователей в БД...")
    
    # Тест пользователей
    print("\n1. Тест пользователей...")
    try:
        repo = UserRepository()
        users = await repo.get_all_users()
        print(f"✅ Пользователей в БД: {len(users)}")
        
        if users:
            print("📋 Примеры пользователей:")
            for i, user in enumerate(users[:3]):
                print(f"  {i+1}. ID: {user.user_id}, Имя: {user.name}, Телефон: {user.phone}")
        else:
            print("⚠️ Пользователей в БД нет")
            
    except Exception as e:
        print(f"❌ Ошибка пользователей: {e}")
    
    # Тест сообщений
    print("\n2. Тест сообщений...")
    try:
        repo = MessageRepository()
        messages = await repo.get_all_messages()
        print(f"✅ Сообщений в БД: {len(messages)}")
        
        if messages:
            print("📋 Примеры сообщений:")
            for i, msg in enumerate(messages[:3]):
                print(f"  {i+1}. От: {msg.sender_id}, Текст: {msg.text[:50]}...")
        else:
            print("⚠️ Сообщений в БД нет")
            
    except Exception as e:
        print(f"❌ Ошибка сообщений: {e}")

if __name__ == "__main__":
    asyncio.run(test_users()) 
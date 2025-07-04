#!/usr/bin/env python3
"""
Скрипт для поиска сессии 20250703_201756_765601_479 в коллекции conversations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database

def search_conversations():
    """Ищет сессию в коллекции conversations"""
    print("=== ПОИСК СЕССИИ В КОЛЛЕКЦИИ CONVERSATIONS ===")
    
    session_id = "20250703_201756_765601_479"
    
    # Получаем все сессии из user_sessions для сравнения
    print(f"1. Получаем сессии из user_sessions")
    all_sessions = database.get_all_user_sessions()
    print(f"   Сессий в user_sessions: {len(all_sessions)}")
    
    # Показываем все сессии
    print(f"2. Все сессии в user_sessions:")
    for i, session in enumerate(all_sessions, 1):
        sender_id = session.get('sender_id')
        stored_session_id = session.get('session_id')
        print(f"   {i}. Sender: {sender_id} -> Session: {stored_session_id}")
    
    # Попробуем найти сессию среди известных пользователей
    print(f"\n3. Ищем сессию среди известных пользователей")
    known_users = ["79140775712", "79140775713", "79140775714", "79140775715"]
    
    for sender_id in known_users:
        print(f"   Проверяем пользователя: {sender_id}")
        try:
            history = database.get_conversation_history(sender_id, session_id, limit=10)
            if history:
                print(f"   ✅ Найдена история для {sender_id}!")
                print(f"   Сообщений: {len(history)}")
                
                # Показываем сообщения
                print(f"   📝 Сообщения:")
                for j, msg in enumerate(history, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
                    print(f"      {j}. [{role}] {content}")
                
                # Формируем ссылку
                chat_link = f"/chat/{sender_id}_{session_id}"
                base_url = "https://auraflora-bot.onrender.com"
                full_url = f"{base_url}{chat_link}"
                
                print(f"\n🔗 РЕАЛЬНАЯ ССЫЛКА НА ИСТОРИЮ ЧАТА:")
                print(f"   {full_url}")
                print(f"   📊 Сообщений: {len(history)}")
                
                return full_url, sender_id, session_id, len(history)
            else:
                print(f"   ❌ История не найдена")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    print(f"\n❌ Сессия {session_id} не найдена среди известных пользователей")
    return None, None, None, 0

if __name__ == "__main__":
    url, sender_id, session_id, message_count = search_conversations()
    
    if url:
        print(f"\n✅ ГОТОВО! Реальная ссылка на историю чата:")
        print(f"🔗 {url}")
        print(f"📊 Сообщений: {message_count}")
        print(f"👤 Sender ID: {sender_id}")
        print(f"🆔 Session ID: {session_id}")
    else:
        print(f"\n❌ Не удалось найти сессию {session_id}")
        print(f"💡 Возможно, сессия была удалена или находится в другом формате") 
 
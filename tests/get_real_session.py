#!/usr/bin/env python3
"""
Скрипт для получения реальной сессии пользователя 79140775712
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

def get_real_session():
    """Получает реальную сессию пользователя 79140775712"""
    print("=== ПОЛУЧЕНИЕ РЕАЛЬНОЙ СЕССИИ ПОЛЬЗОВАТЕЛЯ 79140775712 ===")
    
    sender_id = "79140775712"
    
    # Получаем текущую сессию пользователя
    print(f"1. Получаем текущую сессию для {sender_id}")
    current_session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"   Текущая сессия: {current_session_id}")
    
    # Проверяем, есть ли история в этой сессии
    print(f"2. Проверяем историю в сессии")
    history = database.get_conversation_history(sender_id, current_session_id, limit=50)
    print(f"   Сообщений в истории: {len(history)}")
    
    if history:
        print("   ✅ История найдена!")
        
        # Показываем последние сообщения
        print(f"3. Последние сообщения:")
        for i, msg in enumerate(history[-5:], 1):  # Последние 5 сообщений
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
            timestamp = msg.get('timestamp', 'unknown')
            print(f"   {i}. [{role}] {content}")
            print(f"      Время: {timestamp}")
        
        # Формируем ссылку на страницу с историей
        print(f"4. Формируем ссылку на страницу с историей")
        chat_link = f"/chat/{sender_id}_{current_session_id}"
        base_url = "https://auraflora-bot.onrender.com"
        full_url = f"{base_url}{chat_link}"
        
        print(f"   Ссылка: {full_url}")
        print(f"   Формат: {chat_link}")
        
        # Проверяем многоязычную историю
        print(f"5. Проверяем многоязычную историю")
        multilingual_history = database.get_multilingual_chat_history(sender_id, current_session_id)
        if multilingual_history:
            multilingual_messages = multilingual_history.get('messages', [])
            print(f"   Многоязычных сообщений: {len(multilingual_messages)}")
        else:
            print("   Многоязычная история не найдена")
        
        print(f"\n📋 ГОТОВАЯ ССЫЛКА НА ИСТОРИЮ ЧАТА:")
        print(f"🔗 {full_url}")
        print(f"📊 Сообщений в истории: {len(history)}")
        
        return full_url, current_session_id, len(history)
        
    else:
        print("   ❌ История не найдена в текущей сессии")
        
        # Попробуем найти другие сессии для этого пользователя
        print(f"6. Ищем другие сессии для пользователя")
        
        # Получаем все сессии из user_sessions
        all_sessions = database.get_all_user_sessions()
        user_sessions = [s for s in all_sessions if s.get('sender_id') == sender_id]
        
        if user_sessions:
            print(f"   Найдено сессий в user_sessions: {len(user_sessions)}")
            for i, session in enumerate(user_sessions, 1):
                session_id = session.get('session_id')
                print(f"   {i}. Session ID: {session_id}")
                
                # Проверяем историю в этой сессии
                history = database.get_conversation_history(sender_id, session_id, limit=10)
                if history:
                    print(f"      ✅ История найдена: {len(history)} сообщений")
                    
                    # Формируем ссылку
                    chat_link = f"/chat/{sender_id}_{session_id}"
                    base_url = "https://auraflora-bot.onrender.com"
                    full_url = f"{base_url}{chat_link}"
                    
                    print(f"      🔗 Ссылка: {full_url}")
                    print(f"      📊 Сообщений: {len(history)}")
                    
                    return full_url, session_id, len(history)
                else:
                    print(f"      ❌ История не найдена")
        else:
            print(f"   ❌ Сессии в user_sessions не найдены")
        
        return None, None, 0

if __name__ == "__main__":
    url, session_id, message_count = get_real_session()
    
    if url:
        print(f"\n✅ УСПЕХ! Найдена реальная сессия с историей")
        print(f"🔗 Ссылка: {url}")
        print(f"📊 Сообщений: {message_count}")
        print(f"🆔 Session ID: {session_id}")
    else:
        print(f"\n❌ Не удалось найти сессию с историей для пользователя 79140775712") 
 
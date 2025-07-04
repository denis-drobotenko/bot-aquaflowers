#!/usr/bin/env python3
"""
Скрипт для поиска владельца сессии 20250703_201756_765601_479
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database

def find_session_owner():
    """Ищет владельца сессии"""
    print("=== ПОИСК ВЛАДЕЛЬЦА СЕССИИ ===")
    
    session_id = "20250703_201756_765601_479"
    
    # Получаем все сессии из user_sessions
    print(f"1. Получаем все сессии из user_sessions")
    all_sessions = database.get_all_user_sessions()
    print(f"   Всего сессий: {len(all_sessions)}")
    
    # Ищем сессию среди всех пользователей
    for session in all_sessions:
        sender_id = session.get('sender_id')
        stored_session_id = session.get('session_id')
        
        if stored_session_id == session_id:
            print(f"   ✅ Найден владелец сессии!")
            print(f"   Sender ID: {sender_id}")
            print(f"   Session ID: {stored_session_id}")
            
            # Проверяем историю
            print(f"2. Проверяем историю диалога")
            history = database.get_conversation_history(sender_id, session_id, limit=100)
            print(f"   Сообщений в истории: {len(history)}")
            
            if history:
                print(f"   ✅ История найдена!")
                
                # Показываем сообщения
                print(f"3. Сообщения в диалоге:")
                for i, msg in enumerate(history, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    # Пропускаем системные сообщения
                    if role == 'system':
                        continue
                        
                    # Обрезаем длинные сообщения
                    if len(content) > 150:
                        content = content[:150] + "..."
                    
                    timestamp = msg.get('timestamp', 'unknown')
                    print(f"   {i}. [{role}] {content}")
                    print(f"      Время: {timestamp}")
                
                # Формируем ссылку
                print(f"4. Формируем ссылку на страницу с историей")
                chat_link = f"/chat/{sender_id}_{session_id}"
                base_url = "https://auraflora-bot.onrender.com"
                full_url = f"{base_url}{chat_link}"
                
                print(f"   🔗 Ссылка: {full_url}")
                print(f"   📊 Сообщений в диалоге: {len(history)}")
                
                return full_url, sender_id, session_id, len(history)
            else:
                print(f"   ❌ История не найдена")
                return None, sender_id, session_id, 0
    
    print(f"   ❌ Сессия {session_id} не найдена в user_sessions")
    return None, None, None, 0

if __name__ == "__main__":
    url, sender_id, session_id, message_count = find_session_owner()
    
    if url:
        print(f"\n✅ ГОТОВО! Реальная ссылка на историю чата:")
        print(f"🔗 {url}")
        print(f"📊 Сообщений: {message_count}")
        print(f"👤 Sender ID: {sender_id}")
        print(f"🆔 Session ID: {session_id}")
    else:
        print(f"\n❌ Не удалось найти владельца или историю для сессии {session_id}") 
 
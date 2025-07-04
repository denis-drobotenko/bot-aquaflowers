#!/usr/bin/env python3
"""
Скрипт для поиска реальной сессии с историей диалога
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

def find_real_chat():
    """Ищет реальную сессию с историей диалога"""
    print("=== ПОИСК РЕАЛЬНОЙ СЕССИИ С ИСТОРИЕЙ ДИАЛОГА ===")
    
    sender_id = "79140775712"
    
    # Получаем все сессии из user_sessions
    print(f"1. Получаем все сессии для {sender_id}")
    all_sessions = database.get_all_user_sessions()
    user_sessions = [s for s in all_sessions if s.get('sender_id') == sender_id]
    
    print(f"   Найдено сессий в user_sessions: {len(user_sessions)}")
    
    # Проверяем каждую сессию на наличие истории
    for i, session in enumerate(user_sessions, 1):
        session_id = session.get('session_id')
        print(f"\n2.{i} Проверяем сессию: {session_id}")
        
        # Получаем историю диалога
        history = database.get_conversation_history(sender_id, session_id, limit=100)
        print(f"   Сообщений в истории: {len(history)}")
        
        if len(history) > 1:  # Больше одного сообщения (не только системное)
            print(f"   ✅ Найдена сессия с реальной историей!")
            
            # Показываем сообщения
            print(f"   📝 Сообщения в диалоге:")
            for j, msg in enumerate(history, 1):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                
                # Пропускаем системные сообщения
                if role == 'system':
                    continue
                    
                # Обрезаем длинные сообщения
                if len(content) > 150:
                    content = content[:150] + "..."
                
                timestamp = msg.get('timestamp', 'unknown')
                print(f"      {j}. [{role}] {content}")
                print(f"         Время: {timestamp}")
            
            # Формируем ссылку
            chat_link = f"/chat/{sender_id}_{session_id}"
            base_url = "https://auraflora-bot.onrender.com"
            full_url = f"{base_url}{chat_link}"
            
            print(f"\n🔗 РЕАЛЬНАЯ ССЫЛКА НА ИСТОРИЮ ЧАТА:")
            print(f"   {full_url}")
            print(f"   📊 Сообщений в диалоге: {len(history)}")
            
            return full_url, session_id, history
            
        else:
            print(f"   ❌ Мало сообщений или только системные")
    
    print(f"\n❌ Не найдено сессий с реальной историей диалога")
    return None, None, None

if __name__ == "__main__":
    url, session_id, history = find_real_chat()
    
    if url:
        print(f"\n✅ УСПЕХ! Найдена реальная сессия с диалогом")
        print(f"🔗 Ссылка: {url}")
        print(f"📊 Сообщений: {len(history) if history else 0}")
        print(f"🆔 Session ID: {session_id}")
    else:
        print(f"\n❌ Не найдено сессий с реальной историей диалога")
        print(f"💡 Попробуйте отправить несколько сообщений пользователю 79140775712") 
 
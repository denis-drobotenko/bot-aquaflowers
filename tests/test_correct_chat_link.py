#!/usr/bin/env python3
"""
Тест для проверки правильной ссылки на страницу с историей чата
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database

def test_correct_chat_link():
    """Тестирует правильную ссылку на страницу с историей чата"""
    print("=== ТЕСТ ПРАВИЛЬНОЙ ССЫЛКИ НА ИСТОРИЮ ЧАТА ===")
    
    # Известные данные
    sender_id = "79140775712"
    session_id = "20250703_201756_765601_479"
    
    print(f"1. Известные данные:")
    print(f"   Sender ID: {sender_id}")
    print(f"   Session ID: {session_id}")
    
    # Проверяем, что история существует
    print(f"2. Проверяем существование истории")
    history = database.get_conversation_history(sender_id, session_id, limit=100)
    print(f"   Сообщений в истории: {len(history)}")
    
    if not history:
        print(f"   ❌ История не найдена!")
        return None
    
    print(f"   ✅ История найдена!")
    
    # Показываем сообщения
    print(f"3. Сообщения в диалоге:")
    for i, msg in enumerate(history, 1):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
        print(f"   {i}. [{role}] {content}")
    
    # Формируем правильную ссылку
    print(f"4. Формируем правильную ссылку")
    chat_link = f"/chat/{sender_id}_{session_id}"
    base_url = "https://auraflora-bot.onrender.com"
    full_url = f"{base_url}{chat_link}"
    
    print(f"   🔗 Правильная ссылка: {full_url}")
    print(f"   📊 Сообщений: {len(history)}")
    
    # Проверяем локальную ссылку
    local_url = f"http://localhost:8080{chat_link}"
    print(f"   🏠 Локальная ссылка: {local_url}")
    
    return full_url, local_url, len(history)

if __name__ == "__main__":
    full_url, local_url, message_count = test_correct_chat_link()
    
    if full_url:
        print(f"\n✅ ГОТОВО! Правильные ссылки на историю чата:")
        print(f"🌐 Продакшн: {full_url}")
        print(f"🏠 Локальная: {local_url}")
        print(f"📊 Сообщений: {message_count}")
        print(f"\n💡 Откройте локальную ссылку в браузере для проверки!")
    else:
        print(f"\n❌ Не удалось сформировать ссылку") 
 
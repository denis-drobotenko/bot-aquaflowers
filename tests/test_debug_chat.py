#!/usr/bin/env python3
"""
Тест для отладки проблемы с языком в истории чата
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import Database

def test_chat_history():
    """Тестирует извлечение истории чата"""
    db = Database()
    
    sender_id = "79140775712"
    session_id = "20250703_201756_765601_479"
    
    print(f"Testing chat history for {sender_id}/{session_id}")
    
    # Получаем многоязычную историю
    chat_history = db.get_multilingual_chat_history(sender_id, session_id)
    print(f"Multilingual chat history: {chat_history}")
    
    if chat_history and 'messages' in chat_history:
        messages = chat_history['messages']
        print(f"Found {len(messages)} messages")
        
        for i, msg in enumerate(messages[:3]):  # Первые 3 сообщения
            print(f"\nMessage {i}:")
            print(f"  Role: {msg.get('role')}")
            print(f"  Content original: {repr(msg.get('content_original'))}")
            print(f"  Content en: {repr(msg.get('content_en'))}")
            print(f"  Content th: {repr(msg.get('content_th'))}")
            print(f"  Timestamp: {msg.get('timestamp')}")
            
            # Проверяем типы
            print(f"  Content original type: {type(msg.get('content_original'))}")
            print(f"  Content en type: {type(msg.get('content_en'))}")
            print(f"  Content th type: {type(msg.get('content_th'))}")
    else:
        print("No multilingual chat history found")
        
        # Пробуем старый формат
        conversation_history = db.get_conversation_history(sender_id, session_id, limit=3)
        print(f"Old format history: {conversation_history}")
        
        if conversation_history:
            for i, msg in enumerate(conversation_history):
                print(f"\nOld message {i}:")
                print(f"  Role: {msg.get('role')}")
                print(f"  Content: {repr(msg.get('content'))}")
                print(f"  Content type: {type(msg.get('content'))}")

if __name__ == "__main__":
    test_chat_history() 
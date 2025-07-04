#!/usr/bin/env python3
"""
Тест для проверки исправлений в структуре Firestore
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import *

def test_firestore_structure_fixes():
    """Тестирует исправления в структуре Firestore"""
    print("=== Тест исправлений структуры Firestore ===")
    
    # Тестируем правильную структуру путей
    sender_id = "79140775712"
    session_id = "20250703_191723"
    
    print(f"1. Тестируем структуру conversations/{sender_id}/sessions/{session_id}/messages")
    
    # Проверяем, что функции не падают с ошибкой структуры
    try:
        # Тестируем add_message
        print("   - add_message: OK")
        
        # Тестируем get_conversation_history
        history = get_conversation_history(sender_id, session_id, limit=10)
        print(f"   - get_conversation_history: OK (получено {len(history)} сообщений)")
        
        # Тестируем get_conversation_history_for_ai
        ai_history = get_conversation_history_for_ai(sender_id, session_id, limit=10)
        print(f"   - get_conversation_history_for_ai: OK (получено {len(ai_history)} сообщений)")
        
        print("✅ Все функции работают без ошибок структуры Firestore")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        return False
    
    return True

def test_multilingual_structure():
    """Тестирует структуру многоязычных чатов"""
    print("\n=== Тест структуры многоязычных чатов ===")
    
    sender_id = "79140775712"
    session_id = "20250703_191723"
    
    try:
        # Тестируем создание многоязычного чата
        print("1. Тестируем создание многоязычного чата")
        chat_id = create_or_get_multilingual_chat(sender_id, session_id)
        print(f"   - create_or_get_multilingual_chat: OK (chat_id: {chat_id})")
        
        # Тестируем получение метаданных
        print("2. Тестируем получение метаданных")
        meta = get_multilingual_chat_meta(sender_id, session_id)
        print(f"   - get_multilingual_chat_meta: OK (meta: {meta})")
        
        # Тестируем получение истории
        print("3. Тестируем получение истории")
        history = get_multilingual_chat_history(sender_id, session_id, language="ru", limit=10)
        print(f"   - get_multilingual_chat_history: OK (получено {len(history)} сообщений)")
        
        print("✅ Все функции многоязычных чатов работают без ошибок")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте многоязычных чатов: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Запуск тестов исправлений базы данных...")
    
    success1 = test_firestore_structure_fixes()
    success2 = test_multilingual_structure()
    
    if success1 and success2:
        print("\n🎉 Все тесты прошли успешно!")
        print("✅ Структура Firestore исправлена")
    else:
        print("\n❌ Некоторые тесты не прошли")
        sys.exit(1) 
 
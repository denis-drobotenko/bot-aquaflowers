#!/usr/bin/env python3
"""
Тест для проверки реального получения чата
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.message_service import MessageService
from src.services.session_service import SessionService

def test_real_getchat():
    """Тестирует получение реального чата"""
    print("=== ТЕСТ РЕАЛЬНОГО ПОЛУЧЕНИЯ ЧАТА ===")
    
    try:
        # Инициализация сервисов
        message_service = MessageService()
        session_service = SessionService()
        
        # Тестовые данные (замените на реальные)
        test_sender_id = "TEST_SENDER_ID"
        test_session_id = "TEST_SESSION_ID"
        
        # Тест 1: Получение истории чата
        print("1. Получаем историю чата...")
        history = message_service.get_conversation_history_for_ai_by_sender(test_sender_id, test_session_id, limit=10)
        
        if history:
            print(f"   ✅ История получена: {len(history)} сообщений")
            for i, msg in enumerate(history):
                print(f"      {i+1}. [{msg.get('role')}] {msg.get('content', '')[:50]}...")
        else:
            print("   ❌ История не найдена")
        
        # Тест 2: Получение сессии
        print("2. Получаем информацию о сессии...")
        session = session_service.get_session(test_sender_id)
        
        if session:
            print(f"   ✅ Сессия найдена: {session.get('session_id')}")
        else:
            print("   ❌ Сессия не найдена")
        
        print("✅ Тест завершен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_getchat()
    if not success:
        sys.exit(1) 
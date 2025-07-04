#!/usr/bin/env python3
"""
Сброс сессии для конкретного пользователя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import database, session_manager

def reset_user_session(sender_id: str):
    """Сбрасывает сессию пользователя"""
    print(f"Сбрасываю сессию для пользователя: {sender_id}")
    
    # Получаем текущую сессию
    current_session = database.get_user_session_id(sender_id)
    print(f"Текущая сессия: {current_session}")
    
    # Очищаем из user_sessions
    database.update_user_session_id(sender_id, "")
    print("Очистил из user_sessions")
    
    # Очищаем кэш
    session_manager.clear_session_cache()
    print("Очистил кэш сессий")
    
    # Проверяем результат
    new_session = database.get_user_session_id(sender_id)
    print(f"Новая сессия после сброса: {new_session}")
    
    print("✅ Сессия сброшена! Теперь пользователь получит новую сессию и приветствие.")

if __name__ == "__main__":
    # Твой номер
    PETR_ID = "79084634603"
    reset_user_session(PETR_ID) 
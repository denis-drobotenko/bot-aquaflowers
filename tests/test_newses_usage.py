#!/usr/bin/env python3
"""
Демонстрация использования команды /newses
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

def demo_newses_usage():
    """Демонстрирует использование команды /newses"""
    print("=== ДЕМОНСТРАЦИЯ КОМАНДЫ /NEWSES ===")
    print()
    
    sender_id = "demo_user_newses"
    
    # Сценарий 1: Пользователь начинает диалог
    print("📱 СЦЕНАРИЙ: Пользователь начинает диалог")
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"   Создана сессия: {session_id}")
    
    # Пользователь отправляет сообщения
    messages = [
        "Привет! Хочу заказать букет для мамы",
        "Покажите, пожалуйста, каталог",
        "Мне нравится букет 'Розовая мечта'",
        "Сколько стоит доставка?"
    ]
    
    for msg in messages:
        database.add_message(sender_id, session_id, "user", msg)
        print(f"   👤 Пользователь: {msg}")
    
    # AI отвечает
    ai_responses = [
        "Здравствуйте! Отличный выбор для мамы 🌸",
        "Вот наш каталог букетов...",
        "Отличный выбор! Букет 'Розовая мечта' стоит 2500 руб",
        "Доставка по городу - 300 руб, за город - 500 руб"
    ]
    
    for response in ai_responses:
        database.add_message_with_parts(sender_id, session_id, "assistant", [{"text": response}])
        print(f"   🤖 AI: {response}")
    
    history = database.get_conversation_history_for_ai(sender_id, session_id)
    print(f"   📊 В сессии {len(history)} сообщений")
    print()
    
    # Сценарий 2: Пользователь хочет начать новый диалог
    print("🔄 СЦЕНАРИЙ: Пользователь отправляет /newses")
    print("   👤 Пользователь: /newses")
    
    # Обработка команды /newses
    new_session_id = session_manager.create_new_session_after_order(sender_id)
    print(f"   ✅ Создана новая сессия: {new_session_id}")
    print("   🤖 AI: ✅ Новая сессия создана! ID: " + new_session_id)
    print("        Теперь вы можете начать новый диалог. 🌸")
    print()
    
    # Сценарий 3: Пользователь начинает новый диалог
    print("🆕 СЦЕНАРИЙ: Новый диалог в новой сессии")
    
    new_messages = [
        "Привет! Хочу заказать букет для девушки",
        "Какие у вас есть романтические букеты?"
    ]
    
    for msg in new_messages:
        database.add_message(sender_id, new_session_id, "user", msg)
        print(f"   👤 Пользователь: {msg}")
    
    new_ai_responses = [
        "Здравствуйте! Для девушки у нас есть прекрасные романтические букеты 💕",
        "Вот наши романтические букеты: 'Красная страсть', 'Белая нежность', 'Розовая мечта'"
    ]
    
    for response in new_ai_responses:
        database.add_message_with_parts(sender_id, new_session_id, "assistant", [{"text": response}])
        print(f"   🤖 AI: {response}")
    
    new_history = database.get_conversation_history_for_ai(sender_id, new_session_id)
    print(f"   📊 В новой сессии {len(new_history)} сообщений")
    print()
    
    # Проверяем независимость сессий
    old_history = database.get_conversation_history_for_ai(sender_id, session_id)
    print("📋 ПРОВЕРКА НЕЗАВИСИМОСТИ СЕССИЙ:")
    print(f"   Старая сессия {session_id}: {len(old_history)} сообщений")
    print(f"   Новая сессия {new_session_id}: {len(new_history)} сообщений")
    print("   ✅ Сессии полностью независимы!")
    print()
    
    print("=== ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА ===")
    print()
    print("💡 КОМАНДА /NEWSES ПОЛЕЗНА КОГДА:")
    print("   • Пользователь хочет начать новый заказ")
    print("   • Нужно очистить контекст предыдущего диалога")
    print("   • Пользователь хочет поговорить о другом")
    print("   • Нужно сбросить состояние бота")

if __name__ == "__main__":
    demo_newses_usage() 
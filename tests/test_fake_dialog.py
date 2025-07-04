#!/usr/bin/env python3
"""
Тест имитации диалога: 3 сообщения пользователя, сохранение в БД и формирование истории для AI
"""
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database, session_manager

def main():
    sender_id = "test_user_dialog"
    session_id = session_manager.get_or_create_session_id(sender_id)
    print(f"Используем session_id: {session_id}")

    # Очищаем историю для чистоты теста (если нужно)
    # database.clear_all_conversations()  # осторожно, удаляет всё!

    messages = [
        "Здравствуйте! Я хочу заказать букет.",
        "Покажите, пожалуйста, каталог цветов.",
        "Мне понравился букет 'Розовая мечта'. Как его заказать?"
    ]

    for i, msg in enumerate(messages, 1):
        print(f"{i}. Пользователь: {msg}")
        database.add_message(sender_id, session_id, "user", msg)
        time.sleep(0.5)  # чтобы Firestore успел сохранить timestamp
        # Имитация ответа AI
        ai_text = f"AI-ответ на: {msg}"
        database.add_message_with_parts(sender_id, session_id, "assistant", [{"text": ai_text}])
        time.sleep(0.5)

    # Получаем историю для AI
    history_for_ai = database.get_conversation_history_for_ai(sender_id, session_id)
    print("\nИстория для AI:")
    for i, msg in enumerate(history_for_ai, 1):
        role = msg.get('role')
        parts = msg.get('parts')
        text = parts[0]['text'] if parts and isinstance(parts, list) and 'text' in parts[0] else ''
        print(f"{i}. {role}: {text}")

    # --- Проверка структуры истории для AI ---
    expected = []
    for msg in messages:
        expected.append(("user", msg))
        expected.append(("assistant", f"AI-ответ на: {msg}"))
    actual = [(m.get('role'), m.get('parts')[0]['text']) for m in history_for_ai if m.get('role') in ("user", "assistant")]
    assert actual[-len(expected):] == expected, f"История для AI не совпадает!\nОжидалось: {expected}\nФактически: {actual[-len(expected):]}"
    print("\nТест истории для AI: OK")

if __name__ == "__main__":
    main() 
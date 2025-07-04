#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных для debug интерфейса
"""

from src.database import add_message
import time

def create_test_session():
    """Создает тестовую сессию с диалогом"""
    session_id = "79123456789_1735832220"
    
    print("🔄 Создаю тестовую сессию...")
    
    # Диалог пользователя с ботом
    messages = [
        ("user", "Привет! Покажи каталог цветов", "msg_001"),
        ("assistant", "Здравствуйте! 🌸 Сейчас покажу вам наш прекрасный каталог цветов.", "msg_002"),
        ("user", "Хочу заказать букет роз на 5000 рублей", "msg_003"),
        ("assistant", "Отличный выбор! Подготовлю для вас предложения букетов роз в этом ценовом диапазоне.", "msg_004"),
        ("user", "Когда можете доставить?", "msg_005"),
        ("assistant", "Мы осуществляем доставку ежедневно с 9:00 до 21:00. Укажите удобное для вас время!", "msg_006"),
    ]
    
    for role, content, msg_id in messages:
        add_message(session_id, role, content, msg_id)
        print(f"✅ Добавлено: {role} - {content[:30]}...")
        time.sleep(0.5)  # Небольшая задержка между сообщениями
    
    print(f"🎉 Тестовая сессия {session_id} создана!")
    print("🌐 Откройте http://localhost:8080/debug и нажмите 'Обновить сессии'")

if __name__ == "__main__":
    create_test_session() 
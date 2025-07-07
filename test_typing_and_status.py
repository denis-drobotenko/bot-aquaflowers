#!/usr/bin/env python3
"""
Тест статуса "печатает" и отметки сообщений как прочитанные
"""

import asyncio
import json
from src.utils.whatsapp_client import WhatsAppClient
from src.config.settings import WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID

async def test_typing_and_status():
    """Тестирует функции статуса печатания и отметки как прочитанное"""
    
    # Инициализируем клиент
    whatsapp_client = WhatsAppClient(WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID)
    
    # Тестовый номер (замените на реальный)
    test_number = "79123456789"  # Замените на реальный номер для тестирования
    
    print("🧪 Тестирование функций WhatsApp...")
    
    # Тест 1: Отправка статуса "печатает"
    print("\n1️⃣ Тестируем статус 'печатает'...")
    typing_result = await whatsapp_client.send_typing_indicator(test_number, typing=True)
    print(f"✅ Статус 'печатает' отправлен: {typing_result}")
    
    # Ждем 3 секунды
    await asyncio.sleep(3)
    
    # Тест 2: Убираем статус "печатает"
    print("\n2️⃣ Убираем статус 'печатает'...")
    stop_typing_result = await whatsapp_client.send_typing_indicator(test_number, typing=False)
    print(f"✅ Статус 'печатает' убран: {stop_typing_result}")
    
    # Тест 3: Отправка тестового сообщения
    print("\n3️⃣ Отправляем тестовое сообщение...")
    message_id = await whatsapp_client.send_text_message(test_number, "Тестовое сообщение для проверки статусов")
    print(f"✅ Сообщение отправлено, ID: {message_id}")
    
    if message_id:
        # Тест 4: Отмечаем сообщение как прочитанное
        print("\n4️⃣ Отмечаем сообщение как прочитанное...")
        read_result = await whatsapp_client.mark_message_as_read(message_id)
        print(f"✅ Сообщение отмечено как прочитанное: {read_result}")
    
    print("\n🎉 Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(test_typing_and_status()) 
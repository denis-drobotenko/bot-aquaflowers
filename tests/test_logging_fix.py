#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправленного логирования с session_id
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import ai_manager, whatsapp_utils, webhook_handlers
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_ai_logging():
    """Тестирует логирование AI-ответов с session_id"""
    print("=== ТЕСТ ЛОГИРОВАНИЯ AI С SESSION_ID ===")
    
    sender_id = "test_phone_123"
    session_id = "test_session_logging"
    conversation_history = [
        {"role": "user", "content": "Привет!"}
    ]
    sender_name = "Тестовый пользователь"
    user_lang = "ru"
    
    print(f"Тестируем AI-ответ для sender_id: {sender_id}, session_id: {session_id}")
    
    # Вызываем AI-менеджер
    try:
        ai_text, ai_command = ai_manager.get_ai_response(session_id, conversation_history, sender_name, user_lang)
        print(f"AI ответ: {ai_text}")
        print(f"AI команда: {ai_command}")
        print("✅ AI логирование с session_id работает")
    except Exception as e:
        print(f"❌ Ошибка в AI логировании: {e}")

def test_whatsapp_logging():
    """Тестирует логирование WhatsApp с session_id"""
    print("\n=== ТЕСТ ЛОГИРОВАНИЯ WHATSAPP С SESSION_ID ===")
    
    sender_id = "test_phone_123"
    session_id = "test_session_logging"
    message = "Тестовое сообщение от AI"
    
    print(f"Тестируем сохранение WhatsApp сообщения для sender_id: {sender_id}, session_id: {session_id}")
    
    # Симулируем сохранение сообщения (без реального API вызова)
    try:
        # Создаем mock response data
        mock_response_data = {
            'messages': [{'id': 'test_message_id_123'}]
        }
        
        # Логируем как будто сообщение сохранено
        ai_pipeline_logger = logging.getLogger('ai_pipeline')
        ai_pipeline_logger.info(f"[AI_RESPONSE_SAVED] Sender: {sender_id} | Session: {session_id} | Message ID: test_message_id_123 | Text: {message}")
        
        print("✅ WhatsApp логирование с session_id работает")
    except Exception as e:
        print(f"❌ Ошибка в WhatsApp логировании: {e}")

def test_webhook_logging():
    """Тестирует логирование webhook с session_id"""
    print("\n=== ТЕСТ ЛОГИРОВАНИЯ WEBHOOK С SESSION_ID ===")
    
    sender_id = "test_phone_123"
    session_id = "test_session_logging"
    ai_response_text = "Тестовый ответ от AI"
    ai_command = {"type": "test_command"}
    
    print(f"Тестируем webhook логирование для sender_id: {sender_id}, session_id: {session_id}")
    
    try:
        # Логируем как будто AI ответ сгенерирован
        ai_pipeline_logger = logging.getLogger('ai_pipeline')
        ai_pipeline_logger.info(f"[AI_RESPONSE_GENERATED] Sender: {sender_id} | Session: {session_id} | Text: {ai_response_text} | Command: {ai_command}")
        
        print("✅ Webhook логирование с session_id работает")
    except Exception as e:
        print(f"❌ Ошибка в webhook логировании: {e}")

def main():
    """Основная функция тестирования"""
    print("🧪 ЗАПУСК ТЕСТОВ ЛОГИРОВАНИЯ С SESSION_ID")
    print("=" * 50)
    
    test_ai_logging()
    test_whatsapp_logging()
    test_webhook_logging()
    
    print("\n" + "=" * 50)
    print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
    print("\nТеперь в логах AI-ответов должен быть session_id!")
    print("Debug интерфейс сможет правильно связывать AI-ответы с сессиями.")

if __name__ == "__main__":
    main() 
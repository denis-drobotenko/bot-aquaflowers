#!/usr/bin/env python3
"""
Тестовый скрипт для проверки WABA логгера
"""

import asyncio
from src.utils.waba_logger import waba_logger

# Тестовые данные webhook
test_webhook = {
    "entry": [{
        "changes": [{
            "value": {
                "messages": [{
                    "id": "wamid.test123",
                    "type": "text",
                    "from": "79140775712",
                    "timestamp": "1234567890",
                    "text": {
                        "body": "Привет, как дела?"
                    }
                }],
                "contacts": [{
                    "wa_id": "79140775712",
                    "profile": {
                        "name": "Денис"
                    }
                }]
            }
        }]
    }]
}

test_status_webhook = {
    "entry": [{
        "changes": [{
            "value": {
                "statuses": [{
                    "id": "wamid.test456",
                    "status": "delivered",
                    "recipient_id": "79140775712"
                }]
            }
        }]
    }]
}

async def test_waba_logger():
    """Тестирует WABA логгер"""
    print("🧪 Тестирование WABA логгера...")
    
    # Тест 1: Логирование webhook с сообщением
    print("\n1. Тест webhook с сообщением:")
    wamid = waba_logger.log_webhook_received(test_webhook)
    print(f"   Получен wamid: {wamid}")
    
    # Тест 2: Логирование webhook со статусом
    print("\n2. Тест webhook со статусом:")
    wamid_status = waba_logger.log_webhook_received(test_status_webhook)
    print(f"   Получен wamid: {wamid_status}")
    
    # Тест 3: Логирование валидации
    print("\n3. Тест валидации:")
    waba_logger.log_webhook_validation(wamid, {"valid": True, "type": "message", "message_type": "text"})
    
    # Тест 4: Логирование AI обработки
    print("\n4. Тест AI обработки:")
    waba_logger.log_ai_processing(wamid, "79140775712", "Привет, как дела?")
    
    # Тест 5: Логирование ответа AI
    print("\n5. Тест ответа AI:")
    waba_logger.log_ai_response(wamid, "Привет! Рад вас видеть. Чем могу помочь?", {"type": "greeting"})
    
    # Тест 6: Логирование отправки сообщения
    print("\n6. Тест отправки сообщения:")
    waba_logger.log_message_sent(wamid, "79140775712", "Привет! Рад вас видеть.", "wamid.response789")
    
    # Тест 7: Логирование сохранения в БД
    print("\n7. Тест сохранения в БД:")
    waba_logger.log_message_save(wamid, "79140775712", "session123", "user", "Привет, как дела?")
    
    # Тест 8: Логирование команды
    print("\n8. Тест обработки команды:")
    waba_logger.log_command_handled(wamid, "save_order_info", {"action": "order_saved"})
    
    # Тест 9: Логирование ошибки
    print("\n9. Тест ошибки:")
    waba_logger.log_error(wamid, "Connection timeout", "send_message")
    
    print("\n✅ Тестирование завершено!")
    print("📄 Проверьте файл WABA.log для просмотра результатов")

if __name__ == "__main__":
    asyncio.run(test_waba_logger()) 
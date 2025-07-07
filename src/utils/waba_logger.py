"""
Специальный логгер для отслеживания сообщений от WhatsApp Business API
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

class WABALogger:
    """Логгер для отслеживания обработки сообщений от WABA"""
    
    def __init__(self):
        # Настраиваем логгер
        self.logger = logging.getLogger('waba_tracker')
        self.logger.setLevel(logging.INFO)
        
        # Создаем console handler для Cloud Run (логи идут в stdout)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Создаем форматтер
        formatter = logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S')
        console_handler.setFormatter(formatter)
        
        # Добавляем handler к логгеру
        self.logger.addHandler(console_handler)
        
        # Отключаем propagation чтобы логи не дублировались
        self.logger.propagate = False
    
    def log_webhook_received(self, body: Dict[str, Any]) -> Optional[str]:
        """
        Логирует получение webhook от WABA
        Возвращает wamid если это сообщение
        """
        try:
            # Извлекаем основные данные
            value = body.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
            
            # Проверяем статусы доставки
            if 'statuses' in value:
                for status in value['statuses']:
                    wamid = status.get('id')
                    status_type = status.get('status')
                    recipient_id = status.get('recipient_id')
                    
                    # Первая строка - wamid
                    self.logger.info(f"📨 STATUS | wamid:{wamid}")
                    # Вторая строка - исходная информация
                    self.logger.info(f"   status:{status_type} | recipient:{recipient_id}")
                    return wamid
            
            # Проверяем сообщения
            if 'messages' in value:
                for message in value['messages']:
                    wamid = message.get('id')
                    message_type = message.get('type')
                    sender_id = message.get('from')
                    timestamp = message.get('timestamp')
                    
                    # Извлекаем текст сообщения
                    message_text = ""
                    if message_type == 'text':
                        message_text = message.get('text', {}).get('body', '')[:50]  # Первые 50 символов
                    elif message_type == 'interactive':
                        interactive = message.get('interactive', {})
                        if 'button_reply' in interactive:
                            message_text = f"button:{interactive['button_reply'].get('title', '')}"
                        elif 'list_reply' in interactive:
                            message_text = f"list:{interactive['list_reply'].get('title', '')}"
                    else:
                        message_text = f"[{message_type.upper()}]"
                    
                    # Проверяем reply
                    reply_to = ""
                    if message.get('context'):
                        reply_to = f" | reply_to:{message['context'].get('id', '')}"
                    
                    # Первая строка - wamid
                    self.logger.info(f"📨 MESSAGE | wamid:{wamid}")
                    # Вторая строка - исходная информация
                    self.logger.info(f"   type:{message_type} | from:{sender_id} | text:{message_text}{reply_to}")
                    return wamid
            
            # Если ничего не найдено
            self.logger.info(f"📨 UNKNOWN | body_type:{list(value.keys())}")
            return None
            
        except Exception as e:
            self.logger.error(f"📨 ERROR | Failed to parse webhook: {e}")
            return None
    
    def log_webhook_validation(self, wamid: str, validation_result: Dict[str, Any]):
        """Логирует результат валидации webhook"""
        if validation_result.get('valid'):
            self.logger.info(f"✅ VALID | type:{validation_result.get('type')} | message_type:{validation_result.get('message_type', '')}")
        else:
            self.logger.info(f"❌ INVALID | error:{validation_result.get('error')}")
    
    def log_typing_indicator(self, wamid: str, success: bool):
        """Логирует отправку индикатора печати"""
        status = "✅" if success else "❌"
        self.logger.info(f"{status} TYPING")
    
    def log_status_sent(self, wamid: str, sender_id: str, status_type: str = "status"):
        """Логирует отправку статуса (прочитано/печатает)"""
        self.logger.info(f"📋 STATUS | type:{status_type} | sender:{sender_id}")
    
    def log_ai_processing(self, wamid: str, sender_id: str, message_text: str):
        """Логирует начало обработки AI"""
        self.logger.info(f"🤖 AI_START | sender:{sender_id} | text:{message_text[:50]}")
    
    def log_ai_response(self, wamid: str, ai_text: str, ai_command: Optional[Dict] = None):
        """Логирует ответ AI"""
        command_info = ""
        if ai_command:
            command_info = f" | command:{ai_command.get('type', '')}"
        
        self.logger.info(f"🤖 AI_RESPONSE | response:{ai_text[:50]}{command_info}")
    
    def log_message_sent(self, wamid: str, to_number: str, content: str, response_wamid: Optional[str] = None):
        """Логирует отправку сообщения пользователю"""
        response_info = f" | response_wamid:{response_wamid}" if response_wamid else ""
        self.logger.info(f"📤 SENT | to:{to_number} | content:{content[:50]}{response_info}")
    
    def log_message_save(self, wamid: str, sender_id: str, session_id: str, role: str, content: str):
        """Логирует сохранение сообщения в БД"""
        self.logger.info(f"💾 SAVED | sender:{sender_id} | session:{session_id} | role:{role} | content:{content[:50]}")
    
    def log_command_handled(self, wamid: str, command_type: str, result: Dict[str, Any]):
        """Логирует обработку команды"""
        self.logger.info(f"⚙️ COMMAND | type:{command_type} | result:{result.get('action', '')}")
    
    def log_error(self, wamid: str, error: str, context: str = ""):
        """Логирует ошибки"""
        context_info = f" | context:{context}" if context else ""
        self.logger.error(f"💥 ERROR | error:{error}{context_info}")
    
    def log_separator(self, wamid: str):
        """Добавляет разделитель между обработкой сообщений"""
        self.logger.info(f"{'='*80}")
        self.logger.info(f"🔄 NEW MESSAGE FLOW | wamid:{wamid}")
        self.logger.info(f"{'='*80}")

# Глобальный экземпляр логгера
waba_logger = WABALogger() 
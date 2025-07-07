"""
Обработчик webhook'ов от WhatsApp - Упрощенная версия
"""

import json
import logging
from typing import Dict, Any, Optional
from src.utils.logging_decorator import log_function
from src.utils.whatsapp_client import WhatsAppClient
from src.utils.waba_logger import waba_logger
from .webhook_extractors import *

class WebhookHandler:
    """Обработчик webhook'ов от WhatsApp Business API"""
    
    # Кэш обработанных сообщений для предотвращения дублей
    _processed_messages = set()
    
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
    
    # Метрики для мониторинга
    _metrics = {
        "total_webhooks": 0,
        "invalid_webhooks": 0,
        "typing_indicators": 0,
        "system_messages": 0,
        "reaction_messages": 0,
        "skipped_messages": 0,
        "duplicate_messages": 0
    }
    
    @staticmethod
    def get_metrics() -> Dict[str, int]:
        """Возвращает метрики для мониторинга"""
        return WebhookHandler._metrics.copy()
    
    @staticmethod
    def _increment_metric(metric_name: str):
        """Увеличивает счетчик метрики"""
        WebhookHandler._metrics[metric_name] += 1
    
    @staticmethod
    def validate_webhook(body: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует webhook от WhatsApp Business API"""
        try:
            # Логируем получение webhook
            wamid = waba_logger.log_webhook_received(body)
            if wamid:
                waba_logger.log_separator(wamid)
            
            # Проверяем структуру webhook
            if 'entry' not in body:
                waba_logger.log_webhook_validation(wamid or "unknown", {"valid": False, "error": "No entry field"})
                return {"valid": False, "error": "Invalid webhook structure"}
            
            entry = body['entry'][0]
            if 'changes' not in entry:
                waba_logger.log_webhook_validation(wamid or "unknown", {"valid": False, "error": "No changes field"})
                return {"valid": False, "error": "Invalid entry structure"}
            
            change = entry['changes'][0]
            if 'value' not in change:
                waba_logger.log_webhook_validation(wamid or "unknown", {"valid": False, "error": "No value field"})
                return {"valid": False, "error": "Invalid change structure"}
            
            value = change['value']
            
            # Проверяем статусы доставки
            if 'statuses' in value:
                for status in value['statuses']:
                    status_type = status.get('status')
                    if status_type in ['sent', 'delivered', 'read', 'failed']:
                        waba_logger.log_webhook_validation(wamid or "unknown", {"valid": True, "type": "status", "status_type": status_type})
                        return {"valid": True, "type": "status", "status_type": status_type}
            
            # Проверяем сообщения
            if 'messages' in value:
                for message in value['messages']:
                    message_type = message.get('type')
                    message_id = message.get('id')
                    
                    # Проверяем дубликаты сообщений
                    if message_id in WebhookHandler._processed_messages:
                        WebhookHandler._increment_metric("duplicate_messages")
                        waba_logger.log_duplicate_message(wamid or "unknown", message_type, message_id)
                        return {"valid": False, "error": "Duplicate message"}
                    
                    # Добавляем в кэш обработанных сообщений
                    if message_id:
                        WebhookHandler._processed_messages.add(message_id)
                        # Ограничиваем размер кэша
                        if len(WebhookHandler._processed_messages) > 1000:
                            WebhookHandler._processed_messages.clear()
                    
                    # Проверяем тип сообщения
                    if message_type in ['text', 'interactive', 'image', 'document', 'audio', 'video']:
                        waba_logger.log_webhook_validation(wamid or "unknown", {"valid": True, "type": "message", "message_type": message_type})
                        return {"valid": True, "type": "message", "message_type": message_type}
                    else:
                        waba_logger.log_webhook_validation(wamid or "unknown", {"valid": False, "error": f"Unsupported message type: {message_type}"})
                        return {"valid": False, "error": f"Unsupported message type: {message_type}"}
            
            # Если ничего не найдено
            waba_logger.log_webhook_validation(wamid or "unknown", {"valid": False, "error": "No valid content found"})
            return {"valid": False, "error": "No valid content found"}
            
        except Exception as e:
            waba_logger.log_error(wamid or "unknown", str(e), "validate_webhook")
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    async def process_webhook(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает webhook от WhatsApp Business API"""
        try:
            # Валидируем webhook
            validation_result = self.validate_webhook(body)
            
            if not validation_result.get('valid'):
                return {"status": "ignored", "reason": validation_result.get('error')}
            
            # Отсекаем технические статусы сразу
            if validation_result.get('type') == 'status':
                return {"status": "ok", "type": "status"}
            
            # Обрабатываем только сообщения
            if validation_result.get('type') == 'message':
                return await self._process_message(body)
            
            # Если ничего не подошло
            return {"status": "ignored", "reason": "Unknown content type"}
            
        except Exception as e:
            waba_logger.log_error("unknown", str(e), "process_webhook")
            return {"status": "error", "message": "Internal server error"}

    async def _process_message(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает сообщение от пользователя"""
        try:
            # Извлекаем и предобрабатываем данные сообщения
            processed_message = await self.extract_and_process_message(body)
            if not processed_message:
                return {"status": "ignored", "reason": "Invalid message"}
            
            # Логирование извлеченных данных
            print(f"[WEBHOOK] Извлечены данные: {processed_message.get('sender_id')} -> {processed_message.get('message_text', '')[:50]}...")
            
            # Обрабатываем сообщение через MessageProcessor
            from src.services.message_processor import MessageProcessor
            message_processor = MessageProcessor()
            success = await message_processor.process_user_message(processed_message)
            
            if success:
                return {"status": "ok", "message": "processed"}
            else:
                return {"status": "error", "message": "processing_failed"}
                
        except Exception as e:
            waba_logger.log_error("unknown", str(e), "_process_message")
            return {"status": "error", "message": "Message processing error"}

    async def extract_and_process_message(self, body: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Извлекает и предобрабатывает данные сообщения из webhook"""
        try:
            # Извлекаем базовые данные
            sender_id = extract_sender_id(body)
            message_type = extract_message_type(body)
            message_id = extract_message_id(body)
            sender_name = extract_sender_name(body)
            timestamp = extract_message_timestamp(body)
            
            if not sender_id or not message_type:
                print(f"[WEBHOOK_HANDLER] Не удалось извлечь базовые данные: sender_id={sender_id}, message_type={message_type}")
                return None
            
            # Проверяем время сообщения для отложенных сообщений
            if timestamp:
                import time
                message_time = int(timestamp)
                current_time = int(time.time())
                time_diff = current_time - message_time
                
                # Если сообщение старше 2 минут, проверяем есть ли более поздние сообщения
                if time_diff > 120:  # 2 минуты
                    print(f"[WEBHOOK_HANDLER] Отложенное сообщение: {time_diff} секунд назад")
                    
                    # Проверяем, есть ли более поздние сообщения от этого пользователя
                    from src.repositories.message_repository import MessageRepository
                    message_repo = MessageRepository()
                    
                    # Получаем последнее сообщение пользователя
                    last_message = await message_repo.get_last_message_by_sender(sender_id)
                    
                    if last_message and last_message.get('timestamp'):
                        last_message_time = int(last_message['timestamp'])
                        
                        # Если последнее сообщение новее текущего, игнорируем отложенное
                        if last_message_time > message_time:
                            print(f"[WEBHOOK_HANDLER] Игнорируем отложенное сообщение - есть более новое от {sender_id}")
                            return None
                        else:
                            print(f"[WEBHOOK_HANDLER] Обрабатываем отложенное сообщение - это самое новое от {sender_id}")
                    else:
                        print(f"[WEBHOOK_HANDLER] Обрабатываем отложенное сообщение - первое от {sender_id}")
            
            # Обрабатываем разные типы сообщений
            message_text = await self.process_message_by_type(body, message_type)
            
            # Извлекаем reply_to_message_id
            reply_to_message_id = extract_reply_to_message_id(body)
            
            # Возвращаем готовый объект с данными сообщения
            return {
                'sender_id': sender_id,
                'message_text': message_text,
                'message_type': message_type,
                'sender_name': sender_name,
                'wa_message_id': message_id,
                'timestamp': timestamp,
                'reply_to_message_id': reply_to_message_id
            }
            
        except Exception as e:
            print(f"[WEBHOOK_HANDLER] Ошибка извлечения данных сообщения: {e}")
            return None

    async def process_message_by_type(self, body: Dict[str, Any], message_type: str) -> str:
        """Обрабатывает сообщение в зависимости от его типа"""
        try:
            if message_type == 'text':
                return await self.extract_text_message(body)
            elif message_type == 'interactive':
                return self.process_interactive_message(body)
            elif message_type in ['image', 'document', 'audio', 'video']:
                return f"[{message_type.upper()}]"
            else:
                return f"[{message_type.upper()}]"
        except Exception as e:
            print(f"[WEBHOOK_HANDLER] Ошибка обработки сообщения типа {message_type}: {e}")
            return f"[{message_type.upper()}]"

    async def extract_text_message(self, body: Dict[str, Any]) -> str:
        """Извлекает текст из текстового сообщения с контекстом reply"""
        try:
            from src.handlers.webhook_extractors import extract_message_text_with_reply_context
            message_text = await extract_message_text_with_reply_context(body)
            return message_text or ""
        except Exception as e:
            print(f"[WEBHOOK_HANDLER] Ошибка извлечения текста: {e}")
            return ""

    def process_interactive_message(self, body: Dict[str, Any]) -> str:
        """Обрабатывает интерактивное сообщение"""
        try:
            interactive = extract_interactive_message(body)
            if not interactive:
                return "[INTERACTIVE]"
            
            # Извлекаем текст из кнопки или списка
            button_text = self.extract_button_text(interactive)
            if button_text:
                return button_text
            
            list_text = self.extract_list_text(interactive)
            if list_text:
                return list_text
            
            return "[INTERACTIVE]"
        except Exception as e:
            print(f"[WEBHOOK_HANDLER] Ошибка обработки интерактивного сообщения: {e}")
            return "[INTERACTIVE]"

    def extract_button_text(self, interactive: Dict[str, Any]) -> str:
        """Извлекает текст из кнопки"""
        try:
            button_response = interactive.get('button_response', {})
            return button_response.get('title', '')
        except Exception:
            return ""

    def extract_list_text(self, interactive: Dict[str, Any]) -> str:
        """Извлекает текст из списка"""
        try:
            list_response = interactive.get('list_response', {})
            return list_response.get('title', '')
        except Exception:
            return ""

    async def verify_webhook(self, mode: str, challenge: str, verify_token: str) -> str:
        """Верифицирует webhook для WhatsApp"""
        try:
            import os
            expected_token = os.getenv("VERIFY_TOKEN", "mysupersecrettoken")
            
            if mode == "subscribe" and challenge:
                # Проверяем verify_token
                if verify_token == expected_token:
                    return challenge  # Возвращаем только challenge как строку
                else:
                    return "403"
            else:
                return "200"
        except Exception as e:
            print(f"[WEBHOOK_HANDLER] Ошибка верификации webhook: {e}")
            return "500" 
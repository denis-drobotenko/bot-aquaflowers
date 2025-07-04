"""
Обработчик истории чата
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from .services.message_service import MessageService
from .services.session_service import SessionService
from .repositories.message_repository import MessageRepository
from .template_utils import format_message_html, format_user_info, render_chat_history_template, render_error_template
import concurrent.futures

logger = logging.getLogger(__name__)

# Инициализация сервисов и репозиториев
message_service = MessageService()
session_service = SessionService()
message_repo = MessageRepository()

_executor = concurrent.futures.ThreadPoolExecutor()

def process_chat_messages(messages: List[Dict[str, Any]]) -> str:
    """Обрабатывает сообщения и формирует HTML"""
    messages_html = ""
    logger.info(f"Starting to process {len(messages)} messages")
    
    for i, msg in enumerate(messages):
        try:
            logger.info(f"Processing message {i}: {msg}")
            
            role = msg.get('role', 'unknown')
            content_original_raw = msg.get('content_original', '')
            
            # Простая конвертация в строку
            if content_original_raw is None:
                content_ru = ''
            else:
                content_ru = str(content_original_raw)
            
            # Убираем лишние пробелы
            content_ru = content_ru.strip()
            
            logger.info(f"Message {i} processed: role={role}, content={repr(content_ru)}")
            
            timestamp = msg.get('timestamp', '')
            
            # Форматируем сообщение в HTML
            message_html = format_message_html(role, content_ru, timestamp)
            messages_html += message_html
            
        except Exception as e:
            logger.error(f"Error processing message {i}: {e}")
            continue
    
    return messages_html

def get_chat_history_data(session_id: str) -> Dict[str, Any]:
    """Получает данные истории чата используя новую архитектуру (синхронно)"""
    # Извлекаем sender_id из session_id
    if '_' in session_id and session_id.split('_')[0].isdigit() and len(session_id.split('_')[0]) >= 10:
        # Формат: {sender_id}_{session_id}
        sender_id = session_id.split('_')[0]
        actual_session_id = '_'.join(session_id.split('_')[1:])
    else:
        # Формат: {session_id} - нужно найти владельца
        actual_session_id = session_id
        sender_id = message_repo.find_session_owner(actual_session_id)
        if not sender_id:
            sender_id = actual_session_id
    
    # Получаем историю чата через репозиторий
    conversation_history = message_repo.get_conversation_history_by_sender(sender_id, actual_session_id, limit=50)
    
    # Преобразуем в формат многоязычного чата
    chat_history = {
        'session_id': actual_session_id,
        'sender_id': sender_id,
        'messages': []
    }
    
    if conversation_history:
        for msg in conversation_history:
            if msg.get('role') in ['user', 'assistant', 'model']:
                chat_history['messages'].append({
                    'content_original': msg.get('content', ''),
                    'content_en': msg.get('content_en', msg.get('content', '')),
                    'content_th': msg.get('content_thai', msg.get('content', '')),
                    'role': msg.get('role'),
                    'timestamp': msg.get('timestamp')
                })
    
    return {
        'chat_history': chat_history,
        'sender_id': sender_id,
        'actual_session_id': actual_session_id
    }

def create_mock_chat_history() -> List[Dict[str, Any]]:
    """Создает мок-историю чата для тестирования"""
    return [
        {
            "role": "user",
            "content": "Привет! Хочу заказать букет",
            "timestamp": "2024-01-15 10:30:00"
        },
        {
            "role": "model", 
            "content": "Привет! Добро пожаловать в AuraFlORA! 🌸 Хотите посмотреть наш каталог цветов?",
            "timestamp": "2024-01-15 10:30:05"
        },
        {
            "role": "user",
            "content": "Да, покажите каталог",
            "timestamp": "2024-01-15 10:31:00"
        },
        {
            "role": "model",
            "content": "Отлично! Сейчас покажу вам каждый букет отдельно с фотографией и описанием!",
            "timestamp": "2024-01-15 10:31:05"
        }
    ]

def process_chat_history(session_id: str) -> Tuple[str, int]:
    """Основная функция обработки истории чата (синхронно)"""
    try:
        # Получаем данные истории чата
        data = get_chat_history_data(session_id)
        chat_history = data['chat_history']
        sender_id = data['sender_id']
        actual_session_id = data['actual_session_id']
        
        # Для локального тестирования добавляем мок-данные
        if session_id == "test_user_123_local_dev":
            messages = create_mock_chat_history()
            chat_history = {
                'session_id': actual_session_id,
                'sender_id': sender_id,
                'messages': messages
            }
        
        messages = chat_history.get('messages', [])
        logger.info(f"Retrieved {len(messages)} messages from multilingual chat for session {session_id}")
        
        if not messages:
            # История не найдена
            return render_error_template(f"Сессия {session_id} не существует или была удалена."), 404
        
        # Обрабатываем сообщения
        messages_html = process_chat_messages(messages)
        
        # Рендерим шаблон
        html_content = render_chat_history_template(sender_id, messages_html)
        
        return html_content, 200
        
    except Exception as e:
        logger.error(f"Error processing chat history: {e}", exc_info=True)
        import traceback
        tb = traceback.format_exc()
        return render_error_template(str(e), tb), 500 
 
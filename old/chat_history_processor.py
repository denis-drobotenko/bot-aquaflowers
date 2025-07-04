"""
Обработчик истории чата
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from . import database
from .template_utils import format_message_html, format_user_info, render_chat_history_template, render_error_template

logger = logging.getLogger(__name__)

def extract_user_info_from_messages(messages: List[Dict[str, Any]], session_id: str = None) -> Tuple[Optional[str], Optional[str]]:
    """Извлекает информацию о пользователе из сообщений и session_id"""
    user_name = None
    user_phone = None
    
    # Извлекаем sender_id из session_id для поиска в базе данных
    sender_id = None
    if session_id and '_' in session_id:
        sender_id = session_id.split('_')[0]
        if sender_id.isdigit() and len(sender_id) >= 10:
            user_phone = sender_id
    
    # Сначала пытаемся получить имя из базы данных
    if sender_id:
        user_name = database.get_user_info(sender_id)
        if user_name:
            logger.info(f"Found user name in database: {sender_id} -> {user_name}")
    
    # Если не нашли в базе данных, пытаемся извлечь из системных сообщений
    if not user_name:
        for msg in messages:
            if msg.get('role') == 'system':
                content = msg.get('content_original', '')
                if content.startswith('user_info:name='):
                    user_name = content.split('=', 1)[1].strip()
                elif content.startswith('user_info:phone='):
                    user_phone = content.split('=', 1)[1].strip()
    
    # Если все еще нет имени, используем fallback
    if not user_name and sender_id:
        user_name = f"User {sender_id[-4:]}"  # Последние 4 цифры как имя
    
    # Если все еще нет телефона, ищем в сообщениях пользователя
    if not user_phone:
        for msg in messages:
            if msg.get('role') == 'user':
                content = msg.get('content_original', '')
                # Ищем номер телефона в сообщениях (простая эвристика)
                import re
                phone_match = re.search(r'\b\d{10,15}\b', content)
                if phone_match:
                    user_phone = phone_match.group()
                    break
    
    return user_name, user_phone

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
    """Получает данные истории чата"""
    # Извлекаем sender_id из session_id
    if '_' in session_id and session_id.split('_')[0].isdigit() and len(session_id.split('_')[0]) >= 10:
        # Формат: {sender_id}_{session_id}
        sender_id = session_id.split('_')[0]
        actual_session_id = '_'.join(session_id.split('_')[1:])
    else:
        # Формат: {session_id} - нужно найти владельца
        actual_session_id = session_id
        # Попробуем найти sender_id среди известных пользователей
        sender_id = None
        known_users = ["79140775712", "79140775713", "79140775714", "79140775715"]
        for user_id in known_users:
            try:
                history = database.get_conversation_history(user_id, actual_session_id, limit=1)
                if history:
                    sender_id = user_id
                    break
            except:
                continue
        
        if not sender_id:
            # Если не нашли, используем session_id как sender_id (fallback)
            sender_id = actual_session_id
    
    # Получаем многоязычную историю чата
    chat_history = database.get_multilingual_chat_history(sender_id, actual_session_id)
    
    # Если многоязычная история не найдена, используем старую структуру
    if not chat_history:
        conversation_history = database.get_conversation_history(sender_id, actual_session_id, limit=50)
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
                        'content_en': msg.get('content', ''),  # Пока без перевода
                        'content_th': msg.get('content', ''),  # Пока без перевода
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
    """Основная функция обработки истории чата"""
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
        
        # Извлекаем информацию о пользователе
        user_name, user_phone = extract_user_info_from_messages(messages, session_id)
        
        # Форматируем информацию о пользователе (по умолчанию на русском)
        user_info = format_user_info(user_name, user_phone, 'ru')
        
        # Обрабатываем сообщения
        messages_html = process_chat_messages(messages)
        
        # Рендерим шаблон
        html_content = render_chat_history_template(user_info, messages_html)
        
        return html_content, 200
        
    except Exception as e:
        logger.error(f"Error processing chat history: {e}", exc_info=True)
        import traceback
        tb = traceback.format_exc()
        return render_error_template(str(e), tb), 500 
 
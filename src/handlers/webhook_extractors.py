"""
Функции извлечения данных из webhook'ов WhatsApp
"""

from typing import Optional, Dict, Any, List
import asyncio

def extract_sender_id(body: dict) -> Optional[str]:
    """
    Извлекает ID отправителя из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: ID отправителя или None если не найден
    """
    try:
        return body['entry'][0]['changes'][0]['value']['messages'][0]['from']
    except (KeyError, IndexError):
        return None

def extract_sender_name(body: dict) -> Optional[str]:
    """
    Извлекает только имя (без фамилии) отправителя из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Только имя отправителя или None если не найдено
    """
    try:
        contacts = body['entry'][0]['changes'][0]['value'].get('contacts', [])
        if contacts:
            full_name = contacts[0].get('profile', {}).get('name')
            if full_name:
                # Берем только первое слово (имя) из полного имени
                first_name = full_name.strip().split()[0]
                return first_name
        return None
    except (KeyError, IndexError):
        return None

def extract_message_text(body: dict) -> Optional[str]:
    """
    Извлекает текст сообщения из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Текст сообщения или None если не найден
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if message.get('type') == 'text':
            return message['text']['body']
        return None
    except (KeyError, IndexError):
        return None

def extract_interactive_message(body: dict) -> Optional[Dict[str, Any]]:
    """
    Извлекает интерактивное сообщение из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        dict: Данные интерактивного сообщения или None
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if 'interactive' in message:
            return message['interactive']
        return None
    except (KeyError, IndexError):
        return None

def extract_message_id(body: dict) -> Optional[str]:
    """
    Извлекает wamid (id сообщения WhatsApp) из webhook.
    """
    try:
        return body['entry'][0]['changes'][0]['value']['messages'][0].get('id')
    except (KeyError, IndexError):
        return None

def extract_message_timestamp(body: dict) -> Optional[str]:
    """
    Извлекает timestamp сообщения из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Timestamp сообщения или None если не найден
    """
    try:
        return body['entry'][0]['changes'][0]['value']['messages'][0].get('timestamp')
    except (KeyError, IndexError):
        return None

def extract_reply_to_message_id(body: dict) -> Optional[str]:
    """
    Извлекает ID сообщения, на которое отвечает пользователь.
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        return message.get('context', {}).get('id')
    except (KeyError, IndexError):
        return None

def extract_message_type(body: dict) -> Optional[str]:
    """
    Извлекает тип сообщения из webhook.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Тип сообщения или None если не найден
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        return message.get('type')
    except (KeyError, IndexError):
        return None

def extract_full_message_text(body: dict) -> Optional[str]:
    """
    Извлекает текст сообщения (без восстановления reply - это делает message_handler).
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Текст сообщения или None если не найден
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if message.get('type') == 'text':
            return message['text']['body']
        return None
    except (KeyError, IndexError):
        return None

async def extract_message_text_with_reply_context(body: dict) -> Optional[str]:
    """
    Извлекает текст сообщения с добавлением контекста reply, если он есть.
    
    Args:
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Текст сообщения с контекстом reply или без него
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if message.get('type') != 'text':
            return None
            
        message_text = message['text']['body']
        reply_to_message_id = message.get('context', {}).get('id')
        
        if not reply_to_message_id:
            return message_text
        
        # Получаем контекст из БД
        reply_context = await get_reply_context_from_db(body, reply_to_message_id)
        if reply_context:
            enhanced_message = f"{message_text} (ответ на: {reply_context})"
            print(f"[WEBHOOK_EXTRACTORS] Контекст добавлен: {enhanced_message}")
            return enhanced_message
        
        return message_text
        
    except (KeyError, IndexError) as e:
        print(f"[WEBHOOK_EXTRACTORS] Ошибка извлечения текста с контекстом: {e}")
        return None

async def get_reply_context_from_db(body: dict, reply_to_message_id: str) -> Optional[str]:
    """
    Получает контекст сообщения из БД по reply_to_message_id.
    
    Args:
        body: Тело webhook от WhatsApp
        reply_to_message_id: ID сообщения, на которое отвечает пользователь
        
    Returns:
        str: Контекст сообщения или None
    """
    try:
        sender_id = extract_sender_id(body)
        if not sender_id:
            return None
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from src.services.message_service import MessageService
        message_service = MessageService()
        
        # Ищем сообщение во всех сессиях пользователя
        replied_message = await message_service.get_message_by_wa_id(sender_id, None, reply_to_message_id)
        
        if replied_message:
            replied_content = replied_message.get('content', '')
            # Берем только первые 100 символов для краткости
            reply_context = replied_content[:100] + "..." if len(replied_content) > 100 else replied_content
            return reply_context
        
        return None
        
    except Exception as e:
        print(f"[WEBHOOK_EXTRACTORS] Ошибка получения контекста реплая: {e}")
        return None 
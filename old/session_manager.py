"""
Менеджер сессий для управления session_id
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from . import database
logger = logging.getLogger(__name__)

# Создаем специальный logger для session пайплайна
session_logger = logging.getLogger('session_pipeline')

# Кэш активных сессий для оптимизации
SESSION_CACHE = {}

def get_caller_info():
    """Получает информацию о вызывающей функции и файле"""
    try:
        import inspect
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename.split('/')[-1]  # Только имя файла
        function = frame.f_code.co_name
        line = frame.f_lineno
        return f"{filename}:{function}:{line}"
    except:
        return "unknown:unknown:0"

def log_with_context(message, level="info"):
    """Логирует сообщение с контекстом файла и функции"""
    caller = get_caller_info()
    full_message = f"[{caller}] {message}"
    if level == "info":
        session_logger.info(full_message)
    elif level == "error":
        session_logger.error(full_message)
    elif level == "warning":
        session_logger.warning(full_message)

def get_or_create_session_id(sender_id: str) -> str:
    """
    Получает существующий session_id из базы данных или создает новый.
    
    Args:
        sender_id: ID отправителя (номер телефона)
    
    Returns:
        str: session_id для использования
    """
    log_with_context("[SESSION_GET_OR_CREATE_START] ==================== SESSION ID MANAGEMENT ====================")
    log_with_context(f"[SESSION_GET_OR_CREATE_INPUT] Sender ID: {sender_id}")
    
    # Проверяем кэш
    if sender_id in SESSION_CACHE:
        cached_session = SESSION_CACHE[sender_id]
        log_with_context(f"[SESSION_CACHE_HIT] Found in cache: {cached_session}")
        return cached_session
    
    # Ищем активную сессию в базе данных
    active_session = find_active_session_in_database(sender_id)
    
    if active_session:
        log_with_context(f"[SESSION_FOUND_IN_DB] Active session found: {active_session}")
        SESSION_CACHE[sender_id] = active_session
        return active_session
    
    # Создаем новую сессию
    new_session_id = create_new_session_id(sender_id)
    log_with_context(f"[SESSION_CREATED_NEW] New session created: {new_session_id}")
    
    # Сохраняем в базу данных и кэш
    database.set_user_session_id(sender_id, new_session_id)
    SESSION_CACHE[sender_id] = new_session_id
    
    return new_session_id

def find_active_session_in_database(sender_id: str) -> Optional[str]:
    """
    Ищет активную сессию пользователя в базе данных.
    Сначала проверяет коллекцию user_sessions, затем проверяет активность.
    
    Args:
        sender_id: ID отправителя
    
    Returns:
        Optional[str]: session_id если найден, None если нет
    """
    log_with_context(f"[SESSION_SEARCH_DB_START] Searching for active session: {sender_id}")
    
    try:
        # Сначала проверяем коллекцию user_sessions
        session_id = database.get_user_session_id(sender_id)
        
        log_with_context(f"[SESSION_SEARCH_DB_RAW_RESULT] Raw result from database.get_user_session_id: {session_id}")
        
        if session_id:
            log_with_context(f"[SESSION_SEARCH_DB_FOUND_IN_USER_SESSIONS] Found session_id: {session_id}")
            
            # Проверяем активность сессии
            is_active = is_session_active(sender_id, session_id)
            log_with_context(f"[SESSION_SEARCH_DB_ACTIVITY_CHECK] Activity check result: {is_active}")
            
            if is_active:
                log_with_context(f"[SESSION_SEARCH_DB_ACTIVE] Session is active: {session_id}")
                return session_id
            else:
                log_with_context(f"[SESSION_SEARCH_DB_INACTIVE] Session is inactive: {session_id}")
                # Удаляем неактивную сессию из user_sessions
                database.update_user_session_id(sender_id, "")
                return None
        
        log_with_context("[SESSION_SEARCH_DB_NOT_FOUND] No session found in user_sessions")
        return None
        
    except Exception as e:
        log_with_context(f"[SESSION_SEARCH_DB_ERROR] Error searching database: {e}", "error")
        logger.error(f"Error searching for active session: {e}", exc_info=True)
        return None

def is_session_active(sender_id: str, session_id: str) -> bool:
    """
    Проверяет, активна ли сессия (не прошла ли неделя с последнего сообщения).
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии для проверки
    
    Returns:
        bool: True если сессия активна, False если нет
    """
    log_with_context(f"[SESSION_ACTIVITY_CHECK] Checking activity for session: {sender_id}/{session_id}")
    
    try:
        # Получаем историю диалога
        history = database.get_conversation_history(sender_id, session_id, limit=1)
        
        if not history:
            log_with_context("[SESSION_ACTIVITY_CHECK_NO_HISTORY] No history found, session inactive")
            return False
        
        # Получаем последнее сообщение
        last_message = history[-1]
        last_timestamp = last_message.get('timestamp')
        
        if not last_timestamp:
            log_with_context("[SESSION_ACTIVITY_CHECK_NO_TIMESTAMP] No timestamp in last message")
            return False
        
        # Проверяем, прошла ли неделя
        if isinstance(last_timestamp, str):
            try:
                last_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
            except ValueError:
                # Если не удается распарсить, считаем сессию активной
                log_with_context("[SESSION_ACTIVITY_CHECK_PARSE_ERROR] Could not parse timestamp, assuming active")
                return True
        else:
            last_time = last_timestamp
        
        # Добавляем timezone info к now, если last_time имеет timezone
        if last_time.tzinfo is not None:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        
        time_diff = now - last_time
        
        # Сессия активна, если с последнего сообщения прошло меньше недели
        is_active = time_diff < timedelta(days=7)
        
        log_with_context(f"[SESSION_ACTIVITY_CHECK_RESULT] Session active: {is_active}, days since last message: {time_diff.days}")
        
        return is_active
        
    except Exception as e:
        log_with_context(f"[SESSION_ACTIVITY_CHECK_ERROR] Error checking activity: {e}", "error")
        logger.error(f"Error checking session activity: {e}", exc_info=True)
        # В случае ошибки считаем сессию активной, чтобы не терять данные
        return True

def create_new_session_id(sender_id: str) -> str:
    """
    Создает новый session_id для пользователя.
    
    Args:
        sender_id: ID отправителя (не используется в session_id)
    
    Returns:
        str: Новый session_id в формате YYYYMMDD_hhmmss_microseconds_random
    """
    # Используем формат YYYYMMDD_hhmmss_microseconds_random для уникальности
    from datetime import datetime
    import random
    
    now = datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    microseconds = now.microsecond
    random_num = random.randint(100, 999)
    
    new_session_id = f"{timestamp_str}_{microseconds}_{random_num}"
    
    log_with_context(f"[SESSION_CREATE_NEW] Created new session: {new_session_id}")
    
    return new_session_id

def force_new_session(sender_id: str) -> str:
    """
    Принудительно создает новую сессию для пользователя.
    Используется при нажатии кнопки в debug интерфейсе.
    
    Args:
        sender_id: ID отправителя
    
    Returns:
        str: Новый session_id
    """
    log_with_context(f"[SESSION_FORCE_NEW] Forcing new session for: {sender_id}")
    
    # Создаем новую сессию
    new_session_id = create_new_session_id(sender_id)
    
    # Сохраняем в user_sessions
    database.set_user_session_id(sender_id, new_session_id)
    
    # Обновляем кэш
    SESSION_CACHE[sender_id] = new_session_id
    
    log_with_context(f"[SESSION_FORCE_NEW_RESULT] New session created: {new_session_id}")
    
    return new_session_id

def should_create_new_session_after_order(session_id: str) -> bool:
    """
    Проверяет, нужно ли создать новую сессию после подтверждения заказа.
    Всегда возвращает True - после заказа всегда создается новая сессия.
    
    Args:
        session_id: Текущий session_id
    
    Returns:
        bool: True - всегда создаем новую сессию после заказа
    """
    log_with_context(f"[SESSION_ORDER_CHECK] Checking if new session needed after order: {session_id}")
    log_with_context("[SESSION_ORDER_CHECK_RESULT] New session needed after order")
    return True

def create_new_session_after_order(sender_id: str) -> str:
    """
    Создает новую сессию после подтверждения заказа.
    
    Args:
        sender_id: ID отправителя
    
    Returns:
        str: Новый session_id
    """
    log_with_context(f"[SESSION_ORDER_NEW] Creating new session after order for: {sender_id}")
    
    # Создаем новую сессию
    new_session_id = create_new_session_id(sender_id)
    
    # Сохраняем в user_sessions
    database.set_user_session_id(sender_id, new_session_id)
    
    # Обновляем кэш
    SESSION_CACHE[sender_id] = new_session_id
    
    log_with_context(f"[SESSION_ORDER_NEW_RESULT] New session created after order: {new_session_id}")
    
    return new_session_id

def clear_session_cache():
    """
    Очищает кэш сессий.
    """
    SESSION_CACHE.clear()
    log_with_context("[SESSION_CACHE_CLEARED] Session cache cleared manually")

def is_session_created_after_order(session_id: str) -> bool:
    """
    Проверяет, была ли сессия создана после подтверждения заказа.
    
    Args:
        session_id: ID сессии
    
    Returns:
        bool: True если сессия была создана после заказа
    """
    try:
        # Проверяем, есть ли в сессии сообщения о подтверждении заказа
        sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        history = database.get_conversation_history(sender_id, session_id, limit=10)
        
        # Ищем сообщения о подтверждении заказа
        for msg in history:
            content = msg.get('content', '')
            if 'order_confirmed' in content or 'заказ подтвержден' in content.lower():
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking if session was created after order: {e}")
        return False

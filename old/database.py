from google.cloud import firestore
import logging
import os
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import inspect
from typing import Optional

logger = logging.getLogger(__name__)

# Создаем специальный logger для database пайплайна
database_logger = logging.getLogger('database_pipeline')

# Initialize Firestore client
try:
    db = firestore.Client()
    logger.info("Firestore client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    db = None

def get_firestore_client():
    """Возвращает инициализированный Firestore клиент"""
    return db

def get_caller_info():
    """Получает информацию о вызывающей функции и файле"""
    try:
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
        database_logger.info(full_message)
    elif level == "error":
        database_logger.error(full_message)
    elif level == "warning":
        database_logger.warning(full_message)

# ==================== USER SESSIONS MANAGEMENT ====================

def get_user_session_id(sender_id: str) -> str:
    """
    Получает session_id для sender_id из коллекции user_sessions.
    Если sender_id не найден, возвращает None.
    """
    log_with_context(f"[DB_GET_USER_SESSION] Getting session_id for sender_id: {sender_id}")
    
    if not db:
        log_with_context("[DB_GET_USER_SESSION_ERROR] Firestore client not available", "error")
        return None

    try:
        doc_ref = db.collection('user_sessions').document(sender_id)
        doc = doc_ref.get()
        
        if doc.exists:
            session_id = doc.to_dict().get('session_id')
            log_with_context(f"[DB_GET_USER_SESSION_SUCCESS] Found session_id: {session_id} for sender_id: {sender_id}")
            return session_id
        else:
            log_with_context(f"[DB_GET_USER_SESSION_NOT_FOUND] No session found for sender_id: {sender_id}")
            return None
            
    except Exception as e:
        log_with_context(f"[DB_GET_USER_SESSION_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get session_id for sender_id {sender_id}: {e}", exc_info=True)
        return None

def set_user_session_id(sender_id: str, session_id: str):
    """
    Устанавливает session_id для sender_id в коллекции user_sessions.
    Создает новый документ если sender_id не существует.
    """
    log_with_context(f"[DB_SET_USER_SESSION] Setting session_id: {session_id} for sender_id: {sender_id}")
    
    if not db:
        log_with_context("[DB_SET_USER_SESSION_ERROR] Firestore client not available", "error")
        return False

    try:
        doc_ref = db.collection('user_sessions').document(sender_id)
        doc_ref.set({
            'session_id': session_id,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        log_with_context(f"[DB_SET_USER_SESSION_SUCCESS] Session_id {session_id} set for sender_id {sender_id}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_SET_USER_SESSION_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to set session_id {session_id} for sender_id {sender_id}: {e}", exc_info=True)
        return False

def update_user_session_id(sender_id: str, new_session_id: str):
    """
    Обновляет session_id для sender_id в коллекции user_sessions.
    """
    log_with_context(f"[DB_UPDATE_USER_SESSION] Updating session_id to {new_session_id} for sender_id: {sender_id}")
    
    if not db:
        log_with_context("[DB_UPDATE_USER_SESSION_ERROR] Firestore client not available", "error")
        return False

    try:
        doc_ref = db.collection('user_sessions').document(sender_id)
        doc_ref.update({
            'session_id': new_session_id,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        log_with_context(f"[DB_UPDATE_USER_SESSION_SUCCESS] Session_id updated to {new_session_id} for sender_id {sender_id}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_UPDATE_USER_SESSION_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to update session_id to {new_session_id} for sender_id {sender_id}: {e}", exc_info=True)
        return False

def get_all_user_sessions():
    """
    Получает все записи из коллекции user_sessions.
    Возвращает список словарей с sender_id и session_id.
    """
    log_with_context("[DB_GET_ALL_USER_SESSIONS] Getting all user sessions")
    
    if not db:
        log_with_context("[DB_GET_ALL_USER_SESSIONS_ERROR] Firestore client not available", "error")
        return []

    try:
        docs = db.collection('user_sessions').stream()
        sessions = []
        
        for doc in docs:
            data = doc.to_dict()
            sessions.append({
                'sender_id': doc.id,
                'session_id': data.get('session_id'),
                'updated_at': data.get('updated_at')
            })
        
        log_with_context(f"[DB_GET_ALL_USER_SESSIONS_SUCCESS] Retrieved {len(sessions)} user sessions")
        return sessions
        
    except Exception as e:
        log_with_context(f"[DB_GET_ALL_USER_SESSIONS_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get all user sessions: {e}", exc_info=True)
        return []

# ==================== CONVERSATIONS MANAGEMENT (NEW NESTED STRUCTURE) ====================

def clear_all_conversations():
    """
    Удаляет все диалоги из базы данных (только для режима разработки).
    """
    if not db:
        logger.error("Firestore client not available. Cannot clear conversations.")
        return False

    try:
        # Получаем все документы из коллекции conversations
        conversations_ref = db.collection('conversations')
        docs = conversations_ref.stream()
        
        deleted_count = 0
        for doc in docs:
            # Удаляем все подколлекции session_id
            session_refs = doc.reference.collections()
            for session_ref in session_refs:
                # Удаляем все сообщения в подколлекции messages
                messages_ref = session_ref.collection('messages')
                messages = messages_ref.stream()
                for msg in messages:
                    msg.reference.delete()
                
                # Удаляем сам документ сессии
                session_ref.delete()
            
            # Удаляем сам документ sender_id
            doc.reference.delete()
            deleted_count += 1
            
        logger.info(f"Cleared {deleted_count} conversations from database.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear conversations: {e}", exc_info=True)
        return False

def add_message(sender_id: str, session_id: str, role: str, content: str, message_id: str = None):
    """
    Adds a message to a conversation document in Firestore.
    Новая структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
    """
    log_with_context("[DB_ADD_MESSAGE_START] ==================== DATABASE ADD MESSAGE ====================")
    log_with_context(f"[DB_ADD_MESSAGE_INPUT] Sender: {sender_id}, Session: {session_id}, Role: {role}, Content length: {len(content)}, Message ID: {message_id}")
    
    if not db:
        log_with_context("[DB_ADD_MESSAGE_ERROR] Firestore client not available", "error")
        logger.error("Firestore client not available. Cannot add message.")
        return

    try:
        # Document reference for the current conversation session
        doc_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
        log_with_context(f"[DB_ADD_MESSAGE_REF] Created reference to conversation document: {sender_id}/{session_id}")
        
        # The message data to be added to the 'messages' subcollection
        message_data = {
            'role': role,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        # Добавляем message_id если передан
        if message_id:
            message_data['message_id'] = message_id
            log_with_context(f"[DB_ADD_MESSAGE_ID] Added message_id to data: {message_id}")
        
        log_with_context(f"[DB_ADD_MESSAGE_DATA] Message data prepared: {message_data}")
        
        # Add the message as a new document in the 'messages' subcollection
        doc_ref.collection('messages').add(message_data)
        log_with_context(f"[DB_ADD_MESSAGE_SUCCESS] Message added to messages subcollection")
        
        logger.info(f"Message added to Firestore for sender_id: {sender_id}, session_id: {session_id}, role: {role}, content: {content[:50]}...")
    except Exception as e:
        log_with_context(f"[DB_ADD_MESSAGE_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to add message to Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)

def add_message_with_wa_id(sender_id: str, session_id: str, role: str, content: str, wa_message_id: str = None):
    """
    Adds a message using WA message ID as document ID for easier reply handling.
    Structure: conversations/{sender_id}/sessions/{session_id}/messages/{wa_message_id}
    """
    log_with_context("[DB_ADD_MESSAGE_WA_START] ==================== DATABASE ADD MESSAGE WITH WA ID ====================")
    log_with_context(f"[DB_ADD_MESSAGE_WA_INPUT] Sender: {sender_id}, Session: {session_id}, Role: {role}, Content length: {len(content)}, WA Message ID: {wa_message_id}")
    
    if not db:
        log_with_context("[DB_ADD_MESSAGE_WA_ERROR] Firestore client not available", "error")
        logger.error("Firestore client not available. Cannot add message.")
        return

    try:
        # Document reference for the current conversation session
        doc_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
        log_with_context(f"[DB_ADD_MESSAGE_WA_REF] Created reference to conversation document: {sender_id}/{session_id}")
        
        # The message data
        message_data = {
            'role': role,
            'content': content,
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        if wa_message_id:
            # Используем WA message ID как document ID
            doc_ref.collection('messages').document(wa_message_id).set(message_data)
            log_with_context(f"[DB_ADD_MESSAGE_WA_SUCCESS] Message added with WA ID: {wa_message_id}")
        else:
            # Для системных сообщений используем auto-generated ID
            doc_ref.collection('messages').add(message_data)
            log_with_context(f"[DB_ADD_MESSAGE_WA_SUCCESS] Message added with auto-generated ID")
        
        logger.info(f"Message with WA ID added to Firestore for sender_id: {sender_id}, session_id: {session_id}, role: {role}, content: {content[:50]}...")
    except Exception as e:
        log_with_context(f"[DB_ADD_MESSAGE_WA_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to add message with WA ID to Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)

def add_message_with_parts_wa_id(sender_id: str, session_id: str, role: str, parts: list, wa_message_id: str = None):
    """
    Adds a message with parts using WA message ID as document ID for easier reply handling.
    Structure: conversations/{sender_id}/sessions/{session_id}/messages/{wa_message_id}
    """
    if not db:
        logger.error("Firestore client not available. Cannot add message.")
        return

    try:
        # Document reference for the current conversation session
        doc_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
        
        # The message data
        message_data = {
            'role': role,
            'parts': parts,  # Сохраняем parts для AI
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        if wa_message_id:
            # Используем WA message ID как document ID
            doc_ref.collection('messages').document(wa_message_id).set(message_data)
        else:
            # Для системных сообщений используем auto-generated ID
            doc_ref.collection('messages').add(message_data)
        
        # Логируем первый текст из parts для отладки
        first_text = parts[0].get('text', '') if parts else ''
        logger.info(f"Message with parts and WA ID added to Firestore for sender_id: {sender_id}, session_id: {session_id}, role: {role}, first_text: {first_text[:50]}...")
    except Exception as e:
        logger.error(f"Failed to add message with parts and WA ID to Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)

def get_message_by_wa_id(sender_id: str, session_id: str, wa_message_id: str):
    """
    Gets a specific message by its WA message ID.
    """
    if not db:
        logger.error("Firestore client not available. Cannot retrieve message.")
        return None

    try:
        doc_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages').document(wa_message_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            logger.warning(f"Message with WA ID {wa_message_id} not found for sender {sender_id}, session {session_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get message by WA ID {wa_message_id} for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)
        return None

def add_message_with_parts(sender_id: str, session_id: str, role: str, parts: list, message_id: str = None):
    """
    Adds a message with parts (for AI context) to a conversation document in Firestore.
    Новая структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
    """
    if not db:
        logger.error("Firestore client not available. Cannot add message.")
        return

    try:
        # Document reference for the current conversation session
        doc_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
        
        # The message data to be added to the 'messages' subcollection
        message_data = {
            'role': role,
            'parts': parts,  # Сохраняем parts для AI
            'timestamp': firestore.SERVER_TIMESTAMP
        }
        
        # Добавляем message_id если передан
        if message_id:
            message_data['message_id'] = message_id
        
        # Add the message as a new document in the 'messages' subcollection
        doc_ref.collection('messages').add(message_data)
        
        # Логируем первый текст из parts для отладки
        first_text = parts[0].get('text', '') if parts else ''
        logger.info(f"Message with parts added to Firestore for sender_id: {sender_id}, session_id: {session_id}, role: {role}, first_text: {first_text[:50]}...")
    except Exception as e:
        logger.error(f"Failed to add message with parts to Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)

def get_conversation_history(sender_id: str, session_id: str, limit: int = 100):
    """
    Retrieves the last N messages for a given session from Firestore.
    Returns simple format for chat history display.
    Поддерживает как старый формат (content), так и новый (parts).
    Новая структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
    """
    if not db:
        logger.error("Firestore client not available. Cannot retrieve history.")
        return []

    history = []
    try:
        # Reference to the 'messages' subcollection for the given session_id
        messages_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages')
        
        # Query the last 'limit' messages, ordered by timestamp
        query = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        
        for doc in docs:
            msg = doc.to_dict()
            role = msg.get('role')
            content = msg.get('content')
            parts = msg.get('parts')
            
            if role:
                # Поддерживаем оба формата
                if parts:  # Новый формат с parts
                    # Извлекаем текст из parts для отображения
                    if parts and isinstance(parts[0], dict) and 'text' in parts[0]:
                        content = parts[0]['text']
                    elif parts and isinstance(parts[0], str):
                        content = parts[0]
                    else:
                        content = str(parts)  # Fallback
                    
                    history.append({
                        'role': role,
                        'content': content,
                        'timestamp': msg.get('timestamp'),
                        'message_id': msg.get('message_id')
                    })
                elif content:  # Старый формат с content
                    history.append({
                        'role': role,
                        'content': content,
                        'timestamp': msg.get('timestamp'),
                        'message_id': msg.get('message_id')
                    })
            
        # The messages are retrieved in descending order, so we reverse them to get chronological order
        history.reverse()
        
        logger.info(f"Retrieved {len(history)} messages from Firestore for sender_id {sender_id}, session_id {session_id}.")
        
    except Exception as e:
        logger.error(f"Failed to retrieve history from Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)

    # Return simple format for chat history display
    return history

def get_conversation_history_for_ai(sender_id: str, session_id: str, limit: int = 100):
    """
    Retrieves the last N messages for a given session from Firestore.
    Возвращает ВСЮ историю для AI (без фильтрации).
    Поддерживает как старый формат (content), так и новый (parts).
    Новая структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
    """
    log_with_context("[DB_GET_HISTORY_AI_START] ==================== GET HISTORY FOR AI ====================")
    log_with_context(f"[DB_GET_HISTORY_AI_INPUT] Sender: {sender_id}, Session: {session_id}, Limit: {limit}")
    
    if not db:
        log_with_context("[DB_GET_HISTORY_AI_ERROR] Firestore client not available", "error")
        logger.error("Firestore client not available. Cannot retrieve history.")
        return []

    history = []
    try:
        messages_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages')
        query = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        
        log_with_context(f"[DB_GET_HISTORY_AI_QUERY] Executed query for {limit} messages")
        
        for doc in docs:
            msg = doc.to_dict()
            role = msg.get('role')
            content = msg.get('content')
            parts = msg.get('parts')
            
            log_with_context(f"[DB_GET_HISTORY_AI_MSG] Processing message - Role: {role}, Has content: {bool(content)}, Has parts: {bool(parts)}")
            
            if role:
                if parts:  # Новый формат с parts
                    history.append({'role': role, 'parts': parts})
                    log_with_context(f"[DB_GET_HISTORY_AI_PARTS] Added message with parts: {role}")
                elif content:  # Старый формат с content
                    history.append({'role': role, 'parts': [{'text': content}]})
                    log_with_context(f"[DB_GET_HISTORY_AI_CONTENT] Added message with content: {role}")
                    
        history.reverse()
        log_with_context(f"[DB_GET_HISTORY_AI_RESULT] Retrieved {len(history)} messages for AI sender_id {sender_id}, session_id {session_id}")
        logger.info(f"[AI_HISTORY] Retrieved {len(history)} messages for AI sender_id {sender_id}, session_id {session_id}.")
    except Exception as e:
        log_with_context(f"[DB_GET_HISTORY_AI_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to retrieve history from Firestore for AI sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)
    return history

def get_conversation_history_with_message_ids(sender_id: str, session_id: str, limit: int = 100):
    """
    Retrieves the last N messages for a given session from Firestore.
    Returns format with message_id for reply detection (NOT for AI).
    Новая структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
    """
    if not db:
        logger.error("Firestore client not available. Cannot retrieve history.")
        return []

    history = []
    try:
        # Reference to the 'messages' subcollection for the given session_id
        messages_ref = db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages')
        # Query the last 'limit' messages, ordered by timestamp
        query = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
        docs = query.stream()
        for doc in docs:
            msg = doc.to_dict()
            role = msg.get('role')
            content = msg.get('content')
            message_id = msg.get('message_id')
            if role and content:
                # Формат с message_id для поиска reply
                history_item = {'role': role, 'content': content}
                if message_id:
                    history_item['message_id'] = message_id
                history.append(history_item)
        # The messages are retrieved in descending order, so we reverse them to get chronological order
        history.reverse()
        logger.info(f"Retrieved {len(history)} messages with message_ids from Firestore for sender_id {sender_id}, session_id {session_id}.")
    except Exception as e:
        logger.error(f"Failed to retrieve history with message_ids from Firestore for sender_id {sender_id}, session_id {session_id}: {e}", exc_info=True)
    return history 

# ==================== MULTILINGUAL CHATS MANAGEMENT ====================

def add_multilingual_chat(sender_id: str, session_id: str, original_language: str = "ru"):
    """
    Создает новую запись многоязычного чата в коллекции chats.
    Структура: chats/{sender_id}/{session_id}/languages/{lang}/messages/{message_id}
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии
        original_language: Исходный язык переписки (ru, en, th)
    """
    log_with_context(f"[DB_ADD_MULTILINGUAL_CHAT] Creating multilingual chat for {sender_id}/{session_id}")
    
    if not db:
        log_with_context("[DB_ADD_MULTILINGUAL_CHAT_ERROR] Firestore client not available", "error")
        return False

    try:
        # Создаем метаданные чата
        chat_meta_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id)
        meta_doc = chat_meta_ref.collection('meta').document('info')
        meta_doc.set({
            'original_language': original_language,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'languages': [original_language, 'en', 'th']  # Поддерживаемые языки
        })
        
        log_with_context(f"[DB_ADD_MULTILINGUAL_CHAT_SUCCESS] Created multilingual chat for {sender_id}/{session_id}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_ADD_MULTILINGUAL_CHAT_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to create multilingual chat for {sender_id}/{session_id}: {e}", exc_info=True)
        return False

def create_or_get_multilingual_chat(sender_id: str, session_id: str) -> str:
    """
    Создает или получает ID многоязычного чата.
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии
    
    Returns:
        str: ID чата (sender_id/session_id) или None при ошибке
    """
    log_with_context(f"[DB_CREATE_OR_GET_MULTILINGUAL_CHAT] Creating/getting chat for {sender_id}/{session_id}")
    
    if not db:
        log_with_context("[DB_CREATE_OR_GET_MULTILINGUAL_CHAT_ERROR] Firestore client not available", "error")
        return None

    try:
        # Проверяем, существует ли уже чат
        chat_meta_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id)
        meta_doc = chat_meta_ref.collection('meta').document('info')
        doc = meta_doc.get()
        
        if not doc.exists:
            # Создаем новый чат
            if add_multilingual_chat(sender_id, session_id):
                log_with_context(f"[DB_CREATE_OR_GET_MULTILINGUAL_CHAT_SUCCESS] Created new chat for {sender_id}/{session_id}")
            else:
                log_with_context(f"[DB_CREATE_OR_GET_MULTILINGUAL_CHAT_ERROR] Failed to create chat for {sender_id}/{session_id}", "error")
                return None
        else:
            log_with_context(f"[DB_CREATE_OR_GET_MULTILINGUAL_CHAT_EXISTS] Chat already exists for {sender_id}/{session_id}")
        
        return f"{sender_id}/{session_id}"
        
    except Exception as e:
        log_with_context(f"[DB_CREATE_OR_GET_MULTILINGUAL_CHAT_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to create/get multilingual chat for {sender_id}/{session_id}: {e}", exc_info=True)
        return None

def add_multilingual_message(chat_id: str, message_data: dict) -> bool:
    """
    Добавляет сообщение в многоязычный чат.
    
    Args:
        chat_id: ID чата (sender_id/session_id)
        message_data: Данные сообщения с переводами
    
    Returns:
        bool: True если успешно добавлено
    """
    log_with_context(f"[DB_ADD_MULTILINGUAL_MESSAGE_DATA] Adding message to chat {chat_id}")
    
    if not db:
        log_with_context("[DB_ADD_MULTILINGUAL_MESSAGE_DATA_ERROR] Firestore client not available", "error")
        return False

    try:
        # Разбираем chat_id
        if '/' not in chat_id:
            log_with_context(f"[DB_ADD_MULTILINGUAL_MESSAGE_DATA_ERROR] Invalid chat_id format: {chat_id}", "error")
            return False
        
        sender_id, session_id = chat_id.split('/', 1)
        
        # Генерируем message_id
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Сохраняем сообщение на всех языках
        for lang in ['original', 'en', 'th']:
            content_key = f'content_{lang}' if lang != 'original' else 'content_original'
            content = message_data.get(content_key, message_data.get('content_original', ''))
            
            if content:
                # Сохраняем в соответствующую языковую коллекцию
                lang_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id).collection('languages').document(lang)
                messages_ref = lang_ref.collection('messages')
                
                messages_ref.document(message_id).set({
                    'role': message_data.get('role', 'unknown'),
                    'content': content,
                    'language': lang,
                    'timestamp': message_data.get('timestamp', firestore.SERVER_TIMESTAMP),
                    'message_id': message_id
                })
        
        # Обновляем метаданные чата
        chat_meta_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id)
        meta_doc = chat_meta_ref.collection('meta').document('info')
        meta_doc.update({
            'updated_at': firestore.SERVER_TIMESTAMP,
            'last_message_id': message_id
        })
        
        log_with_context(f"[DB_ADD_MULTILINGUAL_MESSAGE_DATA_SUCCESS] Added message {message_id} to chat {chat_id}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_ADD_MULTILINGUAL_MESSAGE_DATA_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to add multilingual message to chat {chat_id}: {e}", exc_info=True)
        return False

def get_multilingual_chat_history(sender_id: str, session_id: str, language: str = "ru", limit: int = 100):
    """
    Получает историю многоязычного чата на указанном языке.
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии
        language: Язык для получения истории (ru, en, th)
        limit: Максимальное количество сообщений
    
    Returns:
        list: Список сообщений на указанном языке
    """
    log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_HISTORY] Getting {language} history for {sender_id}/{session_id}")
    
    if not db:
        log_with_context("[DB_GET_MULTILINGUAL_CHAT_HISTORY_ERROR] Firestore client not available", "error")
        return []

    try:
        # Получаем сообщения на указанном языке
        lang_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id).collection('languages').document(language)
        messages_ref = lang_ref.collection('messages')
        
        # Получаем сообщения, отсортированные по времени
        messages = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(limit).stream()
        
        chat_history = []
        for msg in messages:
            data = msg.to_dict()
            chat_history.append({
                'role': data.get('role'),
                'content': data.get('content'),
                'language': data.get('language'),
                'timestamp': data.get('timestamp'),
                'message_id': data.get('message_id')
            })
        
        log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_HISTORY_SUCCESS] Retrieved {len(chat_history)} messages for {sender_id}/{session_id} in {language}")
        return chat_history
        
    except Exception as e:
        log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_HISTORY_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get multilingual chat history for {sender_id}/{session_id}: {e}", exc_info=True)
        return []

def get_multilingual_chat_meta(sender_id: str, session_id: str):
    """
    Получает метаданные многоязычного чата.
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии
    
    Returns:
        dict: Метаданные чата или None если не найден
    """
    log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_META] Getting meta for {sender_id}/{session_id}")
    
    if not db:
        log_with_context("[DB_GET_MULTILINGUAL_CHAT_META_ERROR] Firestore client not available", "error")
        return None

    try:
        chat_meta_ref = db.collection('chats').document(sender_id).collection('sessions').document(session_id)
        meta_doc = chat_meta_ref.collection('meta').document('info')
        doc = meta_doc.get()
        
        if doc.exists:
            meta = doc.to_dict()
            log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_META_SUCCESS] Retrieved meta for {sender_id}/{session_id}")
            return meta
        else:
            log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_META_NOT_FOUND] No meta found for {sender_id}/{session_id}")
            return None
            
    except Exception as e:
        log_with_context(f"[DB_GET_MULTILINGUAL_CHAT_META_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get multilingual chat meta for {sender_id}/{session_id}: {e}", exc_info=True)
        return None

def sync_conversation_to_multilingual_chat(sender_id: str, session_id: str, original_language: str = "ru"):
    """
    Синхронизирует существующую переписку из conversations в многоязычный чат.
    
    Args:
        sender_id: ID отправителя
        session_id: ID сессии
        original_language: Исходный язык переписки
    
    Returns:
        bool: True если синхронизация успешна
    """
    log_with_context(f"[DB_SYNC_CONVERSATION] Syncing {sender_id}/{session_id} to multilingual chat")
    
    if not db:
        log_with_context("[DB_SYNC_CONVERSATION_ERROR] Firestore client not available", "error")
        return False

    try:
        # Получаем существующую историю
        original_history = get_conversation_history(sender_id, session_id, limit=1000)
        
        if not original_history:
            log_with_context(f"[DB_SYNC_CONVERSATION_NO_HISTORY] No history found for {sender_id}/{session_id}")
            return False
        
        # Создаем многоязычный чат
        if not add_multilingual_chat(sender_id, session_id, original_language):
            log_with_context(f"[DB_SYNC_CONVERSATION_CREATE_ERROR] Failed to create multilingual chat for {sender_id}/{session_id}")
            return False
        
        # Добавляем все сообщения
        for msg in original_history:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if content:  # Пропускаем пустые сообщения
                add_multilingual_message(
                    f"{sender_id}/{session_id}",
                    {
                        'role': role,
                        'content': content,
                        'timestamp': msg.get('timestamp')
                    }
                )
        
        log_with_context(f"[DB_SYNC_CONVERSATION_SUCCESS] Synced {len(original_history)} messages for {sender_id}/{session_id}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_SYNC_CONVERSATION_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to sync conversation for {sender_id}/{session_id}: {e}", exc_info=True)
        return False

def sync_conversations_to_multilingual_chats() -> bool:
    """
    Синхронизирует все существующие conversations в многоязычные чаты.
    
    Returns:
        bool: True если синхронизация успешна
    """
    log_with_context("[DB_SYNC_CONVERSATIONS_TO_CHATS] Starting sync of all conversations")
    
    if not db:
        log_with_context("[DB_SYNC_CONVERSATIONS_TO_CHATS_ERROR] Firestore client not available", "error")
        return False

    try:
        # Получаем всех пользователей из conversations
        sender_docs = db.collection('conversations').stream()
        total_synced = 0
        
        for sender_doc in sender_docs:
            sender_id = sender_doc.id
            session_docs = sender_doc.reference.collections()
            
            for session_ref in session_docs:
                session_id = session_ref.id
                
                # Проверяем, не синхронизирован ли уже этот чат
                meta = get_multilingual_chat_meta(sender_id, session_id)
                if not meta:
                    # Синхронизируем
                    if sync_conversation_to_multilingual_chat(sender_id, session_id):
                        total_synced += 1
                        log_with_context(f"[DB_SYNC_CONVERSATIONS_TO_CHATS] Synced {sender_id}/{session_id}")
        
        log_with_context(f"[DB_SYNC_CONVERSATIONS_TO_CHATS_SUCCESS] Synced {total_synced} conversations")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_SYNC_CONVERSATIONS_TO_CHATS_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to sync conversations to multilingual chats: {e}", exc_info=True)
        return False

def get_all_multilingual_chats():
    """
    Получает список всех многоязычных чатов.
    
    Returns:
        list: Список чатов с метаданными
    """
    log_with_context("[DB_GET_ALL_MULTILINGUAL_CHATS] Getting all multilingual chats")
    
    if not db:
        log_with_context("[DB_GET_ALL_MULTILINGUAL_CHATS_ERROR] Firestore client not available", "error")
        return []

    try:
        chats = []
        sender_docs = db.collection('chats').stream()
        
        for sender_doc in sender_docs:
            sender_id = sender_doc.id
            session_docs = sender_doc.reference.collections()
            
            for session_ref in session_docs:
                session_id = session_ref.id
                
                # Получаем метаданные
                meta = get_multilingual_chat_meta(sender_id, session_id)
                if meta:
                    chats.append({
                        'sender_id': sender_id,
                        'session_id': session_id,
                        'meta': meta
                    })
        
        log_with_context(f"[DB_GET_ALL_MULTILINGUAL_CHATS_SUCCESS] Retrieved {len(chats)} multilingual chats")
        return chats
        
    except Exception as e:
        log_with_context(f"[DB_GET_ALL_MULTILINGUAL_CHATS_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get all multilingual chats: {e}", exc_info=True)
        return []

def save_completed_chat(chat_data: dict):
    """Сохраняет завершенный диалог с переводами"""
    try:
        if not db:
            logger.error(f"Firestore client not available. Не удалось сохранить: session_id={chat_data.get('session_id')}, sender_id={chat_data.get('sender_id')}")
            return False
        doc_ref = db.collection('completed_chats').document(chat_data['session_id'])
        doc_ref.set(chat_data)
        logger.info(f"✅ Completed chat saved: session_id={chat_data['session_id']}, sender_id={chat_data.get('sender_id')}")
        print(f"✅ Completed chat saved: session_id={chat_data['session_id']}, sender_id={chat_data.get('sender_id')}")
        return True
    except Exception as e:
        logger.error(f"❌ Error saving completed chat: session_id={chat_data.get('session_id')}, sender_id={chat_data.get('sender_id')}, error={e}")
        print(f"❌ Error saving completed chat: session_id={chat_data.get('session_id')}, sender_id={chat_data.get('sender_id')}, error={e}")
        return False

def get_completed_chat(session_id: str) -> Optional[dict]:
    """Получает завершенный диалог из базы"""
    try:
        if not db:
            logger.error("Firestore client not available")
            return None
        doc_ref = db.collection('completed_chats').document(session_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting completed chat: {e}")
        return None

def update_translation_status(session_id: str, status: str):
    """Обновляет статус перевода диалога"""
    try:
        if not db:
            logger.error("Firestore client not available")
            return False
        doc_ref = db.collection('completed_chats').document(session_id)
        doc_ref.update({'translation_status': status})
        logger.info(f"Translation status updated: {session_id} -> {status}")
        return True
    except Exception as e:
        logger.error(f"Error updating translation status: {e}")
        return False

def get_chat_translation_status(session_id: str) -> Optional[str]:
    """Получает статус перевода диалога"""
    try:
        chat_data = get_completed_chat(session_id)
        if chat_data:
            return chat_data.get('translation_status')
        return None
    except Exception as e:
        logger.error(f"Error getting translation status: {e}")
        return None

def save_user_info(sender_id: str, user_name: str):
    """
    Сохраняет информацию о пользователе (имя) в базу данных.
    """
    log_with_context(f"[DB_SAVE_USER_INFO] Saving user info: {sender_id} -> {user_name}")
    
    if not db:
        log_with_context("[DB_SAVE_USER_INFO_ERROR] Firestore client not available", "error")
        logger.error("Firestore client not available. Cannot save user info.")
        return False

    try:
        # Сохраняем в коллекцию user_info
        doc_ref = db.collection('user_info').document(sender_id)
        doc_ref.set({
            'name': user_name,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        log_with_context(f"[DB_SAVE_USER_INFO_SUCCESS] User info saved: {sender_id} -> {user_name}")
        logger.info(f"User info saved: {sender_id} -> {user_name}")
        return True
        
    except Exception as e:
        log_with_context(f"[DB_SAVE_USER_INFO_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to save user info for {sender_id}: {e}", exc_info=True)
        return False

def get_user_info(sender_id: str):
    """
    Получает информацию о пользователе из базы данных.
    """
    log_with_context(f"[DB_GET_USER_INFO] Getting user info for: {sender_id}")
    
    if not db:
        log_with_context("[DB_GET_USER_INFO_ERROR] Firestore client not available", "error")
        logger.error("Firestore client not available. Cannot get user info.")
        return None

    try:
        doc_ref = db.collection('user_info').document(sender_id)
        doc = doc_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            user_name = user_data.get('name')
            log_with_context(f"[DB_GET_USER_INFO_SUCCESS] Found user info: {sender_id} -> {user_name}")
            return user_name
        else:
            log_with_context(f"[DB_GET_USER_INFO_NOT_FOUND] No user info found for: {sender_id}")
            return None
            
    except Exception as e:
        log_with_context(f"[DB_GET_USER_INFO_EXCEPTION] Error: {e}", "error")
        logger.error(f"Failed to get user info for {sender_id}: {e}", exc_info=True)
        return None 
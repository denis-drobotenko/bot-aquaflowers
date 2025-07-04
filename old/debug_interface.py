"""
Веб-интерфейс для отладки диалогов AuraFlora
"""

import logging
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import json
from . import database

logger = logging.getLogger(__name__)

# Router для debug интерфейса
debug_router = APIRouter(prefix="/debug")

# Хранилище логов
LOG_STORAGE = []

class DebugLogHandler(logging.Handler):
    """Собирает логи для отладки"""
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger_name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self.extract_session_id(record.getMessage())
            }
            LOG_STORAGE.append(log_entry)
            
            # Ограничиваем размер
            if len(LOG_STORAGE) > 1000:
                LOG_STORAGE.pop(0)
                
        except Exception:
            pass
    
    def extract_session_id(self, message: str) -> Optional[str]:
        """Извлекает session_id из сообщения"""
        patterns = [
            r'Session: ([^,\s]+)',
            r'session_id[=:\s]+([^,\s]+)', 
            r'for session ([^,\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

def setup_debug_logging():
    """Настраивает сбор логов"""
    handler = DebugLogHandler()
    
    loggers = ['ai_pipeline', 'json_processor', 'command_handler', 'whatsapp_utils', 'webhook_flow']
    
    for logger_name in loggers:
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(handler)

@debug_router.get("/", response_class=HTMLResponse)
async def debug_page():
    """Главная страница отладки"""
    
    try:
        with open("templates/debug_interface.html", "r", encoding="utf-8") as f:
            html = f.read()
    return HTMLResponse(content=html)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Debug interface template not found</h1>", status_code=404)

@debug_router.get("/api/sessions")
async def get_sessions():
    """Получение списка сессий"""
    try:
        sessions = []
        
        # Получаем session_id из логов
        session_ids = set()
        for log_entry in LOG_STORAGE:
            if log_entry.get('session_id'):
                session_ids.add(log_entry['session_id'])
        
        # Собираем данные по сессиям
        for session_id in session_ids:
            try:
                # Извлекаем sender_id из session_id
                sender_id = session_id.split('_')[0] if '_' in session_id else session_id
                history = database.get_conversation_history(sender_id, session_id, limit=50)
                
                if history:
                    sender_id = session_id.split('_')[0]
                    last_message = max(history, key=lambda x: x.get('timestamp', datetime.min))
                    
                    sessions.append({
                        'session_id': session_id,
                        'sender_id': sender_id,
                        'message_count': len(history),
                        'last_message_time': last_message.get('timestamp', datetime.now()).isoformat()
                    })
                    
            except Exception:
                continue
        
        sessions.sort(key=lambda x: x['last_message_time'], reverse=True)
        return JSONResponse(content=sessions)
        
    except Exception:
        return JSONResponse(content=[])

@debug_router.get("/api/session/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Получение сообщений сессии с логами"""
    try:
        # Извлекаем sender_id из session_id
        sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        history = database.get_conversation_history(sender_id, session_id, limit=100)
        
        messages = []
        for msg in history:
            messages.append({
                'role': msg.get('role', 'unknown'),
                'content': msg.get('content', ''),
                'timestamp': msg.get('timestamp', datetime.now()).isoformat()
            })
        
        # Логи для сессии
        session_logs = [log for log in LOG_STORAGE if log.get('session_id') == session_id]
        
        return JSONResponse(content={
            'messages': messages,
            'logs': session_logs
        })
        
    except Exception:
        return JSONResponse(content={'messages': [], 'logs': []})

@debug_router.get("/api/multilingual-chats")
async def get_multilingual_chats():
    """Получение списка многоязычных чатов"""
    try:
        chats = database.get_all_multilingual_chats()
        return JSONResponse(content=chats)
    except Exception as e:
        logger.error(f"Error getting multilingual chats: {e}")
        return JSONResponse(content=[])

@debug_router.get("/api/multilingual-chat/{session_id}")
async def get_multilingual_chat(session_id: str):
    """Получение многоязычного чата по session_id"""
    try:
        # Извлекаем sender_id из session_id
        sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        chat = database.get_multilingual_chat_history(sender_id, session_id)
        return JSONResponse(content=chat)
    except Exception as e:
        logger.error(f"Error getting multilingual chat: {e}")
        return JSONResponse(content=None)

@debug_router.post("/api/translate-chat/{session_id}")
async def translate_chat_endpoint(session_id: str):
    """Запуск перевода истории чата"""
    try:
        from . import ai_manager
        success = await ai_manager.translate_chat_history(session_id)
        return JSONResponse(content={"success": success})
    except Exception as e:
        logger.error(f"Error translating chat: {e}")
        return JSONResponse(content={"success": False, "error": str(e)})

@debug_router.get("/api/sync-conversations-to-chats")
async def sync_conversations_to_chats():
    """Синхронизация conversations в chats"""
    try:
        success = database.sync_conversations_to_multilingual_chats()
        return JSONResponse(content={"success": success})
    except Exception as e:
        logger.error(f"Error syncing conversations: {e}")
        return JSONResponse(content={"success": False, "error": str(e)})

# Инициализация
setup_debug_logging() 
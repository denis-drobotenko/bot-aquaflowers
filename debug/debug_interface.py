"""
Debug интерфейс для локальной разработки
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
from datetime import datetime
import re
import os

from debug.debug_logger import get_debug_logs
from src.services.session_service import SessionService
from src.services.message_service import MessageService

# Router для debug интерфейса
debug_router = APIRouter(prefix="/debug")

# Путь к шаблонам debug интерфейса
templates = Jinja2Templates(directory="debug/templates")

def setup_debug_routes(app):
    """Подключает debug роуты к приложению"""
    app.include_router(debug_router)

@debug_router.get("/", response_class=HTMLResponse)
async def debug_page(request: Request):
    """Главная страница отладки"""
    try:
        return templates.TemplateResponse("debug_interface.html", {"request": request})
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Debug interface template not found</h1>", status_code=404)

@debug_router.get("/api/sessions")
async def get_sessions():
    """Получение списка сессий"""
    try:
        sessions = []
        
        # Получаем session_id из логов
        debug_logs = get_debug_logs()
        session_ids = set()
        for log_entry in debug_logs:
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
        debug_logs = get_debug_logs()
        session_logs = [log for log in debug_logs if log.get('session_id') == session_id]
        
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
        return JSONResponse(content=None)

@debug_router.post("/api/translate-chat/{session_id}")
async def translate_chat_endpoint(session_id: str):
    """Запуск перевода истории чата"""
    try:
        from src import ai_manager
        success = await ai_manager.translate_chat_history(session_id)
        return JSONResponse(content={"success": success})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)})

@debug_router.get("/api/sync-conversations-to-chats")
async def sync_conversations_to_chats():
    """Синхронизация conversations в chats"""
    try:
        success = database.sync_conversations_to_multilingual_chats()
        return JSONResponse(content={"success": success})
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}) 
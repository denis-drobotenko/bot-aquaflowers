"""
Роуты для просмотра истории чата
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from src.services.message_service import MessageService
from src.services.session_service import SessionService
import os
import html

router = APIRouter(prefix="/chat", tags=["chat"])

# Инициализируем сервисы
message_service = MessageService()
session_service = SessionService()

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

def detect_original_language(text: str) -> tuple[str, str]:
    """
    Определяет оригинальный язык текста и возвращает (код_языка, название_языка, флаг)
    """
    if not text:
        return 'en', 'English', '🇬🇧'
    
    # Простые эвристики для определения языка
    text_lower = text.lower()
    
    # Русский язык
    russian_chars = [c for c in text_lower if 'а' <= c <= 'я' or c == 'ё']
    if len(russian_chars) > len(text) * 0.3:
        return 'ru', 'Русский', '🇷🇺'
    
    # Тайский язык
    thai_chars = [c for c in text if '\u0E00' <= c <= '\u0E7F']
    if len(thai_chars) > len(text) * 0.3:
        return 'th', 'ไทย', '🇹🇭'
    
    # Английский язык (по умолчанию)
    return 'en', 'English', '🇬🇧'

def get_available_languages(messages: list, user_language: str = None) -> list:
    """
    Определяет доступные языки на основе сообщений и сохраненного языка пользователя.
    Возвращает список кортежей (код_языка, название_языка, флаг, активный_язык)
    """
    if not messages:
        return [('en', 'English', '🇬🇧', True)]
    
    # Используем сохраненный язык пользователя или определяем по первому сообщению
    original_lang = 'en'
    original_name = 'English'
    original_flag = '🇬🇧'
    
    if user_language and user_language != 'auto':
        # Используем сохраненный язык
        if user_language == 'it':
            original_lang, original_name, original_flag = 'it', 'Italiano', '🇮🇹'
        elif user_language == 'ru':
            original_lang, original_name, original_flag = 'ru', 'Русский', '🇷🇺'
        elif user_language == 'en':
            original_lang, original_name, original_flag = 'en', 'English', '🇬🇧'
        elif user_language == 'th':
            original_lang, original_name, original_flag = 'th', 'ไทย', '🇹🇭'
        else:
            # Для других языков определяем по тексту
            for msg in messages:
                if msg.get('role') == 'user' and msg.get('content'):
                    original_lang, original_name, original_flag = detect_original_language(msg['content'])
                    break
    else:
        # Определяем по первому сообщению пользователя
        for msg in messages:
            if msg.get('role') == 'user' and msg.get('content'):
                original_lang, original_name, original_flag = detect_original_language(msg['content'])
                break
    
    # Проверяем, есть ли переводы
    has_en = any(msg.get('content_en') and msg['content_en'] != msg.get('content') for msg in messages)
    has_thai = any(msg.get('content_thai') and msg['content_thai'] != msg.get('content') for msg in messages)
    
    languages = []
    
    # Всегда показываем оригинальный язык
    languages.append((original_lang, original_name, original_flag, True))
    
    # Показываем английский только если он отличается от оригинального
    if has_en and original_lang != 'en':
        languages.append(('en', 'English', '🇬🇧', False))
    
    # Показываем тайский только если он отличается от оригинального
    if has_thai and original_lang != 'th':
        languages.append(('th', 'ไทย', '🇹🇭', False))
    
    return languages

def format_messages_for_language(messages: list, target_lang: str) -> str:
    """
    Форматирует сообщения для указанного языка
    """
    messages_html = ""
    
    for msg in messages:
        role = msg["role"]
        timestamp = msg["timestamp"]
        
        # Выбираем контент в зависимости от языка
        if target_lang == 'en' and msg.get('content_en'):
            content = msg['content_en']
        elif target_lang == 'th' and msg.get('content_thai'):
            content = msg['content_thai']
        else:
            content = msg.get('content', '')
        
        # Определяем класс сообщения
        message_class = "user" if role == "user" else "model"
        # avatar = "👤" if role == "user" else "🤖"  # убираем аватарки
        
        # Форматируем время
        time_str = ""
        if timestamp:
            try:
                from datetime import datetime
                if isinstance(timestamp, str):
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    dt = timestamp
                time_str = dt.strftime('%H:%M')
            except:
                time_str = ""
        
        # Сначала экранируем HTML, потом заменяем \n на <br>
        content_escaped = html.escape(content)
        content_with_breaks = content_escaped.replace('\\n', '<br>').replace('\n', '<br>')
        
        messages_html += f"""
            <div class="message {message_class}">
                <div class="message-content">{content_with_breaks}</div>
                {f'<div class="timestamp">{time_str}</div>' if time_str else ''}
            </div>
        """
    
    return messages_html

@router.get("/history/{sender_id}", response_class=HTMLResponse)
async def get_chat_history(request: Request, sender_id: str):
    """
    Показывает историю чата для конкретного пользователя.
    
    Args:
        request: FastAPI request
        sender_id: ID пользователя WhatsApp
        
    Returns:
        HTML страница с историей чата
    """
    try:
        print(f"[CHAT_HISTORY] Запрос истории чата для {sender_id}")
        
        # Получаем историю сообщений
        messages = await message_service.get_conversation_history_for_ai_by_sender(sender_id, limit=50)
        
        if not messages:
            print(f"[CHAT_HISTORY] История не найдена для {sender_id}")
            return templates.TemplateResponse(
                "chat_history_not_found.html",
                {"request": request, "sender_id": sender_id}
            )
        
        # Форматируем сообщения для отображения
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", ""),
                "content_en": msg.get("content_en", ""),
                "content_thai": msg.get("content_thai", ""),
                "timestamp": msg.get("timestamp", ""),
                "session_id": msg.get("session_id", "")
            }
            formatted_messages.append(formatted_msg)
        
        print(f"[CHAT_HISTORY] Найдено {len(formatted_messages)} сообщений")
        
        # Получаем информацию о пользователе
        user_info = await session_service.get_user_info(sender_id)
        user_name = user_info.get('name', 'Неизвестный пользователь')
        user_phone = user_info.get('phone', sender_id)
        
        # Получаем сохраненный язык пользователя
        user_language = await session_service.get_user_language(sender_id, formatted_messages[0].get('session_id', '')) if formatted_messages else 'auto'
        
        # Определяем доступные языки
        available_languages = get_available_languages(formatted_messages, user_language)
        
        # Формируем кнопки языков (только флаги)
        language_buttons_html = ""
        for lang_code, lang_name, lang_flag, is_active in available_languages:
            active_class = "active" if is_active else ""
            language_buttons_html += f'<button class="lang-btn {active_class}" data-lang="{lang_code}" title="{lang_name}">{lang_flag}</button>'
        
        # Формируем user_info HTML
        user_info_html = f"""
            <div class='user-header' style='display: flex; align-items: center; justify-content: center; gap: 16px; margin: 24px 0 12px 0;'>
                <span style='font-size:1.3em;font-weight:600;'>{user_name}</span>
                <a href='https://wa.me/{user_phone}' target='_blank' style='color:#34c759;text-decoration:none;font-size:1.1em;margin-left:12px;'>
                    {user_phone}
                </a>
            </div>
        """
        
        # Определяем активный язык (первый в списке)
        active_lang = available_languages[0][0] if available_languages else 'en'
        
        # Формируем HTML для сообщений на активном языке
        messages_html = format_messages_for_language(formatted_messages, active_lang)
        
        return templates.TemplateResponse(
            "chat_history.html",
            {
                "request": request,
                "sender_id": sender_id,
                "user_info": user_info_html,
                "language_buttons": language_buttons_html,
                "messages_html": messages_html,
                "available_languages": available_languages
            }
        )
        
    except Exception as e:
        print(f"[CHAT_HISTORY_ERROR] Ошибка получения истории: {e}")
        raise HTTPException(status_code=500, detail="Error loading chat history")

@router.get("/history/{sender_id}/{session_id}", response_class=HTMLResponse)
async def get_session_history(request: Request, sender_id: str, session_id: str):
    """
    Показывает историю конкретной сессии.
    
    Args:
        request: FastAPI request
        sender_id: ID пользователя WhatsApp
        session_id: ID сессии
        
    Returns:
        HTML страница с историей сессии
    """
    try:
        print(f"[SESSION_HISTORY] Запрос истории сессии {session_id} для {sender_id}")
        
        # Получаем историю сообщений для конкретной сессии
        messages = await message_service.get_conversation_history_for_ai_by_sender(
            sender_id, session_id, limit=50
        )
        
        if not messages:
            print(f"[SESSION_HISTORY] История сессии не найдена: {session_id}")
            return templates.TemplateResponse(
                "chat_history_not_found.html",
                {"request": request, "sender_id": sender_id, "session_id": session_id}
            )
        
        # Форматируем сообщения для отображения
        formatted_messages = []
        for msg in messages:
            formatted_msg = {
                "role": msg.get("role", "unknown"),
                "content": msg.get("content", ""),
                "content_en": msg.get("content_en", ""),
                "content_thai": msg.get("content_thai", ""),
                "timestamp": msg.get("timestamp", ""),
                "session_id": msg.get("session_id", "")
            }
            formatted_messages.append(formatted_msg)
        
        print(f"[SESSION_HISTORY] Найдено {len(formatted_messages)} сообщений в сессии")
        
        # Получаем информацию о пользователе
        user_info = await session_service.get_user_info(sender_id)
        user_name = user_info.get('name', 'Неизвестный пользователь')
        user_phone = user_info.get('phone', sender_id)
        
        # Получаем сохраненный язык пользователя
        user_language = await session_service.get_user_language(sender_id, session_id)
        
        # Определяем доступные языки
        available_languages = get_available_languages(formatted_messages, user_language)
        
        # Формируем кнопки языков (только флаги)
        language_buttons_html = ""
        for lang_code, lang_name, lang_flag, is_active in available_languages:
            active_class = "active" if is_active else ""
            language_buttons_html += f'<button class="lang-btn {active_class}" data-lang="{lang_code}" title="{lang_name}">{lang_flag}</button>'
        
        # Формируем user_info HTML
        user_info_html = f"""
            <div class='user-header' style='display: flex; align-items: center; justify-content: center; gap: 16px; margin: 24px 0 12px 0;'>
                <span style='font-size:1.3em;font-weight:600;'>{user_name}</span>
                <a href='https://wa.me/{user_phone}' target='_blank' style='color:#34c759;text-decoration:none;font-size:1.1em;margin-left:12px;'>
                    {user_phone}
                </a>
            </div>
        """
        
        # Определяем активный язык (первый в списке)
        active_lang = available_languages[0][0] if available_languages else 'en'
        
        # Формируем HTML для сообщений на активном языке
        messages_html = format_messages_for_language(formatted_messages, active_lang)
        
        return templates.TemplateResponse(
            "chat_history.html",
            {
                "request": request,
                "sender_id": sender_id,
                "session_id": session_id,
                "user_info": user_info_html,
                "language_buttons": language_buttons_html,
                "messages_html": messages_html,
                "available_languages": available_languages
            }
        )
        
    except Exception as e:
        print(f"[SESSION_HISTORY_ERROR] Ошибка получения истории сессии: {e}")
        raise HTTPException(status_code=500, detail="Error loading session history")

@router.get("/api/messages/{sender_id}/{session_id}/{language}")
async def get_messages_by_language(request: Request, sender_id: str, session_id: str, language: str):
    """
    API endpoint для получения сообщений на определенном языке
    """
    try:
        print(f"[API_MESSAGES] Запрос сообщений для {sender_id}/{session_id} на языке {language}")
        
        # Получаем историю сообщений напрямую из репозитория
        from src.repositories.message_repository import MessageRepository
        message_repo = MessageRepository()
        messages = await message_repo.get_conversation_history_by_sender(sender_id, session_id, limit=50)
        
        print(f"[API_MESSAGES] Получено {len(messages)} сообщений")
        
        if not messages:
            return {"messages": "", "error": "No messages found"}
        
        # Форматируем сообщения для указанного языка
        messages_html = format_messages_for_language(messages, language)
        
        return {"messages": messages_html}
        
    except Exception as e:
        print(f"[API_MESSAGES_ERROR] Error getting messages: {e}")
        return {"messages": "", "error": str(e)} 
"""
Утилиты для работы с HTML шаблонами
"""

import os
from typing import Dict, Any, Optional, List
from fastapi.responses import HTMLResponse

def load_template(template_name: str) -> str:
    """Загружает HTML шаблон из файла"""
    template_path = os.path.join("templates", template_name)
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template not found: {template_path}")

def render_chat_history_template(user_info: str, messages_html: str) -> str:
    """Рендерит шаблон истории чата"""
    try:
        template = load_template("chat_history.html")
        return template.format(user_info=user_info, messages_html=messages_html)
    except FileNotFoundError:
        # Fallback шаблон
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>История переписки</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>История переписки</h1>
            <div class="session-info">{user_info}</div>
            <div class="chat-container">{messages_html}</div>
            <div class="back-link">
                <a href="/">← Вернуться на главную</a>
            </div>
        </body>
        </html>
        """

def render_error_template(error_message: str, traceback_text: str = "") -> str:
    """Рендерит шаблон ошибки"""
    try:
        template = load_template("chat_history_not_found.html")
        # Форматируем traceback для HTML
        traceback_html = f'<pre class="traceback">{traceback_text}</pre>' if traceback_text else ''
        return template.format(error_message=error_message, traceback_text=traceback_html)
    except FileNotFoundError:
        # Fallback шаблон ошибки
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Ошибка загрузки истории</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ color: red; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>История переписки не найдена</h1>
            <p class="error">Не удалось загрузить историю переписки.</p>
            <p class="error"><b>Текст ошибки:</b> {error_message}</p>
            {f'<pre>{traceback_text}</pre>' if traceback_text else ''}
            <div class="back-link">
                <a href="/">← Вернуться на главную</a>
            </div>
        </body>
        </html>
        """

def format_message_html(role: str, content: str, timestamp: Any, avatar_text: str = None) -> str:
    """Форматирует сообщение в HTML"""
    # Определяем аватар по умолчанию
    if avatar_text is None:
        if role == 'user':
            avatar_text = 'U'
        elif role in ['model', 'assistant']:
            avatar_text = '🌹'
        else:  # system
            avatar_text = '⚙️'
    
    # Определяем класс сообщения
    if role == 'user':
        message_class = 'user'
    elif role in ['model', 'assistant']:
        message_class = 'model'
    else:  # system
        message_class = 'system'
    
    # Экранируем HTML в содержимом
    content_escaped = content.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')
    
    # Добавляем отладочную информацию для системных сообщений
    if role == 'system':
        content_escaped = f"<strong>[{role.upper()}]</strong> {content_escaped}"
    
    # Форматируем timestamp
    timestamp_display = timestamp
    if hasattr(timestamp, 'strftime'):
        timestamp_display = timestamp.strftime('%d.%m.%Y %H:%M:%S')
    elif isinstance(timestamp, str):
        timestamp_display = timestamp
    
    return f"""
        <div class="message {message_class}" data-role="{role}">
            <div class="avatar {message_class}">{avatar_text}</div>
            <div class="message-content">
                {content_escaped}
            </div>
        </div>
        <div class="timestamp">{timestamp_display}</div>
    """

def format_user_info(user_name: Optional[str], user_phone: Optional[str], language: str = 'ru') -> str:
    """Форматирует информацию о пользователе: имя и телефон (ссылка на WhatsApp)"""
    if user_name and user_phone:
        # Формируем ссылку на WhatsApp
        phone_clean = ''.join(filter(str.isdigit, user_phone))
        wa_link = f"https://wa.me/{phone_clean}"
        return f'<div class="client-header"><span class="client-name">{user_name}</span> <a class="client-phone" href="{wa_link}" target="_blank">{user_phone}</a></div>'
    elif user_name:
        return f'<div class="client-header"><span class="client-name">{user_name}</span></div>'
    elif user_phone:
        phone_clean = ''.join(filter(str.isdigit, user_phone))
        wa_link = f"https://wa.me/{phone_clean}"
        return f'<div class="client-header"><a class="client-phone" href="{wa_link}" target="_blank">{user_phone}</a></div>'
    return ''

def process_chat_messages(messages: List[Dict[str, Any]]) -> str:
    """Обрабатывает сообщения и формирует HTML"""
    messages_html = ""
    
    for i, msg in enumerate(messages):
        try:
            role = msg.get('role', 'unknown')
            timestamp = msg.get('timestamp', '')
            
            # Получаем содержимое сообщения - поддерживаем оба формата
            content = msg.get('content', '')
            
            # Если нет content, проверяем parts (новый формат)
            if not content and 'parts' in msg:
                parts = msg.get('parts', [])
                if parts and isinstance(parts[0], dict) and 'text' in parts[0]:
                    content = parts[0]['text']
                elif parts and isinstance(parts[0], str):
                    content = parts[0]
            
            # Если все еще нет содержимого, пропускаем сообщение
            if not content:
                continue
            
            # Форматируем сообщение в HTML
            message_html = format_message_html(role, content, timestamp)
            messages_html += message_html
            
        except Exception as e:
            continue
    
    return messages_html 
 
"""
Менеджер переводов чатов
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from google.generativeai import GenerationConfig

from . import database
from .config import GEMINI_API_KEY, TRANSLATION_MODEL

logger = logging.getLogger(__name__)

def translate_chat_batch(messages: List[Dict[str, Any]], target_lang: str, model_name: str = None) -> str:
    """Переводит сообщения по одному и возвращает готовую HTML верстку"""
    try:
        logger.info(f"Starting translation batch for {target_lang}, messages count: {len(messages)}")
        
        # Определяем язык перевода
        lang_names = {
            'en': 'English',
            'th': 'Thai',
            'ru': 'Russian'
        }
        target_lang_name = lang_names.get(target_lang, 'English')
        
        # Настраиваем модель для быстрого перевода
        use_model = "gemini-2.0-flash-exp"
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=use_model,
            generation_config=GenerationConfig(
                temperature=0.1,  # Низкая температура для стабильности
                max_output_tokens=1024,  # Меньше токенов для скорости
                top_p=0.8
            )
        )
        
        # Формируем HTML верстку
        html_parts = []
        
        for i, msg in enumerate(messages):
            # Получаем содержимое сообщения
            content = msg.get('content', '') or msg.get('content_original', '') or msg.get('text', '')
            
            if not content:
                continue
                
            # Определяем роль
            is_user = msg['role'] == 'user'
            
            # Если это русский язык, не переводим
            if target_lang == 'ru':
                translated_content = content
            else:
                # Переводим одно сообщение
                try:
                    prompt = f"""Переведи на {target_lang_name} только этот текст, сохрани форматирование и эмодзи:

{content}

Перевод:"""
                    
                    response = model.generate_content(prompt)
                    translated_content = response.text.strip()
                    
                    # Если перевод не удался, используем оригинал
                    if not translated_content or len(translated_content) < 2:
                        translated_content = content
                        
                except Exception as e:
                    logger.error(f"Error translating message {i+1}: {e}")
                    translated_content = content
            
            # Формируем HTML для сообщения
            if is_user:
                html_parts.append(f'<div class="message user-message"><div class="message-content">{translated_content}</div></div>')
            else:
                html_parts.append(f'<div class="message bot-message"><div class="message-content">{translated_content}</div></div>')
        
        result_html = '\n'.join(html_parts)
        logger.info(f"Translation completed for {target_lang}, HTML length: {len(result_html)}")
        return result_html
        
    except Exception as e:
        logger.error(f"Error translating chat batch: {e}")
        return ""

def format_timestamp(timestamp: Any) -> str:
    """Форматирует timestamp для отображения"""
    if hasattr(timestamp, 'strftime'):
        return timestamp.strftime('%H:%M')
    elif isinstance(timestamp, str):
        return timestamp[:5] if len(timestamp) >= 5 else timestamp
    return ""

def extract_order_summary(conversation_history: List[Dict]) -> Dict[str, Any]:
    """Извлекает сводку заказа из истории диалога"""
    order_summary = {}
    
    for msg in conversation_history:
        if msg.get('role') == 'system':
            content = msg.get('content', '')
            if content.startswith('order_info:'):
                # Извлекаем информацию о заказе
                parts = content.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].replace('order_info:', '').strip()
                    value = parts[1].strip()
                    order_summary[key] = value
    
    return order_summary

async def save_completed_chat_with_translations(sender_id: str, session_id: str):
    """Сохраняет завершенный диалог с переводами"""
    try:
        logger.info(f"Starting to save completed chat with translations: {session_id}")
        
        # Получаем историю диалога
        conversation_history = database.get_conversation_history(sender_id, session_id)
        
        # Формируем структуру для сохранения
        chat_data = {
            'session_id': session_id,
            'sender_id': sender_id,
            'messages': [],
            'translations': {},
            'translation_status': 'in_progress',
            'completed_at': datetime.now(),
            'order_summary': extract_order_summary(conversation_history)
        }
        
        # Сохраняем оригинальные сообщения
        for msg in conversation_history:
            if msg.get('role') in ['user', 'model']:
                chat_data['messages'].append({
                    'role': msg['role'],
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp')
                })
        
        # Сохраняем в базу с статусом "переводится"
        database.save_completed_chat(chat_data)
        logger.info(f"Original chat saved, starting translations: {session_id}")
        
        # Запускаем переводы в фоне
        if chat_data['messages']:
            # Перевод на английский
            en_translation = translate_chat_batch(chat_data['messages'], 'en')
            if en_translation:
                chat_data['translations']['en'] = en_translation
                logger.info(f"English translation completed: {session_id}")
            
            # Перевод на тайский
            th_translation = translate_chat_batch(chat_data['messages'], 'th')
            if th_translation:
                chat_data['translations']['th'] = th_translation
                logger.info(f"Thai translation completed: {session_id}")
        
        # Сохраняем в базу с переводами
        database.save_completed_chat(chat_data)
        
        # Обновляем статус
        database.update_translation_status(session_id, 'completed')
        logger.info(f"Chat translations completed: {session_id}")
        
    except Exception as e:
        logger.error(f"Error saving completed chat with translations: {e}")
        database.update_translation_status(session_id, 'failed')

async def ensure_chat_messages_available(session_id: str) -> List[Dict[str, Any]]:
    """Проверяет наличие сообщений и заполняет их при необходимости"""
    try:
        # Сначала проверяем completed_chats
        completed_chat = database.get_completed_chat(session_id)
        if completed_chat and completed_chat.get('messages'):
            logger.info(f"Found messages in completed_chats for session: {session_id}")
            return completed_chat['messages']
        
        # Если нет в completed_chats, проверяем chat_sessions
        from .chat_history_processor import get_chat_history_data
        data = get_chat_history_data(session_id)
        messages = data['chat_history'].get('messages', [])
        
        if messages:
            logger.info(f"Found messages in chat_sessions for session: {session_id}")
            return messages
        
        # Если нет нигде, создаем мок-данные для тестирования
        if session_id == "test_user_123_local_dev":
            logger.info(f"Creating mock messages for test session: {session_id}")
            from .chat_history_processor import create_mock_chat_history
            mock_messages = create_mock_chat_history()
            return mock_messages
        
        logger.warning(f"No messages found for session: {session_id}")
        return []
        
    except Exception as e:
        logger.error(f"Error ensuring chat messages: {e}")
        return []

async def translate_unfinished_chat(session_id: str, target_lang: str) -> Dict[str, Any]:
    """Переводит незавершенный диалог по запросу"""
    try:
        logger.info(f"Starting translation for unfinished chat: {session_id}, lang: {target_lang}")
        print(f"🔄 Starting translation for: {session_id}, lang: {target_lang}")
        
        # Проверяем, есть ли уже завершенный диалог
        try:
            completed_chat = database.get_completed_chat(session_id)
            print(f"📋 get_completed_chat result: {completed_chat is not None}")
            if completed_chat:
                print(f"✅ Found completed_chat with translations: {list(completed_chat.get('translations', {}).keys())}")
                # Используем готовый перевод
                translations = completed_chat.get('translations', {})
                if target_lang in translations:
                    print(f"🎯 Using cached translation for {target_lang}")
                    translated_text = translations[target_lang]
                    # Форматируем текст как HTML
                    formatted_html = format_translated_text_as_html(translated_text)
                    return {"success": True, "translated_html": formatted_html}
                else:
                    print(f"❌ No cached translation for {target_lang}, available: {list(translations.keys())}")
            else:
                print(f"❌ No completed_chat found for {session_id}")
        except Exception as e:
            print(f"❌ Error in get_completed_chat: {e}")
            logger.error(f"Error getting completed chat: {e}")
        
        # Убеждаемся, что сообщения доступны
        messages = await ensure_chat_messages_available(session_id)
        
        if not messages:
            return {"error": "No messages found"}
        
        print(f"🔄 Generating new translation for {target_lang}")
        # Переводим диалог и получаем готовую HTML верстку
        translated_html = translate_chat_batch(messages, target_lang)
        
        if not translated_html:
            return {"error": "Translation failed"}
        
        # Сохраняем перевод в базу (как HTML)
        try:
            # Получаем или создаем запись в completed_chats
            completed_chat = database.get_completed_chat(session_id)
            if not completed_chat:
                # Создаем новую запись
                completed_chat = {
                    'session_id': session_id,
                    'messages': messages,
                    'translations': {},
                    'completed_at': datetime.now()
                }
            
            # Добавляем перевод
            completed_chat['translations'][target_lang] = translated_html
            
            # Сохраняем в базу
            database.save_completed_chat(completed_chat)
            logger.info(f"Translation saved to database for {target_lang}")
            
        except Exception as e:
            logger.error(f"Error saving translation to database: {e}")
        
        return {
            "success": True,
            "translated_html": translated_html,
            "lang": target_lang
        }
        
    except Exception as e:
        logger.error(f"Error translating unfinished chat: {e}")
        print(f"❌ Error in translate_unfinished_chat: {e}")
        return {"error": str(e)}

def format_translated_text_as_html(translated_text: str) -> str:
    """Форматирует переведенный текст как HTML"""
    try:
        lines = translated_text.split('\n')
        html_parts = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Определяем роль сообщения по эмодзи
            if '👤' in line or 'User' in line or 'ผู้ใช้' in line:
                # Сообщение пользователя
                content = extract_message_content(line)
                html_parts.append(f'<div class="message user-message"><div class="message-content">{content}</div></div>')
            elif '🤖' in line or 'Bot' in line or 'บอท' in line:
                # Сообщение бота
                content = extract_message_content(line)
                html_parts.append(f'<div class="message bot-message"><div class="message-content">{content}</div></div>')
            else:
                # Обычный текст
                html_parts.append(f'<div class="message-text">{line}</div>')
        
        return '\n'.join(html_parts)
        
    except Exception as e:
        logger.error(f"Error formatting translated text as HTML: {e}")
        # Fallback - просто оборачиваем в div
        return f'<div class="translated-text">{translated_text}</div>'

def extract_message_content(line: str) -> str:
    """Извлекает содержимое сообщения из строки"""
    try:
        # Ищем контент после двоеточия
        if ': ' in line:
            return line.split(': ', 1)[1]
        return line
    except:
        return line 
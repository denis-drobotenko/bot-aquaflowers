"""
Обработчики webhook-ов для WhatsApp Business API
"""

import logging
import re
import time
import os
from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import PlainTextResponse, JSONResponse, HTMLResponse
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from . import database
from . import whatsapp_utils
from . import command_handler
from . import ai_manager
from .config import VERIFY_TOKEN, GEMINI_API_KEY
import google.generativeai as genai
from google.generativeai import GenerationConfig
import inspect
import sys
sys.path.append('archive')
from get_logs_api_fixed import get_logs_via_api
import traceback

logger = logging.getLogger(__name__)

# Создаем специальный logger для webhook flow
webhook_logger = logging.getLogger('webhook_flow')

# Создаем специальный logger для AI пайплайна
ai_pipeline_logger = logging.getLogger('ai_pipeline')

router = APIRouter()

FORCED_SESSION_IDS = {}

# Импортируем менеджер сессий
from . import session_manager

# --- Вспомогательные функции для парсинга Webhook ---

def get_sender_id(body: dict) -> str | None:
    """Извлекает ID отправителя из тела запроса."""
    try:
        return body['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    except (KeyError, IndexError):
        return None

def get_sender_name(body: dict) -> str | None:
    """Извлекает имя отправителя из тела запроса."""
    try:
        profile = body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']
        full_name = profile.get('name', '')
        
        # Берем только первое имя (до первого пробела)
        if full_name:
            first_name = full_name.split()[0]
            return first_name
        return None
    except (KeyError, IndexError):
        return None

def get_message_text(body: dict) -> str | None:
    """Извлекает текст сообщения из тела запроса."""
    try:
        return body['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    except (KeyError, IndexError):
        return None

def get_interactive_message(body: dict) -> dict | None:
    """Извлекает интерактивное сообщение (кнопки, элементы каталога, корзина)."""
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if 'interactive' in message:
            return message['interactive']
        return None
    except (KeyError, IndexError):
        return None

def get_button_reply(body: dict) -> dict | None:
    """Извлекает ответ на кнопку."""
    try:
        interactive = get_interactive_message(body)
        if interactive and interactive.get('type') == 'button_reply':
            return {
                'type': 'button_reply',
                'id': interactive['button_reply']['id'],
                'title': interactive['button_reply']['title']
            }
        return None
    except (KeyError, IndexError):
        return None

def get_list_reply(body: dict) -> dict | None:
    """Извлекает ответ на список."""
    try:
        interactive = get_interactive_message(body)
        if interactive and interactive.get('type') == 'list_reply':
            return {
                'type': 'list_reply',
                'id': interactive['list_reply']['id'],
                'title': interactive['list_reply']['title'],
                'description': interactive['list_reply'].get('description', '')
            }
        return None
    except (KeyError, IndexError):
        return None

def get_product(body: dict) -> dict | None:
    """Извлекает информацию о выбранном товаре из каталога."""
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if 'product' in message:
            return {
                'type': 'product',
                'product_id': message['product']['id'],
                'catalog_id': message['product']['catalog_id'],
                'product_retailer_id': message['product']['product_retailer_id']
            }
        return None
    except (KeyError, IndexError):
        return None

def get_order(body: dict) -> dict | None:
    """Извлекает информацию о заказе из корзины."""
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if 'order' in message:
            return {
                'type': 'order',
                'order_id': message['order']['id'],
                'catalog_id': message['order']['catalog_id'],
                'product_items': message['order'].get('product_items', [])
            }
        return None
    except (KeyError, IndexError):
        return None

def is_valid_whatsapp_message(body: Dict[str, Any]) -> bool:
    """Проверяет, является ли webhook валидным сообщением от пользователя."""
    try:
        return (
            body.get("object") == "whatsapp_business_account" and
            body["entry"][0]["changes"][0]["value"]["messages"][0]
        )
    except (KeyError, IndexError):
        return False

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
        webhook_logger.info(full_message)
    elif level == "error":
        webhook_logger.error(full_message)
    elif level == "warning":
        webhook_logger.warning(full_message)

# --- Конечные точки Webhook ---

@router.get("/webhook")
async def verify_webhook(request: Request):
    """Проверка webhook от Meta"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        logger.error("Webhook verification failed")
        return Response(content="Failed to verify webhook", status_code=403)

@router.post("/webhook")
async def webhook_handler(request: Request):
    """Обрабатывает входящие webhook от WhatsApp Business API"""
    try:
        # Импорты в начале функции
        from . import session_manager, database, ai_manager, whatsapp_utils, command_handler
        
        # 🔍 ЛОГИРОВАНИЕ НАЧАЛА WEBHOOK
        log_with_context("[WEBHOOK_START] ==================== WEBHOOK RECEIVED ====================")
        log_with_context(f"[WEBHOOK_CALLER] {get_caller_info()}")
        
        # Получаем тело запроса
        body = await request.json()
        log_with_context(f"[WEBHOOK_BODY] Request body: {body}")
        
        # Проверяем валидность сообщения
        if not is_valid_whatsapp_message(body):
            log_with_context("[WEBHOOK_INVALID] Invalid WhatsApp message, ignoring")
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        
        # 🔍 ЛОГИРОВАНИЕ ВАЛИДНОГО СООБЩЕНИЯ
        log_with_context("[WEBHOOK_VALID] Valid WhatsApp message received")
        
        # Извлекаем данные из сообщения
        sender_id = get_sender_id(body)
        sender_name = get_sender_name(body)
        message_body = get_message_text(body)
        
        # 🔍 ЛОГИРОВАНИЕ ИЗВЛЕЧЕННЫХ ДАННЫХ
        log_with_context(f"[WEBHOOK_EXTRACTED] Sender ID: {sender_id}")
        log_with_context(f"[WEBHOOK_EXTRACTED] Sender Name: {sender_name}")
        log_with_context(f"[WEBHOOK_EXTRACTED] Message Body: {message_body}")
        
        # Проверяем, что есть sender_id и message_body
        if not sender_id or not message_body:
            log_with_context("[WEBHOOK_MISSING_DATA] Missing sender_id or message_body")
            return JSONResponse(content={"status": "error", "message": "Missing required data"}, status_code=400)
        
        # 🔍 ЛОГИРОВАНИЕ ТИПА СООБЩЕНИЯ
        message_type = body['entry'][0]['changes'][0]['value']['messages'][0]['type']
        logger.info(f"[RAW_MESSAGE] Message type: {message_type}")
        log_with_context(f"[WEBHOOK_RAW_MESSAGE] Type: {message_type}")
        
        # 🔍 ЛОГИРОВАНИЕ ПОЛНЫХ ДАННЫХ СООБЩЕНИЯ
        full_message_data = body['entry'][0]['changes'][0]['value']['messages'][0]
        logger.info(f"[RAW_MESSAGE] Full message data: {full_message_data}")
        log_with_context(f"[WEBHOOK_RAW_MESSAGE] Full data: {full_message_data}")
        
        # Проверяем различные типы сообщений
        button_reply = get_button_reply(body)
        list_reply = get_list_reply(body)
        product = get_product(body)
        order = get_order(body)
        
        # 🔍 ЛОГИРОВАНИЕ ТИПОВ СООБЩЕНИЙ
        log_with_context(f"[WEBHOOK_MESSAGE_TYPES] Button: {button_reply}, List: {list_reply}, Product: {product}, Order: {order}")
        
        # Обрабатываем текстовые сообщения
        if message_type == 'text':
            logger.info(f"[TEXT] Text message: {message_body}")
            log_with_context(f"[WEBHOOK_TEXT_MESSAGE] {message_body}")
        elif message_type == 'button':
            if button_reply:
                message_body = button_reply.get('title', '')
                logger.info(f"[BUTTON] Button reply: {message_body}")
                log_with_context(f"[WEBHOOK_BUTTON_MESSAGE] {message_body}")
        elif message_type == 'interactive':
            if list_reply:
                message_body = list_reply.get('title', '')
                logger.info(f"[LIST] List reply: {message_body}")
                log_with_context(f"[WEBHOOK_LIST_MESSAGE] {message_body}")
        elif message_type == 'order':
            if order:
                message_body = f"Заказ: {order.get('id', 'Unknown')}"
                logger.info(f"[ORDER] Order message: {message_body}")
                log_with_context(f"[WEBHOOK_ORDER_MESSAGE] {message_body}")
        else:
            logger.warning(f"[UNKNOWN] Unknown message type: {message_type}")
            log_with_context(f"[WEBHOOK_UNKNOWN_TYPE] Unknown message type: {message_type}")
            return JSONResponse(content={"status": "ignored", "message": "Unknown message type"}, status_code=200)
        
        # 🔍 ЛОГИРОВАНИЕ УПРАВЛЕНИЯ СЕССИЯМИ
        log_with_context("[WEBHOOK_SESSION_START] ==================== SESSION ID MANAGEMENT ====================")
        
        # Получаем или создаем session_id
        if sender_id in FORCED_SESSION_IDS:
            session_id = FORCED_SESSION_IDS[sender_id]
            log_with_context(f"[WEBHOOK_SESSION_FORCED] Using forced session: {session_id}")
        else:
            # Используем менеджер сессий для проверки базы данных
            session_id = session_manager.get_or_create_session_id(sender_id)
            log_with_context(f"[WEBHOOK_SESSION_MANAGED] Using managed session: {session_id}")
        
        # 🔍 ЛОГИРОВАНИЕ СЕССИИ
        log_with_context(f"[WEBHOOK_SESSION_FINAL] Final Session ID: {session_id}")
        
        logger.info(f"Using session_id: {session_id}")

        # Проверяем, есть ли reply на сообщение с букетом
        original_message = body['entry'][0]['changes'][0]['value']['messages'][0]
        # Извлекаем reply_to_message_id из context.id (WhatsApp Business API формат)
        reply_to = None
        if 'context' in original_message and 'id' in original_message['context']:
            reply_to = original_message['context']['id']
        
        # 🔍 ЛОГИРОВАНИЕ REPLY
        log_with_context(f"[WEBHOOK_REPLY] Reply to message ID: {reply_to}")
        
        # Если это reply, добавляем контекст к сообщению пользователя
        if reply_to:
            logger.info(f"[REPLY_DEBUG] Found reply_to_message_id: {reply_to}")
            # Получаем сообщение по WA ID
            replied_message = database.get_message_by_wa_id(sender_id, session_id, reply_to)
            
            if replied_message:
                # Добавляем контекст reply к сообщению пользователя
                replied_text = replied_message.get('content', '')
                message_body = f"{message_body} (ответ на: {replied_text})"
                logger.info(f"[REPLY_DEBUG] Enhanced message with reply context: {message_body}")
                log_with_context(f"[WEBHOOK_REPLY_CONTEXT] Enhanced message: {message_body}")
        
        # 🔍 ЛОГИРОВАНИЕ СОХРАНЕНИЯ СООБЩЕНИЯ ПОЛЬЗОВАТЕЛЯ
        log_with_context(f"[WEBHOOK_SAVE_USER_MESSAGE] Saving user message to database")
        
        # Сохраняем имя пользователя при первом сообщении
        if sender_name:
            database.save_user_info(sender_id, sender_name)
            log_with_context(f"[WEBHOOK_USER_INFO_SAVED] User name saved: {sender_name}")
        
        # Извлекаем WA message ID из входящего сообщения
        wa_message_id = None
        try:
            message_data = body['entry'][0]['changes'][0]['value']['messages'][0]
            wa_message_id = message_data.get('id')
            log_with_context(f"[WEBHOOK_WA_MESSAGE_ID] Extracted WA message ID: {wa_message_id}")
        except Exception as e:
            log_with_context(f"[WEBHOOK_WA_MESSAGE_ID_ERROR] Failed to extract WA message ID: {e}")
        
        # Добавляем сообщение в историю с WA ID (если есть)
        if wa_message_id:
            database.add_message_with_wa_id(sender_id, session_id, "user", message_body, wa_message_id)
            log_with_context(f"[WEBHOOK_USER_MESSAGE_SAVED_WA_ID] User message saved with WA ID: {wa_message_id}")
        else:
            database.add_message(sender_id, session_id, "user", message_body)
            log_with_context(f"[WEBHOOK_USER_MESSAGE_SAVED_AUTO_ID] User message saved with auto-generated ID")
        
        logger.info(f"[CHAT_LOG] USER ({sender_id}): {message_body}")
        
        log_with_context(f"[WEBHOOK_USER_MESSAGE_SAVED] User message saved")
        
        # Получаем язык пользователя из сессии (определяем только если еще не был сохранен)
        user_lang = ai_manager.get_user_language_from_session(sender_id, session_id)
        if user_lang == 'auto' or not user_lang:
            # Определяем язык только по первым сообщениям
            user_lang = ai_manager.detect_user_language(message_body)
            ai_manager.save_user_language_to_session(sender_id, session_id, user_lang)
            logger.info(f"[CHAT_LOG] Detected and saved user language: {user_lang}")
            log_with_context(f"[WEBHOOK_LANG_DETECTED] Language detected and saved: {user_lang}")
        else:
            logger.info(f"[CHAT_LOG] Using language from session: {user_lang}")
            log_with_context(f"[WEBHOOK_LANG_FROM_SESSION] Using existing language: {user_lang}")
        
        # Получаем историю диалога
        conversation_history = database.get_conversation_history_for_ai(sender_id, session_id)
        logger.info(f"[CHAT_LOG] Conversation history length: {len(conversation_history)} messages")
        
        log_with_context(f"[WEBHOOK_HISTORY] Retrieved {len(conversation_history)} messages from history")
        
        # Проверяем, новая ли это сессия (нет истории сообщений)
        if not conversation_history or len(conversation_history) == 0:
            # Если это новая сессия и нет текста от пользователя (например, сессия создана после заказа),
            # НЕ генерируем автоматический ответ AI
            if not message_body or message_body.strip() == '':
                log_with_context("[WEBHOOK_NEW_SESSION_NO_USER_MESSAGE] New session, no user message, skipping AI response")
                return JSONResponse(content={"status": "ok", "info": "new session, no user message"})
            
            # Дополнительная проверка: если сессия была создана недавно (после заказа), не генерируем ответ
            if session_manager.is_session_created_after_order(session_id):
                log_with_context("[WEBHOOK_SESSION_AFTER_ORDER] Session created after order, skipping AI response")
                return JSONResponse(content={"status": "ok", "info": "session created after order"})
            
            # Для новых пользователей тоже генерируем ответ через ИИ
            # Создаём пустую историю, ИИ увидит что это первое сообщение и поприветствует
            conversation_history = []
            log_with_context("[WEBHOOK_NEW_SESSION] New session detected, empty history")
        
        # 🔍 ЛОГИРОВАНИЕ НАЧАЛА AI ЗАПРОСА
        log_with_context("[WEBHOOK_AI_REQUEST_START] ==================== AI REQUEST STARTING ====================")
        log_with_context(f"[WEBHOOK_AI_INPUT] Session: {session_id}, Sender: {sender_name}, Lang: {user_lang}")
        log_with_context(f"[WEBHOOK_AI_HISTORY] History for AI: {conversation_history}")
        
        # Отправляем индикатор печатания перед запросом к AI
        await whatsapp_utils.send_typing_indicator(sender_id, True)
        
        # Получаем ответ от AI с контекстом времени, имени и языка
        ai_response_text, ai_command = ai_manager.get_ai_response(sender_id, session_id, conversation_history, sender_name, user_lang)
        
        # 🔍 ЛОГИРОВАНИЕ РЕЗУЛЬТАТА AI
        log_with_context("[WEBHOOK_AI_REQUEST_END] ==================== AI REQUEST COMPLETED ====================")
        log_with_context(f"[WEBHOOK_AI_RESPONSE_TEXT] {ai_response_text}")
        log_with_context(f"[WEBHOOK_AI_RESPONSE_COMMAND] {ai_command}")
        
        # 🔍 ЛОГИРОВАНИЕ AI RESPONSE В AI PIPELINE
        ai_pipeline_logger.info(f"[AI_RESPONSE_GENERATED] Session: {session_id} | Text: {ai_response_text} | Command: {ai_command}")
        
        logger.info(f"[AI_DEBUG] AI response: {ai_response_text}")
        if ai_command:
            logger.info(f"[AI_DEBUG] Command: {ai_command}")

        # Останавливаем индикатор печатания
        await whatsapp_utils.send_typing_indicator(sender_id, False)

        # 🔍 ЛОГИРОВАНИЕ ОТПРАВКИ ТЕКСТОВОГО ОТВЕТА (ПЕРЕД КОМАНДАМИ)
        if ai_response_text:
            log_with_context("[WEBHOOK_SEND_MESSAGE_START] ==================== SENDING AI RESPONSE ====================")
            log_with_context(f"[WEBHOOK_SEND_MESSAGE_TEXT] Text to send: {ai_response_text}")
            log_with_context(f"[WEBHOOK_SEND_MESSAGE_TO] Sending to: {sender_id}")
            
            logger.info(f"[CHAT_LOG] SENDING TO USER ({sender_id}): {ai_response_text}")
            await whatsapp_utils.send_whatsapp_message(sender_id, ai_response_text, sender_id, session_id)
            
            log_with_context("[WEBHOOK_SEND_MESSAGE_END] ==================== AI RESPONSE SENT ====================")
        else:
            logger.info(f"[CHAT_LOG] No AI response text, skipping message")
            log_with_context("[WEBHOOK_NO_TEXT] No AI response text, skipping message send")

        # 🔍 ЛОГИРОВАНИЕ ОБРАБОТКИ КОМАНД
        if ai_command:
            log_with_context("[WEBHOOK_COMMAND_START] ==================== COMMAND PROCESSING ====================")
            log_with_context(f"[WEBHOOK_COMMAND_INPUT] Command to process: {ai_command}")
            
            # Выполняем команду (отправляем каталог, сохраняем данные и т.д.)
            command_results = await command_handler.handle_commands(sender_id, session_id, ai_command)
            
            log_with_context(f"[WEBHOOK_COMMAND_RESULT] Command processing result: {command_results}")
            log_with_context("[WEBHOOK_COMMAND_END] ==================== COMMAND PROCESSING COMPLETED ====================")
            
            logger.info(f"[COMMAND_LOG] Command results: {command_results}")
            action = command_results.get('action', '') if isinstance(command_results, dict) else ''
            
            # Если команда выполнена успешно, проверяем нужно ли отправлять дополнительное сообщение
            if isinstance(command_results, dict) and command_results.get('status') == 'success':
                if action == 'catalog_sent':
                    # Каталог уже отправлен, текстовое сообщение уже отправлено выше
                    logger.info(f"[COMMAND_LOG] Catalog sent, text already sent above")
                    log_with_context("[WEBHOOK_CATALOG_COMPLETE] Catalog sent, text already sent above")
                    log_with_context("[WEBHOOK_END] ==================== WEBHOOK COMPLETED ====================")
                    return JSONResponse(content={"status": "ok"}, status_code=200)
                elif action == 'bouquet_selected':
                    # Букет выбран через reply, текстовое сообщение уже отправлено выше
                    logger.info(f"[COMMAND_LOG] Bouquet selected via reply, text already sent above")
                    log_with_context("[WEBHOOK_BOUQUET_COMPLETE] Bouquet selected via reply, text already sent above")
                    log_with_context("[WEBHOOK_END] ==================== WEBHOOK COMPLETED ====================")
                    return JSONResponse(content={"status": "ok"}, status_code=200)
                elif action == 'data_saved':
                    # Данные сохранены, текстовое сообщение уже отправлено выше
                    logger.info(f"[COMMAND_LOG] Data saved, text already sent above")
                    log_with_context("[WEBHOOK_DATA_SAVED] Data saved, text already sent above")
                elif action == 'order_confirmed':
                    # Заказ подтвержден, текстовое сообщение уже отправлено выше
                    logger.info(f"[COMMAND_LOG] Order confirmed, text already sent above")
                    log_with_context("[WEBHOOK_ORDER_CONFIRMED] Order confirmed, text already sent above")
                    log_with_context("[WEBHOOK_END] ==================== WEBHOOK COMPLETED ====================")
                    return JSONResponse(content={"status": "ok"}, status_code=200)
                else:
                    # Для остальных команд текстовое сообщение уже отправлено выше
                    logger.info(f"[COMMAND_LOG] Command '{action}' executed, text already sent above")
                    log_with_context(f"[WEBHOOK_COMMAND_COMPLETE] Command '{action}' executed, text already sent above")
        else:
            log_with_context("[WEBHOOK_NO_COMMAND] No command from AI, text already sent above")
        
        log_with_context(f"[WEBHOOK_SUCCESS] Successfully processed webhook for user {sender_id}")
        log_with_context("[WEBHOOK_END] ==================== WEBHOOK COMPLETED SUCCESSFULLY ====================")
        
        logger.info(f"Successfully processed webhook for user {sender_id}")
        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        logger.error(f"Error in webhook handler: {e}", exc_info=True)
        log_with_context(f"[WEBHOOK_EXCEPTION] ==================== WEBHOOK ERROR ====================")
        log_with_context(f"[WEBHOOK_EXCEPTION] Error: {e}")
        log_with_context(f"[WEBHOOK_EXCEPTION] ==================== WEBHOOK ERROR END ====================")
        return JSONResponse(content={"status": "error", "message": "Internal server error"}, status_code=500)

# Семафор для ограничения количества одновременных переводов
import asyncio
translation_semaphore = asyncio.Semaphore(2)  # Максимум 2 одновременных перевода

@router.post("/translate")
async def translate_messages(request: Request):
    """Переводит сообщения с помощью AI"""
    import threading
    import time
    
    # Проверяем, не превышен ли лимит одновременных переводов
    if translation_semaphore.locked():
        logger.warning("[TRANSLATE] Too many concurrent translations, returning 429")
        return JSONResponse(content={"error": "Too many concurrent translations"}, status_code=429)
    
    async with translation_semaphore:
        try:
            data = await request.json()
            text = data.get('text', '')
            target_lang = data.get('lang', 'en')
            logger.info(f"[TRANSLATE] Incoming text (len={len(text)}): {text[:100]}... lang={target_lang}")
            
            if not text:
                logger.warning("[TRANSLATE] No text provided!")
                return JSONResponse(content={"error": "No text provided"}, status_code=400)
            
            lang_names = {
                'en': 'English',
                'th': 'Thai',
                'ru': 'Russian'
            }
            target_lang_name = lang_names.get(target_lang, 'English')
            prompt = f"""Переведи следующий текст на {target_lang_name}. Сохрани форматирование и эмодзи:\n\n{text}\n\nПеревод:"""
            logger.info(f"[TRANSLATE] Prompt (len={len(prompt)}): {prompt[:200]}...")
            
            result = {'translated_text': None, 'error': None}
            def run_gemini():
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel(
                        model_name="gemini-2.0-flash-exp",
                        generation_config=GenerationConfig(
                            temperature=0.3,
                            max_output_tokens=8192  # Максимальное значение для Gemini
                        )
                    )
                    response = model.generate_content(prompt)
                    result['translated_text'] = response.text.strip()
                except Exception as e:
                    logger.error(f"[TRANSLATE] Gemini error: {e}")
                    result['error'] = str(e)
            
            thread = threading.Thread(target=run_gemini)
            thread.start()
            thread.join(timeout=30)
            if thread.is_alive():
                logger.error("[TRANSLATE] Gemini translation timeout!")
                return JSONResponse(content={"error": "Translation timeout"}, status_code=504)
            if result['error']:
                return JSONResponse(content={"error": result['error']}, status_code=500)
            return JSONResponse(content={"translated_text": result['translated_text']})
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return JSONResponse(content={"error": "Translation failed"}, status_code=500)

@router.post("/translate-chat")
async def translate_chat(request: Request):
    """Переводит незавершенный диалог по запросу"""
    try:
        data = await request.json()
        session_id = data.get('session_id', '')
        target_lang = data.get('lang', 'en')
        logger.info(f"[TRANSLATE_CHAT] Translating unfinished chat for session {session_id} to {target_lang}")
        
        if not session_id:
            logger.warning("[TRANSLATE_CHAT] No session_id provided!")
            return JSONResponse(content={"error": "No session_id provided"}, status_code=400)
        
        # Проверяем, есть ли уже завершенный диалог
        completed_chat = database.get_completed_chat(session_id)
        if completed_chat:
            # Используем готовый перевод
            translations = completed_chat.get('translations', {})
            if target_lang in translations:
                translated_html = translations[target_lang]
                return JSONResponse(content={"translated_html": translated_html})
        
        # Переводим незавершенный диалог
        from .chat_translation_manager import translate_unfinished_chat
        result = await translate_unfinished_chat(session_id, target_lang)
        
        if result.get('success'):
            return JSONResponse(content={"translated_html": result['translated_html']})
        else:
            return JSONResponse(content={"error": result.get('error', 'Translation failed')}, status_code=500)
        
    except Exception as e:
        logger.error(f"Error translating chat: {e}")
        return JSONResponse(content={"error": "Translation failed"}, status_code=500)

@router.get("/chat/{session_id}")
async def get_chat_history(session_id: str, lang: str = Query('ru')):
    """Отображает историю переписки для заданной сессии с многоязычной поддержкой"""
    try:
        # Сначала проверяем, есть ли завершенный диалог с переводами
        from . import database
        completed_chat = database.get_completed_chat(session_id)
        
        if completed_chat:
            # Используем готовый диалог
            from .chat_history_processor import extract_user_info_from_messages, process_chat_messages
            from .template_utils import format_user_info, render_chat_history_template
            
            messages = completed_chat.get('messages', [])
            translations = completed_chat.get('translations', {})
            translation_status = completed_chat.get('translation_status', 'not_started')
            
            # Выбираем сообщения на нужном языке
            if lang == 'ru':
                display_messages = messages
            elif lang in ['en', 'th'] and translations.get(lang):
                display_messages = translations[lang]
            else:
                # Если перевода нет, показываем оригинал
                display_messages = messages
            
            # Формируем информацию о пользователе
            user_name, user_phone = extract_user_info_from_messages(messages)
            user_info = format_user_info(user_name, user_phone, lang)
            
            # Добавляем информацию о заказе
            order_summary = completed_chat.get('order_summary', {})
            if order_summary:
                # Словари для разных языков
                order_labels = {
                    'ru': {'order': 'Заказ', 'bouquet': 'Букет', 'date': 'Дата', 'address': 'Адрес'},
                    'en': {'order': 'Order', 'bouquet': 'Bouquet', 'date': 'Date', 'address': 'Address'},
                    'th': {'order': 'คำสั่งซื้อ', 'bouquet': 'ช่อดอกไม้', 'date': 'วันที่', 'address': 'ที่อยู่'}
                }
                lang_labels = order_labels.get(lang, order_labels['ru'])
                
                order_info = f"<br><strong>{lang_labels['order']}:</strong> "
                if order_summary.get('bouquet'):
                    order_info += f"{lang_labels['bouquet']}: {order_summary['bouquet']}"
                if order_summary.get('date'):
                    order_info += f", {lang_labels['date']}: {order_summary['date']}"
                if order_summary.get('address'):
                    order_info += f", {lang_labels['address']}: {order_summary['address']}"
                user_info += order_info
            
            # Обрабатываем сообщения
            messages_html = process_chat_messages(display_messages)
            
            # Добавляем индикатор статуса перевода
            if translation_status == 'in_progress':
                messages_html += '<div class="translation-status">🔄 Перевод в процессе...</div>'
            elif translation_status == 'failed':
                messages_html += '<div class="translation-status error">❌ Ошибка перевода</div>'
            
            # Рендерим шаблон
            html_content = render_chat_history_template(user_info, messages_html)
            return HTMLResponse(content=html_content)
        
        else:
            # Используем старую логику для незавершенных диалогов
            from .chat_history_processor import process_chat_history
            html_content, status_code = process_chat_history(session_id)
            return HTMLResponse(content=html_content, status_code=status_code)
            
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        from .template_utils import render_error_template
        error_html = render_error_template(str(e), tb)
        return HTMLResponse(content=error_html, status_code=500)

@router.post("/session/{sender_id}/new")
async def create_new_session(sender_id: str):
    """Генерирует новый session_id для пользователя (sender_id) с уникальным timestamp-суффиксом."""
    from . import session_manager
    
    # Используем менеджер сессий для создания новой сессии
    new_session_id = session_manager.force_new_session(sender_id)
    
    return {"session_id": new_session_id}

@router.post("/api/force_session/{sender_id}")
async def force_session_id(sender_id: str, request: Request):
    data = await request.json()
    new_session_id = data.get("session_id")
    if not new_session_id:
        return {"success": False, "error": "No session_id provided"}
    old_session_id = FORCED_SESSION_IDS.get(sender_id)
    FORCED_SESSION_IDS[sender_id] = new_session_id
    logging.info(f"[FORCE_SESSION] sender_id={sender_id} old_session_id={old_session_id} new_session_id={new_session_id}")
    logging.info(f"[FORCED_SESSION_IDS_STATE] {FORCED_SESSION_IDS}")
    return {"success": True, "session_id": new_session_id}

@router.get("/api/debug/sessions")
async def get_sessions_for_period(period_min: int = Query(20, alias="period_min")):
    import logging
    logging.info(f"[DEBUG_LOGS] Запрос на загрузку логов за период: {period_min} минут")
    if os.environ.get('GAE_ENV', '') or os.environ.get('K_SERVICE', ''):
        logging.warning("[DEBUG_LOGS] Попытка загрузки логов на сервере — запрещено!")
        return {"sessions": [], "error": "Этот функционал доступен только локально!"}
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=period_min)
        logging.info(f"[DEBUG_LOGS] Скачивание логов через get_logs_via_api с {start_time} по {end_time}")
        logs_data, success = get_logs_via_api(start_time, end_time)
        logging.info(f"[DEBUG_LOGS] Результат скачивания: success={success}, записей={len(logs_data) if logs_data else 0}")
        if not success or not logs_data:
            logging.error("[DEBUG_LOGS] Не удалось получить логи с сервера!")
            return {"sessions": [], "error": "Не удалось получить логи с сервера"}
        with open("logs.log", "w", encoding="utf-8") as f:
            for entry in logs_data:
                ts = entry.get('timestamp', '')
                text = entry.get('textPayload', '')
                f.write(f"[{ts}] {text}\n")
        logging.info("[DEBUG_LOGS] Логи сохранены в logs.log, начинаю парсинг...")
        now = datetime.utcnow()
        sessions = set()
        with open("logs.log", encoding="utf-8") as f:
            for line in f:
                m = re.search(r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
                if not m:
                    continue
                log_time = datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S')
                if (now - log_time).total_seconds() > period_min * 60:
                    continue
                session_ids = re.findall(r'(?:session_id|Session)[=: ]+([\w\-]+)', line)
                for sid in session_ids:
                    sessions.add(sid)
        logging.info(f"[DEBUG_LOGS] Найдено сессий: {len(sessions)}")
        return {"sessions": sorted(sessions)}
    except Exception as e:
        import traceback
        err = f"{e}\n{traceback.format_exc()}"
        logging.error(f"[DEBUG_LOGS] Ошибка: {err}")
        return {"sessions": [], "error": err}
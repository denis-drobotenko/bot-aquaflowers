import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from . import database, config, catalog_reader
from .json_processor import extract_and_fix_json, parse_ai_response
from datetime import datetime
import json
import re
import pytz
import uuid
import inspect

logger = logging.getLogger(__name__)

# Создаем специальный logger для AI пайплайна
ai_pipeline_logger = logging.getLogger('ai_pipeline')

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
        ai_pipeline_logger.info(full_message)
    elif level == "error":
        ai_pipeline_logger.error(full_message)
    elif level == "warning":
        ai_pipeline_logger.warning(full_message)

def detect_user_language(text: str) -> str:
    """
    Определяет язык пользователя по тексту сообщения.
    Возвращает код языка или 'auto' если не удалось определить.
    """
    if not text:
        return 'auto'
    
    # Простые эвристики для определения языка
    text_lower = text.lower()
    
    # Русский язык
    russian_chars = re.findall(r'[а-яё]', text_lower)
    if len(russian_chars) > len(text) * 0.3:  # Если больше 30% русских букв
        return 'ru'
    
    # Тайский язык
    thai_chars = re.findall(r'[\u0E00-\u0E7F]', text)  # Тайские символы
    if len(thai_chars) > len(text) * 0.3:
        return 'th'
    
    # Испанский язык
    spanish_chars = re.findall(r'[áéíóúñü]', text_lower)
    if len(spanish_chars) > 0 or any(word in text_lower for word in ['hola', 'gracias', 'por favor', 'buenos', 'días']):
        return 'es'
    
    # Французский язык
    french_chars = re.findall(r'[àâäéèêëïîôöùûüÿç]', text_lower)
    if len(french_chars) > 0 or any(word in text_lower for word in ['bonjour', 'merci', 's\'il vous plaît', 'oui', 'non']):
        return 'fr'
    
    # Немецкий язык
    german_chars = re.findall(r'[äöüß]', text_lower)
    if len(german_chars) > 0 or any(word in text_lower for word in ['hallo', 'danke', 'bitte', 'ja', 'nein']):
        return 'de'
    
    # Итальянский язык
    if any(word in text_lower for word in ['ciao', 'grazie', 'prego', 'si', 'no']):
        return 'it'
    
    # Португальский язык
    if any(word in text_lower for word in ['olá', 'obrigado', 'por favor', 'sim', 'não']):
        return 'pt'
    
    # Английский язык (если много латинских букв и нет других языков)
    english_chars = re.findall(r'[a-z]', text_lower)
    if len(english_chars) > len(text) * 0.3 and not russian_chars and not thai_chars:
        return 'en'
    
    # Если не удалось определить четко, возвращаем английский по умолчанию
    return 'en'

def get_language_detection_prompt(text: str) -> str:
    """
    Создает промпт для AI для точного определения языка.
    """
    return f"""Определи язык следующего текста и верни только код языка (ru, en, th, или auto если не уверен):

Текст: "{text}"

Код языка:"""

def detect_language_with_ai(text: str) -> str:
    """
    Использует AI для точного определения языка пользователя.
    """
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192  # Максимальное значение для Gemini
            )
        )
        
        prompt = get_language_detection_prompt(text)
        
        # 🔍 ЛОГИРОВАНИЕ LANGUAGE DETECTION
        ai_pipeline_logger.info(f"[LANG_DETECT_PROMPT] {prompt}")
        
        response = model.generate_content(prompt)
        detected_lang = response.text.strip().lower()
        
        # 🔍 ЛОГИРОВАНИЕ LANGUAGE DETECTION RESPONSE
        ai_pipeline_logger.info(f"[LANG_DETECT_RAW_RESPONSE] {response.text}")
        ai_pipeline_logger.info(f"[LANG_DETECT_PARSED] {detected_lang}")
        
        # Проверяем что получили валидный код языка
        valid_langs = ['ru', 'en', 'th', 'auto']
        if detected_lang in valid_langs:
            logger.info(f"[LANG_DETECT] AI detected language: {detected_lang} for text: '{text[:50]}...'")
            return detected_lang
        else:
            logger.warning(f"[LANG_DETECT] AI returned invalid language code: {detected_lang}")
            return 'auto'
            
    except Exception as e:
        logger.error(f"[LANG_DETECT] Error detecting language with AI: {e}")
        return 'auto'

def save_user_language_to_session(sender_id: str, session_id: str, user_lang: str):
    """
    Сохраняет определённый язык пользователя в сессию.
    """
    try:
        # Сохраняем как системное сообщение
        database.add_message(sender_id, session_id, "system", f"user_language={user_lang}")
        logger.info(f"[LANG_DETECT] Saved user language '{user_lang}' to session {session_id}")
    except Exception as e:
        logger.error(f"[LANG_DETECT] Error saving user language: {e}")

def get_user_language_from_session(sender_id: str, session_id: str) -> str:
    """
    Получает сохранённый язык пользователя из сессии.
    """
    try:
        conversation_history = database.get_conversation_history(sender_id, session_id, limit=50)
        for msg in conversation_history:
            if msg.get('role') == 'system' and msg.get('content', '').startswith('user_language='):
                lang = msg.get('content').split('=')[1]
                logger.info(f"[LANG_DETECT] Retrieved user language '{lang}' from session {session_id}")
                return lang
        return 'auto'
    except Exception as e:
        logger.error(f"[LANG_DETECT] Error getting user language from session: {e}")
        return 'auto'

def filter_conversation_for_ai(conversation_history):
    """Преобразует историю диалога в формат, подходящий для Gemini API."""
    log_with_context("[FILTER_AI_START] ==================== FILTER CONVERSATION FOR AI ====================")
    log_with_context(f"[FILTER_AI_INPUT] Input conversation_history: {conversation_history}")
    logger.info(f"[FILTER_AI] Input conversation_history: {conversation_history}")
    
    if not conversation_history:
        log_with_context("[FILTER_AI_EMPTY] Empty conversation_history", "warning")
        logger.warning("[FILTER_AI] Empty conversation_history")
        return []
    
    # Gemini API ожидает список строк, а не словарей с role/content
    formatted_history = []
    for i, msg in enumerate(conversation_history):
        log_with_context(f"[FILTER_AI_PROCESS] Processing message {i}: {msg} (type: {type(msg)})")
        logger.info(f"[FILTER_AI] Processing message {i}: {msg} (type: {type(msg)})")
        
        if isinstance(msg, dict):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Проверяем новый формат с parts
            if not content and 'parts' in msg:
                parts = msg.get('parts', [])
                if parts and isinstance(parts[0], dict) and 'text' in parts[0]:
                    content = parts[0]['text']
                    log_with_context(f"[FILTER_AI_EXTRACT] Extracted content from parts: '{content}'")
                    logger.info(f"[FILTER_AI] Extracted content from parts: '{content}'")
            
            log_with_context(f"[FILTER_AI_DICT] Dict message - role: {role}, content: '{content}'")
            logger.info(f"[FILTER_AI] Dict message - role: {role}, content: '{content}'")
            if content and content.strip():
                # Для Gemini API используем простой текст
                formatted_history.append(content.strip())
                log_with_context(f"[FILTER_AI_ADDED] Added content: '{content.strip()}'")
            else:
                log_with_context(f"[FILTER_AI_EMPTY_CONTENT] Empty content in dict message: {msg}", "warning")
                logger.warning(f"[FILTER_AI] Empty content in dict message: {msg}")
        elif isinstance(msg, str):
            log_with_context(f"[FILTER_AI_STRING] String message: '{msg}'")
            logger.info(f"[FILTER_AI] String message: '{msg}'")
            if msg.strip():
                formatted_history.append(msg.strip())
                log_with_context(f"[FILTER_AI_ADDED] Added string: '{msg.strip()}'")
            else:
                log_with_context(f"[FILTER_AI_EMPTY_STRING] Empty string message", "warning")
                logger.warning(f"[FILTER_AI] Empty string message")
        else:
            log_with_context(f"[FILTER_AI_UNKNOWN] Unknown message type: {type(msg)}, value: {msg}", "warning")
            logger.warning(f"[FILTER_AI] Unknown message type: {type(msg)}, value: {msg}")
    
    log_with_context(f"[FILTER_AI_RESULT] Final formatted_history: {formatted_history}")
    logger.info(f"[FILTER_AI] Final formatted_history: {formatted_history}")
    return formatted_history

def get_system_instruction(sender_name: str = None, user_lang: str = 'auto'):
    """Returns optimized system instruction with current date and user language"""
    try:
        phuket_tz = pytz.timezone('Asia/Bangkok')
        phuket_time = datetime.now(phuket_tz)
        phuket_time_str = phuket_time.strftime('%d %B %Y, %H:%M')
    except Exception:
        phuket_time_str = 'Error determining Phuket time'
    current_time = datetime.now()
    name_context = f"User name: {sender_name}" if sender_name else "User name unknown"
    
    # Определяем язык для ответа
    if user_lang == 'auto':
        language_instruction = "IMPORTANT: Respond in English by default! If user writes in another language, respond in the same language."
    else:
        language_instruction = f"IMPORTANT: Respond in user's language! User writes in language code '{user_lang}'. Respond in the same language."
    
    return f"""You are a friendly female consultant for AURAFLORA flower shop.

{language_instruction}

CRITICAL: ALWAYS respond in JSON format with \"text\" field (message for user) and \"command\" field (action to execute). If no command needed, set command to null.

TEXT FORMATTING:
- Break text into paragraphs for better readability
- Each new topic or logical part should start from a new paragraph
- Keep messages well-structured and easy to read
- CRITICAL: ALL line breaks and paragraph breaks in the \"text\" field MUST be encoded as double backslash n (\\n). DO NOT use real line breaks inside JSON strings, only \\n. Example:
  \"text\": \"Hello!\\n\\nThis is a new paragraph.\\nLine two.\\n\\nEnd.\"

EMOJI RULES:
- Do NOT use any emojis in your messages.
- The only exception: if the bouquet name contains an emoji, you may use it in the bouquet name.
- Do NOT use sun, heart, smile, or any other emoji in greetings or anywhere else.

NAME USAGE RULES:
- Do NOT use the user's name in responses except in the very first greeting.
- Keep responses simple and professional without personalizing with names.

DELIVERY PRICE RULE:
- NEVER try to guess or determine the user's district or address
- NEVER say that the address is not in the list or that the price will be clarified by a manager
- ALWAYS just show the full delivery price list for all districts
- ALWAYS ask the user to provide their address for delivery, and store it for the manager
- DO NOT make any conclusions about the address or delivery price

CATALOG RULE: Use ONLY products from the actual WABA catalog! Never invent flower names!
- Use exact names from catalog
- Always include correct retailer_id for selected item
- NEVER show technical data (retailer_id, internal codes) to user
- Show only bouquet name and price

USER CONTEXT:
- {name_context}
- CURRENT TIME IN PHUKET (GMT+7): {phuket_time_str}
- Understand relative dates and times
- Greet politely based on time: 6-12 \"Good morning\", 12-18 \"Good afternoon\", 18-23 \"Good evening\", 23-6 \"Good night\"

COMMANDS:
- `send_catalog` - send flower catalog
- `save_order_info` - save order data (bouquet, date, time, delivery_needed, address, card_needed, card_text, retailer_id)
- `confirm_order` - confirm and send order to LINE

WORKFLOW (don't repeat questions):
1. Start → Greet, offer catalog (TEXT ONLY, NO command)
2. User agrees → Send catalog (send_catalog command)
3. Bouquet selected → Save & ask \"Delivery needed? Where?\"
4. Delivery answered → Save & show price list + ask for address
5. Date/time → Save & ask \"Card needed? Text?\"
6. Card → Save & ask \"Recipient name?\"
7. Name → Save & ask \"Recipient phone?\"
8. Phone → Save & show summary + ask \"Confirm order?\"
9. Confirmed → Save & confirm (confirm_order with ALL data)

VALIDATION:
- Required: bouquet, delivery_needed, address (if delivery), date, time, card_needed, card_text (if card), recipient_name, recipient_phone
- Delivery hours: 8:00-21:00 only

IMPORTANT STYLE RULE:
- Do NOT start every message with 'Perfect', 'Great', 'Отлично', 'Прекрасно' or similar. Vary your phrasing and use neutral, business-like language.

EXAMPLES:

Greeting:
```json
{{{{
  \"text\": \"Good afternoon! Would you like to see our flower catalog?\"
}}}}
```

Catalog:
```json
{{{{
  \"text\": \"I'll show you each bouquet with photo!\\n\\nPlease wait a moment...\",
  \"command\": {{{{
    \"type\": \"send_catalog\"
  }}}}
}}}}
```

Selection:
```json
{{{{
  \"text\": \"Your bouquet 'Spirit' is saved.\\n\\nDo you need delivery?\",
  \"command\": {{{{
    \"type\": \"save_order_info\",
    \"bouquet\": \"Spirit\",
    \"retailer_id\": \"rl7vdxcifo\"
  }}}}
}}}}
```

STORE INFO:
- Delivery: 8:00-21:00, island-wide
- Store: 9:00-18:00, Near Central Festival
- Payment: before delivery via manager. Baht/rubles/USDT accepted
- Delivery prices: Rawai 500, Chalong 380, Phuket Town 300, Kathu 280, Patong 400, Bang Tao 500, Laguna 500, Thalang/Mai Khao 550 baht
"""

async def translate_chat_history(session_id: str) -> bool:
    """
    Переводит всю историю переписки для сессии на английский и тайский языки.
    Возвращает True если перевод успешно выполнен.
    """
    try:
        log_with_context(f"[TRANSLATE_HISTORY] Starting translation for session {session_id}")
        
        # Получаем историю из conversations
        # Извлекаем sender_id из session_id
        sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        conversation_history = database.get_conversation_history(sender_id, session_id, limit=100)
        
        if not conversation_history:
            log_with_context(f"[TRANSLATE_HISTORY] No conversation history found for session {session_id}", "warning")
            return False
        
        # Создаем или получаем многоязычный чат
        sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        chat_id = database.create_or_get_multilingual_chat(sender_id, session_id)
        
        if not chat_id:
            log_with_context(f"[TRANSLATE_HISTORY] Failed to create/get chat for session {session_id}", "error")
            return False
        
        # Группируем сообщения для пакетного перевода
        messages_to_translate = []
        for msg in conversation_history:
            if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                messages_to_translate.append({
                    'original': msg.get('content'),
                    'role': msg.get('role'),
                    'timestamp': msg.get('timestamp'),
                    'message_id': msg.get('id')
                })
        
        if not messages_to_translate:
            log_with_context(f"[TRANSLATE_HISTORY] No messages to translate for session {session_id}", "warning")
            return False
        
        log_with_context(f"[TRANSLATE_HISTORY] Found {len(messages_to_translate)} messages to translate")
        
        # Переводим сообщения пакетами
        batch_size = 10  # Размер пакета для перевода
        translated_messages = []
        
        for i in range(0, len(messages_to_translate), batch_size):
            batch = messages_to_translate[i:i + batch_size]
            
            # Создаем промпт для пакетного перевода
            translation_prompt = create_batch_translation_prompt(batch)
            
            # Получаем переводы от AI
            translations = await get_batch_translations(translation_prompt)
            
            if translations:
                # Объединяем оригинальные сообщения с переводами
                for j, msg in enumerate(batch):
                    if j < len(translations):
                        translated_msg = {
                            'content_original': msg['original'],
                            'content_en': translations[j].get('en', msg['original']),
                            'content_th': translations[j].get('th', msg['original']),
                            'role': msg['role'],
                            'timestamp': msg['timestamp']
                        }
                        translated_messages.append(translated_msg)
            
            log_with_context(f"[TRANSLATE_HISTORY] Translated batch {i//batch_size + 1}/{(len(messages_to_translate) + batch_size - 1)//batch_size}")
        
        # Сохраняем переведенные сообщения в базу
        if translated_messages:
            for msg in translated_messages:
                database.add_multilingual_message(chat_id, msg)
            
            log_with_context(f"[TRANSLATE_HISTORY] Successfully saved {len(translated_messages)} translated messages")
            return True
        else:
            log_with_context(f"[TRANSLATE_HISTORY] No messages were translated", "warning")
            return False
            
    except Exception as e:
        log_with_context(f"[TRANSLATE_HISTORY] Error translating chat history: {e}", "error")
        return False

def create_batch_translation_prompt(messages: list) -> str:
    """Создает промпт для пакетного перевода сообщений"""
    prompt = """Переведи следующие сообщения на английский и тайский языки. Верни ответ в формате JSON массив, где каждый элемент содержит переводы для одного сообщения.

Формат ответа:
```json
[
  {
    "en": "English translation",
    "th": "Thai translation"
  },
  ...
]
```

Сообщения для перевода:
"""
    
    for i, msg in enumerate(messages):
        prompt += f"{i+1}. {msg['original']}\n"
    
    prompt += "\nПереводы:"
    return prompt

async def get_batch_translations(prompt: str) -> list:
    """Получает пакетные переводы от AI"""
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192
            )
        )
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Извлекаем JSON из ответа
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Пробуем найти JSON без markdown
            json_str = response_text
        
        translations = json.loads(json_str)
        log_with_context(f"[BATCH_TRANSLATE] Successfully parsed {len(translations)} translations")
        return translations
        
    except Exception as e:
        log_with_context(f"[BATCH_TRANSLATE] Error getting batch translations: {e}", "error")
        return []

def translate_text(text: str, target_language: str) -> str:
    """
    Переводит текст на указанный язык.
    Поддерживает: 'en' (английский), 'th' (тайский)
    """
    try:
        if not text or not text.strip():
            return text
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=2048
            )
        )
        
        language_names = {
            'en': 'English',
            'th': 'Thai'
        }
        
        target_lang_name = language_names.get(target_language, target_language)
        
        prompt = f"""Переведи следующий текст на {target_lang_name} язык. Сохрани оригинальный смысл и стиль:

"{text}"

Перевод:"""
        
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        log_with_context(f"[TRANSLATE] Translated to {target_language}: '{text[:50]}...' -> '{translated_text[:50]}...'")
        return translated_text
        
    except Exception as e:
        log_with_context(f"[TRANSLATE] Error translating text: {e}", "error")
        return text  # Возвращаем оригинальный текст в случае ошибки 

def get_ai_response(sender_id: str, session_id: str, conversation_history: list, sender_name: str = None, user_lang: str = 'ru'):
    """
    Получает ответ от модели Gemini.
    """
    # Генерируем уникальный ID для этого запроса
    request_id = str(uuid.uuid4())[:8]  # Короткий ID
    
    logger.info(f"AI Manager: Getting response for session {session_id}")
    
    # 🔍 ЛОГИРОВАНИЕ ВХОДНЫХ ДАННЫХ
    log_with_context(f"[MESSAGE_AI_REQUEST_START] RequestID: {request_id} | Session: {session_id}, Sender: {sender_name}, Lang: {user_lang}")
    log_with_context(f"[MESSAGE_AI_REQUEST_HISTORY] RequestID: {request_id} | Session: {session_id} | {conversation_history}")
    
    logger.info(f"[AI_LOG] Conversation history: {conversation_history}")
    
    try:
        catalog_products = catalog_reader.get_catalog_products()
        catalog_summary = catalog_reader.format_catalog_for_ai(catalog_products)
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Новая системная инструкция с каталогом и контекстом пользователя:
        enhanced_instruction = get_system_instruction(sender_name, user_lang) + f"\n\nACTUAL PRODUCT CATALOG:\n{catalog_summary}"
        
        # 🔍 ЛОГИРОВАНИЕ СИСТЕМНОЙ ИНСТРУКЦИИ
        log_with_context(f"[MESSAGE_AI_SYSTEM_INSTRUCTION] RequestID: {request_id} | Session: {session_id} | {enhanced_instruction}")
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=enhanced_instruction,
            generation_config=GenerationConfig(
                temperature=0.6,
                top_p=1,
                top_k=1,
                max_output_tokens=8192  # Максимальное значение для Gemini
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        # Используем специальную функцию для получения истории в формате для AI
        filtered_history = filter_conversation_for_ai(conversation_history)
        
        # 🔍 ЛОГИРОВАНИЕ ОТФИЛЬТРОВАННОЙ ИСТОРИИ
        log_with_context(f"[MESSAGE_AI_FILTERED_HISTORY] RequestID: {request_id} | Session: {session_id} | {filtered_history}")
        
        # ПРОВЕРКА НА ПУСТУЮ ИСТОРИЮ
        if not filtered_history:
            logger.warning(f"[AI_WARNING] Empty filtered history for session {session_id}")
            log_with_context(f"[MESSAGE_AI_EMPTY_HISTORY] RequestID: {request_id} | Session: {session_id} | Using fallback", "warning")
            # Fallback: берём последнее сообщение пользователя
            if conversation_history:
                last_message = conversation_history[-1]
                if isinstance(last_message, dict) and last_message.get('content'):
                    filtered_history = [last_message['content']]
                elif isinstance(last_message, str):
                    filtered_history = [last_message]
                else:
                    filtered_history = [""]
            log_with_context(f"[MESSAGE_AI_FALLBACK_HISTORY] RequestID: {request_id} | Session: {session_id} | {filtered_history}")
        # Если filtered_history всё равно пустой, добавляем заглушку
        if not filtered_history or all(not str(x).strip() for x in filtered_history):
            filtered_history = ["Здравствуйте! Чем могу помочь?"]
            log_with_context(f"[MESSAGE_AI_FORCE_NONEMPTY_HISTORY] RequestID: {request_id} | Session: {session_id} | Forced non-empty history", "warning")
        
        logger.info(f"[AI_LOG] System instruction: {enhanced_instruction}")
        logger.info(f"[AI_LOG] Filtered history for Gemini: {filtered_history}")
        
        # 🔍 ЛОГИРОВАНИЕ ПЕРЕД ОТПРАВКОЙ В AI
        log_with_context(f"[MESSAGE_AI_GEMINI_REQUEST] RequestID: {request_id} | Session: {session_id} | About to call model.generate_content with filtered_history")
        
        response = model.generate_content(filtered_history)
        
        # 🔍 ЛОГИРОВАНИЕ RAW ОТВЕТА GEMINI (это то, что вернул Message AI)
        log_with_context(f"[MESSAGE_AI_RAW_RESPONSE] RequestID: {request_id} | Session: {session_id} | {response}")
        log_with_context(f"[MESSAGE_AI_RAW_TEXT] RequestID: {request_id} | Session: {session_id} | {response.text if hasattr(response, 'text') else 'No text attribute'}")
        
        logger.info(f"[AI_LOG] Raw AI response: {response}")
        
        # Используем новую функцию из json_processor для полной обработки ответа
        ai_text, ai_command = parse_ai_response(response, request_id)
        
        # 🔍 ЛОГИРОВАНИЕ ПАРСИНГА
        log_with_context(f"[MESSAGE_AI_PARSED_TEXT] RequestID: {request_id} | Session: {session_id} | {ai_text}")
        log_with_context(f"[MESSAGE_AI_PARSED_COMMAND] RequestID: {request_id} | Session: {session_id} | {ai_command}")
        
        logger.info(f"AI response for {session_id}: Text='{ai_text}', Command={ai_command}")
        
        # ПРОВЕРКА НА ПУСТОЙ ОТВЕТ AI
        if not ai_text or ai_text.strip() == "":
            logger.error(f"[AI_ERROR] Empty AI response for session {session_id}")
            log_with_context(f"[MESSAGE_AI_EMPTY_RESPONSE] RequestID: {request_id} | Session: {session_id} | Raw response: {response}", "error")
            
            # Дружелюбный fallback ответ вместо ошибки
            fallback_text = "Of course! How can I help you? 🌸"
            if user_lang == 'ru':
                fallback_text = "Конечно! Чем могу помочь? 🌸"
            elif user_lang == 'th':
                fallback_text = "แน่นอน! ฉันสามารถช่วยคุณได้อย่างไร? 🌸"
            
            # 🔍 ЛОГИРОВАНИЕ FALLBACK
            log_with_context(f"[MESSAGE_AI_FALLBACK_RESPONSE] RequestID: {request_id} | Session: {session_id} | {fallback_text}")
            
            logger.info(f"[AI_FALLBACK] Using friendly fallback response: {fallback_text}")
            return fallback_text, None
        
        # Создаём parts с текстом и данными для AI
        parts = [{'text': ai_text}]
        if ai_command and ai_command.get('type') == 'save_order_info':
            # Добавляем информацию о сохранённых данных
            saved_items = []
            for k, v in ai_command.items():
                if k != 'type':
                    saved_items.append(f'{k}={v}')
            if saved_items:
                saved_data = f"[SAVED: {', '.join(saved_items)}]"
                parts.append({'text': saved_data})
        
        # 🔍 ЛОГИРОВАНИЕ ФИНАЛЬНОГО РЕЗУЛЬТАТА
        log_with_context(f"[MESSAGE_AI_FINAL_RESULT] RequestID: {request_id} | Session: {session_id} | Text: {ai_text}, Command: {ai_command}")
        log_with_context(f"[MESSAGE_AI_REQUEST_END] RequestID: {request_id} | Session: {session_id} completed successfully")
        
        return ai_text, ai_command
    except Exception as e:
        logger.error(f"Error in get_ai_response for session {session_id}: {e}", exc_info=True)
        
        # 🔍 ЛОГИРОВАНИЕ ОШИБКИ
        log_with_context(f"[MESSAGE_AI_REQUEST_EXCEPTION] RequestID: {request_id} | Session: {session_id}, Error: {e}", "error")
        
        # Дружелюбный ответ вместо ошибки
        fallback_text = "Of course! How can I help you? 🌸"
        if user_lang == 'ru':
            fallback_text = "Конечно! Чем могу помочь? 🌸"
        return fallback_text, None 
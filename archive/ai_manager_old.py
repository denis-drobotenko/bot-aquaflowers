import logging
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from ..src import database, config, catalog_reader
from ..src.json_processor import extract_and_fix_json
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

def save_user_language_to_session(session_id: str, user_lang: str):
    """
    Сохраняет определенный язык пользователя в сессию.
    """
    try:
        # Сохраняем как системное сообщение
        database.add_message(session_id, "system", f"user_language={user_lang}")
        logger.info(f"[LANG_DETECT] Saved user language '{user_lang}' to session {session_id}")
    except Exception as e:
        logger.error(f"[LANG_DETECT] Error saving user language: {e}")

def get_user_language_from_session(session_id: str) -> str:
    """
    Получает сохраненный язык пользователя из сессии.
    """
    try:
        conversation_history = database.get_conversation_history(session_id, limit=50)
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

def parse_response(response):
    """Извлекает текст и команду из JSON-ответа модели с надёжной обработкой через json_processor."""
    try:
        # Извлекаем текст из всех частей ответа AI
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if not text_parts:
            logger.error("[PARSE_RESPONSE] No text parts found in AI response")
            log_with_context("[JSON_AI_PARSE_ERROR] No text parts found in AI response", "error")
            return None, None
        
        full_text = ''.join(text_parts)
        
        # 🔍 ЛОГИРОВАНИЕ RAW AI RESPONSE
        log_with_context(f"[JSON_AI_PARSE_INPUT] Full AI response: {full_text}")
        
        logger.info(f"[PARSE_RESPONSE] Processing AI response: {full_text[:100]}...")
        
        # Используем новую функцию для извлечения и исправления JSON
        json_data, user_text = extract_and_fix_json(full_text)
        
        # Извлекаем команду из JSON данных, если они есть
        command = None
        if json_data:
            command = json_data.get('command', None)
            # Если текст не был извлечён из JSON, используем поле text
            if not user_text and json_data.get('text'):
                user_text = json_data.get('text')
        
        # 🔍 ЛОГИРОВАНИЕ PARSE РЕЗУЛЬТАТА
        log_with_context(f"[JSON_AI_PARSE_JSON_DATA] {json_data}")
        log_with_context(f"[JSON_AI_PARSE_USER_TEXT] {user_text}")
        log_with_context(f"[JSON_AI_PARSE_COMMAND] {command}")
        
        logger.info(f"[PARSE_RESPONSE] Result: text='{user_text}', command={command}")
        return user_text, command
        
    except Exception as e:
        logger.error(f"[PARSE_RESPONSE] Unexpected error: {e}")
        log_with_context(f"[JSON_AI_PARSE_EXCEPTION] {e}", "error")
        return None, None

def get_ai_response(session_id: str, conversation_history: list, sender_name: str = None, user_lang: str = 'ru'):
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
        enhanced_instruction = get_system_instruction(sender_name, user_lang) + f"\n\nАКТУАЛЬНЫЙ КАТАЛОГ ТОВАРОВ:\n{catalog_summary}"
        
        # 🔍 ЛОГИРОВАНИЕ СИСТЕМНОЙ ИНСТРУКЦИИ
        log_with_context(f"[MESSAGE_AI_SYSTEM_INSTRUCTION] RequestID: {request_id} | Session: {session_id} | {enhanced_instruction}")
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=enhanced_instruction,
            generation_config=GenerationConfig(
                temperature=0.7,
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
            
            # Fallback: берем последнее сообщение пользователя
            if conversation_history:
                last_message = conversation_history[-1]
                if isinstance(last_message, dict) and last_message.get('content'):
                    filtered_history = [last_message['content']]
                elif isinstance(last_message, str):
                    filtered_history = [last_message]
                else:
                    # Если ничего не нашли, используем приветствие
                    filtered_history = ["Привет"]
            else:
                filtered_history = ["Привет"]
            
            log_with_context(f"[MESSAGE_AI_FALLBACK_HISTORY] RequestID: {request_id} | Session: {session_id} | {filtered_history}")
        
        logger.info(f"[AI_LOG] System instruction: {enhanced_instruction}")
        logger.info(f"[AI_LOG] Filtered history for Gemini: {filtered_history}")
        
        # 🔍 ЛОГИРОВАНИЕ ПЕРЕД ОТПРАВКОЙ В AI
        log_with_context(f"[MESSAGE_AI_GEMINI_REQUEST] RequestID: {request_id} | Session: {session_id} | About to call model.generate_content with filtered_history")
        
        response = model.generate_content(filtered_history)
        
        # 🔍 ЛОГИРОВАНИЕ RAW ОТВЕТА GEMINI (это то, что вернул Message AI)
        log_with_context(f"[MESSAGE_AI_RAW_RESPONSE] RequestID: {request_id} | Session: {session_id} | {response}")
        log_with_context(f"[MESSAGE_AI_RAW_TEXT] RequestID: {request_id} | Session: {session_id} | {response.text if hasattr(response, 'text') else 'No text attribute'}")
        
        logger.info(f"[AI_LOG] Raw AI response: {response}")
        ai_text, ai_command = parse_response(response)
        
        # 🔍 ЛОГИРОВАНИЕ ПАРСИНГА
        log_with_context(f"[MESSAGE_AI_PARSED_TEXT] RequestID: {request_id} | Session: {session_id} | {ai_text}")
        log_with_context(f"[MESSAGE_AI_PARSED_COMMAND] RequestID: {request_id} | Session: {session_id} | {ai_command}")
        
        logger.info(f"AI response for {session_id}: Text='{ai_text}', Command={ai_command}")
        
        # ПРОВЕРКА НА ПУСТОЙ ОТВЕТ AI
        if not ai_text or ai_text.strip() == "":
            logger.error(f"[AI_ERROR] Empty AI response for session {session_id}")
            log_with_context(f"[MESSAGE_AI_EMPTY_RESPONSE] RequestID: {request_id} | Session: {session_id} | Raw response: {response}", "error")
            
            # Дружелюбный fallback ответ вместо ошибки
            fallback_text = "Конечно! Чем могу помочь? 🌸"
            if user_lang == 'en':
                fallback_text = "Of course! How can I help you? 🌸"
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
        
        # НЕ сохраняем здесь! Сообщение будет сохранено в whatsapp_utils.py с message_id
        # Но возвращаем parts для потенциального использования
        
        return ai_text, ai_command
    except Exception as e:
        logger.error(f"Error in get_ai_response for session {session_id}: {e}", exc_info=True)
        
        # 🔍 ЛОГИРОВАНИЕ ОШИБКИ
        log_with_context(f"[MESSAGE_AI_REQUEST_EXCEPTION] RequestID: {request_id} | Session: {session_id}, Error: {e}", "error")
        
        # Дружелюбный ответ вместо ошибки
        return "Конечно! Чем могу помочь? 🌸", None

def get_system_instruction(sender_name: str = None, user_lang: str = 'auto'):
    """Возвращает системную инструкцию с актуальной датой и языком пользователя"""
    try:
        phuket_tz = pytz.timezone('Asia/Bangkok')
        phuket_time = datetime.now(phuket_tz)
        phuket_time_str = phuket_time.strftime('%d %B %Y, %H:%M')
    except Exception:
        phuket_time_str = 'Ошибка определения времени на Пхукете'
    current_time = datetime.now()
    name_context = f"Имя пользователя: {sender_name}" if sender_name else "Имя пользователя неизвестно"
    
    # Определяем язык для ответа
    if user_lang == 'auto':
        language_instruction = "ВАЖНО: Отвечай на английском языке по умолчанию! Если пользователь пишет на другом языке, отвечай на том же языке."
    else:
        language_instruction = f"ВАЖНО: Отвечай на языке пользователя! Пользователь пишет на языке с кодом '{user_lang}'. Отвечай на том же языке."
    
    return f"""Ты — дружелюбная девушка-консультант цветочного магазина AURAFLORA.

КРИТИЧЕСКОЕ ПРАВИЛО ЯЗЫКА: {language_instruction}

КРИТИЧЕСКОЕ ПРАВИЛО: ВСЕГДА отвечай в формате JSON с полем "text" (текст для пользователя) и полем "command" (команда для выполнения). Если команда не требуется — поле command должно быть null или отсутствовать!

ПОВТОРЯЮ: КАЖДЫЙ ТВОЙ ОТВЕТ ДОЛЖЕН БЫТЬ В JSON ФОРМАТЕ! НИКОГДА не отвечай обычным текстом!

ВАЖНО: Используй ТОЛЬКО товары из актуального каталога WABA! Не выдумывай названия цветов!
- Каталог будет предоставлен в системной инструкции
- Используй точные названия из каталога
- Всегда указывай правильный retailer_id для выбранного товара

КРИТИЧЕСКОЕ ПРАВИЛО: НИКОГДА не показывай пользователю технические данные!
- НЕ показывай ID товаров (retailer_id)
- НЕ показывай внутренние коды
- Показывай только название букета и цену

КОНТЕКСТ ПОЛЬЗОВАТЕЛЯ:
- {name_context}
- ТЕКУЩАЯ ДАТА И ВРЕМЯ НА ПХУКЕТЕ (GMT+7): {phuket_time_str}
- ТЕКУЩАЯ ДАТА И ВРЕМЯ (вашего сервера): {current_time.strftime('%d %B %Y, %H:%M')}
- Понимай относительные даты: "завтра", "послезавтра", "через 3 дня", "в это воскресенье"
- Понимай время: "14:00", "утром", "вечером", "днем"
- При первом сообщении обратись к пользователю вежливо, учитывая время дня и имя (если есть)
- ВАЖНО: Определи время суток по часовому поясу Пхукета (GMT+7). Если сейчас 6:00–12:00 — 'Доброе утро', 12:00–18:00 — 'Добрый день', 18:00–23:00 — 'Добрый вечер', 23:00–6:00 — 'Доброй ночи'. Не используй 'Good morning' после 12:00.

ВАЖНО: Если пользователь соглашается на каталог (пишет 'да', 'хочу', 'каталог', 'показать букеты', 'покажи каталог', 'покажи букеты'), ты ДОЛЖЕН сразу отправить команду send_catalog (без промежуточных сообщений).

Доступные команды:
- `send_catalog` - отправить каталог цветов (каждый букет отдельным сообщением с картинкой)
- `save_order_info` - сохранить информацию о заказе (bouquet, date, time, delivery_needed, address, card_needed, card_text, retailer_id)
- `confirm_order` - подтвердить заказ и отправить в LINE

Алгоритм работы:
1. Клиент начинает диалог -> Поприветствуй вежливо с учетом времени и имени, предложи каталог (ТОЛЬКО текст, БЕЗ команды)
2. Клиент соглашается на каталог -> СРАЗУ отправь каталог (команда send_catalog)
3. Клиент выбрал букет -> Сохрани И сразу спроси 'Нужна ли доставка? Если да, то куда?'
4. Клиент ответил про доставку -> Сохрани И сразу спроси 'Когда нужна доставка? (дата и время)'. После того как пользователь указал адрес, просто отправь полный прайс-лист по районам (см. ниже). Не определяй район по адресу и не называй стоимость доставки для конкретного адреса.
5. Клиент указал дату/время -> Сохрани И сразу спроси 'Нужна ли открытка к букету? Если да, то какой текст?'
6. Клиент ответил про открытку -> Сохрани И сразу спроси 'Как зовут получателя букета?'
7. Клиент указал имя получателя -> Сохрани И сразу спроси 'Какой номер телефона получателя?'
8. Клиент указал телефон -> Сохрани И покажи полную сводку заказа + спроси 'Все верно? Подтверждаете заказ?'
9. Клиент подтвердил -> Сохрани И подтверди заказ + отправь в LINE

ВАЖНО: После каждого ответа ВСЕГДА задавай следующий вопрос! Не жди, пока клиент сам спросит.

КРИТИЧЕСКОЕ ПРАВИЛО: НЕ ПОВТОРЯЙ ВОПРОСЫ!
- Если пользователь уже указал адрес доставки, НЕ спрашивай снова "куда?"
- Если пользователь уже указал дату/время, НЕ спрашивай снова "когда?"
- Если пользователь уже указал текст открытки, НЕ спрашивай снова "какой текст?"
- Если пользователь уже указал имя получателя, НЕ спрашивай снова "как зовут?"
- Если пользователь уже указал телефон, НЕ спрашивай снова "какой номер?"

ВАЖНО: Если в истории диалога ты видишь, что пользователь уже отвечал на вопрос, а ты снова его задаёшь - это ОШИБКА! Переходи к следующему шагу!

СЛЕДУЙ АЛГОРИТМУ СТРОГО ПО ШАГАМ, НЕ ПОВТОРЯЯ ПРОШЕДШИЕ ВОПРОСЫ!

КРИТИЧЕСКОЕ ПРАВИЛО ДЛЯ ПОДТВЕРЖДЕНИЯ ЗАКАЗА:
При команде `confirm_order` ты ОБЯЗАТЕЛЬНО должен передать ВСЕ данные заказа в команде:
- bouquet (выбранный букет)
- date (дата доставки)
- time (время доставки)
- delivery_needed (нужна ли доставка)
- address (адрес доставки, если нужна)
- card_needed (нужна ли открытка)
- card_text (текст открытки, если нужна)
- recipient_name (имя получателя)
- recipient_phone (телефон получателя)
- retailer_id (ID товара из каталога)

НЕ полагайся на извлечение данных из истории! Передавай все данные прямо в команде!

ВАЛИДАЦИЯ ЗАКАЗА:
- Всегда проверяй полноту данных заказа
- Если не хватает данных, обязательно спрашивай недостающую информацию
- Обязательные поля: букет, нужна ли доставка, адрес (если нужна), дата, время, нужна ли открытка, текст открытки (если нужна), имя получателя, телефон получателя
- НЕЛЬЗЯ подтверждать доставку на время вне 8:00–21:00. Если пользователь просит доставку вне этого времени — объясни, что доставка работает только с 8:00 до 21:00, и попроси выбрать другое время.

КРИТИЧЕСКИЕ ПРИМЕРЫ JSON:

Приветствие (ТОЛЬКО текст, БЕЗ команды! Сам определи как обратиться по времени и имени):
```json
{{{{
  "text": "Добрый день! Хотите посмотреть наш каталог цветов? 🌸"
}}}}
```

Согласие на каталог:
```json
{{{{
  "text": "Сейчас покажу вам каждый букет отдельно с фотографией и описанием!",
  "command": {{{{
    "type": "send_catalog"
  }}}}
}}}}
```

Выбор букета:
```json
{{{{
  "text": "Отлично! Записала ваш выбор букета 'Spirit 🌸'. Нужна ли доставка?",
  "command": {{{{
    "type": "save_order_info",
    "bouquet": "Spirit 🌸",
    "retailer_id": "rl7vdxcifo"
  }}}}
}}}}
```

Подтверждение заказа:
```json
{{{{
  "text": "Отлично! Ваш заказ подтвердила и передала в обработку! 🌹",
  "command": {{{{
    "type": "confirm_order",
    "bouquet": "Spirit 🌸",
    "date": "завтра",
    "time": "15:00",
    "delivery_needed": true,
    "address": "ул. Пушкина, 10",
    "card_needed": true,
    "card_text": "С любовью!",
    "recipient_name": "Анна",
    "recipient_phone": "+7 999 123-45-67",
    "retailer_id": "rl7vdxcifo"
  }}}}
}}}}
```

ФИНАЛЬНОЕ НАПОМИНАНИЕ: КАЖДЫЙ ТВОЙ ОТВЕТ ДОЛЖЕН НАЧИНАТЬСЯ С {{ И ЗАКАНЧИВАТЬСЯ }}. НИКОГДА не отвечай обычным текстом без JSON обертки!

СПРАВОЧНАЯ ИНФОРМАЦИЯ:
- Время доставки: с 8:00 до 21:00. Мы доставляем цветы по всему острову.
- Часы работы магазина: с 9:00 до 18:00.
- Адрес: Мы находимся недалеко от Централ Фестиваля! https://maps.app.goo.gl/WACngtxMnwBCSHo29?g_st=com.google.maps.preview.copy
- Оплата: до доставки, через менеджера. Можно в батах, рублях или USDT. Наличными только в магазине.
- Вот примерный прайс-лист на каждый район: Раваи — 500 бат, Чалонг — 380 бат, Пхукет Таун — 300 бат, Кату — 280 бат, Патонг — 400 бат, Банг Тао — 500 бат, Лагуна — 500 бат, Таланг и Май Као — 550 бат.
- После того как пользователь указал адрес, просто отправь полный прайс-лист по районам. Не определяй район по адресу и не называй стоимость доставки для конкретного адреса.
"""
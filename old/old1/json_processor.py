import json
import re
import logging
from typing import Dict, Any, Optional, Tuple
from src import config
import uuid
import inspect
from google.generativeai import GenerationConfig

logger = logging.getLogger(__name__)

# Создаем специальный logger для JSON парсинга
json_processor_logger = logging.getLogger('json_processor')

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
        json_processor_logger.info(full_message)
    elif level == "error":
        json_processor_logger.error(full_message)
    elif level == "warning":
        json_processor_logger.warning(full_message)

def parse_ai_response(response, request_id: str = None) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Полностью обрабатывает ответ AI и извлекает текст и команду.
    AI ВСЕГДА должен возвращать JSON согласно системной инструкции.
    
    Args:
        response: Ответ от Gemini API
        request_id: ID запроса для логирования
        
    Returns:
        Tuple[Optional[str], Optional[Dict]]: (текст_для_пользователя, команда)
    """
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    
    try:
        # Извлекаем текст из всех частей ответа AI
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        
        if not text_parts:
            logger.error("[JSON_PROCESSOR] No text parts found in AI response")
            log_with_context("[JSON_AI_PARSE_ERROR] No text parts found in AI response", "error")
            return None, None
        
        full_text = ''.join(text_parts)
        
        # 🔍 ЛОГИРОВАНИЕ RAW AI RESPONSE
        log_with_context(f"[JSON_AI_PARSE_INPUT] RequestID: {request_id} | Full AI response: {full_text}")
        
        logger.info(f"[JSON_PROCESSOR] Processing AI response: {full_text[:100]}...")
        
        # Извлекаем JSON из ответа AI
        json_data, user_text = extract_and_fix_json(full_text)
        
        # Если JSON не найден - это ошибка, AI должен был вернуть JSON
        if json_data is None:
            logger.error("[JSON_PROCESSOR] AI не вернул JSON - это ошибка согласно системной инструкции")
            log_with_context(f"[JSON_AI_PARSE_NO_JSON] RequestID: {request_id} | AI should have returned JSON according to system instruction", "error")
            return None, None
        
        # Извлекаем команду из JSON данных
        command = json_data.get('command', None)
        
        # Если текст не был извлечён из JSON, используем поле text
        if not user_text and json_data.get('text'):
            user_text = json_data.get('text')
        
        # 🔍 ЛОГИРОВАНИЕ PARSE РЕЗУЛЬТАТА
        log_with_context(f"[JSON_AI_PARSE_JSON_DATA] RequestID: {request_id} | {json_data}")
        log_with_context(f"[JSON_AI_PARSE_USER_TEXT] RequestID: {request_id} | {user_text}")
        log_with_context(f"[JSON_AI_PARSE_COMMAND] RequestID: {request_id} | {command}")
        
        logger.info(f"[JSON_PROCESSOR] Result: text='{user_text}', command={command}")
        return user_text, command
        
    except Exception as e:
        logger.error(f"[JSON_PROCESSOR] Unexpected error in parse_ai_response: {e}")
        log_with_context(f"[JSON_AI_PARSE_EXCEPTION] RequestID: {request_id} | {e}", "error")
        return None, None

def extract_and_fix_json(ai_response: str, retry_count: int = 2) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Извлекает JSON из ответа AI. AI ВСЕГДА должен возвращать JSON согласно системной инструкции.
    
    Args:
        ai_response: Ответ от AI (должен содержать JSON)
        retry_count: Количество попыток исправления через AI
        
    Returns:
        Tuple[Optional[Dict], str]: (извлеченные_данные, текст_для_пользователя)
    """
    # Генерируем уникальный ID для этого запроса
    request_id = str(uuid.uuid4())[:8]  # Короткий ID
    
    # 🔍 ЛОГИРОВАНИЕ ВХОДНЫХ ДАННЫХ
    log_with_context(f"[JSON_AI_EXTRACT_START] RequestID: {request_id} | AI response length: {len(ai_response)}")
    log_with_context(f"[JSON_AI_EXTRACT_INPUT] RequestID: {request_id} | Raw AI response: {ai_response}")
    
    logger.info(f"[JSON_PROCESSOR] Обработка ответа AI, длина: {len(ai_response)}")
    
    # Шаг 1: Попытка извлечь JSON напрямую
    log_with_context(f"[JSON_AI_EXTRACT_STEP1] RequestID: {request_id} | Trying direct JSON extraction")
    json_data, user_text = _try_extract_json_direct(ai_response, request_id)
    
    if json_data is not None:
        logger.info("[JSON_PROCESSOR] JSON успешно извлечён напрямую")
        log_with_context(f"[JSON_AI_EXTRACT_SUCCESS_DIRECT] RequestID: {request_id} | JSON extracted successfully on first try")
        log_with_context(f"[JSON_AI_EXTRACT_RESULT] RequestID: {request_id} | JSON data: {json_data}")
        log_with_context(f"[JSON_AI_EXTRACT_RESULT] RequestID: {request_id} | User text: {user_text}")
        return json_data, user_text
    
    # Шаг 2: JSON некорректный, пытаемся исправить через AI
    logger.warning("[JSON_PROCESSOR] JSON некорректный, пытаемся исправить через AI")
    log_with_context(f"[JSON_AI_EXTRACT_STEP2] RequestID: {request_id} | JSON invalid, attempting AI fix")
    
    for attempt in range(retry_count):
        logger.info(f"[JSON_PROCESSOR] Попытка исправления #{attempt + 1}")
        log_with_context(f"[JSON_AI_FIX_ATTEMPT] RequestID: {request_id} | Attempt #{attempt + 1}/{retry_count}")
        
        try:
            fixed_response = _fix_json_with_ai(ai_response, request_id)
            if not fixed_response:
                log_with_context(f"[JSON_AI_FIX_ATTEMPT_{attempt + 1}] RequestID: {request_id} | AI returned empty response", "warning")
                continue
                
            log_with_context(f"[JSON_AI_FIX_ATTEMPT_{attempt + 1}] RequestID: {request_id} | AI returned: {fixed_response}")
            
            json_data, user_text = _try_extract_json_direct(fixed_response, request_id)
            
            if json_data is not None:
                logger.info(f"[JSON_PROCESSOR] JSON исправлен на попытке #{attempt + 1}")
                log_with_context(f"[JSON_AI_FIX_SUCCESS] RequestID: {request_id} | JSON fixed on attempt #{attempt + 1}")
                log_with_context(f"[JSON_AI_FIX_RESULT] RequestID: {request_id} | JSON data: {json_data}")
                log_with_context(f"[JSON_AI_FIX_RESULT] RequestID: {request_id} | User text: {user_text}")
                return json_data, user_text
                
        except Exception as e:
            logger.error(f"[JSON_PROCESSOR] Ошибка при исправлении JSON (попытка #{attempt + 1}): {e}")
            log_with_context(f"[JSON_AI_FIX_ATTEMPT_{attempt + 1}_ERROR] RequestID: {request_id} | {e}", "error")
            continue
    
    # Шаг 3: Если не удалось исправить - возвращаем None (AI должен был вернуть JSON)
    logger.error("[JSON_PROCESSOR] Не удалось исправить JSON - AI должен был вернуть JSON согласно системной инструкции")
    log_with_context(f"[JSON_AI_EXTRACT_FAILED] RequestID: {request_id} | All fix attempts failed - AI should have returned JSON", "error")
    
    return None, None


def _try_extract_json_direct(response: str, request_id: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Пытается извлечь JSON напрямую из ответа.
    
    Returns:
        Tuple[Optional[Dict], str]: (json_данные, текст_для_пользователя)
    """
    # 🔍 ЛОГИРОВАНИЕ ПРЯМОГО ИЗВЛЕЧЕНИЯ
    log_with_context(f"[JSON_DIRECT_START] RequestID: {request_id} | Attempting direct extraction from: {response}")
    
    # Удаляем markdown блоки
    cleaned_response = _clean_markdown(response)
    log_with_context(f"[JSON_DIRECT_CLEANED] RequestID: {request_id} | After markdown cleaning: {cleaned_response}")
    
    # Пытаемся найти JSON блок
    json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
    if not json_match:
        log_with_context(f"[JSON_DIRECT_NO_MATCH] RequestID: {request_id} | No JSON pattern found")
        return None, None
    
    json_str = json_match.group()
    log_with_context(f"[JSON_DIRECT_FOUND] RequestID: {request_id} | JSON string found: {json_str}")
    
    try:
        # Пытаемся распарсить JSON как есть
        json_data = json.loads(json_str)
        log_with_context(f"[JSON_DIRECT_PARSED] RequestID: {request_id} | Successfully parsed JSON: {json_data}")
        
        # Извлекаем текст из JSON - это основной источник текста
        user_text = json_data.get('text', '').strip()
        
        # Если text пустой, это ошибка - AI должен был вернуть текст
        if not user_text:
            logger.error("[JSON_PROCESSOR] AI вернул JSON без поля 'text' - это ошибка")
            log_with_context(f"[JSON_DIRECT_NO_TEXT] RequestID: {request_id} | AI returned JSON without 'text' field", "error")
            return None, None
        
        # НЕ очищаем текст - сохраняем оригинальное форматирование
        log_with_context(f"[JSON_DIRECT_TEXT_EXTRACTED] RequestID: {request_id} | Text from JSON: {user_text}")
        
        return json_data, user_text
        
    except json.JSONDecodeError as e:
        logger.warning(f"[JSON_PROCESSOR] Ошибка парсинга JSON: {e}")
        log_with_context(f"[JSON_DIRECT_PARSE_ERROR] RequestID: {request_id} | JSON parse error: {e}")
        log_with_context(f"[JSON_DIRECT_PARSE_ERROR] RequestID: {request_id} | Problematic JSON: {json_str}")
        
        # Попробуем исправить простые ошибки с переносами строк
        try:
            # Заменяем неэкранированные переносы строк в строковых значениях
            fixed_json = re.sub(r'(["\'])([^"\']*?)\n([^"\']*?)\1', r'\1\2\\n\3\1', json_str)
            json_data = json.loads(fixed_json)
            
            user_text = json_data.get('text', '').strip()
            if user_text:
                log_with_context(f"[JSON_DIRECT_FIXED] RequestID: {request_id} | JSON fixed with regex: {user_text}")
                return json_data, user_text
        except:
            pass
        
        return None, None


def _fix_json_with_ai(broken_response: str, request_id: str) -> Optional[str]:
    """
    Отправляет некорректный JSON другой AI для исправления.
    """
    # 🔍 ЛОГИРОВАНИЕ AI ИСПРАВЛЕНИЯ
    log_with_context(f"[JSON_AI_FIX_START] RequestID: {request_id} | Starting AI fix process")
    log_with_context(f"[JSON_AI_FIX_INPUT] RequestID: {request_id} | Broken response: {broken_response}")
    
    try:
        import google.generativeai as genai
        
        # Используем тот же API ключ, что и основная AI
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192  # Максимальное значение для Gemini
            )
        )
        
        fix_prompt = f"""
Fix this JSON response to make it valid JSON.
IMPORTANT: Preserve ALL line breaks and formatting in the "text" field!
DO NOT replace \\n with spaces, DO NOT merge lines!

Preserve all data, but fix only syntax errors.
Return ONLY the fixed JSON, without explanations.

Original response:
{broken_response}
"""
        
        log_with_context(f"[JSON_AI_FIX_PROMPT] RequestID: {request_id} | Prompt sent to AI: {fix_prompt}")
        
        response = model.generate_content(fix_prompt)
        fixed_text = response.text.strip()
        
        log_with_context(f"[JSON_AI_FIX_RAW_RESPONSE] RequestID: {request_id} | AI raw response: {response}")
        log_with_context(f"[JSON_AI_FIX_TEXT] RequestID: {request_id} | AI response text: {fixed_text}")
        
        logger.info(f"[JSON_PROCESSOR] AI ответил для исправления: {fixed_text[:100]}...")
        return fixed_text
        
    except Exception as e:
        logger.error(f"[JSON_PROCESSOR] Ошибка при исправлении через AI: {e}")
        log_with_context(f"[JSON_AI_FIX_ERROR] RequestID: {request_id} | AI fix failed: {e}", "error")
        return None


def _clean_markdown(text: str) -> str:
    """Удаляет markdown форматирование."""
    # 🔍 ЛОГИРОВАНИЕ ОЧИСТКИ MARKDOWN
    log_with_context(f"[MARKDOWN_CLEAN_INPUT] {text}")
    
    # Удаляем блоки кода
    text = re.sub(r'^```[a-zA-Z]*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```$', '', text, flags=re.MULTILINE)
    text = re.sub(r'```', '', text)
    
    cleaned = text.strip()
    log_with_context(f"[MARKDOWN_CLEAN_OUTPUT] {cleaned}")
    
    return cleaned 
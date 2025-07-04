import logging
from . import catalog_reader, database
from .whatsapp_utils import send_whatsapp_message
import inspect

logger = logging.getLogger(__name__)

# Создаем специальный logger для reply пайплайна
reply_logger = logging.getLogger('reply_pipeline')

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
        reply_logger.info(full_message)
    elif level == "error":
        reply_logger.error(full_message)
    elif level == "warning":
        reply_logger.warning(full_message)

def extract_bouquet_name_or_id_from_caption(caption: str, products=None):
    """Извлекает название или ID букета из подписи к картинке WhatsApp. Ищет по всем строкам, сверяет с каталогом."""
    log_with_context("[EXTRACT_BOUQUET_START] ==================== BOUQUET EXTRACTION ====================")
    log_with_context(f"[EXTRACT_BOUQUET_INPUT] Caption: {caption}")
    
    import re
    import unicodedata
    def clean_text(text):
        text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+', '', text)
        text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
        return text.replace(' ', '').lower()
    
    lines = [l.strip() for l in caption.split('\n') if l.strip()]
    log_with_context(f"[EXTRACT_BOUQUET_LINES] Parsed lines: {lines}")
    
    bouquet_id = None
    bouquet_name = None
    
    # 1. Ищем ID по всем строкам
    log_with_context("[EXTRACT_BOUQUET_SEARCH_ID] Searching for ID in lines")
    for line in lines:
        id_match = re.search(r'ID[:\s]*([a-zA-Z0-9]+)', line)
        if id_match:
            bouquet_id = id_match.group(1)
            log_with_context(f"[EXTRACT_BOUQUET_FOUND_ID] Found ID: {bouquet_id} in line: {line}")
            break
    
    # 2. Если есть каталог — ищем совпадение по имени (гибко)
    if products:
        log_with_context(f"[EXTRACT_BOUQUET_SEARCH_NAME] Searching for name match in {len(products)} products")
        for line in lines:
            clean_line = clean_text(line)
            log_with_context(f"[EXTRACT_BOUQUET_CLEAN_LINE] Cleaned line: '{line}' -> '{clean_line}'")
            
            for p in products:
                pname = p.get('name', '').replace('🌸', '').strip()
                clean_pname = clean_text(pname)
                log_with_context(f"[EXTRACT_BOUQUET_COMPARE] Comparing '{clean_line}' with '{clean_pname}'")
                
                if clean_line == clean_pname:
                    bouquet_name = p.get('name')
                    bouquet_id = p.get('retailer_id')
                    log_with_context(f"[EXTRACT_BOUQUET_MATCH_FOUND] Name match: {bouquet_name}, ID: {bouquet_id}")
                    return bouquet_name, bouquet_id
    
    # 3. Если не нашли — пробуем первую строку (как fallback)
    if not bouquet_name and lines:
        name_clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+', '', lines[0]).strip()
        bouquet_name = name_clean
        log_with_context(f"[EXTRACT_BOUQUET_FALLBACK] Using first line as fallback: {bouquet_name}")
    
    log_with_context(f"[EXTRACT_BOUQUET_RESULT] Final result - Name: {bouquet_name}, ID: {bouquet_id}")
    return bouquet_name, bouquet_id

async def handle_bouquet_selection(session_id: str, bouquet_caption: str):
    """Обрабатывает выбор букета через reply (по подписи к картинке)."""
    log_with_context("[REPLY_BOUQUET_START] ==================== REPLY BOUQUET SELECTION ====================")
    log_with_context(f"[REPLY_BOUQUET_INPUT] Session: {session_id}, Caption: {bouquet_caption}")
    logger.info(f"Handling bouquet selection via reply: {bouquet_caption} for session {session_id}")
    
    products = catalog_reader.get_catalog_products()
    log_with_context(f"[REPLY_BOUQUET_CATALOG] Retrieved {len(products)} products from catalog")
    
    name, bouquet_id = extract_bouquet_name_or_id_from_caption(bouquet_caption, products)
    log_with_context(f"[REPLY_BOUQUET_EXTRACTED] Name: {name}, ID: {bouquet_id}")
    
    validation = None
    if bouquet_id:
        log_with_context(f"[REPLY_BOUQUET_VALIDATE_ID] Validating by ID: {bouquet_id}")
        validation = catalog_reader.validate_product_selection(bouquet_id)
        if validation['valid']:
            log_with_context(f"[REPLY_BOUQUET_VALID_ID] Bouquet found by ID: {bouquet_id}")
            logger.info(f"Bouquet found by ID: {bouquet_id}")
    
    if not validation or not validation['valid']:
        log_with_context(f"[REPLY_BOUQUET_VALIDATE_NAME] Validating by name: {name}")
        validation = catalog_reader.validate_product_by_name(name)
    
    if not validation['valid']:
        log_with_context(f"[REPLY_BOUQUET_INVALID] Invalid selection: {bouquet_caption}", "warning")
        logger.warning(f"Invalid bouquet selection via reply: {bouquet_caption}")
        available_products = validation.get('available_products', [])
        product_names = available_products[:5]  # Первые 5 товаров
        phone_number = session_id.split('_')[0]
        log_with_context(f"[REPLY_BOUQUET_ERROR_MESSAGE] Sending error message to: {phone_number}")
        await send_whatsapp_message(phone_number, \
            f"Такого букета нет в каталоге. Вот что у нас есть: {', '.join(product_names)} 🌸")
        return {"status": "error", "action": "invalid_product"}
    
    product = validation['product']
    log_with_context(f"[REPLY_BOUQUET_PRODUCT] Validated product: {product}")
    
    order_data = {
        'bouquet': product.get('name', name),
        'retailer_id': product.get('retailer_id'),
        'product_name': product.get('name', name),
        'product_price': product.get('price', 'Цена не указана')
    }
    log_with_context(f"[REPLY_BOUQUET_ORDER_DATA] Order data: {order_data}")
    
    # Данные теперь сохраняются в parts AI-сообщения, не нужно отдельные system-сообщения
    phone_number = session_id.split('_')[0]
    log_with_context(f"[REPLY_BOUQUET_PHONE] Extracted phone: {phone_number}")
    
    success_message = f"Отлично! Записал ваш выбор букета '{product.get('name', name)}'. Нужна ли доставка? Если да, то куда? 🌸"
    log_with_context(f"[REPLY_BOUQUET_SUCCESS_MESSAGE] Sending success message: {success_message}")
    await send_whatsapp_message(phone_number, success_message)
    
    log_with_context("[REPLY_BOUQUET_END] ==================== REPLY BOUQUET SELECTION END ====================")
    return {"status": "success", "action": "bouquet_selected"} 
"""
Обработчик команд от AI в JSON формате
"""

import logging
import asyncio
from . import whatsapp_utils, database, catalog_reader, order_utils
import re
import unicodedata
import json
import inspect

logger = logging.getLogger(__name__)

# Создаем специальный logger для команд
command_logger = logging.getLogger('command_handler')

# Создаем специальный logger для command пайплайна
command_pipeline_logger = logging.getLogger('command_pipeline')

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
        command_logger.info(full_message)
    elif level == "error":
        command_logger.error(full_message)
    elif level == "warning":
        command_logger.warning(full_message)

async def handle_commands(sender_id: str, session_id: str, command: dict):
    """
    Выполняет команду, полученную от AI в JSON формате.
    """
    # 🔍 ЛОГИРОВАНИЕ НАЧАЛА ОБРАБОТКИ КОМАНДЫ
    command_logger.info(f"[COMMAND_START] Session: {session_id}")
    command_logger.info(f"[COMMAND_INPUT] Command received: {command}")
    
    logger.info(f"[COMMAND_LOG] Starting command handling for session {session_id}")
    logger.info(f"[COMMAND_LOG] Command received: {command}")
    
    try:
        if not isinstance(command, dict):
            logger.error(f"Invalid command format: {command}")
            command_logger.error(f"[COMMAND_ERROR] Invalid format - not a dict: {command}")
            return {"status": "error", "message": "Invalid command format"}
        
        if not command:  # Пустой словарь
            logger.warning("Empty command")
            command_logger.warning("[COMMAND_EMPTY] Empty command dict")
            return {"status": "success", "message": "No command to execute"}
        
        command_type = command.get('type')
        
        if not command_type:
            logger.error(f"No command type found in command: {command}")
            command_logger.error(f"[COMMAND_ERROR] No type field: {command}")
            return {"status": "error", "message": "No command type found"}
        
        # 🔍 ЛОГИРОВАНИЕ ТИПА КОМАНДЫ
        command_logger.info(f"[COMMAND_TYPE] Processing command type: {command_type}")
        
        logger.info(f"[COMMAND_LOG] Processing command: {command}")
        
        # Выполняем команду в зависимости от типа
        if command_type == 'send_catalog':
            command_logger.info("[COMMAND_EXEC] Executing send_catalog")
            result = await handle_send_catalog(sender_id, session_id, command)
        elif command_type == 'save_order_info':
            command_logger.info("[COMMAND_EXEC] Executing save_order_info")
            result = await handle_save_order_info(sender_id, session_id, command)
        elif command_type == 'confirm_order':
            command_logger.info("[COMMAND_EXEC] Executing confirm_order")
            result = await handle_confirm_order(sender_id, session_id, command)
        elif command_type == 'clarify_request':
            command_logger.info("[COMMAND_EXEC] Executing clarify_request")
            result = await handle_clarify_request(sender_id, session_id, command)
        else:
            logger.error(f"Unknown command type: {command_type}")
            command_logger.error(f"[COMMAND_ERROR] Unknown command type: {command_type}")
            result = {"status": "error", "message": f"Unknown command: {command_type}"}
        
        # 🔍 ЛОГИРОВАНИЕ РЕЗУЛЬТАТА
        command_logger.info(f"[COMMAND_RESULT] Command '{command_type}' result: {result}")
        
        logger.info(f"[COMMAND_LOG] Command '{command_type}' result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error handling command: {e}", exc_info=True)
        command_logger.error(f"[COMMAND_EXCEPTION] Session: {session_id}, Error: {e}")
        return {"status": "error", "message": str(e)}

async def handle_send_catalog(sender_id: str, session_id: str, command: dict):
    """Обрабатывает команду отправки каталога (только по согласию пользователя)"""
    # 🔍 ЛОГИРОВАНИЕ ОТПРАВКИ КАТАЛОГА
    command_logger.info(f"[CATALOG_START] Sender: {sender_id}, Session: {session_id}")
    command_logger.info(f"[CATALOG_COMMAND] Command details: {command}")
    
    logger.info(f"Executing 'send_catalog' command for sender {sender_id}, session {session_id}")
    # Каталог отправляется только если пользователь явно запросил (например, написал 'хочу', 'каталог', 'показать букеты' и т.д.)
    
    command_logger.info(f"[CATALOG_PHONE] Using sender_id: {sender_id}")
    
    await whatsapp_utils.handle_send_catalog(sender_id, session_id)
    
    result = {"status": "success", "action": "catalog_sent"}
    command_logger.info(f"[CATALOG_RESULT] {result}")
    
    return result

async def handle_save_order_info(sender_id: str, session_id: str, command: dict):
    """Обрабатывает команду сохранения информации о заказе"""
    # 🔍 ЛОГИРОВАНИЕ СОХРАНЕНИЯ ЗАКАЗА
    command_logger.info(f"[SAVE_ORDER_START] Sender: {sender_id}, Session: {session_id}")
    command_logger.info(f"[SAVE_ORDER_COMMAND] Command details: {command}")
    
    logger.info(f"Executing 'save_order_info' command for sender {sender_id}, session {session_id}")
    # Проверка delivery_question_asked больше не нужна, так как system-сообщения не сохраняются
    # Извлекаем данные из команды
    order_data = {}
    for key in ['bouquet', 'date', 'time', 'delivery_needed', 'address', 'card_needed', 'card_text']:
        if key in command:
            order_data[key] = command[key]
    
    command_logger.info(f"[SAVE_ORDER_DATA] Extracted order data: {order_data}")
    
    # Если указан букет, валидируем его
    if 'bouquet' in order_data:
        retailer_id = command.get('retailer_id')
        command_logger.info(f"[SAVE_ORDER_VALIDATION] Validating bouquet: {order_data['bouquet']}, retailer_id: {retailer_id}")
        
        if retailer_id:
            validation = catalog_reader.validate_product_selection(retailer_id)
            command_logger.info(f"[SAVE_ORDER_VALIDATION_RESULT] {validation}")
            
            if not validation['valid']:
                logger.warning(f"Invalid product selection: {retailer_id}")
                
                # Получаем список доступных товаров для предложения альтернатив
                available_products = catalog_reader.get_catalog_products()
                product_names = [p.get('name', 'Без названия') for p in available_products[:5]]  # Первые 5 товаров
                
                error_result = {
                    "status": "error", 
                    "action": "invalid_product",
                    "message": f"Такого букета нет в каталоге. Вот что у нас есть: {', '.join(product_names)}",
                    "available_products": product_names
                }
                
                command_logger.error(f"[SAVE_ORDER_INVALID_PRODUCT] {error_result}")
                return error_result
            else:
                # Сохраняем информацию о реальном товаре
                product = validation['product']
                order_data['product_name'] = product.get('name', order_data['bouquet'])
                order_data['product_price'] = product.get('price', 'Цена не указана')
                order_data['retailer_id'] = retailer_id
                
                command_logger.info(f"[SAVE_ORDER_PRODUCT_INFO] Product validated and added: {product}")
    
    # Данные теперь сохраняются в parts AI-сообщения, не нужно отдельные system-сообщения
    
    # Не отправляем лишнее сообщение пользователю
    # Данные сохраняются в parts AI-сообщения
    
    result = {"status": "success", "action": "data_saved", "data": order_data}
    command_logger.info(f"[SAVE_ORDER_RESULT] {result}")
    
    return result

async def handle_confirm_order(sender_id: str, session_id: str, command: dict):
    """Обрабатывает команду подтверждения заказа"""
    logger.info(f"Executing 'confirm_order' command for sender {sender_id}, session {session_id}")
    
    # 1. Сначала проверяем, есть ли данные заказа прямо в команде
    order_data = {}
    
    # Извлекаем данные из команды confirm_order (если AI передал их)
    for key in ['bouquet', 'date', 'time', 'delivery_needed', 'address', 'card_needed', 'card_text', 'recipient_name', 'recipient_phone', 'retailer_id']:
        if key in command:
            order_data[key] = command[key]
    
    command_logger.info(f"[CONFIRM_ORDER_DATA_FROM_COMMAND] {order_data}")
    
    # Если в команде нет данных, собираем из истории
    if not order_data:
        logger.info(f"No order data in command, collecting from history for sender {sender_id}, session {session_id}")
        command_logger.info("[CONFIRM_ORDER_COLLECTING_FROM_HISTORY] No data in command, collecting from history")
        
        history = database.get_conversation_history_for_ai(sender_id, session_id)  # Используем историю для AI
        command_logger.info(f"[CONFIRM_ORDER_HISTORY] Retrieved history: {history}")
        
        for msg in history:
            if msg.get('role') == 'model' and msg.get('parts'):
                # Ищем данные в parts
                for part in msg['parts']:
                    if part.get('text', '').startswith('[SAVED:'):
                        saved_text = part['text']
                        command_logger.info(f"[CONFIRM_ORDER_FOUND_SAVED] Found saved data: {saved_text}")
                        
                        # Извлекаем данные из [SAVED: key=value, key2=value2]
                        try:
                            data_part = saved_text[7:-1]  # Убираем [SAVED: и ]
                            for item in data_part.split(', '):
                                if '=' in item:
                                    key, value = item.split('=', 1)
                                    order_data[key] = value
                        except Exception as e:
                            logger.warning(f"Failed to parse saved data: {saved_text}, error: {e}")
                            command_logger.warning(f"[CONFIRM_ORDER_PARSE_ERROR] Failed to parse: {saved_text}, error: {e}")
                            continue
    else:
        logger.info(f"Found order data in command: {order_data}")
        command_logger.info(f"[CONFIRM_ORDER_DATA_FOUND_IN_COMMAND] {order_data}")

    # 2. НЕ отправляем сообщение пользователю - AI уже отправил
    # order_summary = command.get('order_summary', 'Отлично! Ваш заказ подтвержден и передан в обработку.')
    # await whatsapp_utils.send_whatsapp_message(phone_number, order_summary, session_id)
    
    # 3. Отправить уведомление в LINE
    order_data["session_id"] = session_id  # Добавляем session_id для логирования и ссылки
    
    command_logger.info(f"[CONFIRM_ORDER_SENDING_TO_LINE] Final order data: {order_data}")
    
    # Запускаем сохранение завершенного диалога с переводами в фоне
    from .chat_translation_manager import save_completed_chat_with_translations
    asyncio.create_task(save_completed_chat_with_translations(sender_id, session_id))
    command_logger.info(f"[CONFIRM_ORDER_TRANSLATION_STARTED] Started background translation for session: {session_id}")
    
    # Отправляем заказ в Line с многоязычной историей
    line_result = await order_utils.send_order_to_line(sender_id, session_id, order_data)
    command_logger.info(f"[CONFIRM_ORDER_LINE_RESULT] LINE result: {line_result}")

    # Проверяем успешность отправки в LINE перед уведомлением пользователя
    if line_result == "ok":
        # Уведомить пользователя, что заказ отправлен и менеджер свяжется для оплаты
        await order_utils.notify_user_order_sent(sender_id, session_id)
        command_logger.info(f"[CONFIRM_ORDER_USER_NOTIFIED] User notification sent")
    else:
        command_logger.error(f"[CONFIRM_ORDER_LINE_FAILED] Failed to send to LINE: {line_result}")
        # Не отправляем уведомление пользователю, если LINE не работает
    
    # 4. Создать новую сессию после подтверждения заказа
    from . import session_manager
    new_session_id = session_manager.create_new_session_after_order(sender_id)
    
    command_logger.info(f"[CONFIRM_ORDER_NEW_SESSION] Created new session after order: {new_session_id}")
    
    result = {"status": "success", "action": "order_confirmed", "data": order_data, "new_session_id": new_session_id}
    command_logger.info(f"[CONFIRM_ORDER_RESULT] {result}")
    
    return result

async def handle_clarify_request(sender_id: str, session_id: str, command: dict):
    """Обрабатывает команду уточнения запроса"""
    command_logger.info(f"[CLARIFY_START] Sender: {sender_id}, Session: {session_id}")
    command_logger.info(f"[CLARIFY_COMMAND] Command details: {command}")
    
    logger.info(f"Executing 'clarify_request' command for sender {sender_id}, session {session_id}")
    
    # Команда не требует дополнительных действий, только логирование
    result = {"status": "success", "action": "request_clarified"}
    command_logger.info(f"[CLARIFY_RESULT] {result}")
    
    return result

async def handle_user_message(sender_id: str, session_id: str, message: dict):
    """Обрабатывает входящее сообщение пользователя, включая reply на букет"""
    log_with_context("[USER_MESSAGE_START] ==================== USER MESSAGE PROCESSING ====================")
    log_with_context(f"[USER_MESSAGE_INPUT] Sender: {sender_id}, Session: {session_id}, Message: {message}")
    command_logger.info(f"[USER_MESSAGE_START] Sender: {sender_id}, Session: {session_id}")
    command_logger.info(f"[USER_MESSAGE_DATA] Message: {message}")
    
    # Если есть reply_to_message_id и он относится к сообщению с букетом — это выбор букета
    reply_to = message.get('reply_to_message_id')
    if reply_to:
        log_with_context(f"[USER_MESSAGE_REPLY] Found reply_to: {reply_to}")
        command_logger.info(f"[USER_MESSAGE_REPLY] Found reply_to: {reply_to}")
        
        # Получаем сообщение по WA ID
        from . import database
        replied_message = database.get_message_by_wa_id(sender_id, session_id, reply_to)
        
        if replied_message and replied_message.get('role') == 'model':
            content = replied_message.get('content', '')
            if '🌸' in content:  # Это сообщение с букетом
                bouquet_name = content.split('\n')[0]
                log_with_context(f"[USER_MESSAGE_BOUQUET_SELECTED] Bouquet: {bouquet_name}")
                command_logger.info(f"[USER_MESSAGE_BOUQUET_SELECTED] Bouquet: {bouquet_name}")
                return await handle_bouquet_selection(sender_id, session_id, bouquet_name)
    
    log_with_context("[USER_MESSAGE_END] ==================== USER MESSAGE PROCESSING END ====================")
    # ... остальная логика ... 

def extract_bouquet_name_or_id_from_caption(caption: str, products=None):
    """Извлекает название или ID букета из подписи к картинке WhatsApp. Ищет по всем строкам, сверяет с каталогом."""
    # 🔍 ЛОГИРОВАНИЕ ИЗВЛЕЧЕНИЯ БУКЕТА
    command_logger.info(f"[BOUQUET_EXTRACT_START] Caption: {caption}")
    command_logger.info(f"[BOUQUET_EXTRACT_PRODUCTS] Products count: {len(products) if products else 0}")
    
    def clean_text(text):
        # Удаляем эмодзи, пробелы, приводим к нижнему регистру
        text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+', '', text)
        text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C')
        return text.replace(' ', '').lower()
    
    lines = [l.strip() for l in caption.split('\n') if l.strip()]
    bouquet_id = None
    bouquet_name = None
    
    logger.info(f"[REPLY_DEBUG] Extracting from caption: {caption}")
    logger.info(f"[REPLY_DEBUG] Lines: {lines}")
    
    command_logger.info(f"[BOUQUET_EXTRACT_LINES] {lines}")
    
    # 1. Ищем ID по всем строкам (если есть)
    for line in lines:
        id_match = re.search(r'ID[:\s]*([a-zA-Z0-9]+)', line)
        if id_match:
            bouquet_id = id_match.group(1)
            logger.info(f"[REPLY_DEBUG] Found ID in line: {bouquet_id}")
            command_logger.info(f"[BOUQUET_EXTRACT_ID_FOUND] ID: {bouquet_id} in line: {line}")
            break
    
    # 2. Если есть каталог — ищем совпадение по имени (гибко)
    if products:
        for line in lines:
            clean_line = clean_text(line)
            logger.info(f"[REPLY_DEBUG] Checking line: '{line}' -> clean: '{clean_line}'")
            command_logger.info(f"[BOUQUET_EXTRACT_CHECKING] Line: '{line}' -> clean: '{clean_line}'")
            for p in products:
                pname = p.get('name', '').replace('🌸', '').strip()
                if clean_line == clean_text(pname):
                    bouquet_name = p.get('name')
                    bouquet_id = p.get('retailer_id')
                    command_logger.info(f"[BOUQUET_EXTRACT_MATCH] Found match: {bouquet_name}, ID: {bouquet_id}")
                    return bouquet_name, bouquet_id
    
    # 3. Если не нашли — пробуем первую строку (как fallback)
    if not bouquet_name and lines:
        name_clean = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+', '', lines[0]).strip()
        bouquet_name = name_clean
        command_logger.info(f"[BOUQUET_EXTRACT_FALLBACK] Using first line: {bouquet_name}")
    
    result = (bouquet_name, bouquet_id)
    command_logger.info(f"[BOUQUET_EXTRACT_RESULT] {result}")
    
    return result

async def handle_bouquet_selection(sender_id: str, session_id: str, bouquet_caption: str):
    """Обрабатывает выбор букета через reply (по подписи к картинке)."""
    log_with_context("[BOUQUET_SELECTION_START] ==================== BOUQUET SELECTION PROCESSING ====================")
    log_with_context(f"[BOUQUET_SELECTION_INPUT] Sender: {sender_id}, Session: {session_id}, Caption: {bouquet_caption}")
    logger.info(f"Handling bouquet selection via reply: {bouquet_caption} for sender {sender_id}, session {session_id}")
    
    from . import catalog_reader
    products = catalog_reader.get_catalog_products()
    log_with_context(f"[BOUQUET_SELECTION_CATALOG] Retrieved {len(products)} products from catalog")
    
    name, bouquet_id = extract_bouquet_name_or_id_from_caption(bouquet_caption, products)
    log_with_context(f"[BOUQUET_SELECTION_EXTRACTED] Name: {name}, ID: {bouquet_id}")
    
    validation = None
    if bouquet_id:
        log_with_context(f"[BOUQUET_SELECTION_VALIDATE_ID] Validating by ID: {bouquet_id}")
        validation = catalog_reader.validate_product_selection(bouquet_id)
        if validation['valid']:
            log_with_context(f"[BOUQUET_SELECTION_VALID_ID] Bouquet found by ID: {bouquet_id}")
            logger.info(f"Bouquet found by ID: {bouquet_id}")
    
    if not validation or not validation['valid']:
        log_with_context(f"[BOUQUET_SELECTION_VALIDATE_NAME] Validating by name: {name}")
        validation = catalog_reader.validate_product_by_name(name)
    
    if not validation['valid']:
        log_with_context(f"[BOUQUET_SELECTION_INVALID] Invalid selection: {bouquet_caption}", "warning")
        logger.warning(f"Invalid bouquet selection via reply: {bouquet_caption}")
        available_products = validation.get('available_products', [])
        product_names = available_products[:5]  # Первые 5 товаров
        return {
            "status": "error", 
            "action": "invalid_product",
            "message": f"Такого букета нет в каталоге. Вот что у нас есть: {', '.join(product_names)} 🌸",
            "available_products": product_names
        }
    
    product = validation['product']
    log_with_context(f"[BOUQUET_SELECTION_PRODUCT] Validated product: {product}")
    
    order_data = {
        'bouquet': product.get('name', name),
        'retailer_id': product.get('retailer_id'),
        'product_name': product.get('name', name),
        'product_price': product.get('price', 'Цена не указана')
    }
    log_with_context(f"[BOUQUET_SELECTION_ORDER_DATA] Order data: {order_data}")
    
    # Данные теперь сохраняются в parts AI-сообщения, не нужно отдельные system-сообщения
    
    phone_number = session_id.split('_')[0]
    log_with_context(f"[BOUQUET_SELECTION_PHONE] Extracted phone: {phone_number}")
    await whatsapp_utils.send_whatsapp_message(phone_number, \
        f"Отлично! Записал ваш выбор букета '{product.get('name', name)}'. Нужна ли доставка? Если да, то куда? 🌸", session_id)
    
    return {"status": "success", "action": "bouquet_selected"} 
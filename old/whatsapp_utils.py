"""
Утилиты для работы с WhatsApp Business API
"""

import logging
import httpx
import json
import inspect
from .config import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_CATALOG_ID
from . import catalog_reader

logger = logging.getLogger(__name__)

# Создаем специальный logger для WhatsApp
whatsapp_logger = logging.getLogger('whatsapp_utils')

# Создаем специальный logger для AI пайплайна
ai_pipeline_logger = logging.getLogger('ai_pipeline')

# Создаем специальный logger для whatsapp пайплайна
whatsapp_pipeline_logger = logging.getLogger('whatsapp_pipeline')

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
        whatsapp_logger.info(full_message)
    elif level == "error":
        whatsapp_logger.error(full_message)
    elif level == "warning":
        whatsapp_logger.warning(full_message)

async def handle_send_catalog(to_number: str, session_id: str = None):
    """Отправляет каталог товаров пользователю по одному товару (только в наличии, только по согласию)"""
    # 🔍 ЛОГИРОВАНИЕ ОТПРАВКИ КАТАЛОГА
    log_with_context(f"[CATALOG_SEND_START] To: {to_number}, Session: {session_id}", "info")
    
    try:
        catalog_products = catalog_reader.get_catalog_products()
        available_products = catalog_reader.filter_available_products(catalog_products)

        log_with_context(f"[CATALOG_SEND_PRODUCTS] Total products: {len(catalog_products)}, Available: {len(available_products)}", "info")

        if not available_products:
            log_with_context("[CATALOG_SEND_NO_PRODUCTS] No available products found", "warning")
            await send_whatsapp_message(to_number, "Извините, сейчас нет букетов в наличии. Попробуйте позже. 🌸", to_number, session_id)
            log_with_context(f"[CATALOG_LOG] Нет доступных букетов для session_id={session_id}", "info")
            return False

        # Отправляем только фото, название и цену каждого букета
        for idx, product in enumerate(available_products):
            name = product.get('name', 'Без названия')
            price = product.get('price', 'Цена не указана')
            image_url = product.get('image_url')
            caption = f"{name}\n{price} 🌸"
            
            log_with_context(f"[CATALOG_SEND_ITEM] {idx+1}/{len(available_products)} - Name: {name}, Price: {price}, URL: {image_url}", "info")
            
            log_with_context(f"[CATALOG_LOG] Отправляю букет: session_id={session_id}, name={name}, price={price}, image_url={image_url}", "info")
            await send_whatsapp_image_with_caption(to_number, image_url, caption, to_number, session_id)
            
        log_with_context(f"[CATALOG_SEND_SUCCESS] Sent {len(available_products)} products to {to_number}", "info")
        log_with_context(f"[CATALOG_LOG] Каталог отправлен пользователю {to_number} (session_id={session_id})", "info")
        return True
        
    except Exception as e:
        log_with_context(f"[CATALOG_SEND_ERROR] {e} | to_number={to_number}, session_id={session_id}", "error")
        whatsapp_logger.error(f"[CATALOG_SEND_ERROR] Error: {e}, To: {to_number}, Session: {session_id}")
        await send_whatsapp_message(to_number, "Произошла ошибка при отправке каталога. 🌸", to_number, session_id)
        return False

def add_flower_emoji(text: str) -> str:
    text = text.rstrip()
    if not text.endswith('🌸'):
        return text + ' 🌸'
    return text

async def send_whatsapp_message(to_number: str, message: str, sender_id: str = None, session_id: str = None):
    """Отправляет текстовое сообщение через WhatsApp и сохраняет message_id для reply"""
    # ЛОГИРОВАНИЕ ОТПРАВКИ СООБЩЕНИЯ
    log_with_context(f"[MESSAGE_SEND_START] To: {to_number}, Sender: {sender_id}, Session: {session_id}", "info")
    log_with_context(f"[MESSAGE_SEND_INPUT] Message: {message}", "info")
    
    def clean_message(text):
        # Сохраняем переносы строк для WhatsApp, но убираем лишние пробелы
        # Заменяем множественные пробелы на один, но сохраняем \n
        import re
        # Убираем множественные пробелы, но сохраняем переносы строк
        text = re.sub(r'[ \t]+', ' ', text)
        # Убираем пробелы в начале и конце строк
        text = re.sub(r'^[ \t]+', '', text, flags=re.MULTILINE)
        text = re.sub(r'[ \t]+$', '', text, flags=re.MULTILINE)
        # Убираем пустые строки в начале и конце
        text = text.strip()
        return text
    
    message = clean_message(message)
    
    log_with_context(f"[MESSAGE_SEND_CLEANED] Cleaned message: {message}", "info")
    log_with_context(f"[WHATSAPP_LOG] Sending message to {to_number}: '{message}' (sender_id={sender_id}, session_id={session_id})", "info")
    
    try:
        url = f"https://graph.facebook.com/v23.0/{WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": add_flower_emoji(message)
            }
        }
        
        log_with_context(f"[MESSAGE_SEND_API_REQUEST] URL: {url}", "info")
        log_with_context(f"[MESSAGE_SEND_API_PAYLOAD] {payload}", "info")
        
        log_with_context(f"[WHATSAPP_LOG] Request payload: {payload}", "info")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            log_with_context(f"[MESSAGE_SEND_API_RESPONSE_STATUS] {response.status_code}", "info")
            log_with_context(f"[MESSAGE_SEND_API_RESPONSE_BODY] {response.text}", "info")
            
            log_with_context(f"[WHATSAPP_LOG] Response status: {response.status_code}", "info")
            log_with_context(f"[WHATSAPP_LOG] Response body: {response.text}", "info")
            
            response.raise_for_status()
            
            # Если передан session_id, сохраняем message_id в базе данных
            if session_id and sender_id:
                try:
                    response_data = json.loads(response.text)
                    if 'messages' in response_data and len(response_data['messages']) > 0:
                        message_id = response_data['messages'][0]['id']
                        
                        log_with_context(f"[MESSAGE_SEND_SAVE_ID] Message ID: {message_id}", "info")
                        
                        from . import database
                        database.add_message_with_wa_id(sender_id, session_id, "model", message, message_id)
                        log_with_context(f"[REPLY_DEBUG] Saved text message with ID {message_id} for sender {sender_id}, session {session_id} | message={message}", "info")
                        
                        log_with_context(f"[MESSAGE_SEND_SAVED] Saved to database with ID: {message_id}", "info")
                        
                        # ЛОГИРОВАНИЕ AI RESPONSE SAVED
                        ai_pipeline_logger.info(f"[AI_RESPONSE_SAVED] Sender: {sender_id}, Session: {session_id} | Message ID: {message_id} | Text: {message}")
                        
                except Exception as e:
                    log_with_context(f"[REPLY_DEBUG] Failed to save message_id: {e} | sender_id={sender_id}, session_id={session_id} | message={message}", "error")
                    whatsapp_logger.error(f"[MESSAGE_SEND_SAVE_ERROR] Error saving to DB: {e}")
            
            log_with_context(f"[MESSAGE_SEND_SUCCESS] Message sent successfully", "info")
            log_with_context(f"Message sent successfully to {to_number} (sender_id={sender_id}, session_id={session_id})", "info")
            return True
            
    except Exception as e:
        log_with_context(f"Failed to send message to {to_number}: {e} | sender_id={sender_id}, session_id={session_id}", "error")
        whatsapp_logger.error(f"[MESSAGE_SEND_ERROR] Error: {e}, To: {to_number}, Sender: {sender_id}, Session: {session_id}")
        return False

async def send_whatsapp_image_with_caption(to_number: str, image_url: str, caption: str, sender_id: str = None, session_id: str = None):
    """Отправляет изображение с подписью через WhatsApp и сохраняет message_id для reply"""
    # ЛОГИРОВАНИЕ ОТПРАВКИ ИЗОБРАЖЕНИЯ
    log_with_context(f"[IMAGE_SEND_START] To: {to_number}, Sender: {sender_id}, Session: {session_id}", "info")
    log_with_context(f"[IMAGE_SEND_INPUT] Caption: {caption}, URL: {image_url}", "info")
    
    import re
    def clean_caption(text):
        text = re.sub(r"[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+", '', text)
        text = text.strip()
        if not text.endswith('🌸'):
            text += ' 🌸'
        return text
    caption = clean_caption(caption)
    
    log_with_context(f"[IMAGE_SEND_CLEANED] Cleaned caption: {caption}", "info")
    log_with_context(f"[WHATSAPP_LOG] Sending image with caption to {to_number}: '{caption}' (sender_id={sender_id}, session_id={session_id}, image_url={image_url})", "info")
    
    try:
        url = f"https://graph.facebook.com/v23.0/{WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": {
                "link": image_url,
                "caption": caption
            }
        }
        
        log_with_context(f"[IMAGE_SEND_API_REQUEST] URL: {url}", "info")
        log_with_context(f"[IMAGE_SEND_API_PAYLOAD] {payload}", "info")
        
        log_with_context(f"[WHATSAPP_LOG] Image request payload: {payload}", "info")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            log_with_context(f"[IMAGE_SEND_API_RESPONSE_STATUS] {response.status_code}", "info")
            log_with_context(f"[IMAGE_SEND_API_RESPONSE_BODY] {response.text}", "info")
            
            log_with_context(f"[WHATSAPP_LOG] Image response status: {response.status_code}", "info")
            log_with_context(f"[WHATSAPP_LOG] Image response body: {response.text}", "info")
            
            response.raise_for_status()
            
            # Если передан session_id, сохраняем message_id в базе данных
            if session_id and sender_id:
                try:
                    response_data = json.loads(response.text)
                    if 'messages' in response_data and len(response_data['messages']) > 0:
                        message_id = response_data['messages'][0]['id']
                        
                        log_with_context(f"[IMAGE_SEND_SAVE_ID] Message ID: {message_id}", "info")
                        
                        from . import database
                        database.add_message_with_wa_id(sender_id, session_id, "model", caption, message_id)
                        log_with_context(f"[REPLY_DEBUG] Saved bouquet message with ID {message_id} for sender {sender_id}, session {session_id} | caption={caption} | image_url={image_url}", "info")
                        
                        log_with_context(f"[IMAGE_SEND_SAVED] Saved to database with ID: {message_id}", "info")
                        
                        # ЛОГИРОВАНИЕ AI RESPONSE SAVED (IMAGE)
                        ai_pipeline_logger.info(f"[AI_RESPONSE_SAVED] Sender: {sender_id}, Session: {session_id} | Message ID: {message_id} | Caption: {caption}")
                        
                except Exception as e:
                    log_with_context(f"[REPLY_DEBUG] Failed to save message_id: {e} | sender_id={sender_id}, session_id={session_id} | caption={caption} | image_url={image_url}", "error")
                    whatsapp_logger.error(f"[IMAGE_SEND_SAVE_ERROR] Error saving to DB: {e}")
            
            log_with_context(f"[IMAGE_SEND_SUCCESS] Image sent successfully", "info")
            log_with_context(f"Image with caption sent successfully to {to_number} (sender_id={sender_id}, session_id={session_id})", "info")
            return True
            
    except Exception as e:
        log_with_context(f"Failed to send image with caption to {to_number}: {e} | sender_id={sender_id}, session_id={session_id} | caption={caption} | image_url={image_url}", "error")
        whatsapp_logger.error(f"[IMAGE_SEND_ERROR] Error: {e}, To: {to_number}, Sender: {sender_id}, Session: {session_id}")
        
        # Если не удалось отправить изображение, отправляем только текст
        try:
            log_with_context("[IMAGE_SEND_FALLBACK] Trying to send text only", "info")
            await send_whatsapp_message(to_number, caption, sender_id, session_id)
        except:
            log_with_context("[IMAGE_SEND_FALLBACK_ERROR] Text fallback also failed", "error")
            pass
        return False

async def mark_message_as_read(message_id: str):
    """Отмечает сообщение как прочитанное в WhatsApp Cloud API"""
    # 🔍 ЛОГИРОВАНИЕ MARK AS READ
    log_with_context(f"[MARK_READ_START] Message ID: {message_id}", "info")
    
    url = f"https://graph.facebook.com/v23.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    log_with_context(f"[MARK_READ_API_REQUEST] URL: {url}", "info")
    log_with_context(f"[MARK_READ_API_PAYLOAD] {payload}", "info")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            log_with_context(f"[MARK_READ_API_RESPONSE_STATUS] {response.status_code}", "info")
            log_with_context(f"[MARK_READ_API_RESPONSE_BODY] {response.text}", "info")
            
            log_with_context(f"[WHATSAPP_LOG] Mark as read response status: {response.status_code}", "info")
            log_with_context(f"[WHATSAPP_LOG] Mark as read response body: {response.text}", "info")
            response.raise_for_status()
            
            log_with_context("[MARK_READ_SUCCESS] Message marked as read", "info")
            return True
            
    except Exception as e:
        log_with_context(f"Failed to mark message as read: {e} | message_id={message_id}", "error")
        whatsapp_logger.error(f"[MARK_READ_ERROR] Error: {e}, Message ID: {message_id}")
        return False

async def send_typing_indicator(to_number: str, typing: bool = True):
    """Отправляет индикатор печатания в WhatsApp Cloud API"""
    # 🔍 ЛОГИРОВАНИЕ TYPING INDICATOR
    log_with_context(f"[TYPING_INDICATOR] To: {to_number}, Typing: {typing}", "info")
    
    # WhatsApp Cloud API не поддерживает typing indicator напрямую
    # Вместо этого можно отправить пустое сообщение или просто логировать
    if typing:
        log_with_context(f"[TYPING_LOG] User {to_number} would see typing indicator", "info")
    else:
        log_with_context(f"[TYPING_LOG] User {to_number} typing indicator stopped", "info")
    return True 
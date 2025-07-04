import logging
import httpx
from .config import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_CATALOG_ID
from . import catalog_reader

logger = logging.getLogger(__name__)

async def handle_send_catalog(to_number: str, sender_id: str = None, session_id: str = None):
    """Отправляет каталог товаров пользователю по одному товару (только в наличии, только по согласию)"""
    try:
        catalog_products = catalog_reader.get_catalog_products()
        available_products = catalog_reader.filter_available_products(catalog_products)

        if not available_products:
            from .whatsapp_utils import send_whatsapp_message
            await send_whatsapp_message(to_number, "Извините, сейчас нет букетов в наличии. Попробуйте позже. 🌸", sender_id, session_id)
            return False

        # Отправляем только фото, название и цену каждого букета
        for product in available_products:
            name = product.get('name', 'Без названия')
            price = product.get('price', 'Цена не указана')
            image_url = product.get('image_url')
            caption = f"{name}\n{price} 🌸"
            await send_whatsapp_image_with_caption(to_number, image_url, caption, sender_id, session_id)
        return True
    except Exception as e:
        logger.error(f"[CATALOG_SEND_ERROR] {e}")
        from .whatsapp_utils import send_whatsapp_message
        await send_whatsapp_message(to_number, "Произошла ошибка при отправке каталога. 🌸", sender_id, session_id)
        return False

async def send_whatsapp_image_with_caption(to_number: str, image_url: str, caption: str, sender_id: str = None, session_id: str = None):
    """Отправляет изображение с подписью через WhatsApp и сохраняет message_id для reply"""
    import re
    def clean_caption(text):
        text = re.sub(r"[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+", '', text)
        text = text.strip()
        if not text.endswith('🌸'):
            text += ' 🌸'
        return text
    caption = clean_caption(caption)
    logger.info(f"[WHATSAPP_LOG] Sending image with caption to {to_number}: '{caption}' (sender_id={sender_id}, session_id={session_id})")
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
        logger.info(f"[WHATSAPP_LOG] Image request payload: {payload}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"[WHATSAPP_LOG] Image response status: {response.status_code}")
            logger.info(f"[WHATSAPP_LOG] Image response body: {response.text}")
            response.raise_for_status()
            # Если передан session_id, сохраняем message_id в базе данных
            if session_id and sender_id:
                try:
                    import json
                    response_data = json.loads(response.text)
                    if 'messages' in response_data and len(response_data['messages']) > 0:
                        message_id = response_data['messages'][0]['id']
                        from . import database
                        database.add_message(sender_id, session_id, "model", caption, message_id=message_id)
                        logger.info(f"[REPLY_DEBUG] Saved bouquet message with ID {message_id} for sender {sender_id}, session {session_id}")
                except Exception as e:
                    logger.error(f"[REPLY_DEBUG] Failed to save message_id: {e}")
            logger.info(f"Image with caption sent successfully to {to_number}")
            return True
    except Exception as e:
        logger.error(f"Failed to send image with caption to {to_number}: {e}")
        # Если не удалось отправить изображение, отправляем только текст
        from .whatsapp_utils import send_whatsapp_message
        try:
            await send_whatsapp_message(to_number, caption, sender_id, session_id)
        except:
            pass
        return False 
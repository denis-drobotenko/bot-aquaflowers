"""
Отправка каталога товаров через WhatsApp Business API
"""

import httpx
from typing import Optional
from src.config.settings import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_CATALOG_ID
from src.services.catalog_service import CatalogService
from src.utils.whatsapp_client import WhatsAppClient
from src.services.message_service import MessageService
from src.models.message import Message, MessageRole
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CatalogSender:
    """Класс для подготовки каталога товаров для отправки через WhatsApp"""
    def __init__(self):
        self.catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        self.whatsapp_client = WhatsAppClient()
        self.message_service = MessageService()

    async def get_catalog_messages(self, to_number: str, sender_id: str = None, session_id: str = None):
        """
        Возвращает список структур сообщений для отправки каталога товаров.
        Каждый элемент — dict с type, image_url, caption.
        """
        print(f"[CATALOG_SEND] Формирование каталога для пользователя {to_number}")
        try:
            catalog_products = self.catalog_service.get_available_products()
            if not catalog_products:
                return [{
                    "type": "text",
                    "content": "Извините, сейчас нет букетов в наличии. Попробуйте позже."
                }]
            messages = []
            for product in catalog_products:
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                image_url = product.get('image_url')
                caption = f"{name}\n{price}"
                messages.append({
                    "type": "image",
                    "image_url": image_url,
                    "caption": caption
                })
            return messages
        except Exception as e:
            print(f"[CATALOG_SEND_ERROR] {e}")
            return [{
                "type": "text",
                "content": "Произошла ошибка при отправке каталога. Попробуйте позже."
            }]

    async def send_catalog(self, to_number: str, session_id: str = None) -> bool:
        """Отправляет каталог товаров пользователю по одному товару (только в наличии)"""
        try:
            # Логируем параметры каталога
            logger.info(f"[CATALOG_SEND] WHATSAPP_CATALOG_ID: {WHATSAPP_CATALOG_ID}")
            logger.info(f"[CATALOG_SEND] WHATSAPP_TOKEN: {WHATSAPP_TOKEN[:8]}... (скрыт)")
            
            # Получаем только доступные товары
            available_products = self.catalog_service.get_available_products()
            logger.info(f"[CATALOG_SEND] Найдено {len(available_products)} доступных товаров (всего: {len(self.catalog_service.get_products())})")

            if not available_products:
                # Отправляем сообщение об отсутствии товаров
                message_id = await self.whatsapp_client.send_text_message(
                    to_number, 
                    "Извините, сейчас нет букетов в наличии. Попробуйте позже. 🌸",
                    session_id
                )
                
                # Сохраняем в БД
                if message_id and session_id:
                    message = Message(
                        sender_id=to_number,
                        session_id=session_id,
                        role=MessageRole.ASSISTANT,
                        content="Извините, сейчас нет букетов в наличии. Попробуйте позже. 🌸",
                        content_en="Sorry, there are no bouquets available now. Please try later. 🌸",
                        content_thai="ขออภัย ตอนนี้ไม่มีช่อดอกไม้ในสต็อก กรุณาลองใหม่ภายหลัง 🌸",
                        wa_message_id=message_id,
                        image_url=None,
                        timestamp=datetime.now()
                    )
                    await self.message_service.add_message_to_conversation(message)
                
                return False

            # Отправляем только фото, название и цену каждого букета
            for product in available_products:
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                image_url = product.get('image_url')
                caption = f"{name}\n{price} 🌸"
                
                logger.info(f"[CATALOG_SEND] Отправляю товар: {name} - {price}")
                
                if image_url:
                    message_id = await self.whatsapp_client.send_image_with_caption(
                        to_number, 
                        image_url, 
                        caption,
                        session_id
                    )
                else:
                    # Если нет изображения, отправляем только текст
                    message_id = await self.whatsapp_client.send_text_message(
                        to_number, 
                        caption,
                        session_id
                    )
                
                # Сохраняем в БД
                if message_id and session_id:
                    message = Message(
                        sender_id=to_number,
                        session_id=session_id,
                        role=MessageRole.ASSISTANT,
                        content=caption,
                        content_en=caption,
                        content_thai=caption,
                        wa_message_id=message_id,
                        image_url=image_url,
                        timestamp=datetime.now()
                    )
                    await self.message_service.add_message_to_conversation(message)
            
            logger.info(f"[CATALOG_SEND] Каталог успешно отправлен пользователю {to_number}")
            return True
            
        except Exception as e:
            logger.error(f"[CATALOG_SEND_ERROR] Ошибка отправки каталога: {e}")
            
            # Отправляем сообщение об ошибке
            message_id = await self.whatsapp_client.send_text_message(
                to_number, 
                "Произошла ошибка при отправке каталога. 🌸",
                session_id
            )
            
            # Сохраняем в БД
            if message_id and session_id:
                message = Message(
                    sender_id=to_number,
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content="Произошла ошибка при отправке каталога. 🌸",
                    content_en="An error occurred while sending the catalog. 🌸",
                    content_thai="เกิดข้อผิดพลาดในการส่งแคตตาล็อก 🌸",
                    wa_message_id=message_id,
                    image_url=None,
                    timestamp=datetime.now()
                )
                await self.message_service.add_message_to_conversation(message)
            
            return False

# Создаем глобальный экземпляр
catalog_sender = CatalogSender()

# Функция для обратной совместимости
async def handle_send_catalog(to_number: str, sender_id: str = None, session_id: str = None) -> bool:
    """Функция-обертка для обратной совместимости"""
    return await catalog_sender.send_catalog(to_number, session_id) 
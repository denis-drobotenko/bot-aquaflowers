"""
Клиент для WhatsApp Business API
"""

import httpx
import json
from src.utils.logging_utils import ContextLogger
from src.config import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID
from typing import Optional, Dict, Any

class WhatsAppClient:
    def __init__(self):
        self.token = WHATSAPP_TOKEN
        self.phone_id = WHATSAPP_PHONE_ID
        self.logger = ContextLogger("whatsapp_client")
        self.base_url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"

    def _get_headers(self) -> Dict[str, str]:
        """Получает заголовки для запросов"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _add_flower_emoji(self, text: str) -> str:
        """Добавляет эмодзи цветка к тексту"""
        text = text.rstrip()
        if not text.endswith('🌸'):
            return text + ' 🌸'
        return text

    async def send_text_message(self, to_number: str, message: str) -> Optional[str]:
        """Отправляет текстовое сообщение"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": self._add_flower_emoji(message)
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, 
                    headers=self._get_headers(), 
                    json=payload
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'messages' in response_data and len(response_data['messages']) > 0:
                    message_id = response_data['messages'][0]['id']
                    self.logger.info(f"Message sent successfully to {to_number}, ID: {message_id}")
                    return message_id
                
                return None

        except Exception as e:
            self.logger.error(f"Error sending message to {to_number}: {e}")
            return None

    async def send_image_with_caption(self, to_number: str, image_url: str, caption: str) -> Optional[str]:
        """Отправляет изображение с подписью"""
        try:
            # Очищаем подпись от эмодзи
            import re
            caption = re.sub(r"[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+", '', caption)
            caption = caption.strip()
            if not caption.endswith('🌸'):
                caption += ' 🌸'

            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "image",
                "image": {
                    "link": image_url,
                    "caption": caption
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, 
                    headers=self._get_headers(), 
                    json=payload
                )
                response.raise_for_status()
                
                response_data = response.json()
                if 'messages' in response_data and len(response_data['messages']) > 0:
                    message_id = response_data['messages'][0]['id']
                    self.logger.info(f"Image sent successfully to {to_number}, ID: {message_id}")
                    return message_id
                
                return None

        except Exception as e:
            self.logger.error(f"Error sending image to {to_number}: {e}")
            return None

    async def send_typing_indicator(self, to_number: str, typing: bool = True) -> bool:
        """Отправляет индикатор печати"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "reaction",
                "reaction": {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "type": "typing" if typing else "read"
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url, 
                    headers=self._get_headers(), 
                    json=payload
                )
                response.raise_for_status()
                return True

        except Exception as e:
            self.logger.error(f"Error sending typing indicator to {to_number}: {e}")
            return False 
"""
Клиент для WhatsApp Business API
"""

import httpx
import json
from typing import Optional, Dict, Any
from src.config.settings import WHATSAPP_TOKEN, WHATSAPP_PHONE_ID

class WhatsAppClient:
    def __init__(self):
        self.token = WHATSAPP_TOKEN
        self.phone_id = WHATSAPP_PHONE_ID
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
        if not text:
            return '🌸'
        if not text.endswith('🌸'):
            return text + ' 🌸'
        return text

    def _fix_newlines_for_whatsapp(self, text: str) -> str:
        """
        Преобразует \\n в реальные переносы строк для WhatsApp API
        """
        if not text:
            return text
        # Заменяем \\n на реальные переносы строк
        return text.replace('\\n', '\n')

    async def send_text_message(self, to_number: str, text: str, session_id: str = None) -> Optional[str]:
        """
        Отправляет текстовое сообщение.
        
        Returns:
            str: message_id (wamid) если успешно, None если ошибка
        """
        # Исправляем переносы строк для WhatsApp
        fixed_text = self._fix_newlines_for_whatsapp(text)
        print(f"[WHATSAPP] Отправка текста: {fixed_text[:50]}... (session_id={session_id})")
        
        try:
            url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"
            headers = self._get_headers()
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": fixed_text}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                print(f"[WHATSAPP] Статус ответа: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    if 'messages' in response_data and len(response_data['messages']) > 0:
                        message_id = response_data['messages'][0]['id']
                        print(f"[WHATSAPP] Сообщение отправлено, ID: {message_id}")
                        return message_id
                    else:
                        print(f"[WHATSAPP] Неожиданный формат ответа: {response_data}")
                        return None
                else:
                    print(f"[WHATSAPP] Ошибка отправки: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"[WHATSAPP] Исключение при отправке: {e}")
            return None

    async def send_message(self, to_number: str, text: str, session_id: str = None) -> Optional[str]:
        """Алиас для send_text_message для совместимости"""
        return await self.send_text_message(to_number, text, session_id)

    async def send_image_with_caption(self, to_number: str, image_url: str, caption: str, session_id: str = None) -> Optional[str]:
        """Отправляет изображение с подписью"""
        try:
            # Очищаем подпись от эмодзи
            import re
            caption = re.sub(r"[\U00010000-\U0010ffff\u2600-\u26FF\u2700-\u27BF]+", '', caption)
            caption = caption.strip()
            if not caption.endswith('🌸'):
                caption += ' 🌸'
            
            # Исправляем переносы строк для WhatsApp
            fixed_caption = self._fix_newlines_for_whatsapp(caption)

            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "image",
                "image": {
                    "link": image_url,
                    "caption": fixed_caption
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
                    print(f"Image sent successfully to {to_number}, ID: {message_id} (session_id={session_id})")
                    return message_id
                
                return None

        except Exception as e:
            print(f"Error sending image to {to_number}: {e}")
            return None

    async def send_typing_indicator(self, message_id: str) -> bool:
        """
        Отправляет индикатор "печатает" и отмечает сообщение как прочитанное.
        
        Согласно документации WhatsApp Business API, индикатор печати отправляется
        вместе с отметкой сообщения как прочитанного. Индикатор автоматически
        исчезает через 25 секунд или при отправке ответа.
        
        Args:
            message_id: ID сообщения для отметки как прочитанное
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"
            headers = self._get_headers()
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
                "typing_indicator": {
                    "type": "text"
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                # print(f"[WHATSAPP_TYPING] Статус: {response.status_code}")
                
                if response.status_code == 200:
                    # print(f"[WHATSAPP_TYPING] Индикатор печати отправлен для сообщения {message_id}")
                    return True
                else:
                    # print(f"[WHATSAPP_TYPING] Ошибка: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            # print(f"[WHATSAPP_TYPING] Исключение: {e}")
            return False

    async def mark_message_as_read(self, message_id: str) -> bool:
        """
        Отмечает сообщение как прочитанное (синие галочки).
        
        Args:
            message_id: ID сообщения для отметки как прочитанное
            
        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"
            headers = self._get_headers()
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                # print(f"[WHATSAPP_READ] Статус: {response.status_code}")
                
                if response.status_code == 200:
                    # print(f"[WHATSAPP_READ] Сообщение {message_id} отмечено как прочитанное")
                    return True
                else:
                    # print(f"[WHATSAPP_READ] Ошибка: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            # print(f"[WHATSAPP_READ] Исключение: {e}")
            return False 
"""
Сервис для работы с WhatsApp Media API
"""

import os
import aiohttp
import logging
from typing import Optional, Dict, Any
from google.cloud import storage
import uuid
from datetime import datetime

class WhatsAppMediaService:
    """Сервис для работы с медиафайлами WhatsApp"""
    
    def __init__(self):
        self.whatsapp_token = os.getenv("WHATSAPP_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_ID")
        self.base_url = "https://graph.facebook.com/v23.0"
        
        # Инициализация Google Cloud Storage
        self.storage_client = storage.Client()
        self.bucket_name = "aquaflowers-bot-audio"
        
    async def download_audio_file(self, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Скачивает аудиофайл из WhatsApp Media API
        
        Args:
            media_id: ID медиафайла из webhook'а
            
        Returns:
            dict: Информация о скачанном файле или None при ошибке
        """
        try:
            # 1. Получаем информацию о медиафайле
            media_info = await self._get_media_info(media_id)
            if not media_info:
                logging.error(f"Не удалось получить информацию о медиафайле {media_id}")
                return None
            
            # 2. Скачиваем файл
            audio_content = await self._download_media_content(media_info['url'])
            if not audio_content:
                logging.error(f"Не удалось скачать аудиофайл {media_id}")
                return None
            
            # 3. Сохраняем в Google Cloud Storage
            gcs_url = await self._upload_to_gcs(audio_content, media_id, media_info.get('mime_type', 'audio/ogg'))
            if not gcs_url:
                logging.error(f"Не удалось загрузить аудиофайл в GCS {media_id}")
                return None
            
            return {
                "gcs_url": gcs_url,
                "media_id": media_id,
                "mime_type": media_info.get('mime_type', 'audio/ogg'),
                "file_size": len(audio_content)
            }
            
        except Exception as e:
            logging.error(f"Ошибка при скачивании аудиофайла {media_id}: {e}")
            return None
    
    async def _get_media_info(self, media_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о медиафайле из WhatsApp API"""
        try:
            url = f"{self.base_url}/{media_id}"
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "url": data.get('url'),
                            "mime_type": data.get('mime_type'),
                            "sha256": data.get('sha256'),
                            "file_size": data.get('file_size')
                        }
                    else:
                        logging.error(f"Ошибка получения информации о медиафайле: {response.status}")
                        return None
                        
        except Exception as e:
            logging.error(f"Ошибка при получении информации о медиафайле: {e}")
            return None
    
    async def _download_media_content(self, media_url: str) -> Optional[bytes]:
        """Скачивает содержимое медиафайла"""
        try:
            headers = {
                "Authorization": f"Bearer {self.whatsapp_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(media_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logging.error(f"Ошибка скачивания медиафайла: {response.status}")
                        return None
                        
        except Exception as e:
            logging.error(f"Ошибка при скачивании медиафайла: {e}")
            return None
    
    async def _upload_to_gcs(self, content: bytes, media_id: str, mime_type: str) -> Optional[str]:
        """Загружает файл в Google Cloud Storage"""
        try:
            # Получаем или создаем бакет
            bucket = self.storage_client.bucket(self.bucket_name)
            if not bucket.exists():
                bucket = self.storage_client.create_bucket(self.bucket_name, location="us-central1")
            
            # Определяем расширение файла
            extension = self._get_extension_from_mime_type(mime_type)
            filename = f"whatsapp_audio_{media_id}_{uuid.uuid4().hex[:8]}{extension}"
            
            # Создаем blob и загружаем файл
            blob = bucket.blob(filename)
            blob.upload_from_string(content, content_type=mime_type)
            
            # Делаем файл публичным
            blob.make_public()
            
            logging.info(f"Аудиофайл загружен в GCS: {blob.public_url}")
            return blob.public_url
            
        except Exception as e:
            logging.error(f"Ошибка при загрузке в GCS: {e}")
            return None
    
    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        """Определяет расширение файла по MIME-типу"""
        mime_to_ext = {
            "audio/ogg": ".ogg",
            "audio/ogg; codecs=opus": ".ogg",
            "audio/mp4": ".mp4",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
            "audio/webm": ".webm"
        }
        return mime_to_ext.get(mime_type, ".ogg") 
"""
Сервис для транскрипции аудиосообщений через Google Speech-to-Text API
"""

import os
import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from google.cloud import speech
from google.cloud.speech import RecognitionAudio, RecognitionConfig
from google.cloud import storage
import tempfile
import requests
import uuid

class AudioTranscriptionService:
    """Сервис для транскрипции аудиосообщений"""
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SPEECH_TO_TEXT_API_KEY')
        if not self.api_key:
            logging.warning("GOOGLE_SPEECH_TO_TEXT_API_KEY не установлен")
        
        # Инициализируем Google Speech-to-Text клиент
        try:
            self.speech_client = speech.SpeechClient()
        except Exception as e:
            logging.error(f"Ошибка инициализации Google Speech-to-Text: {e}")
            self.speech_client = None
        
        # Инициализируем Google Cloud Storage клиент
        try:
            self.storage_client = storage.Client()
            self.bucket_name = os.getenv('AUDIO_BUCKET_NAME', 'aquaf-audio-files')
            self.bucket = self.storage_client.bucket(self.bucket_name)
        except Exception as e:
            logging.error(f"Ошибка инициализации Google Cloud Storage: {e}")
            self.storage_client = None
            self.bucket = None
    
    async def save_audio_to_gcs(self, audio_content: bytes, ext: str = 'ogg') -> str:
        """
        Сохраняет аудиофайл в Google Cloud Storage и возвращает публичный URL
        """
        try:
            if not self.bucket:
                logging.error("Google Cloud Storage не инициализирован")
                return None
            
            filename = f"audio_{uuid.uuid4().hex}.{ext}"
            blob = self.bucket.blob(f"whatsapp_audio/{filename}")
            
            # Загружаем файл в GCS
            blob.upload_from_string(audio_content, content_type='audio/ogg')
            
            # Делаем файл публично доступным
            blob.make_public()
            
            # Возвращаем публичный URL
            return blob.public_url
            
        except Exception as e:
            logging.error(f"Ошибка сохранения аудио в GCS: {e}")
            return None

    async def transcribe_audio_from_url(self, audio_url: str, language_code: str = 'ru-RU') -> Optional[dict]:
        """
        Транскрибирует аудио из URL через Google Speech-to-Text API и сохраняет файл в GCS
        
        Returns:
            dict: {'transcription': str, 'gcs_url': str}
        """
        try:
            if not self.speech_client:
                logging.error("Google Speech-to-Text клиент не инициализирован")
                return None
            
            # Скачиваем аудиофайл
            audio_content = await self._download_audio(audio_url)
            if not audio_content:
                logging.error(f"Не удалось скачать аудио из {audio_url}")
                return None
            
            # Сохраняем аудиофайл в Google Cloud Storage
            gcs_url = await self.save_audio_to_gcs(audio_content)
            if not gcs_url:
                logging.error("Не удалось сохранить аудио в GCS")
                return None
            
            # Транскрибируем аудио
            transcription = await self._transcribe_audio_content(audio_content, language_code)
            
            if transcription:
                logging.info(f"Успешная транскрипция аудио: {transcription[:50]}...")
            else:
                logging.warning("Транскрипция не дала результатов")
            
            return {"transcription": transcription, "gcs_url": gcs_url}
            
        except Exception as e:
            logging.error(f"Ошибка транскрипции аудио: {e}")
            return None
    
    async def _download_audio(self, audio_url: str) -> Optional[bytes]:
        """Скачивает аудиофайл из URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logging.error(f"Ошибка скачивания аудио: HTTP {response.status}")
                        return None
        except Exception as e:
            logging.error(f"Ошибка скачивания аудио: {e}")
            return None
    
    async def _transcribe_audio_content(self, audio_content: bytes, language_code: str) -> Optional[str]:
        """Транскрибирует аудиоконтент через Google Speech-to-Text"""
        try:
            if not self.speech_client:
                logging.error("Google Speech-to-Text клиент не инициализирован")
                return None
            
            # Создаем конфигурацию для распознавания
            config = RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                sample_rate_hertz=16000,  # WhatsApp использует 16kHz
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=False,
                enable_word_confidence=False,
                model="latest_long"  # Для длинных аудиосообщений
            )
            
            # Создаем объект аудио
            audio = RecognitionAudio(content=audio_content)
            
            # Выполняем распознавание
            response = self.speech_client.recognize(config=config, audio=audio)
            
            # Извлекаем результат
            if response.results:
                transcript = ""
                for result in response.results:
                    if result.alternatives:
                        transcript += result.alternatives[0].transcript + " "
                
                return transcript.strip()
            else:
                logging.warning("Google Speech-to-Text не вернул результатов")
                return None
                
        except Exception as e:
            logging.error(f"Ошибка транскрипции через Google Speech-to-Text: {e}")
            return None
    
    def detect_language_from_text(self, text: str) -> str:
        """
        Определяет язык текста для выбора правильного кода языка
        Возвращает код языка для Google Speech-to-Text
        """
        if not text:
            return 'ru-RU'  # По умолчанию русский
        
        # Простые эвристики для определения языка
        text_lower = text.lower()
        
        # Русский язык
        russian_chars = [c for c in text_lower if 'а' <= c <= 'я' or c == 'ё']
        if len(russian_chars) > len(text) * 0.3:
            return 'ru-RU'
        
        # Тайский язык
        thai_chars = [c for c in text if '\u0E00' <= c <= '\u0E7F']
        if len(thai_chars) > len(text) * 0.3:
            return 'th-TH'
        
        # Английский язык
        return 'en-US'
    
    async def transcribe_whatsapp_audio(self, audio_url: str, context_text: str = "") -> Optional[dict]:
        """
        Специализированный метод для транскрипции WhatsApp аудиосообщений и сохранения файла
        
        Returns:
            dict: {'transcription': str, 'local_url': str}
        """
        try:
            # Определяем язык на основе контекста
            language_code = self.detect_language_from_text(context_text)
            logging.info(f"Определен язык для транскрипции: {language_code}")
            
            # Транскрибируем аудио и сохраняем файл
            result = await self.transcribe_audio_from_url(audio_url, language_code)
            return result
        except Exception as e:
            logging.error(f"Ошибка транскрипции WhatsApp аудио: {e}")
            return None 
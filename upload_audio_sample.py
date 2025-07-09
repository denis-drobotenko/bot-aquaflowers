#!/usr/bin/env python3
import os
from google.cloud import storage

def upload_audio_file():
    """Загружает аудиофайл в Google Cloud Storage"""
    try:
        # Инициализация клиента
        storage_client = storage.Client()
        bucket_name = "aquaflowers-bot-audio"
        bucket = storage_client.bucket(bucket_name)
        
        # Путь к локальному файлу
        local_file = "sample_voice.mp3"
        blob_name = "voice_message_sample.mp3"
        
        # Проверяем, что файл существует
        if not os.path.exists(local_file):
            print(f"Файл {local_file} не найден!")
            return None
        
        # Создаем blob и загружаем файл
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file)
        
        # Делаем файл публичным
        blob.make_public()
        
        print(f"Файл загружен: {blob.public_url}")
        return blob.public_url
        
    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return None

if __name__ == "__main__":
    url = upload_audio_file()
    if url:
        print(f"URL для тестирования: {url}") 
#!/usr/bin/env python3
import os
from google.cloud import storage

def create_bucket_and_upload():
    """Загружает новый аудиофайл с речью"""
    try:
        storage_client = storage.Client()
        bucket_name = "aquaflowers-bot-audio"
        bucket = storage_client.bucket(bucket_name)
        
        local_file = "sample_voice.wav"
        blob_name = "voice_message_real_speech.wav"
        
        if not os.path.exists(local_file):
            print(f"Файл {local_file} не найден!")
            return None
        
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file)
        blob.make_public()
        print(f"Файл загружен: {blob.public_url}")
        return blob.public_url
    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return None

if __name__ == "__main__":
    url = create_bucket_and_upload()
    if url:
        print(f"URL для тестирования: {url}") 
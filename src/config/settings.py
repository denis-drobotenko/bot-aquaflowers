"""
Настройки приложения
"""

import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

# --- Основные настройки ---
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_DEVELOPMENT = ENVIRONMENT == 'development'
DEV_MODE = IS_DEVELOPMENT
DEBUG_MODE = IS_DEVELOPMENT  # Добавляем DEBUG_MODE

PORT = int(os.getenv('PORT', 8080))
SERVICE_URL = os.getenv('SERVICE_URL', "https://auraflora-bot-75152239022.asia-southeast1.run.app")
CHAT_BASE_URL = os.getenv('CHAT_BASE_URL', SERVICE_URL)
DEPLOY_ID = os.getenv('DEPLOY_ID', 'local_dev')

# --- Локальная разработка ---
LOCAL_DEV = os.getenv('LOCAL_DEV', 'false').lower() == 'true'
if LOCAL_DEV:
    IS_DEVELOPMENT = True
    DEV_MODE = True
    ENVIRONMENT = 'development'

# --- WhatsApp API ---
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')
WHATSAPP_PHONE_NUMBER_ID = WHATSAPP_PHONE_ID  # Алиас для совместимости
WHATSAPP_CATALOG_ID = os.getenv('WHATSAPP_CATALOG_ID')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

# --- AI API ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TRANSLATION_MODEL = os.getenv('TRANSLATION_MODEL', 'gemini-2.0-flash-exp')

# --- LINE API ---
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_GROUP_ID = os.getenv('LINE_GROUP_ID')
LINE_WEBHOOK_URL = os.getenv('LINE_WEBHOOK_URL')

# --- Google Cloud ---
PROJECT_ID = os.getenv('PROJECT_ID')
FIRESTORE_COLLECTION = os.getenv('FIRESTORE_COLLECTION', 'chat_sessions')

# --- Логирование ---
LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
LOG_FILE = os.getenv('LOG_FILE')

# --- Debug компоненты ---
ENABLE_DEBUG_INTERFACE = IS_DEVELOPMENT
ENABLE_DEBUG_LOGGING = IS_DEVELOPMENT
ENABLE_CORS = IS_DEVELOPMENT

# --- Транслитерация ---
TRANSLIT_TABLE = {
    'en_to_ru': {
        'a': 'а', 'b': 'б', 'c': 'к', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г', 'h': 'х', 
        'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л', 'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 
        'q': 'к', 'r': 'р', 's': 'с', 't': 'т', 'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс', 
        'y': 'и', 'z': 'з',
        'A': 'А', 'B': 'Б', 'C': 'К', 'D': 'Д', 'E': 'Е', 'F': 'Ф', 'G': 'Г', 'H': 'Х', 
        'I': 'И', 'J': 'Й', 'K': 'К', 'L': 'Л', 'M': 'М', 'N': 'Н', 'O': 'О', 'P': 'П', 
        'Q': 'К', 'R': 'Р', 'S': 'С', 'T': 'Т', 'U': 'У', 'V': 'В', 'W': 'В', 'X': 'КС', 
        'Y': 'И', 'Z': 'З',
    },
    'ru_to_en': {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 
        'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 
        'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 
        'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ы': 'y', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E', 'Ж': 'Zh', 
        'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N', 'О': 'O', 
        'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 
        'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch', 'Ы': 'Y', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
}

def detect_language(text: str) -> str:
    """
    Определяет язык текста: ru или en (по алфавиту).
    """
    import re
    if re.search(r'[\u0430-\u044f\u0410-\u042f\u0451\u0401]', text):
        return 'ru'
    if re.search(r'[a-zA-Z]', text):
        return 'en'
    return 'unknown'

def transliterate_name(name: str, to_lang: str) -> str:
    """
    Транслитерирует имя в нужный алфавит.
    """
    if to_lang == 'ru':
        return ''.join(TRANSLIT_TABLE['en_to_ru'].get(c, c) for c in name)
    if to_lang == 'en':
        return ''.join(TRANSLIT_TABLE['ru_to_en'].get(c, c) for c in name)
    return name 
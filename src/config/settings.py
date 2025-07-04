"""
Настройки приложения
"""

import os
from typing import Optional

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

# --- Основные настройки ---
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
IS_PRODUCTION = ENVIRONMENT == 'production'
IS_DEVELOPMENT = ENVIRONMENT == 'development'
DEV_MODE = IS_DEVELOPMENT

PORT = int(os.getenv('PORT', 8080))
SERVICE_URL = os.getenv('SERVICE_URL', "https://auraflora-bot-xicvc2y5hq-as.a.run.app")

# --- WhatsApp API ---
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', 'EAAZAVqMls3gQBOzAss3TUHsMQNFNbq6GccRd8Lwzemwe92T1aTB5j7ooT4sGw2wVZBknmDxICmPUKzx3kJ7MdnDFnEtYIabRJEqFZAtgy8lLLD7quNtxfGK7Ha3dBDcaDkxZAxNNu57CUSUhD20UCfstZAIZCyN4bsYBlzZAwEZCgs88dHLz5HHl1JYl8x422IY95AZDZD')
WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID', '494991623707876')
WHATSAPP_CATALOG_ID = os.getenv('WHATSAPP_CATALOG_ID', '742818811434193')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'my-super-secret-token')

# --- AI API ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCC4T7oOuWRNwNAsV9GDSCWZTg2rKoNS-4')

# --- Google Cloud ---
PROJECT_ID = os.getenv('PROJECT_ID', 'aquaf-464414')
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
    """Определяет язык текста: ru или en (по алфавиту)."""
    import re
    if re.search(r'[а-яА-ЯёЁ]', text):
        return 'ru'
    if re.search(r'[a-zA-Z]', text):
        return 'en'
    return 'unknown'

def transliterate_name(name: str, to_lang: str) -> str:
    """Транслитерирует имя в нужный алфавит."""
    if to_lang == 'ru':
        return ''.join(TRANSLIT_TABLE['en_to_ru'].get(c, c) for c in name)
    if to_lang == 'en':
        return ''.join(TRANSLIT_TABLE['ru_to_en'].get(c, c) for c in name)
    return name 
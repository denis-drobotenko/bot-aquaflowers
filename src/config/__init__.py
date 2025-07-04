"""
Конфигурация приложения
"""

from .settings import *

__all__ = [
    'ENVIRONMENT', 'IS_PRODUCTION', 'IS_DEVELOPMENT', 'DEV_MODE',
    'PORT', 'SERVICE_URL',
    'WHATSAPP_TOKEN', 'WHATSAPP_PHONE_ID', 'WHATSAPP_CATALOG_ID', 'VERIFY_TOKEN',
    'GEMINI_API_KEY',
    'PROJECT_ID', 'FIRESTORE_COLLECTION',
    'LOGGING_LEVEL', 'LOG_FILE',
    'ENABLE_DEBUG_INTERFACE', 'ENABLE_DEBUG_LOGGING', 'ENABLE_CORS',
    'detect_language', 'transliterate_name'
] 
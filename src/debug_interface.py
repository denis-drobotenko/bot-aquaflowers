"""
Веб-интерфейс для отладки диалогов AuraFlora
"""

import logging
from typing import Optional
from datetime import datetime
import re
from . import database

logger = logging.getLogger(__name__)



# Хранилище логов
LOG_STORAGE = []

class DebugLogHandler(logging.Handler):
    """Собирает логи для отладки"""
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger_name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self.extract_session_id(record.getMessage())
            }
            LOG_STORAGE.append(log_entry)
            
            # Ограничиваем размер
            if len(LOG_STORAGE) > 1000:
                LOG_STORAGE.pop(0)
                
        except Exception:
            pass
    
    def extract_session_id(self, message: str) -> Optional[str]:
        """Извлекает session_id из сообщения"""
        patterns = [
            r'Session: ([^,\s]+)',
            r'session_id[=:\s]+([^,\s]+)', 
            r'for session ([^,\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

def setup_debug_logging():
    """Настраивает сбор логов"""
    handler = DebugLogHandler()
    
    loggers = ['ai_pipeline', 'json_processor', 'command_handler', 'whatsapp_utils', 'webhook_flow']
    
    for logger_name in loggers:
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(handler)



# Инициализация
setup_debug_logging() 
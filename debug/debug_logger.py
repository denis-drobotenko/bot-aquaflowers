"""
Debug логирование для локальной разработки
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Хранилище логов в памяти (только для дебага)
debug_logs_storage: List[Dict[str, Any]] = []

class DebugLogHandler(logging.Handler):
    """Собирает логи для отладки (только локально)"""
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger_name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self.extract_session_id(record.getMessage())
            }
            debug_logs_storage.append(log_entry)
            
            # Ограничиваем размер
            if len(debug_logs_storage) > 1000:
                debug_logs_storage.pop(0)
                
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
    """Настраивает debug логирование (только локально)"""
    handler = DebugLogHandler()
    
    loggers = ['ai_pipeline', 'json_processor', 'command_handler', 'whatsapp_utils', 'webhook_flow']
    
    for logger_name in loggers:
        target_logger = logging.getLogger(logger_name)
        target_logger.addHandler(handler)
        target_logger.setLevel(logging.DEBUG)

def get_debug_logs() -> List[Dict[str, Any]]:
    """Возвращает все debug логи"""
    return debug_logs_storage.copy()

def clear_debug_logs():
    """Очищает debug логи"""
    debug_logs_storage.clear() 
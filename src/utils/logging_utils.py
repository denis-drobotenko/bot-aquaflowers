"""
Утилиты для логирования с контекстом
"""

import logging
import inspect
from typing import Optional


def get_caller_info() -> str:
    """
    Получает информацию о вызывающей функции и файле.
    
    Returns:
        str: Формат "filename:function:line"
    """
    try:
        frame = inspect.currentframe().f_back
        if frame is None:
            return "unknown:unknown:0"
        
        filename = frame.f_code.co_filename.split('/')[-1]  # Только имя файла
        function = frame.f_code.co_name
        line = frame.f_lineno
        return f"{filename}:{function}:{line}"
    except Exception:
        return "unknown:unknown:0"


def log_with_context(
    message: str, 
    level: str = "info", 
    logger_name: str = "default",
    include_caller: bool = True
) -> None:
    """
    Логирует сообщение с контекстом вызывающей функции.
    
    Args:
        message: Сообщение для логирования
        level: Уровень логирования (info, error, warning, debug)
        logger_name: Имя логгера
        include_caller: Включать ли информацию о вызывающей функции
    """
    logger = logging.getLogger(logger_name)
    
    if include_caller:
        caller = get_caller_info()
        full_message = f"[{caller}] {message}"
    else:
        full_message = message
    
    if level == "info":
        logger.info(full_message)
    elif level == "error":
        logger.error(full_message)
    elif level == "warning":
        logger.warning(full_message)
    elif level == "debug":
        logger.debug(full_message)
    else:
        logger.info(full_message)


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """
    Настраивает базовое логирование для приложения.
    
    Args:
        level: Уровень логирования
        format_string: Строка форматирования логов
        log_file: Путь к файлу для записи логов
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройка корневого логгера
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),  # Консоль
        ]
    )
    
    # Добавляем файловый хендлер если указан файл
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        logging.getLogger().addHandler(file_handler)
    
    # Настраиваем специальные логгеры
    loggers = [
        'webhook_flow',
        'ai_pipeline', 
        'database_pipeline',
        'session_pipeline',
        'command_pipeline',
        'whatsapp_pipeline'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))


class ContextLogger:
    """
    Логгер с автоматическим добавлением контекста.
    """
    
    def __init__(self, logger_name: str = "default"):
        self.logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
    
    def info(self, message: str, include_caller: bool = True) -> None:
        """Логирует информационное сообщение"""
        log_with_context(message, "info", self.logger_name, include_caller)
    
    def error(self, message: str, include_caller: bool = True) -> None:
        """Логирует сообщение об ошибке"""
        log_with_context(message, "error", self.logger_name, include_caller)
    
    def warning(self, message: str, include_caller: bool = True) -> None:
        """Логирует предупреждение"""
        log_with_context(message, "warning", self.logger_name, include_caller)
    
    def debug(self, message: str, include_caller: bool = True) -> None:
        """Логирует отладочное сообщение"""
        log_with_context(message, "debug", self.logger_name, include_caller) 
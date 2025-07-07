"""
Конфигурация логирования для системы
"""

import os
from typing import Dict, List, Any
from src.utils.logging_decorator import (
    enable_logging_for_module, 
    disable_logging_for_module,
    enable_logging_for_function,
    disable_logging_for_function,
    get_logging_config
)


class LoggingSettings:
    """Настройки логирования для разных окружений"""
    
    # Модули, которые логируются по умолчанию - только основные
    DEFAULT_ENABLED_MODULES = []
    
    # Модули, которые НЕ логируются по умолчанию
    DEFAULT_DISABLED_MODULES = [
        "test_",  # Все тестовые модули
        "debug_",  # Отладочные модули
        "utils",   # Утилиты
        "order_service",
        "command_service", 
        "message_service",
        "session_service",
        "user_service",
        "catalog_sender",
        "catalog_service"
    ]
    
    # Функции, которые логируются по умолчанию
    DEFAULT_ENABLED_FUNCTIONS = []
    
    # Функции, которые НЕ логируются по умолчанию
    DEFAULT_DISABLED_FUNCTIONS = [
        # Функции, которые могут быть слишком шумными
        "order_service.get_order_status",  # Частые проверки статуса
        "session_service.get_session",     # Частые обращения к сессии
    ]
    
    @classmethod
    def setup_default_logging(cls):
        """Настраивает логирование по умолчанию"""
        config = get_logging_config()
        
        # Включаем модули по умолчанию
        for module in cls.DEFAULT_ENABLED_MODULES:
            enable_logging_for_module(module)
        
        # Отключаем модули по умолчанию
        for module in cls.DEFAULT_DISABLED_MODULES:
            disable_logging_for_module(module)
        
        # Включаем функции по умолчанию
        for function in cls.DEFAULT_ENABLED_FUNCTIONS:
            enable_logging_for_function(function)
        
        # Отключаем функции по умолчанию
        for function in cls.DEFAULT_DISABLED_FUNCTIONS:
            disable_logging_for_function(function)
    
    @classmethod
    def setup_development_logging(cls):
        """Настройки для разработки - больше логов"""
        config = get_logging_config()
        
        # Очищаем все настройки
        config.enabled_modules.clear()
        config.disabled_modules.clear()
        config.enabled_functions.clear()
        config.disabled_functions.clear()
        
        # Включаем все модули (кроме тестовых)
        config.disabled_modules = ["test_"]
    
    @classmethod
    def setup_production_logging(cls):
        """Настройки для продакшена - только критические логи"""
        config = get_logging_config()
        
        # Очищаем все настройки
        config.enabled_modules.clear()
        config.disabled_modules.clear()
        config.enabled_functions.clear()
        config.disabled_functions.clear()
        
        # Включаем только критические модули
        critical_modules = [
            "ai_service",
            "message_processor"
        ]
        
        for module in critical_modules:
            enable_logging_for_module(module)
        
        # Включаем только критические функции
        critical_functions = [
            "ai_service.generate_response",
            "message_processor.process_user_message"
        ]
        
        for function in critical_functions:
            enable_logging_for_function(function)
    
    @classmethod
    def setup_debug_logging(cls):
        """Настройки для отладки - все логи"""
        config = get_logging_config()
        
        # Очищаем все настройки
        config.enabled_modules.clear()
        config.disabled_modules.clear()
        config.enabled_functions.clear()
        config.disabled_functions.clear()
        
        # Включаем все модули (кроме тестовых)
        config.disabled_modules = ["test_"]
    
    @classmethod
    def setup_custom_logging(cls, settings: Dict[str, Any]):
        """
        Настройка кастомного логирования
        
        Args:
            settings: Словарь с настройками
                {
                    "enabled_modules": ["module1", "module2"],
                    "disabled_modules": ["module3"],
                    "enabled_functions": ["module1.func1"],
                    "disabled_functions": ["module2.func2"]
                }
        """
        config = get_logging_config()
        
        # Очищаем текущие настройки
        config.enabled_modules.clear()
        config.disabled_modules.clear()
        config.enabled_functions.clear()
        config.disabled_functions.clear()
        
        # Применяем новые настройки
        if "enabled_modules" in settings:
            for module in settings["enabled_modules"]:
                enable_logging_for_module(module)
        
        if "disabled_modules" in settings:
            for module in settings["disabled_modules"]:
                disable_logging_for_module(module)
        
        if "enabled_functions" in settings:
            for function in settings["enabled_functions"]:
                enable_logging_for_function(function)
        
        if "disabled_functions" in settings:
            for function in settings["disabled_functions"]:
                disable_logging_for_function(function)


def setup_logging_by_environment():
    """Настраивает логирование в зависимости от окружения"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    # В Cloud Run логи идут в stdout/stderr, файлы не нужны
    if environment == "production":
        LoggingSettings.setup_production_logging()
    elif environment == "development":
        LoggingSettings.setup_development_logging()
    elif environment == "debug":
        LoggingSettings.setup_debug_logging()
    else:
        LoggingSettings.setup_default_logging()


# Примеры использования:

def example_usage():
    """Примеры использования системы логирования"""
    
    # Настройка по умолчанию
    LoggingSettings.setup_default_logging()
    
    # Настройка для разработки
    LoggingSettings.setup_development_logging()
    
    # Настройка для продакшена
    LoggingSettings.setup_production_logging()
    
    # Кастомная настройка
    custom_settings = {
        "enabled_modules": ["ai_service", "message_processor"],
        "disabled_modules": ["test_"],
        "enabled_functions": ["ai_service.generate_response"],
        "disabled_functions": ["order_service.get_order_status"]
    }
    LoggingSettings.setup_custom_logging(custom_settings)


if __name__ == "__main__":
    # Настраиваем логирование при запуске
    setup_logging_by_environment()


# Переменные окружения для настройки:

"""
LOG_ENABLED_MODULES=order_service,ai_service,command_service
LOG_DISABLED_MODULES=test_,debug_
LOG_ENABLED_FUNCTIONS=order_service.create_order,order_service.confirm_order
LOG_DISABLED_FUNCTIONS=order_service.get_order_status
LOG_LEVEL=INFO
LOG_FILE=app.log
LOG_FORMAT=json
ENVIRONMENT=development
"""

# Настройки логирования для разных модулей
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s: %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {  # Root logger
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'src.handlers.webhook_handler': {
            'level': 'WARNING',  # Уменьшаем логирование webhook'ов
            'handlers': ['console'],
            'propagate': False
        },
        'src.services.ai_service': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'src.services.message_processor': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        },
        'uvicorn': {
            'level': 'WARNING',  # Уменьшаем логирование uvicorn
            'handlers': ['console'],
            'propagate': False
        },
        'fastapi': {
            'level': 'WARNING',  # Уменьшаем логирование fastapi
            'handlers': ['console'],
            'propagate': False
        }
    }
} 
"""
AuraFlora WhatsApp Bot - Точка входа
====================================

Этот файл является точкой входа для запуска FastAPI приложения.
Вся основная логика вынесена в отдельные модули:

- handlers/: обработчики webhook'ов и сообщений
- routes/: FastAPI роуты
- app.py: создание и настройка приложения
"""

import uvicorn
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настраиваем логирование
from src.config.logging_config import setup_logging_by_environment
from src.utils.logging_decorator import enable_logging_for_module

# Инициализируем логирование
setup_logging_by_environment()

# Включаем логирование для основных модулей
enable_logging_for_module("ai_service")
enable_logging_for_module("message_processor")
enable_logging_for_module("webhook_handler")

def main():
    """Запуск FastAPI приложения"""
    from src.app import app
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8080))
    reload = os.getenv('RELOAD', 'false').lower() == 'true'
    uvicorn.run(
        "src.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="critical",
        access_log=False
    )

if __name__ == "__main__":
    main()

from src.app import app 
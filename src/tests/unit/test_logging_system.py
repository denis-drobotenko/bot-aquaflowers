"""
Тесты для системы логирования с декораторами
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from src.utils.logging_decorator import (
    log_function, 
    LoggingConfig, 
    enable_logging_for_module,
    disable_logging_for_module,
    enable_logging_for_function,
    disable_logging_for_function,
    get_logging_config
)
from src.config.logging_config import LoggingSettings


class TestLoggingConfig:
    """Тесты для конфигурации логирования"""
    
    def test_default_config(self):
        """Тест создания конфигурации по умолчанию"""
        config = LoggingConfig()
        
        assert isinstance(config.enabled_modules, list)
        assert isinstance(config.disabled_modules, list)
        assert isinstance(config.enabled_functions, list)
        assert isinstance(config.disabled_functions, list)
        assert config.log_level == "INFO"
        assert config.log_format == "json"
    
    def test_load_from_env(self):
        """Тест загрузки конфигурации из переменных окружения"""
        with patch.dict(os.environ, {
            "LOG_ENABLED_MODULES": "module1,module2",
            "LOG_DISABLED_MODULES": "module3",
            "LOG_ENABLED_FUNCTIONS": "module1.func1",
            "LOG_DISABLED_FUNCTIONS": "module2.func2",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text"
        }):
            config = LoggingConfig()
            
            assert "module1" in config.enabled_modules
            assert "module2" in config.enabled_modules
            assert "module3" in config.disabled_modules
            assert "module1.func1" in config.enabled_functions
            assert "module2.func2" in config.disabled_functions
            assert config.log_level == "DEBUG"
            assert config.log_format == "text"
    
    def test_is_logging_enabled(self):
        """Тест проверки включения логирования"""
        config = LoggingConfig()
        
        # По умолчанию логирование включено
        assert config.is_logging_enabled("test_module", "test_function") == True
        
        # Отключаем модуль
        config.add_disabled_module("test_module")
        assert config.is_logging_enabled("test_module", "test_function") == False
        
        # Включаем только определенные модули
        config.enabled_modules = ["module1", "module2"]
        config.disabled_modules = []
        assert config.is_logging_enabled("module1", "func1") == True
        assert config.is_logging_enabled("module3", "func1") == False
        
        # Отключаем конкретную функцию
        config.add_disabled_function("module1.noisy_func")
        assert config.is_logging_enabled("module1", "noisy_func") == False
        assert config.is_logging_enabled("module1", "other_func") == True


class TestLoggingDecorator:
    """Тесты для декоратора логирования"""
    
    def test_log_function_decorator(self):
        """Тест декоратора log_function"""
        
        @log_function("test_module")
        def test_function(param1: str, param2: int = 10) -> str:
            return f"result: {param1} {param2}"
        
        # Проверяем, что функция работает
        result = test_function("hello", 20)
        assert result == "result: hello 20"
        
        # Проверяем, что декоратор сохранил метаданные
        assert test_function.__name__ == "test_function"
    
    def test_log_function_with_disabled_logging(self):
        """Тест декоратора с отключенным логированием"""
        config = get_logging_config()
        config.add_disabled_module("test_module")
        
        @log_function("test_module")
        def test_function(param: str) -> str:
            return f"result: {param}"
        
        # Функция должна работать без логирования
        result = test_function("test")
        assert result == "result: test"
        
        # Восстанавливаем настройки
        config.disabled_modules.clear()
    
    def test_log_function_with_error(self):
        """Тест декоратора с ошибкой в функции"""
        
        @log_function("test_module")
        def test_function(param: str) -> str:
            raise ValueError(f"Test error: {param}")
        
        # Функция должна пробросить ошибку
        with pytest.raises(ValueError, match="Test error: test"):
            test_function("test")


class TestLoggingSettings:
    """Тесты для настроек логирования"""
    
    def test_setup_default_logging(self):
        """Тест настройки логирования по умолчанию"""
        LoggingSettings.setup_default_logging()
        config = get_logging_config()
        
        # Проверяем, что включены нужные модули
        for module in LoggingSettings.DEFAULT_ENABLED_MODULES:
            assert module in config.enabled_modules
        
        # Проверяем, что отключены нужные модули
        for module in LoggingSettings.DEFAULT_DISABLED_MODULES:
            assert module in config.disabled_modules
    
    def test_setup_production_logging(self):
        """Тест настройки логирования для продакшена"""
        LoggingSettings.setup_production_logging()
        config = get_logging_config()
        
        # В продакшене должны быть только критические модули
        assert "order_service" in config.enabled_modules
        assert "ai_service" in config.enabled_modules
        assert len(config.enabled_modules) == 2
    
    def test_setup_custom_logging(self):
        """Тест кастомной настройки логирования"""
        custom_settings = {
            "enabled_modules": ["custom_module"],
            "disabled_modules": ["noisy_module"],
            "enabled_functions": ["custom_module.important_func"],
            "disabled_functions": ["custom_module.noisy_func"]
        }
        
        LoggingSettings.setup_custom_logging(custom_settings)
        config = get_logging_config()
        
        assert "custom_module" in config.enabled_modules
        assert "noisy_module" in config.disabled_modules
        assert "custom_module.important_func" in config.enabled_functions
        assert "custom_module.noisy_func" in config.disabled_functions


class TestFunctionLogger:
    """Тесты для логгера функций"""
    
    def test_filter_sensitive_data(self):
        """Тест фильтрации чувствительных данных"""
        from src.utils.logging_decorator import FunctionLogger
        
        logger = FunctionLogger("test_module", "test_function")
        
        # Тест с чувствительными данными
        data = {
            "username": "john",
            "password": "secret123",
            "token": "abc123",
            "normal_field": "value"
        }
        
        filtered = logger._filter_sensitive_data(data)
        
        assert filtered["username"] == "john"
        assert filtered["password"] == "[REDACTED]"
        assert filtered["token"] == "[REDACTED]"
        assert filtered["normal_field"] == "value"
    
    def test_filter_nested_data(self):
        """Тест фильтрации вложенных данных"""
        from src.utils.logging_decorator import FunctionLogger
        
        logger = FunctionLogger("test_module", "test_function")
        
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret",
                    "api_key": "key123"
                }
            },
            "settings": ["normal", "data"]
        }
        
        filtered = logger._filter_sensitive_data(data)
        
        assert filtered["user"]["name"] == "John"
        assert filtered["user"]["credentials"]["password"] == "[REDACTED]"
        assert filtered["user"]["credentials"]["api_key"] == "[REDACTED]"
        assert filtered["settings"] == ["normal", "data"]


class TestIntegration:
    """Интеграционные тесты"""
    
    def test_logging_integration(self):
        """Интеграционный тест системы логирования"""
        
        # Настраиваем логирование
        LoggingSettings.setup_custom_logging({
            "enabled_modules": ["test_module"],
            "enabled_functions": ["test_module.test_func"]
        })
        
        # Создаем тестовую функцию
        @log_function("test_module")
        def test_func(param1: str, param2: int = 5) -> dict:
            return {"result": f"{param1}_{param2}", "status": "success"}
        
        # Вызываем функцию
        result = test_func("hello", 10)
        
        # Проверяем результат
        assert result == {"result": "hello_10", "status": "success"}
        
        # Проверяем, что логирование работает
        config = get_logging_config()
        assert "test_module" in config.enabled_modules
        assert config.is_logging_enabled("test_module", "test_func") == True


if __name__ == "__main__":
    pytest.main([__file__]) 
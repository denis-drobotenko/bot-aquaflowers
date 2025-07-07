"""
Система логирования с декораторами для автоматического логирования функций
"""

import functools
import inspect
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

# Настройка логирования для записи в файл
def setup_file_logging():
    """Настраивает логирование в файл"""
    log_file = os.getenv("LOG_FILE", "app.json")
    
    # Получаем root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Удаляем существующие handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Добавляем console handler для Cloud Run (логи идут в stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Форматтер для JSON
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(console_handler)
    
    # Отключаем вывод в консоль
    root_logger.propagate = False

# Инициализируем файловое логирование при импорте модуля
setup_file_logging()


class LoggingConfig:
    """Конфигурация логирования"""
    
    def __init__(self):
        self.enabled_modules: List[str] = []
        self.disabled_modules: List[str] = []
        self.enabled_functions: List[str] = []
        self.disabled_functions: List[str] = []
        self.log_level: str = "INFO"
        self.log_file: Optional[str] = None
        self.log_format: str = "compact"  # "json", "text" или "compact"
        self.max_log_size: int = 10 * 1024 * 1024  # 10MB
        self.backup_count: int = 5
        
        # Загружаем конфигурацию из переменных окружения
        self._load_from_env()
    
    def _load_from_env(self):
        """Загружает конфигурацию из переменных окружения"""
        # Модули для логирования
        enabled_modules = os.getenv("LOG_ENABLED_MODULES", "")
        if enabled_modules:
            self.enabled_modules = [m.strip() for m in enabled_modules.split(",") if m.strip()]
        
        disabled_modules = os.getenv("LOG_DISABLED_MODULES", "")
        if disabled_modules:
            self.disabled_modules = [m.strip() for m in disabled_modules.split(",") if m.strip()]
        
        # Функции для логирования
        enabled_functions = os.getenv("LOG_ENABLED_FUNCTIONS", "")
        if enabled_functions:
            self.enabled_functions = [f.strip() for f in enabled_functions.split(",") if f.strip()]
        
        disabled_functions = os.getenv("LOG_DISABLED_FUNCTIONS", "")
        if disabled_functions:
            self.disabled_functions = [f.strip() for f in disabled_functions.split(",") if f.strip()]
        
        # Уровень логирования
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Файл логирования
        self.log_file = os.getenv("LOG_FILE")
        
        # Формат логирования
        self.log_format = os.getenv("LOG_FORMAT", "json").lower()
        
        # Отладочная информация
        # print(f"[DEBUG] Logging config loaded: file={self.log_file}, format={self.log_format}")
        # print(f"[DEBUG] Enabled modules: {self.enabled_modules}")
        # print(f"[DEBUG] Disabled modules: {self.disabled_modules}")
    
    def is_logging_enabled(self, module_name: str, function_name: str) -> bool:
        """
        Проверяет, включено ли логирование для модуля и функции
        
        Args:
            module_name: Имя модуля
            function_name: Имя функции
            
        Returns:
            bool: True если логирование включено
        """
        # Проверяем отключенные модули (приоритет выше)
        if module_name in self.disabled_modules:
            # print(f"[DEBUG] Module {module_name} is disabled")
            return False
        
        # Проверяем отключенные функции
        full_function_name = f"{module_name}.{function_name}"
        if full_function_name in self.disabled_functions:
            # print(f"[DEBUG] Function {full_function_name} is disabled")
            return False
        
        # Проверяем включенные модули
        if self.enabled_modules:
            if module_name not in self.enabled_modules:
                # print(f"[DEBUG] Module {module_name} not in enabled modules: {self.enabled_modules}")
                return False
        
        # Проверяем включенные функции
        if self.enabled_functions:
            if full_function_name not in self.enabled_functions:
                # print(f"[DEBUG] Function {full_function_name} not in enabled functions: {self.enabled_functions}")
                return False
        
        # print(f"[DEBUG] Logging enabled for {module_name}.{function_name}")
        return True
    
    def add_enabled_module(self, module_name: str):
        """Добавляет модуль в список включенных для логирования"""
        if module_name not in self.enabled_modules:
            self.enabled_modules.append(module_name)
    
    def add_disabled_module(self, module_name: str):
        """Добавляет модуль в список отключенных для логирования"""
        if module_name not in self.disabled_modules:
            self.disabled_modules.append(module_name)
    
    def add_enabled_function(self, function_name: str):
        """Добавляет функцию в список включенных для логирования"""
        if function_name not in self.enabled_functions:
            self.enabled_functions.append(function_name)
    
    def add_disabled_function(self, function_name: str):
        """Добавляет функцию в список отключенных для логирования"""
        if function_name not in self.disabled_functions:
            self.disabled_functions.append(function_name)


# Глобальный экземпляр конфигурации
logging_config = LoggingConfig()


class FunctionLogger:
    """Логгер для функций"""
    
    def __init__(self, module_name: str, function_name: str):
        self.module_name = module_name
        self.function_name = function_name
        self.full_name = f"{module_name}.{function_name}"
        # Используем root logger
        self.logger = logging.getLogger()  # root logger
    
    def log_function_start(self, args: tuple, kwargs: dict, function_signature: inspect.Signature):
        try:
            bound_args = function_signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            safe_params = self._filter_sensitive_data(bound_args.arguments)
            log_data = {
                "event": "function_start",
                "module": self.module_name,
                "function": self.function_name,
                "timestamp": datetime.now().isoformat(),
                "parameters": safe_params
            }
            if logging_config.log_format == "json":
                self.logger.info(json.dumps(log_data, ensure_ascii=False, default=str))
            else:
                params_str = ", ".join([f"{k}={v}" for k, v in safe_params.items()])
                self.logger.info(f"START {self.full_name}({params_str})")
        except Exception as e:
            self.logger.error(f"Error logging function start: {e}")
    
    def log_function_end(self, result: Any, execution_time: float):
        try:
            safe_result = self._filter_sensitive_data({"result": result})
            log_data = {
                "event": "function_end",
                "module": self.module_name,
                "function": self.function_name,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": round(execution_time * 1000, 2),
                "result": safe_result.get("result")
            }
            if logging_config.log_format == "json":
                self.logger.info(json.dumps(log_data, ensure_ascii=False, default=str))
            else:
                result_str = str(safe_result.get("result"))[:200]
                self.logger.info(f"END {self.full_name} -> {result_str} ({execution_time:.3f}s)")
        except Exception as e:
            self.logger.error(f"Error logging function end: {e}")
    
    def log_function_error(self, error: Exception, execution_time: float):
        try:
            log_data = {
                "event": "function_error",
                "module": self.module_name,
                "function": self.function_name,
                "timestamp": datetime.now().isoformat(),
                "execution_time_ms": round(execution_time * 1000, 2),
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
            if logging_config.log_format == "json":
                self.logger.error(json.dumps(log_data, ensure_ascii=False, default=str))
            else:
                self.logger.error(f"ERROR {self.full_name} -> {type(error).__name__}: {error} ({execution_time:.3f}s)")
        except Exception as e:
            self.logger.error(f"Error logging function error: {e}")
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Фильтрует чувствительные данные из параметров
        
        Args:
            data: Словарь с данными
            
        Returns:
            Dict[str, Any]: Отфильтрованные данные
        """
        sensitive_keys = {
            'password', 'token', 'api_key', 'secret', 'key', 'auth',
            'authorization', 'bearer', 'access_token', 'refresh_token'
        }
        
        def filter_value(value):
            if isinstance(value, dict):
                return {k: "[REDACTED]" if k.lower() in sensitive_keys else filter_value(v) 
                       for k, v in value.items()}
            elif isinstance(value, list):
                return [filter_value(v) for v in value]
            elif isinstance(value, str) and any(key in value.lower() for key in sensitive_keys):
                return "[REDACTED]"
            else:
                return value
        
        return filter_value(data)


def log_function(module_name: Optional[str] = None):
    """
    Декоратор для автоматического логирования функций
    
    Args:
        module_name: Имя модуля (если не указано, будет определено автоматически)
    
    Returns:
        Callable: Декорированная функция
    """
    def decorator(func: Callable) -> Callable:
        # Определяем имя модуля
        if module_name is None:
            module_name_actual = func.__module__.split('.')[-1]
        else:
            module_name_actual = module_name
        
        function_name = func.__name__
        
        # Получаем сигнатуру функции
        try:
            signature = inspect.signature(func)
        except ValueError:
            signature = None
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Проверяем, включено ли логирование
            if not logging_config.is_logging_enabled(module_name_actual, function_name):
                return func(*args, **kwargs)
            
            # Создаем логгер
            function_logger = FunctionLogger(module_name_actual, function_name)
            
            # Логируем начало
            if signature:
                function_logger.log_function_start(args, kwargs, signature)
            
            start_time = datetime.now()
            
            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                
                # Проверяем, является ли результат корутиной (async функция)
                if inspect.iscoroutine(result):
                    # Для async функций возвращаем корутину-обертку
                    return _async_wrapper(result, function_logger, start_time)
                else:
                    # Для обычных функций логируем сразу
                    execution_time = (datetime.now() - start_time).total_seconds()
                    function_logger.log_function_end(result, execution_time)
                    return result
                
            except Exception as e:
                # Вычисляем время выполнения
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Логируем ошибку
                function_logger.log_function_error(e, execution_time)
                
                # Пробрасываем ошибку дальше
                raise
        
        async def _async_wrapper(coro, function_logger, start_time):
            """Обертка для async функций"""
            try:
                result = await coro
                execution_time = (datetime.now() - start_time).total_seconds()
                function_logger.log_function_end(result, execution_time)
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                function_logger.log_function_error(e, execution_time)
                raise
        
        return wrapper
    
    return decorator


def log_class_methods(module_name: Optional[str] = None):
    """
    Декоратор для автоматического логирования всех методов класса
    
    Args:
        module_name: Имя модуля (если не указано, будет определено автоматически)
    
    Returns:
        Callable: Декорированный класс
    """
    def decorator(cls):
        # Определяем имя модуля
        if module_name is None:
            module_name_actual = cls.__module__.split('.')[-1]
        else:
            module_name_actual = module_name
        
        # Декорируем все методы класса
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            
            # Проверяем, что это метод и не является магическим методом
            if (inspect.isfunction(attr) and 
                not attr_name.startswith('_') and 
                attr_name not in ['__init__', '__new__']):
                
                # Декорируем метод
                setattr(cls, attr_name, log_function(module_name_actual)(attr))
        
        return cls
    
    return decorator


# Утилиты для управления конфигурацией
def enable_logging_for_module(module_name: str):
    """Включает логирование для модуля"""
    logging_config.add_enabled_module(module_name)

def disable_logging_for_module(module_name: str):
    """Отключает логирование для модуля"""
    logging_config.add_disabled_module(module_name)

def enable_logging_for_function(function_name: str):
    """Включает логирование для функции"""
    logging_config.add_enabled_function(function_name)

def disable_logging_for_function(function_name: str):
    """Отключает логирование для функции"""
    logging_config.add_disabled_function(function_name)

def get_logging_config() -> LoggingConfig:
    """Возвращает текущую конфигурацию логирования"""
    return logging_config 
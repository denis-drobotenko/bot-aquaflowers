# Система логирования с декораторами

Система автоматического логирования функций с гибкой конфигурацией и фильтрацией чувствительных данных.

## 🚀 Возможности

- **Автоматическое логирование** начала и конца функций
- **Гибкая конфигурация** по модулям и функциям
- **Фильтрация чувствительных данных** (пароли, токены, API ключи)
- **Поддержка асинхронных функций**
- **Структурированные логи** в JSON или текстовом формате
- **Измерение времени выполнения**
- **Логирование ошибок** с контекстом
- **Настройка через переменные окружения**

## 📦 Установка и настройка

### 1. Импорт декоратора

```python
from src.utils.logging_decorator import log_function
```

### 2. Базовое использование

```python
@log_function("my_module")
def my_function(param1: str, param2: int) -> str:
    return f"Result: {param1} {param2}"
```

### 3. Настройка конфигурации

```python
from src.config.logging_config import LoggingSettings

# Настройка по окружению
LoggingSettings.setup_development_logging()

# Кастомная настройка
LoggingSettings.setup_custom_logging({
    "enabled_modules": ["order_service", "ai_service"],
    "disabled_modules": ["test_"],
    "enabled_functions": ["order_service.create_order"],
    "disabled_functions": ["order_service.get_order_status"]
})
```

## 🔧 Конфигурация

### Переменные окружения

```bash
# Модули для логирования
LOG_ENABLED_MODULES=order_service,ai_service,command_service
LOG_DISABLED_MODULES=test_,debug_

# Функции для логирования
LOG_ENABLED_FUNCTIONS=order_service.create_order,order_service.confirm_order
LOG_DISABLED_FUNCTIONS=order_service.get_order_status

# Настройки логов
LOG_LEVEL=INFO
LOG_FILE=app.log
LOG_FORMAT=json
ENVIRONMENT=development
```

### Программная настройка

```python
from src.utils.logging_decorator import (
    enable_logging_for_module,
    disable_logging_for_module,
    enable_logging_for_function,
    disable_logging_for_function
)

# Включить логирование для модуля
enable_logging_for_module("order_service")

# Отключить логирование для модуля
disable_logging_for_module("noisy_module")

# Включить логирование для конкретной функции
enable_logging_for_function("order_service.create_order")

# Отключить логирование для конкретной функции
disable_logging_for_function("order_service.get_order_status")
```

## 📝 Примеры использования

### Простая функция

```python
@log_function("user_service")
def create_user(username: str, email: str, password: str) -> dict:
    # Пароль будет автоматически отфильтрован в логах
    return {"user_id": "123", "username": username}
```

### Асинхронная функция

```python
@log_function("order_service")
async def process_order(order_data: dict) -> dict:
    await asyncio.sleep(1)
    return {"status": "processed", "order_id": "456"}
```

### Методы класса

```python
class OrderService:
    @log_function("order_service")
    def create_order(self, session_id: str, items: list) -> str:
        return f"order_{session_id}"
    
    @log_function("order_service")
    async def confirm_order(self, order_id: str) -> bool:
        await self.send_confirmation(order_id)
        return True
```

### Логирование всех методов класса

```python
from src.utils.logging_decorator import log_class_methods

@log_class_methods("order_service")
class OrderService:
    def create_order(self, data):
        pass
    
    def update_order(self, data):
        pass
    
    # Все методы будут автоматически логироваться
```

## 📊 Форматы логов

### JSON формат (по умолчанию)

```json
{
  "event": "function_start",
  "module": "order_service",
  "function": "create_order",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "parameters": {
    "session_id": "session_123",
    "items": [{"id": "1", "name": "Bouquet"}],
    "password": "[REDACTED]"
  }
}
```

### Текстовый формат

```
2024-01-01 12:00:00 INFO START order_service.create_order(session_id=session_123, items=[...])
2024-01-01 12:00:01 INFO END order_service.create_order -> order_session_123 (0.123s)
```

## 🔒 Безопасность

### Автоматическая фильтрация чувствительных данных

Система автоматически фильтрует следующие поля:
- `password`
- `token`
- `api_key`
- `secret`
- `key`
- `auth`
- `authorization`
- `bearer`
- `access_token`
- `refresh_token`

### Пример фильтрации

```python
@log_function("auth_service")
def authenticate_user(credentials: dict) -> dict:
    # В логах пароль будет заменен на [REDACTED]
    return {"user_id": "123", "token": "secret_token"}
```

**Результат в логах:**
```json
{
  "parameters": {
    "credentials": {
      "username": "john_doe",
      "password": "[REDACTED]"
    }
  }
}
```

## 🎯 Настройки для разных окружений

### Разработка (Development)

```python
LoggingSettings.setup_development_logging()
```

Включает логирование для:
- Всех основных сервисов
- Дополнительных модулей для отладки
- Подробных логов

### Продакшен (Production)

```python
LoggingSettings.setup_production_logging()
```

Включает логирование только для:
- Критических операций
- Создания и подтверждения заказов
- Обработки сообщений AI

### Отладка (Debug)

```python
LoggingSettings.setup_debug_logging()
```

Включает логирование для:
- Всех модулей (кроме тестовых)
- Максимальной детализации

## 🧪 Тестирование

### Запуск тестов

```bash
# Тесты системы логирования
python -m pytest src/tests/unit/test_logging_system.py -v

# Все тесты
python -m pytest src/tests/ -v
```

### Пример теста

```python
def test_logging_decorator():
    @log_function("test_module")
    def test_function(param: str) -> str:
        return f"result: {param}"
    
    result = test_function("hello")
    assert result == "result: hello"
```

## 📈 Мониторинг и анализ

### Структура логов

Каждая запись лога содержит:
- **event**: тип события (`function_start`, `function_end`, `function_error`)
- **module**: имя модуля
- **function**: имя функции
- **timestamp**: время выполнения
- **execution_time_ms**: время выполнения в миллисекундах
- **parameters**: входные параметры (отфильтрованные)
- **result**: результат выполнения
- **error_type**: тип ошибки (если есть)
- **error_message**: сообщение ошибки (если есть)

### Анализ производительности

```python
# Логи содержат время выполнения каждой функции
{
  "event": "function_end",
  "execution_time_ms": 123.45,
  "function": "order_service.process_order"
}
```

## 🔧 Интеграция с существующим кодом

### Пошаговая интеграция

1. **Добавьте импорт:**
```python
from src.utils.logging_decorator import log_function
```

2. **Добавьте декоратор к важным функциям:**
```python
@log_function("your_module")
def your_function(param):
    # ваш код
    pass
```

3. **Настройте конфигурацию:**
```python
from src.config.logging_config import LoggingSettings
LoggingSettings.setup_development_logging()
```

4. **Запустите и проверьте логи**

### Миграция существующих сервисов

```python
# Было
class OrderService:
    def create_order(self, data):
        self.logger.info("Creating order...")
        # код
        self.logger.info("Order created")
        return result

# Стало
class OrderService:
    @log_function("order_service")
    def create_order(self, data):
        # код
        return result
```

## 🚨 Обработка ошибок

### Автоматическое логирование ошибок

```python
@log_function("order_service")
def risky_function(param):
    if param == "error":
        raise ValueError("Something went wrong")
    return "success"

# При ошибке автоматически логируется:
# - Тип ошибки
# - Сообщение ошибки
# - Время выполнения
# - Параметры функции
```

### Пример лога ошибки

```json
{
  "event": "function_error",
  "module": "order_service",
  "function": "risky_function",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "execution_time_ms": 5.23,
  "error_type": "ValueError",
  "error_message": "Something went wrong"
}
```

## 📚 Дополнительные возможности

### Кастомные настройки фильтрации

```python
# Можно расширить список чувствительных полей
sensitive_keys = {
    'password', 'token', 'api_key', 'secret', 'key', 'auth',
    'authorization', 'bearer', 'access_token', 'refresh_token',
    'custom_sensitive_field'  # Добавить свои поля
}
```

### Интеграция с внешними системами

Логи в JSON формате легко интегрируются с:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana
- CloudWatch
- Datadog
- Splunk

## 🤝 Поддержка

### Полезные команды

```bash
# Запуск примера
python examples/logging_example.py

# Тестирование
python -m pytest src/tests/unit/test_logging_system.py -v

# Просмотр конфигурации
python -c "from src.config.logging_config import LoggingSettings; LoggingSettings.setup_development_logging(); from src.utils.logging_decorator import get_logging_config; print(get_logging_config().__dict__)"
```

### Частые вопросы

**Q: Как отключить логирование для конкретной функции?**
A: Используйте `disable_logging_for_function("module.function_name")`

**Q: Как изменить формат логов?**
A: Установите переменную окружения `LOG_FORMAT=text` или `LOG_FORMAT=json`

**Q: Как добавить свои чувствительные поля?**
A: Отредактируйте список `sensitive_keys` в `FunctionLogger._filter_sensitive_data`

**Q: Как логировать только ошибки?**
A: Настройте `LOG_LEVEL=ERROR` и отключите логирование для всех модулей, кроме критических 
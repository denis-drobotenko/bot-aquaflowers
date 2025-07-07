# Тестирование сервисов

## 📋 Обзор

Этот каталог содержит полный набор тестов для всех сервисов проекта. Тесты разделены на модульные (unit) и интеграционные (integration) для обеспечения качественного покрытия кода.

## 🏗️ Структура тестов

```
src/tests/
├── __init__.py
├── conftest.py              # Конфигурация pytest и общие фикстуры
├── run_tests.py             # Скрипт для запуска тестов
├── README.md               # Этот файл
├── TEST_PLAN.md            # План тестирования
├── unit/                   # Модульные тесты
│   ├── test_ai_service.py
│   ├── test_catalog_service.py
│   ├── test_catalog_sender.py
│   ├── test_command_service.py
│   ├── test_message_service.py
│   ├── test_order_service.py
│   ├── test_session_service.py
│   └── test_user_service.py
├── integration/            # Интеграционные тесты
│   ├── test_ai_catalog_integration.py
│   ├── test_message_session_integration.py
│   └── test_order_workflow.py
├── fixtures/               # Тестовые данные
│   ├── mock_catalog_data.py
│   ├── mock_messages.py
│   └── mock_orders.py
└── utils/                  # Утилиты для тестов
    ├── test_helpers.py
    └── mock_services.py
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements-test.txt
```

### Запуск всех тестов

```bash
# Используя скрипт
python src/tests/run_tests.py

# Или напрямую pytest
python -m pytest src/tests/ -v
```

### Запуск с покрытием кода

```bash
# С текстовым отчетом
python src/tests/run_tests.py --type coverage

# С HTML отчетом
python src/tests/run_tests.py --type coverage --html-report
```

## 📊 Типы тестов

### Модульные тесты (unit/)

Тестируют отдельные функции и методы сервисов в изоляции:

- **AIService**: определение языка, перевод, генерация ответов
- **CatalogService**: получение товаров, поиск, валидация
- **CatalogSender**: отправка каталога через WhatsApp
- **MessageService**: работа с сообщениями и историей диалогов
- **OrderService**: создание, обновление, управление заказами
- **SessionService**: управление сессиями пользователей
- **UserService**: управление пользователями

### Интеграционные тесты (integration/)

Тестируют взаимодействие между сервисами:

- **AI + Catalog**: интеграция AI с каталогом товаров
- **Message + Session**: работа с сообщениями в рамках сессий
- **Order Workflow**: полный цикл заказа от создания до завершения

## 🎯 Команды запуска

### Базовые команды

```bash
# Все тесты
python src/tests/run_tests.py --type all

# Только модульные тесты
python src/tests/run_tests.py --type unit

# Только интеграционные тесты
python src/tests/run_tests.py --type integration

# Быстрые тесты (без медленных)
python src/tests/run_tests.py --type fast
```

### Тестирование конкретного сервиса

```bash
# Тестирование AI сервиса
python src/tests/run_tests.py --service ai_service

# Тестирование каталога
python src/tests/run_tests.py --service catalog_service

# С подробным выводом
python src/tests/run_tests.py --service message_service --verbose
```

### Покрытие кода

```bash
# Покрытие с текстовым отчетом
python src/tests/run_tests.py --type coverage

# Покрытие с HTML отчетом
python src/tests/run_tests.py --type coverage --html-report

# Открыть HTML отчет (macOS)
open htmlcov/index.html

# Открыть HTML отчет (Linux)
xdg-open htmlcov/index.html
```

## 📈 Метрики качества

### Цели покрытия

- **Общее покрытие**: 90%+
- **Критические сервисы**: 95%+
- **Время выполнения**: < 30 секунд для всех тестов

### Мониторинг качества

```bash
# Запуск с детальной статистикой
python -m pytest src/tests/ --cov=src/services --cov-report=term-missing --cov-report=html

# Проверка медленных тестов
python -m pytest src/tests/ --durations=10

# Проверка дублирования кода
python -m pytest src/tests/ --cov=src/services --cov-report=html --cov-fail-under=90
```

## 🔧 Настройка и конфигурация

### Переменные окружения

Создайте файл `.env.test` для тестового окружения:

```env
# Тестовые настройки
TEST_MODE=true
MOCK_EXTERNAL_SERVICES=true

# Тестовые API ключи
TEST_AI_API_KEY=test_key
TEST_WHATSAPP_TOKEN=test_token
```

### Конфигурация pytest

Основные настройки в `conftest.py`:

- Автоматическая маркировка тестов (unit/integration)
- Общие фикстуры для моков
- Настройки покрытия кода
- Тестовые данные

## 🐛 Отладка тестов

### Подробный вывод

```bash
# Максимальная детализация
python -m pytest src/tests/ -vvv -s

# Только неудачные тесты
python -m pytest src/tests/ -x --tb=short

# Остановка на первой ошибке
python -m pytest src/tests/ -x
```

### Отладка конкретного теста

```bash
# Запуск одного теста
python -m pytest src/tests/unit/test_ai_service.py::test_detect_language -v

# Запуск тестов по паттерну
python -m pytest src/tests/ -k "test_detect" -v
```

## 📝 Написание новых тестов

### Структура теста

```python
import pytest
from unittest.mock import patch, MagicMock
from src.services.your_service import YourService

@pytest.fixture
def your_service():
    return YourService()

@pytest.mark.asyncio
async def test_your_function_success(your_service):
    """Тест успешного выполнения функции"""
    # Arrange
    with patch.object(your_service, 'dependency') as mock_dep:
        mock_dep.return_value = "expected_result"
        
        # Act
        result = await your_service.your_function("input")
        
        # Assert
        assert result == "expected_result"
        mock_dep.assert_called_once_with("input")

@pytest.mark.asyncio
async def test_your_function_error(your_service):
    """Тест обработки ошибок"""
    # Arrange
    with patch.object(your_service, 'dependency') as mock_dep:
        mock_dep.side_effect = Exception("Test error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await your_service.your_function("input")
```

### Лучшие практики

1. **Изоляция**: каждый тест должен быть независимым
2. **Именование**: описательные имена тестов и функций
3. **AAA паттерн**: Arrange, Act, Assert
4. **Моки**: используйте моки для внешних зависимостей
5. **Покрытие**: тестируйте как успешные, так и ошибочные сценарии

## 🔄 CI/CD интеграция

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run tests
        run: python src/tests/run_tests.py --type coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 📚 Дополнительные ресурсы

- [План тестирования](TEST_PLAN.md) - детальный план всех тестов
- [Документация pytest](https://docs.pytest.org/) - официальная документация
- [Документация pytest-cov](https://pytest-cov.readthedocs.io/) - покрытие кода
- [Документация unittest.mock](https://docs.python.org/3/library/unittest.mock.html) - моки

## 🤝 Вклад в тестирование

1. Следуйте существующим паттернам
2. Добавляйте тесты для новых функций
3. Обновляйте тесты при изменении API
4. Поддерживайте высокое покрытие кода
5. Документируйте сложные тестовые сценарии 
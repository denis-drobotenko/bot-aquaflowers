# Упрощенная архитектура бота

## Основные принципы

1. **Единая точка входа** - `MessageProcessor.process_user_message()`
2. **Простая последовательность** - сохранить → AI → команда → отправить
3. **Минимум дублей** - убраны повторяющиеся методы
4. **Четкое разделение ответственности**

## Архитектура

### 1. WebhookHandler
- **Назначение**: Валидация и извлечение данных из webhook
- **Основные методы**:
  - `validate_webhook()` - проверка структуры и дублей
  - `process_webhook()` - основная обработка
  - `extract_and_process_message()` - извлечение данных сообщения

### 2. MessageProcessor (главный компонент)
- **Назначение**: Единая точка обработки всех сообщений
- **Основной метод**: `process_user_message()`

**Последовательность обработки:**
```
1. Получить сессию и пользователя
2. Проверить специальные команды (/newses)
3. Сохранить сообщение пользователя
4. Получить историю и обработать через AI
5. Сохранить ответ AI
6. Обработать команду AI (если есть)
7. Отправить ответ пользователю
```

**Вспомогательные методы:**
- `_create_user_message()` - создание объекта сообщения пользователя
- `_create_ai_message()` - создание объекта сообщения AI
- `_process_ai()` - обработка через AI
- `_send_ai_response()` - отправка ответа
- `_send_text_message()` - отправка текста

### 3. AIService
- **Назначение**: Работа с Gemini AI
- **Основные методы**:
  - `generate_response()` - генерация ответа AI
  - `detect_language()` - определение языка
  - `translate_user_message()` - перевод на 3 языка
  - `get_system_prompt()` - формирование промпта

### 4. Вспомогательные сервисы
- **SessionService** - управление сессиями
- **UserService** - управление пользователями
- **MessageService** - работа с сообщениями в БД
- **CommandService** - обработка команд AI

## Устраненные дубли

### MessageProcessor
- ❌ Удалены: `process_with_ai()`, `process_with_ai_with_history()`, `_process_ai_without_save()`
- ❌ Удалены: `send_message()`, `_send_image_message()`, `_save_message()`
- ❌ Удалены: дублирующие методы создания `AIResponse`
- ✅ Оставлен: только основной `process_user_message()` и вспомогательные методы

### AIService
- ❌ Удалены: `generate_response_sync()`, `_generate_contextual_response()`, `_generate_standard_response()`
- ❌ Удалены: `_generate_request_id()`, избыточное логирование
- ✅ Оставлен: только основной `generate_response()` и вспомогательные методы

### WebhookHandler
- ❌ Удалены: `send_typing_indicator()`, статические методы-дубли
- ❌ Упрощены: методы обработки интерактивных сообщений
- ✅ Оставлена: только основная логика валидации и извлечения

## Преимущества упрощенной архитектуры

1. **Понятность** - четкая последовательность обработки
2. **Поддерживаемость** - меньше кода, проще отладка
3. **Производительность** - убраны лишние операции
4. **Надежность** - меньше точек отказа
5. **Масштабируемость** - легко добавлять новую функциональность

## Поток обработки сообщения

```
Webhook → WebhookHandler.validate_webhook()
         ↓
WebhookHandler.process_webhook()
         ↓
WebhookHandler._process_message()
         ↓
MessageProcessor.process_user_message()
         ↓
1. SessionService.get_or_create_session_id()
2. UserService.get_user()
3. MessageService.add_message_with_transaction_sync() (пользователь)
4. MessageService.get_conversation_history_for_ai_by_sender()
5. AIService.generate_response()
6. MessageService.add_message_with_transaction_sync() (AI)
7. CommandService.handle_command() (если есть команда)
8. WhatsAppClient.send_text_message()
```

## Удаленные файлы

- `old/ai_manager.py` - заменен на `AIService`
- `old/command_handler.py` - заменен на `CommandService`
- `old/chat_history_processor.py` - функциональность в `MessageService`
- `old/webhook_handlers.py` - заменен на `WebhookHandler` 
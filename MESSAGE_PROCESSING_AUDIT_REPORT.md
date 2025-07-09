# Отчет об аудите обработки сообщений AquaFlora Bot

## 🔍 Выявленные проблемы

### 1. **КРИТИЧЕСКАЯ ПРОБЛЕМА: AI возвращает невалидные ответы**

**Симптомы:**
- AI возвращает команду `send_catalog` без текстового поля
- Система отправляет fallback сообщение "Конечно! Чем могу помочь? 🌸"
- Повторные попытки не помогают

**Логи показывают:**
```
[AI_VALIDATION] Invalid response: Missing 'text' field
[AI_VALIDATION] Response data: {'command': 'send_catalog'}
[AI_ERROR] Empty AI response on attempt 3
```

**Причина:**
AI возвращает JSON только с командой, без обязательного поля `text`:
```json
{
  "command": "send_catalog"
}
```

### 2. **ПРОБЛЕМА: Неправильная обработка команд без текста**

**Текущая логика в `ai_service.py`:**
```python
# Проверяем на пустой ответ (но с командой)
if (not ai_text or ai_text.strip() == "") and not ai_command:
    # Возвращает fallback
```

**Проблема:** Логика не учитывает случай, когда есть команда, но нет текста.

### 3. **ПРОБЛЕМА: Fallback сообщения отправляются пользователю**

**Текущий fallback в `ai_utils.py`:**
```python
def get_fallback_text(user_lang: str) -> str:
    return "Конечно! Чем могу помочь? 🌸"
```

**Проблема:** Это общее сообщение, которое не решает проблему пользователя.

## 🔧 Рекомендации по исправлению

### 1. **Исправить валидацию AI ответов**

**Файл:** `src/utils/ai_utils.py`

```python
def validate_ai_response(response_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Валидирует ответ AI и возвращает (is_valid, error_message).
    """
    # Проверяем обязательные поля
    if 'text' not in response_data:
        return False, "Missing 'text' field"
    
    # ИЗМЕНЕНИЕ: Разрешаем пустой text если есть команда
    if not response_data.get('text') and not response_data.get('command'):
        return False, "Empty 'text' field and no command"
    
    # Проверяем переводы (делаем необязательными)
    if 'text_en' not in response_data:
        response_data['text_en'] = response_data.get('text', '')
    if 'text_thai' not in response_data:
        response_data['text_thai'] = response_data.get('text', '')
    
    # Проверяем формат команды
    command = response_data.get('command')
    if command is not None:
        if isinstance(command, str):
            return False, f"Command should be object with 'type' field, got string: '{command}'"
        elif isinstance(command, dict):
            if 'type' not in command:
                return False, "Command object missing 'type' field"
            if not isinstance(command['type'], str):
                return False, "Command 'type' should be string"
        else:
            return False, f"Command should be object or null, got: {type(command)}"
    
    return True, ""
```

### 2. **Исправить обработку команд в AI Service**

**Файл:** `src/services/ai_service.py`

```python
# В методе generate_response, заменить логику проверки:
# Было:
if (not ai_text or ai_text.strip() == "") and not ai_command:
    print(f"[AI_ERROR] Empty AI response on attempt {attempt + 1}")
    if attempt < max_retries:
        print(f"[AI_RETRY] Retrying... (attempt {attempt + 2}/{max_retries + 1})")
        continue
    else:
        fallback_text = get_fallback_text(user_lang)
        return fallback_text, fallback_text, fallback_text, None

# Стало:
if not ai_text and not ai_command:
    print(f"[AI_ERROR] Empty AI response on attempt {attempt + 1}")
    if attempt < max_retries:
        print(f"[AI_RETRY] Retrying... (attempt {attempt + 2}/{max_retries + 1})")
        continue
    else:
        fallback_text = get_fallback_text(user_lang)
        return fallback_text, fallback_text, fallback_text, None

# Если есть команда, но нет текста - это нормально
if ai_command and (not ai_text or ai_text.strip() == ""):
    print(f"[AI_INFO] Command without text: {ai_command}")
    return "", "", "", ai_command
```

### 3. **Улучшить обработку команд в MessageProcessor**

**Файл:** `src/services/message_processor.py`

```python
async def _send_ai_response(self, ai_response: AIResponse, sender_id: str, session_id: str, wamid: str = None, retry_count: int = 0) -> bool:
    """Отправляет ответ AI пользователю"""
    try:
        # 1. Если есть текстовый ответ от AI, отправляем его
        if ai_response.text and ai_response.text.strip():
            success = await self._send_text_message(
                sender_id, 
                ai_response.text, 
                session_id, 
                ai_response.text_en, 
                ai_response.text_thai
            )
            if wamid:
                waba_logger.log_message_sent(wamid, sender_id, ai_response.text)
            
            if not success:
                return False
        
        # 2. Если есть команда, выполняем её (даже если нет текста)
        if ai_response.command:
            command_type = ai_response.command.get('type') if isinstance(ai_response.command, dict) else None
            if not command_type or command_type not in self.SUPPORTED_COMMANDS:
                # Логируем ошибку в Errors
                await self.error_service.log_error(
                    error=Exception(f"Unknown AI command: {command_type}"),
                    sender_id=sender_id,
                    session_id=session_id,
                    ai_response=str(ai_response.command),
                    context_data={"command": ai_response.command, "wamid": wamid},
                    module="message_processor",
                    function="_send_ai_response"
                )
                return False
            
            command_result = await self._handle_ai_command(ai_response.command, session_id, sender_id, wamid)
            
            # Если команда не выполнена, отправляем ошибку
            if command_result.get('status') != 'success':
                user_lang = await self.session_service.get_user_language(sender_id, session_id)
                error_messages = self._get_error_messages(user_lang)
                error_message = command_result.get('message', error_messages['ru'])
                error_success = await self._send_text_message(
                    sender_id, 
                    error_message, 
                    session_id
                )
                if wamid:
                    waba_logger.log_message_sent(wamid, sender_id, error_message)
                return error_success
        
        return True
        
    except Exception as e:
        logging.error(f"[MESSAGE_PROCESSOR] Send response error: {e}")
        return False
```

### 4. **Улучшить системный промпт для AI**

**Файл:** `src/services/ai_service.py`

```python
def get_system_prompt(self, user_lang: str = 'auto', sender_name: str = None, is_first_message: bool = False) -> str:
    # ... существующий код ...
    
    prompt_template = """You are AURAFLORA, a friendly flower shop assistant in Phuket.

RESPONSE FORMAT:
You MUST respond in JSON format with these fields:
{
  "text": "Your response in user's language",
  "text_en": "English translation",
  "text_thai": "Thai translation", 
  "command": {
    "type": "command_type" // or null if no command needed
  }
}

IMPORTANT RULES:
1. Always include ALL fields: text, text_en, text_thai, command
2. If you need to show catalog, use command: {"type": "send_catalog"}
3. If you need to save order info, use command: {"type": "save_order_info"}
4. If no command needed, use: "command": null
5. Never return empty text field unless you have a command
6. Always end responses with 🌸 emoji

Available commands:
- send_catalog: Display flower catalog
- save_order_info: Save order data  
- add_order_item: Add item to order
- remove_order_item: Remove item from order
- update_order_delivery: Update delivery info
- confirm_order: Confirm final order

{rest_of_prompt}"""
```

### 5. **Добавить контекстные fallback сообщения**

**Файл:** `src/utils/ai_utils.py`

```python
def get_contextual_fallback_text(user_lang: str, context: str = None) -> str:
    """
    Возвращает контекстный fallback-ответ в зависимости от ситуации.
    """
    if context == "catalog_requested":
        if user_lang == 'en':
            return "Let me show you our flower catalog! 🌸"
        elif user_lang == 'th':
            return "ให้ฉันแสดงแคตตาล็อกดอกไม้ของเรา! 🌸"
        return "Покажу вам наш каталог цветов! 🌸"
    
    elif context == "order_info":
        if user_lang == 'en':
            return "I'll help you with your order! 🌸"
        elif user_lang == 'th':
            return "ฉันจะช่วยคุณกับคำสั่งซื้อ! 🌸"
        return "Помогу вам с заказом! 🌸"
    
    # Общий fallback
    if user_lang == 'en':
        return "How can I help you today? 🌸"
    elif user_lang == 'th':
        return "ฉันสามารถช่วยคุณได้อย่างไรวันนี้? 🌸"
    return "Чем могу помочь сегодня? 🌸"
```

## 🚀 План внедрения исправлений

### Этап 1: Критические исправления (немедленно)
1. ✅ Исправить валидацию AI ответов
2. ✅ Исправить обработку команд без текста
3. ✅ Улучшить системный промпт

### Этап 2: Улучшения (в течение дня)
1. ✅ Добавить контекстные fallback сообщения
2. ✅ Улучшить логирование ошибок
3. ✅ Добавить мониторинг качества AI ответов

### Этап 3: Долгосрочные улучшения (неделя)
1. ✅ Кэширование частых AI запросов
2. ✅ A/B тестирование промптов
3. ✅ Автоматическое обучение на ошибках

## 📊 Метрики для мониторинга

### Ключевые метрики:
```python
# Качество AI ответов
- Процент валидных JSON ответов
- Процент ответов с командами
- Время обработки AI запросов
- Количество повторных попыток

# Пользовательский опыт
- Время ответа бота
- Количество fallback сообщений
- Успешность выполнения команд
- Конверсия диалогов в заказы
```

### Алерты:
```python
# Критические алерты
- Процент невалидных AI ответов > 20%
- Время ответа > 10 секунд
- Количество fallback сообщений > 50 в час
- Ошибки выполнения команд > 10%
```

## 🔍 Дополнительные рекомендации

### 1. **Улучшить промпт для каталога**
```python
# Добавить в промпт:
"When user asks for catalog or shows interest in flowers, 
ALWAYS respond with text explaining you'll show the catalog, 
then use command: {'type': 'send_catalog'}"
```

### 2. **Добавить обработку контекста**
```python
# Анализировать последние сообщения для понимания контекста
# Если пользователь просит каталог - сразу показывать
# Если отвечает "хочу" - уточнять что именно
```

### 3. **Улучшить логирование**
```python
# Добавить детальное логирование:
- Полный промпт, отправленный AI
- Полный ответ от AI
- Причины валидационных ошибок
- Контекст диалога при ошибках
```

Эти исправления должны решить проблему с fallback сообщениями и улучшить качество обработки запросов пользователей. 
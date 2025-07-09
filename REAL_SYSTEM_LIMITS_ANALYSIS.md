# Анализ реальных лимитов системы AquaFlora WhatsApp Bot

## 🔍 Изученные лимиты в коде

### 1. Лимиты истории диалога

**Основные лимиты:**
- **50 сообщений** - используется в `message_processor.py` для получения истории для AI
- **100 сообщений** - используется в `message_repository.py` как дефолтный лимит
- **10 сообщений** - используется в транзакциях для оптимизации

**Где используются:**
```python
# message_processor.py
conversation_history = await self.message_service.get_conversation_history_for_ai_by_sender(
    sender_id, session_id, limit=50
)

# message_repository.py  
async def get_conversation_history_by_sender(self, sender_id: str, session_id: str, limit: int = 100)

# Транзакции
def add_message_with_transaction_sync(self, message: Message, limit: int = 10)
```

### 2. Лимиты токенов для AI

**Текущие настройки в `ai_service.py`:**

```python
# Основная модель Gemini 2.5 Flash
generation_config=GenerationConfig(
    temperature=0.7,
    top_p=0.9,
    top_k=40,
    max_output_tokens=8192  # ← МАКСИМАЛЬНЫЙ ЛИМИТ
)

# Модель для определения языка
generation_config=GenerationConfig(
    temperature=0.1,
    top_p=1,
    top_k=1,
    max_output_tokens=200  # ← МАЛЕНЬКИЙ ЛИМИТ
)

# Модель для перевода
generation_config=GenerationConfig(
    temperature=0.3,
    top_p=1,
    top_k=1,
    max_output_tokens=4096  # ← СРЕДНИЙ ЛИМИТ
)
```

### 3. Лимиты логирования

**GCloud логи:**
- **1000 записей** - стандартный лимит для скачивания логов
- **5000 записей** - расширенный лимит для анализа

## 📊 Реальные ограничения контекста

### Текущая ситуация:

1. **История диалога:** максимум 50-100 сообщений
2. **Выходные токены:** максимум 8192 токена
3. **Системный промпт:** ~2,474 токена (новый структурированный)

### Расчет для Gemini 2.0 Flash (128,000 токенов):

```
Доступный контекст: 128,000 токенов
- Системный промпт: 2,474 токена
- Безопасный запас (20%): 25,600 токенов
= Доступно для истории: ~99,926 токенов
```

### Проблема с текущими лимитами:

**Система НЕ использует полный потенциал контекстного окна!**

- **Текущий лимит:** 50-100 сообщений
- **Потенциальный лимит:** ~1000-2000 сообщений (при среднем размере 50-100 токенов на сообщение)

## 🚀 Рекомендации по оптимизации

### 1. Увеличить лимиты истории

```python
# В message_processor.py изменить:
limit=50 → limit=200  # или больше

# В message_repository.py изменить:
limit: int = 100 → limit: int = 500
```

### 2. Динамические лимиты

```python
def calculate_optimal_history_limit(system_prompt_tokens: int, max_context: int = 128000) -> int:
    """Рассчитывает оптимальный лимит истории на основе размера системного промпта"""
    available_tokens = max_context - system_prompt_tokens - (max_context * 0.2)  # 20% запас
    estimated_tokens_per_message = 75  # средний размер сообщения
    return int(available_tokens / estimated_tokens_per_message)
```

### 3. Адаптивная история

```python
async def get_adaptive_conversation_history(sender_id: str, session_id: str) -> List[Dict]:
    """Получает адаптивную историю в зависимости от размера системного промпта"""
    system_prompt_size = len(get_system_prompt()) * 1.3  # примерная оценка в токенах
    optimal_limit = calculate_optimal_history_limit(system_prompt_size)
    return await get_conversation_history_by_sender(sender_id, session_id, limit=optimal_limit)
```

## 📈 Потенциальные улучшения

### Текущие лимиты vs Потенциал:

| Компонент | Текущий лимит | Потенциальный лимит | Увеличение |
|-----------|---------------|-------------------|------------|
| История диалога | 50-100 сообщений | 500-1000 сообщений | **5-10x** |
| Выходные токены | 8192 | 8192 | Без изменений |
| Системный промпт | 2474 токена | 2474 токена | Без изменений |

### Ожидаемые результаты:

1. **Лучший контекст:** AI будет видеть больше истории диалога
2. **Более релевантные ответы:** Учет долгосрочного контекста
3. **Меньше повторений:** AI не будет забывать предыдущие решения
4. **Лучшая персонализация:** Больше данных о предпочтениях пользователя

## 🎯 Заключение

**Система использует только 5-10% от доступного контекстного окна Gemini 2.0 Flash!**

Рекомендуется увеличить лимиты истории диалога в 5-10 раз для максимального использования возможностей модели. 
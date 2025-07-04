# Архив файлов AURAFLORA Bot

Эта папка содержит файлы, которые были перемещены из корневой директории проекта для очистки рабочего пространства.

## 📁 Содержимое архива

### 🔧 Отладочные файлы
- `debug_viewer.py` - Основной отладчик (дублирует функциональность из main.py)
- `debug_viewer_simple.py` - Упрощенная версия отладчика
- `debug_clean.html` - HTML файл отладки
- `current_debug_page.html` - Пустой HTML файл отладки
- `chat_history_debug.html` - HTML файл для отладки истории чата

### 📊 Утилиты для работы с логами
- `extract_last_5min_logs.py` - Извлечение логов за последние 5 минут
- `extract_last_20min_logs.py` - Извлечение логов за последние 20 минут
- `extract_dialogs.py` - Извлечение диалогов из логов
- `decode_all_ai_lines.py` - Декодирование всех AI строк
- `decode_existing_logs.py` - Декодирование существующих логов
- `simple_unicode_decoder.py` - Простой декодер Unicode
- `analyze_logs.py` - Анализ логов
- `get_logs.py` - Получение логов
- `get_logs_api_fixed.py` - Исправленная версия получения логов через API
- `get_logs_cyrillic_fixed.py` - Исправленная версия для кириллицы
- `get_logs_proper_api.py` - Правильная версия API для логов
- `get_ai_logs_proper.py` - Правильное получение AI логов
- `get_ai_responses.py` - Получение AI ответов
- `get_ai_responses_fixed.py` - Исправленная версия получения AI ответов
- `get_ai_responses_utf8.py` - UTF-8 версия получения AI ответов
- `get_all_logs.py` - Получение всех логов

### 🧪 Тестовые файлы
- `add_test_data.py` - Добавление тестовых данных
- `run_test_server.py` - Запуск тестового сервера
- `ai_manager_old.py` - Старая версия AI менеджера
- `ai_manager copy.py` - Копия AI менеджера

### 📄 Файлы логов и данных
- `logs.log` - Основной файл логов
- `fresh_logs.log` - Свежие логи
- `petr_logs_last_5min.txt` - Логи Петра за последние 5 минут
- `petr_logs_last_20min.txt` - Логи Петра за последние 20 минут
- `petr_logs_last_20min_raw.txt` - Сырые логи Петра за последние 20 минут
- `petr_logs_last2000.txt` - Последние 2000 строк логов Петра
- `petr_last_logs_head.json` - Заголовок последних логов Петра
- `petr_last_logs.json` - Последние логи Петра
- `petr_last_hour_logs.json` - Логи Петра за последний час
- `stdout_logs.json` - Логи stdout
- `last_100_json.log` - Последние 100 JSON логов
- `json_lines.txt` - JSON строки
- `full_dialog_with_tech.txt` - Полный диалог с техподдержкой
- `payload.json` - Тестовый payload

## 🔄 Восстановление файлов

Если какой-то файл понадобится, его можно восстановить командой:
```bash
move archive/имя_файла ./
```

## 📝 Примечания

- Все файлы в архиве не используются в основном коде приложения
- Файлы логов могут быть большими (несколько МБ)
- Старые версии AI менеджера сохранены для сравнения
- Отладочные файлы дублируют функциональность из основного кода 
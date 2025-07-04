# AURAFLORA Bot - Google Cloud Run версия

Цветочный бот для WhatsApp с интеграцией AI (Gemini), базой данных Firestore и уведомлениями в LINE.

## 📁 Структура проекта

```
auraflora-bot-complete/
├── src/                          # Основной код приложения
│   ├── __init__.py              # Инициализация пакета
│   ├── main.py                  # FastAPI сервер и основные роуты (1.7KB)
│   ├── ai_manager.py            # Интеграция с Gemini AI (5.6KB)
│   ├── database.py              # Работа с Firestore (4.0KB)
│   ├── config.py                # Конфигурация и токены (14KB)
│   ├── webhook_handlers.py      # Обработка webhook-ов (13KB)
│   ├── whatsapp_utils.py        # Утилиты WhatsApp API (3.8KB)
│   ├── order_utils.py           # Обработка заказов (25KB)
│   ├── command_handler.py       # Обработка команд от AI (9.4KB)
│   ├── catalog_reader.py        # Чтение каталога товаров (3.3KB)
│   └── catalog_utils.py         # Работа с каталогом (1.9KB)
├── tests/                        # Тестовые файлы
│   ├── __init__.py              # Инициализация пакета тестов
│   ├── test_quick.py            # Быстрый тест работоспособности
│   ├── test_active_dialog.py    # Тест активного диалога AI
│   ├── test_full_dialog.py      # Полный тест диалога с заказом
│   ├── test_json_ai.py          # Тест JSON ответов от AI
│   ├── test_interactive_messages.py # Тест интерактивных сообщений
│   ├── test_catalog_reading.py  # Тест чтения каталога
│   ├── run_tests.py             # Скрипт запуска всех тестов
│   ├── TESTING.md               # Документация по тестированию
│   └── README.md                # Документация тестов
├── scripts/                      # Скрипты для управления
│   ├── deploy.sh                # Скрипт деплоя на Google Cloud Run
│   └── save_logs_from_gcloud.py # Скрипт получения логов
├── config/                       # Конфигурационные файлы
│   └── log-access.json          # Сервисный ключ для доступа к логам
├── requirements.txt              # Зависимости для FastAPI
├── Dockerfile                    # Контейнеризация
└── README.md                     # Этот файл
```

## 🚀 Деплой на Google Cloud Run

### Автоматический деплой
```bash
# Убедитесь, что у вас настроен gcloud CLI
./scripts/deploy.sh
```

### Ручной деплой
```bash
docker build -t gcr.io/auraflora-bot-75152239022/auraflora-bot .
docker push gcr.io/auraflora-bot-75152239022/auraflora-bot
gcloud run deploy auraflora-bot \
    --image gcr.io/auraflora-bot-75152239022/auraflora-bot \
    --platform managed \
    --region asia-southeast1 \
    --project auraflora-bot-75152239022 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars="DEV_MODE=false"
```

## 📊 Получение логов

### Автоматическое получение логов
```bash
python scripts/save_logs_from_gcloud.py
```

Скрипт получает логи за последние 10 минут и сохраняет их в файл `logs.log`.

### Настройка логов
1. Убедитесь, что файл `config/log-access.json` содержит правильный сервисный ключ
2. В `scripts/save_logs_from_gcloud.py` настройте:
   - `PROJECT_ID` - ID вашего Google Cloud проекта
   - `SERVICE_NAME` - имя Cloud Run сервиса
   - `minutes_back` - количество минут для получения логов

## 🔧 Конфигурация

### Переменные окружения
- `DEV_MODE` - режим разработки (очистка базы при запуске)
- `GEMINI_API_KEY` - ключ для Gemini AI
- `LINE_ACCESS_TOKEN` - токен для LINE API
- `WHATSAPP_TOKEN` - токен для WhatsApp Business API

### Токены и ключи
Все токены и ключи хранятся в `src/config.py`. Для продакшена рекомендуется использовать переменные окружения или секреты Google Cloud.

## 📱 Интеграции

### WhatsApp Business API
- Webhook для получения сообщений
- Отправка каталога товаров
- Обработка заказов

### LINE API
- Отправка уведомлений о заказах в групповой чат
- Получение информации о пользователях

### Google Cloud
- Firestore для хранения диалогов
- Cloud Run для развертывания
- Cloud Logging для логов

### Gemini AI
- Генерация ответов на сообщения пользователей
- Обработка контекста диалога

## 🧪 Тестирование

### Запуск всех тестов
```bash
python tests/run_tests.py
```

### Запуск отдельных тестов
```bash
# Быстрый тест работоспособности
python tests/test_quick.py

# Тест активного диалога AI
python tests/test_active_dialog.py

# Полный тест диалога с заказом
python tests/test_full_dialog.py
```

### Документация по тестированию
Подробная информация о тестах находится в `tests/README.md`

## 🔍 Мониторинг

### Проверка статуса
- URL сервиса: `https://auraflora-bot-75152239022-as.a.run.app`
- Health check: `/health`
- Логи: через `scripts/save_logs_from_gcloud.py`

### Отладка
- Логи сохраняются в Firestore
- Подробные логи в Google Cloud Logging

## 📝 Примечания

1. **Безопасность**: Все токены и ключи должны быть защищены в продакшене
2. **Масштабирование**: Сервис настроен на максимум 10 инстансов
3. **Логи**: Рекомендуется настроить автоматическое получение логов
4. **Резервное копирование**: Регулярно делайте бэкапы базы данных Firestore

## 🆘 Поддержка

При возникновении проблем:
1. Проверьте логи через `scripts/save_logs_from_gcloud.py`
2. Убедитесь, что все токены актуальны
3. Проверьте статус Google Cloud сервисов 
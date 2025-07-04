"""
AuraFlora WhatsApp Bot - Основная логика обработки сообщений
============================================================

Этот файл содержит всю основную логику обработки сообщений от пользователей WhatsApp.
Читая этот файл, вы поймете полный flow обработки сообщений:

1. Получение webhook от WhatsApp
2. Извлечение данных из сообщения
3. Управление сессиями пользователей
4. Сохранение сообщений в базу данных
5. Генерация ответов с помощью AI (Gemini)
6. Интеграция с каталогом товаров
7. Отправка ответов обратно в WhatsApp

Основные компоненты:
- SessionService: управление сессиями пользователей
- MessageService: сохранение и получение истории сообщений
- AIService: генерация ответов с помощью Google Gemini
- CatalogService: работа с каталогом товаров WhatsApp
- WhatsAppClient: отправка сообщений в WhatsApp
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Any, Optional

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
from src.utils.logging_utils import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

# ============================================================================
# ИМПОРТ СЕРВИСОВ И КОМПОНЕНТОВ
# ============================================================================

from src.services.session_service import SessionService
from src.services.message_service import MessageService
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.services.command_service import CommandService
from src.utils.whatsapp_client import WhatsAppClient
from src.models.message import Message, MessageRole
from src.utils.logging_utils import ContextLogger
from src.config import VERIFY_TOKEN, GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

# Инициализация всех сервисов
session_service = SessionService()
message_service = MessageService()
ai_service = AIService(GEMINI_API_KEY)
catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
command_service = CommandService()
whatsapp_client = WhatsAppClient()
webhook_logger = ContextLogger("webhook_flow")

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ИЗВЛЕЧЕНИЯ ДАННЫХ ИЗ WEBHOOK
# ============================================================================

def extract_sender_id(body: dict) -> Optional[str]:
    """
    Извлекает ID отправителя из webhook WhatsApp.
    
    WhatsApp отправляет webhook в формате:
    {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"wa_id": "1234567890"}],
                    "messages": [...]
                }
            }]
        }]
    }
    """
    try:
        return body['entry'][0]['changes'][0]['value']['contacts'][0]['wa_id']
    except (KeyError, IndexError):
        webhook_logger.warning("Не удалось извлечь sender_id из webhook")
        return None

def extract_sender_name(body: dict) -> Optional[str]:
    """
    Извлекает имя отправителя из webhook WhatsApp.
    
    Имя приходит в формате:
    {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{
                        "profile": {"name": "Иван Иванов"}
                    }]
                }
            }]
        }]
    }
    """
    try:
        profile = body['entry'][0]['changes'][0]['value']['contacts'][0]['profile']
        full_name = profile.get('name', '')
        
        # Берем только первое имя (до первого пробела)
        if full_name:
            first_name = full_name.split()[0]
            webhook_logger.info(f"[SENDER_NAME] Извлечено имя: {first_name}")
            return first_name
        return None
    except (KeyError, IndexError):
        webhook_logger.warning("Не удалось извлечь имя отправителя из webhook")
        return None

def extract_message_text(body: dict) -> Optional[str]:
    """
    Извлекает текст сообщения из webhook.
    
    Текстовые сообщения приходят в формате:
    {
        "messages": [{
            "text": {"body": "Привет, как дела?"}
        }]
    }
    """
    try:
        return body['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
    except (KeyError, IndexError):
        return None

def extract_interactive_message(body: dict) -> Optional[Dict[str, Any]]:
    """
    Извлекает интерактивное сообщение (кнопки, каталог товаров).
    
    Интерактивные сообщения приходят в формате:
    {
        "messages": [{
            "interactive": {
                "type": "button" | "catalog_message",
                "button_reply": {"id": "button_id"},
                "catalog_message": {...}
            }
        }]
    }
    """
    try:
        message = body['entry'][0]['changes'][0]['value']['messages'][0]
        if 'interactive' in message:
            return message['interactive']
        return None
    except (KeyError, IndexError):
        return None

# ============================================================================
# ОСНОВНАЯ ЛОГИКА ОБРАБОТКИ СООБЩЕНИЙ
# ============================================================================

async def process_text_message(sender_id: str, message_text: str, sender_name: str = None) -> str:
    """
    Обрабатывает текстовое сообщение от пользователя.
    
    Flow обработки:
    1. Создаем/получаем сессию пользователя
    2. Проверяем специальные команды (/newses)
    3. Сохраняем сообщение пользователя в базу
    4. Получаем историю диалога для контекста
    5. Определяем язык пользователя
    6. Генерируем ответ с помощью AI с полным промптом
    7. Сохраняем ответ AI в базу
    8. Обрабатываем команды (каталог, заказы)
    9. Отправляем ответ в WhatsApp
    
    Args:
        sender_id: ID пользователя WhatsApp
        message_text: Текст сообщения пользователя
        sender_name: Имя пользователя (опционально)
        
    Returns:
        str: Ответ AI для отправки пользователю
    """
    webhook_logger.info(f"[TEXT_MESSAGE] Обработка текстового сообщения от {sender_id} (имя: {sender_name})")
    
    # 1. Создаем или получаем сессию пользователя
    session_id = await session_service.get_or_create_session_id(sender_id)
    webhook_logger.info(f"[SESSION] Сессия: {session_id}")
    
    # 2. Проверяем специальные команды
    if message_text.strip().lower() == '/newses':
        webhook_logger.info(f"[NEWSES] Обработка команды /newses для {sender_id}")
        
        # Создаем новую сессию
        new_session_id = await session_service.create_new_session_after_order(sender_id)
        webhook_logger.info(f"[NEWSES] Создана новая сессия: {new_session_id}")
        
        # Отправляем подтверждение (НЕ сохраняем в БД)
        confirmation_message = f"✅ Новая сессия создана! ID: {new_session_id}\n\nТеперь вы можете начать новый диалог. 🌸"
        
        # Сохраняем только сообщение пользователя в старую сессию
        user_message = Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.USER,
            content=message_text
        )
        await message_service.add_message_to_conversation(user_message)
        webhook_logger.info(f"[NEWSES] Сообщение пользователя сохранено в старую сессию")
        
        # НЕ сохраняем ответ AI в БД - только возвращаем для отправки
        webhook_logger.info(f"[NEWSES] Ответ AI НЕ сохраняется в БД, только отправляется пользователю")
        
        return confirmation_message
    
    # 3. Определяем язык пользователя и переводим сообщение
    user_lang = ai_service.detect_language(message_text)
    webhook_logger.info(f"[LANGUAGE] Определен язык: {user_lang}")
    
    # Переводим сообщение пользователя на все языки
    text, text_en, text_thai = ai_service.translate_user_message(message_text, user_lang)
    webhook_logger.info(f"[TRANSLATE] Сообщение пользователя переведено на все языки")
    
    # Сохраняем имя пользователя в коллекцию users если есть
    if sender_name:
        await session_service.save_user_info(sender_id, sender_name)
        webhook_logger.info(f"[USER_INFO] Имя пользователя сохранено: {sender_name}")
    
    # Сохраняем сообщение пользователя в базу данных с переводами
    user_message = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.USER,
        content=text,
        content_en=text_en,
        content_thai=text_thai
    )
    await message_service.add_message_to_conversation(user_message)
    webhook_logger.info(f"[DB] Сообщение пользователя сохранено с переводами")
    
    # 4. Получаем историю диалога для контекста AI
    # Берем последние 10 сообщений для контекста
    conversation_history = await message_service.get_conversation_history_for_ai_by_sender(sender_id, session_id, limit=10)
    webhook_logger.info(f"[HISTORY] Получено {len(conversation_history)} сообщений из истории")
    
    # Конвертируем словари в объекты Message для AI
    ai_messages = []
    for msg_dict in conversation_history:
        message = Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.USER if msg_dict.get('role') == 'user' else MessageRole.ASSISTANT,
            content=msg_dict.get('content', ''),
            content_en=msg_dict.get('content_en'),
            content_thai=msg_dict.get('content_thai')
        )
        ai_messages.append(message)
    
    # 5. Генерируем ответ с помощью AI (Google Gemini) с полным промптом
    ai_response_text = await ai_service.generate_response(
        ai_messages,  # Теперь передаем список объектов Message
        user_lang=user_lang,
        sender_name=sender_name  # Передаем реальное имя пользователя
    )
    webhook_logger.info(f"[AI] Сгенерирован ответ длиной {len(ai_response_text)} символов")
    
    # 6. Парсим ответ AI для поиска команд и переводов
    ai_text, ai_text_en, ai_text_thai, ai_command = ai_service.parse_ai_response(ai_response_text)
    
    # 7. Сохраняем ответ AI в базу данных с переводами
    ai_message = Message(
        sender_id=sender_id,
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=ai_text,
        content_en=ai_text_en,
        content_thai=ai_text_thai
    )
    await message_service.add_message_to_conversation(ai_message)
    webhook_logger.info(f"[DB] Ответ AI сохранен с переводами")
    
    # 8. Обрабатываем команды (если AI вернул команду)
    
    if ai_command:
        webhook_logger.info(f"[COMMAND] Найдена команда: {ai_command}")
        
        # Обрабатываем команду send_catalog
        if ai_command.get('type') == 'send_catalog':
            webhook_logger.info(f"[CATALOG] Отправляем каталог пользователю {sender_id}")
            try:
                from src.catalog_sender import handle_send_catalog
                await handle_send_catalog(sender_id, sender_id, session_id)
                webhook_logger.info(f"[CATALOG] Каталог отправлен успешно")
            except Exception as e:
                webhook_logger.error(f"[CATALOG_ERROR] Ошибка отправки каталога: {e}")
        
        # TODO: Добавить обработку других команд save_order_info, confirm_order
    
    return ai_text if ai_text else ai_response_text

async def process_interactive_message(sender_id: str, interactive_data: Dict[str, Any]) -> str:
    """
    Обрабатывает интерактивные сообщения (кнопки, каталог товаров).
    
    Типы интерактивных сообщений:
    - button: нажатие кнопки
    - catalog_message: выбор товара из каталога
    - list_reply: выбор из списка
    
    Args:
        sender_id: ID пользователя WhatsApp
        interactive_data: Данные интерактивного сообщения
        
    Returns:
        str: Ответ для отправки пользователю
    """
    interactive_type = interactive_data.get('type')
    webhook_logger.info(f"[INTERACTIVE] Обработка {interactive_type} от {sender_id}")
    
    if interactive_type == 'button':
        # Обработка нажатия кнопки
        button_id = interactive_data.get('button_reply', {}).get('id')
        webhook_logger.info(f"[BUTTON] Нажата кнопка: {button_id}")
        
        # Здесь можно добавить логику для разных кнопок
        if button_id == 'catalog':
            return "Вот наш каталог товаров! 🌸"
        elif button_id == 'help':
            return "Чем могу помочь? 🌸"
        else:
            return "Спасибо за выбор! 🌸"
    
    elif interactive_type == 'catalog_message':
        # Обработка выбора товара из каталога
        catalog_data = interactive_data.get('catalog_message', {})
        retailer_id = catalog_data.get('retailer_id')  # Используем retailer_id
        webhook_logger.info(f"[CATALOG] Выбран товар: {retailer_id}")
        
        # Валидируем товар в каталоге
        validation = await catalog_service.validate_product(retailer_id)
        if validation['valid']:
            product = validation['product']
            return f"Отличный выбор! {product.get('name')} - {product.get('price')} 🌸"
        else:
            return "Извините, этот товар временно недоступен 🌸"
    
    else:
        webhook_logger.warning(f"[INTERACTIVE] Неизвестный тип: {interactive_type}")
        return "Спасибо за взаимодействие! 🌸"

async def handle_webhook_message(sender_id: str, body: dict) -> str:
    """
    Главная функция обработки webhook сообщений.
    
    Определяет тип сообщения и направляет в соответствующую функцию обработки.
    
    Args:
        sender_id: ID пользователя WhatsApp
        body: Тело webhook от WhatsApp
        
    Returns:
        str: Ответ для отправки пользователю
    """
    webhook_logger.info(f"[WEBHOOK] Обработка сообщения от {sender_id}")
    
    # Извлекаем имя пользователя
    sender_name = extract_sender_name(body)
    if sender_name:
        webhook_logger.info(f"[WEBHOOK] Имя пользователя: {sender_name}")
    
    # Проверяем тип сообщения
    message_text = extract_message_text(body)
    interactive_message = extract_interactive_message(body)
    
    if message_text:
        # Текстовое сообщение
        return await process_text_message(sender_id, message_text, sender_name)
    
    elif interactive_message:
        # Интерактивное сообщение
        return await process_interactive_message(sender_id, interactive_message)
    
    else:
        # Неизвестный тип сообщения
        webhook_logger.warning(f"[WEBHOOK] Неизвестный тип сообщения от {sender_id}")
        return "Извините, не понимаю этот тип сообщения 🌸"

# ============================================================================
# FASTAPI ПРИЛОЖЕНИЕ
# ============================================================================

# Контекстный менеджер для жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    logger.info("🚀 AuraFlora Bot запускается...")
    yield
    logger.info("🛑 AuraFlora Bot останавливается...")

# Создаем приложение FastAPI
app = FastAPI(
    title="AuraFlora WhatsApp Bot",
    description="AI-бот для обработки сообщений WhatsApp с интеграцией каталога товаров",
    version="1.0.0",
    lifespan=lifespan
)

# CORS только для DEV_MODE
if os.getenv('DEV_MODE', 'false').lower() == 'true':
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Верификация webhook от Meta/WhatsApp.
    
    WhatsApp требует верификации webhook для подтверждения подлинности.
    Отправляет GET запрос с параметрами:
    - hub.mode: "subscribe"
    - hub.verify_token: наш токен
    - hub.challenge: строка для ответа
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        webhook_logger.info("[VERIFY] Webhook успешно верифицирован")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        webhook_logger.error("[VERIFY] Ошибка верификации webhook")
        return Response(content="Failed to verify webhook", status_code=403)

@app.post("/webhook")
async def webhook_handler(request: Request):
    """
    Основной обработчик webhook от WhatsApp.
    
    Получает все сообщения от пользователей и обрабатывает их.
    
    Flow:
    1. Получаем webhook от WhatsApp
    2. Извлекаем данные (sender_id, тип сообщения)
    3. Обрабатываем сообщение через handle_webhook_message
    4. Отправляем ответ обратно в WhatsApp
    5. Логируем результат
    """
    try:
        # Получаем тело webhook
        body = await request.json()
        webhook_logger.info("[WEBHOOK_START] ==================== WEBHOOK RECEIVED ====================")
        
        # Проверяем, что это webhook от WhatsApp Business API
        if not body.get("object") == "whatsapp_business_account":
            webhook_logger.info("[WEBHOOK_INVALID] Invalid WhatsApp message, ignoring")
            return JSONResponse({"status": "ignored"})
        
        # Извлекаем ID отправителя
        sender_id = extract_sender_id(body)
        if not sender_id:
            webhook_logger.warning("[WEBHOOK] Не удалось извлечь sender_id")
            return JSONResponse({"status": "no_sender"})
        
        webhook_logger.info(f"[WEBHOOK_CALLER] webhook_handlers.py:webhook_handler:198")
        
        # Обрабатываем сообщение и получаем ответ
        response_text = await handle_webhook_message(sender_id, body)
        
        # Отправляем ответ через WhatsApp
        message_id = await whatsapp_client.send_text_message(sender_id, response_text)
        
        if message_id:
            webhook_logger.info(f"[WHATSAPP] Ответ отправлен, message_id: {message_id}")
        else:
            webhook_logger.error(f"[WHATSAPP] Ошибка отправки ответа")
        
        webhook_logger.info(f"[WEBHOOK_END] Обработка завершена для {sender_id}")
        return JSONResponse({"status": "success"})
        
    except Exception as e:
        webhook_logger.error(f"[WEBHOOK_ERROR] Ошибка обработки webhook: {e}")
        return JSONResponse({"status": "error"}, status_code=500)

# ============================================================================
# ОСНОВНЫЕ ENDPOINTS
# ============================================================================

@app.get("/", summary="Корневой эндпоинт")
async def root():
    """Корневой эндпоинт для проверки работы сервиса"""
    return {
        "status": "AuraFlora Bot is running",
        "service": "WhatsApp AI Bot",
        "version": "1.0.0",
        "features": [
            "AI-powered responses (Google Gemini)",
            "WhatsApp Business API integration",
            "Product catalog integration",
            "Session management",
            "Message history"
        ]
    }

@app.get("/health", summary="Проверка состояния")
async def health_check():
    """Health check для мониторинга состояния сервиса"""
    try:
        return {
            "status": "healthy",
            "service": "AuraFlora WhatsApp Bot",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "ai_service": "✅",
                "whatsapp_client": "✅",
                "catalog_service": "✅",
                "database": "✅"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "AuraFlora WhatsApp Bot"
        }

# ============================================================================
# ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS
# ============================================================================

# Debug интерфейс только для DEV_MODE
if os.getenv('DEV_MODE', 'false').lower() == 'true':
    from src.debug.debug_interface import setup_debug_routes
    setup_debug_routes(app)

# ============================================================================
# ЗАПУСК СЕРВЕРА
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8080))
    logger.info(f"🌐 Запуск сервера на порту {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 
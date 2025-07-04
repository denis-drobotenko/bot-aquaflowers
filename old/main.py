import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Optional
import re
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.webhook_handlers import router as webhook_router
from src.config import DEV_MODE, PORT
from src import database

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования (базовая)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище логов для debug интерфейса
debug_logs_storage = []

class DebugLogHandler(logging.Handler):
    """Собирает логи AI пайплайна для отладочного интерфейса"""
    
    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'logger_name': record.name,
                'level': record.levelname,
                'message': record.getMessage(),
                'session_id': self.extract_session_id(record.getMessage())
            }
            debug_logs_storage.append(log_entry)
            
            # Ограничиваем размер хранилища (последние 1000 записей)
            if len(debug_logs_storage) > 1000:
                debug_logs_storage.pop(0)
                
        except Exception:
            pass  # Игнорируем ошибки в логгере
    
    def extract_session_id(self, message: str) -> Optional[str]:
        """Извлекает session_id из сообщения лога"""
        patterns = [
            r'Session: ([^,\s]+)',
            r'session_id[=:\s]+([^,\s]+)',
            r'for session ([^,\s]+)',
            r'Session ID: ([^,\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        return None

# Настройка специальных логгеров для AI пайплайна
def setup_ai_pipeline_loggers():
    """Настраивает специальные логгеры для детального трейсинга AI пайплайна"""
    
    # Создаем formatter для детального логирования
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Создаем debug handler для сбора логов
    debug_handler = DebugLogHandler()
    
    # Настройка логгера для AI pipeline
    ai_pipeline_logger = logging.getLogger('ai_pipeline')
    ai_pipeline_logger.setLevel(logging.INFO)
    ai_handler = logging.StreamHandler()
    ai_handler.setFormatter(detailed_formatter)
    ai_pipeline_logger.addHandler(ai_handler)
    ai_pipeline_logger.addHandler(debug_handler)  # Добавляем debug handler
    ai_pipeline_logger.propagate = False  # Не дублируем в root logger
    
    # Настройка логгера для JSON processor
    json_processor_logger = logging.getLogger('json_processor')
    json_processor_logger.setLevel(logging.INFO)
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(detailed_formatter)
    json_processor_logger.addHandler(json_handler)
    json_processor_logger.addHandler(debug_handler)
    json_processor_logger.propagate = False
    
    # Настройка логгера для command handler
    command_logger = logging.getLogger('command_handler')
    command_logger.setLevel(logging.INFO)
    command_handler = logging.StreamHandler()
    command_handler.setFormatter(detailed_formatter)
    command_logger.addHandler(command_handler)
    command_logger.addHandler(debug_handler)
    command_logger.propagate = False
    
    # Настройка логгера для WhatsApp utils
    whatsapp_logger = logging.getLogger('whatsapp_utils')
    whatsapp_logger.setLevel(logging.INFO)
    whatsapp_handler = logging.StreamHandler()
    whatsapp_handler.setFormatter(detailed_formatter)
    whatsapp_logger.addHandler(whatsapp_handler)
    whatsapp_logger.addHandler(debug_handler)
    whatsapp_logger.propagate = False
    
    # Настройка логгера для webhook flow
    webhook_logger = logging.getLogger('webhook_flow')
    webhook_logger.setLevel(logging.INFO)
    webhook_handler = logging.StreamHandler()
    webhook_handler.setFormatter(detailed_formatter)
    webhook_logger.addHandler(webhook_handler)
    webhook_logger.addHandler(debug_handler)
    webhook_logger.propagate = False
    
    print("🔍 AI Pipeline loggers configured:")
    print("   - ai_pipeline: AI requests, responses, and processing")
    print("   - json_processor: JSON parsing, fixing, and extraction")
    print("   - command_handler: Command execution and results")
    print("   - whatsapp_utils: WhatsApp API calls and message sending")
    print("   - webhook_flow: Complete webhook processing flow")
    print("   - Debug interface: http://localhost:{}/debug".format(PORT))

# Контекстный менеджер Lifespan должен быть определен ПЕРЕД его использованием
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Контекстный менеджер для инициализации и очистки ресурсов при старте и остановке приложения.
    """
    logger.info("Application startup.")
    setup_ai_pipeline_loggers()
    yield
    logger.info("Application shutdown.")

# Теперь создаем приложение FastAPI
app = FastAPI(
    title="AuraFlora WhatsApp Bot",
    description="API для обработки сообщений от WhatsApp и интеграции с Gemini.",
    version="1.0.0",
    lifespan=lifespan
)

# Добавляем CORS middleware для debug интерфейса
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

@app.get("/", summary="Корневой эндпоинт", description="Простой эндпоинт для проверки, что сервис работает.")
async def root():
    """Простой эндпоинт для проверки, что сервис работает."""
    return {"status": "AuraFlora Bot is running"}

@app.get("/health", summary="Проверка состояния", description="Проверка состояния сервиса и подключений.")
async def health_check():
    """Проверка состояния сервиса."""
    try:
        # Здесь можно добавить проверки подключений к базе данных и другим сервисам
        return {
            "status": "healthy",
            "service": "AuraFlora WhatsApp Bot",
            "version": "1.0.0",
            "timestamp": "2024-12-19T10:00:00Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "AuraFlora WhatsApp Bot"
        }

# Подключаем роутер с webhook'ами
app.include_router(webhook_router)

# Debug интерфейс для просмотра диалогов
@app.get("/debug", response_class=HTMLResponse)
async def debug_interface(request: Request):
    """Интерфейс отладки диалогов"""
    return templates.TemplateResponse("debug_interface.html", {"request": request})

@app.get("/debug/api/sessions")
async def debug_get_sessions():
    """API для получения списка активных сессий из логов"""
    try:
        sessions = {}
        
        # Анализируем логи для извлечения информации о сессиях
        for log_entry in debug_logs_storage:
            session_id = log_entry.get('session_id')
            if not session_id:
                continue
                
            if session_id not in sessions:
                sender_id = session_id.split('_')[0] if '_' in session_id else session_id
                sessions[session_id] = {
                    'session_id': session_id,
                    'sender_id': sender_id,
                    'message_count': 0,
                    'last_message_time': log_entry.get('timestamp'),
                    'first_seen': log_entry.get('timestamp')
                }
            
            # Подсчитываем сообщения по webhook_flow логам
            if 'WEBHOOK_INPUT' in log_entry.get('message', '') or 'Получено сообщение' in log_entry.get('message', ''):
                sessions[session_id]['message_count'] += 1
            
            # Обновляем время последней активности
            if log_entry.get('timestamp') > sessions[session_id]['last_message_time']:
                sessions[session_id]['last_message_time'] = log_entry.get('timestamp')
        
        # Сортируем по времени последней активности
        sessions_list = list(sessions.values())
        sessions_list.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        return JSONResponse(content=sessions_list)
        
    except Exception as e:
        logger.error(f"Error getting sessions from logs: {e}")
        return JSONResponse(content=[])

@app.get("/debug/api/session/{session_id}/messages")
async def debug_get_session_messages(session_id: str):
    """API для получения сообщений конкретной сессии из логов"""
    try:
        # Получаем все логи для этой сессии
        session_logs = [
            log for log in debug_logs_storage 
            if log.get('session_id') == session_id
        ]
        
        # Извлекаем сообщения из логов
        messages = []
        
        for log in session_logs:
            message = log.get('message', '')
            timestamp = log.get('timestamp')
            
            # Ищем входящие сообщения пользователя
            if 'WEBHOOK_INPUT' in message and 'Получено сообщение' in message:
                # Извлекаем текст сообщения из лога
                content = extract_user_message_from_log(message)
                if content:
                    messages.append({
                        'role': 'user',
                        'content': content,
                        'timestamp': timestamp
                    })
            
            # Ищем ответы бота
            elif 'MESSAGE_SEND_START' in message and 'Отправляем сообщение' in message:
                # Извлекаем текст ответа из лога
                content = extract_bot_response_from_log(message)
                if content:
                    messages.append({
                        'role': 'assistant', 
                        'content': content,
                        'timestamp': timestamp
                    })
        
        # Сортируем по времени
        messages.sort(key=lambda x: x['timestamp'])
        
        return JSONResponse(content={
            'messages': messages,
            'logs': session_logs
        })
        
    except Exception as e:
        logger.error(f"Error getting session messages from logs: {e}")
        return JSONResponse(content={'messages': [], 'logs': []})

def extract_user_message_from_log(log_message: str) -> str:
    """Извлекает текст сообщения пользователя из лога"""
    try:
        # Ищем паттерн: "text": "сообщение"
        import re
        pattern = r'"text":\s*"([^"]*)"'
        match = re.search(pattern, log_message)
        if match:
            return match.group(1)
            
        # Альтернативный паттерн
        pattern = r'Получено сообщение.*?:\s*(.+)'
        match = re.search(pattern, log_message)
        if match:
            return match.group(1).strip()
            
    except Exception:
        pass
    return ""

def extract_bot_response_from_log(log_message: str) -> str:
    """Извлекает текст ответа бота из лога"""
    try:
        # Ищем паттерн отправки сообщения
        import re
        pattern = r'Отправляем сообщение.*?:\s*(.+)'
        match = re.search(pattern, log_message)
        if match:
            return match.group(1).strip()
            
        # Ищем текст в JSON
        pattern = r'"text":\s*"([^"]*)"'
        match = re.search(pattern, log_message)
        if match:
            return match.group(1)
            
    except Exception:
        pass
    return ""

@app.get("/api/debug/logs")
async def export_debug_logs(period_min: int = 20):
    """API для экспорта debug логов за указанный период (для удаленного доступа)"""
    try:
        from scripts.save_logs_from_gcloud import get_logs_via_api
        
        print(f"🔍 [DEBUG_LOGS] Запрос логов за {period_min} минут...")
        
        # Скачиваем логи с сервера
        success, logs_data = get_logs_via_api(period_min)
        
        if not success:
            print(f"❌ [DEBUG_LOGS] Ошибка при скачивании логов")
            return JSONResponse(content={'logs': [], 'count': 0, 'error': 'Failed to download logs'})
        
        if not logs_data:
            print(f"⚠️ [DEBUG_LOGS] Получен пустой список логов")
            return JSONResponse(content={'logs': [], 'count': 0, 'error': 'Empty logs data'})
        
        # Сохраняем в файл для отладки
        import json
        with open('log.logs', 'w', encoding='utf-8') as f:
            json.dump(logs_data, f, ensure_ascii=False, indent=2)
        print(f"💾 [DEBUG_LOGS] Сохранено {len(logs_data)} логов в log.logs")
        
        return JSONResponse(content={
            'logs': logs_data,
            'count': len(logs_data),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"💥 [DEBUG_LOGS] Ошибка: {e}")
        logger.error(f"Error exporting debug logs: {e}")
        return JSONResponse(content={'logs': [], 'count': 0, 'error': str(e)})

@app.post("/api/save_fresh_logs")
async def save_fresh_logs(request: Request, logs: list = Body(...)):
    """Сохраняет переданные логи в файл fresh_logs.log"""
    try:
        with open("fresh_logs.log", "w", encoding="utf-8") as f:
            for log in logs:
                ts = log.get("timestamp", "")
                msg = log.get("textPayload") or log.get("message", "")
                f.write(f"[{ts}] {msg}\n")
        return {"status": "ok", "count": len(logs)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

# Раздача статики - только в самом конце!
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT) 
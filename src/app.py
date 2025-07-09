"""
Создание FastAPI приложения
"""

import os
import logging.config
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from src.routes.chat_routes import router as chat_router
from src.routes.healthcheck import router as healthcheck_router
from src.routes.crm_routes import router as crm_router
from src.routes.error_routes import router as error_router
from src.handlers.webhook_handler import WebhookHandler
from fastapi.responses import JSONResponse
from src.config.settings import DEBUG_MODE
from src.config.logging_config import LOGGING_CONFIG

# Применяем конфигурацию логирования
logging.config.dictConfig(LOGGING_CONFIG)

def create_app() -> FastAPI:
    """
    Создает и настраивает FastAPI приложение.
    Returns:
        FastAPI: Настроенное приложение
    """
    # Настраиваем шаблоны
    templates = Jinja2Templates(directory="templates")

    # Создаем приложение
    app = FastAPI(
        title="Aqua Flowers Bot API",
        description="WhatsApp Bot для цветочного магазина",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        debug=DEBUG_MODE
    )

    # Настраиваем CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Добавляем middleware для ngrok и кэширования
    @app.middleware("http")
    async def add_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        
        # Добавляем заголовки для статических файлов
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

    # Подключаем статические файлы стандартным способом
    try:
        app.mount("/static", StaticFiles(directory="static"), name="static")
        print("✅ Статические файлы подключены через StaticFiles")
    except Exception as e:
        print(f"⚠️ Ошибка подключения StaticFiles: {e}")
        
        # Fallback: кастомный обработчик статических файлов
        @app.get("/static/{path:path}")
        async def serve_static_files(path: str, request: Request):
            """Кастомный обработчик статических файлов с правильными заголовками"""
            file_path = f"static/{path}"
            print(f"📁 Запрос статического файла: {file_path}")
            
            if os.path.exists(file_path):
                print(f"✅ Файл найден: {file_path}")
                return FileResponse(
                    file_path,
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                        "ngrok-skip-browser-warning": "true"
                    }
                )
            else:
                print(f"❌ Файл не найден: {file_path}")
                return JSONResponse({"error": "File not found"}, status_code=404)

    # Подключаем роуты
    app.include_router(chat_router)
    app.include_router(healthcheck_router)
    app.include_router(crm_router)
    app.include_router(error_router)

    # Создаем экземпляр WebhookHandler
    webhook_handler = WebhookHandler()

    # Корневой роут для webhook (WhatsApp иногда обращается к /)
    @app.get("/")
    async def root_webhook(request: Request):
        """Корневой роут для webhook от WhatsApp"""
        try:
            params = dict(request.query_params)
            mode = params.get("hub.mode")
            challenge = params.get("hub.challenge")
            verify_token = params.get("hub.verify_token")
            
            if mode and challenge and verify_token:
                result = await webhook_handler.verify_webhook(mode, challenge, verify_token)
                if result.isdigit():
                    return PlainTextResponse(content=result)  # Возвращаем только challenge как plain text
                else:
                    return JSONResponse(content={"error": "Invalid token"}, status_code=int(result))
            else:
                # Перенаправляем на CRM вместо API сообщения
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url="/crm/")
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=403)

    # Webhook эндпоинты (заменяют webhook_routes.py)
    @app.get("/webhook")
    async def verify_webhook_no_slash(request: Request):
        """Верификация webhook от WhatsApp (без слеша)"""
        try:
            params = dict(request.query_params)
            mode = params.get("hub.mode")
            challenge = params.get("hub.challenge")
            verify_token = params.get("hub.verify_token")
            
            result = await webhook_handler.verify_webhook(mode, challenge, verify_token)
            if result.isdigit():
                return PlainTextResponse(content=result)  # Возвращаем только challenge как plain text
            else:
                return JSONResponse(content={"error": "Invalid token"}, status_code=int(result))
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=403)

    @app.get("/webhook/")
    async def verify_webhook(request: Request):
        """Верификация webhook от WhatsApp"""
        try:
            params = dict(request.query_params)
            mode = params.get("hub.mode")
            challenge = params.get("hub.challenge")
            verify_token = params.get("hub.verify_token")
            
            result = await webhook_handler.verify_webhook(mode, challenge, verify_token)
            if result.isdigit():
                return PlainTextResponse(content=result)  # Возвращаем только challenge как plain text
            else:
                return JSONResponse(content={"error": "Invalid token"}, status_code=int(result))
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=403)

    @app.post("/webhook")
    async def webhook_handler_route_no_slash(request: Request):
        """Обработчик webhook'ов от WhatsApp Business API (без слеша)"""
        try:
            body = await request.json()
            result = await webhook_handler.process_webhook(body)
            return JSONResponse(content=result)
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

    @app.post("/webhook/")
    async def webhook_handler_route(request: Request):
        """Обработчик webhook'ов от WhatsApp Business API"""
        try:
            body = await request.json()
            result = await webhook_handler.process_webhook(body)
            return JSONResponse(content=result)
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

    @app.get("/webhook/metrics")
    async def get_webhook_metrics():
        """Возвращает метрики обработки webhook'ов"""
        metrics = WebhookHandler.get_metrics()
        return JSONResponse(content=metrics, status_code=200)

    # Маршрут для лог-вьювера
    @app.get("/logs", response_class=HTMLResponse)
    async def log_viewer(request: Request):
        return templates.TemplateResponse("log_viewer.html", {"request": request})

    @app.get("/api/logs")
    async def get_logs():
        try:
            log_file = os.getenv("LOG_FILE", "logs/app.json")
            if not os.path.exists(log_file):
                return {"logs": [], "error": "Log file not found"}
            logs = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            import json
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            return {"logs": logs}
        except Exception as e:
            return {"logs": [], "error": str(e)}

    # Тестовый роут для проверки статических файлов
    @app.get("/test-static")
    async def test_static_files():
        """Тестовый роут для проверки доступности статических файлов"""
        files_to_check = [
            "static/css/chat_history.css",
            "static/js/chat_history.js"
        ]
        
        results = {}
        for file_path in files_to_check:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                results[file_path] = {
                    "exists": True,
                    "size": file_size,
                    "readable": os.access(file_path, os.R_OK)
                }
            else:
                results[file_path] = {
                    "exists": False,
                    "size": 0,
                    "readable": False
                }
        
        return JSONResponse(content={
            "static_files": results,
            "static_dir_exists": os.path.exists("static"),
            "static_dir_readable": os.access("static", os.R_OK) if os.path.exists("static") else False
        })

    return app

app = create_app() 
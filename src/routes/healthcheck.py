"""
Роуты для healthcheck API
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.config.settings import GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
from src.utils.logging_decorator import log_function
import asyncio
import os

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    """
    Базовый healthcheck - проверяет доступность сервиса.
    """
    return {"status": "healthy", "service": "auraflora-bot"}

@router.get("/ai")
async def ai_health_check():
    """
    Проверяет доступность AI сервиса (Google Gemini).
    """
    try:
        ai_service = AIService(GEMINI_API_KEY)
        
        # Тестируем простой запрос к AI
        test_response = await ai_service.generate_response(
            messages=[],
            user_lang="ru",
            sender_name="Test User"
        )
        
        if test_response and len(test_response) >= 3:
            return {
                "status": "healthy",
                "service": "ai",
                "provider": "google-gemini",
                "response_length": len(test_response[0]) if test_response[0] else 0
            }
        else:
            return {
                "status": "unhealthy",
                "service": "ai",
                "error": "Invalid AI response format"
            }
            
    except Exception as e:
        print(f"[HEALTH_AI_ERROR] Ошибка проверки AI: {e}")
        return {
            "status": "unhealthy",
            "service": "ai",
            "error": str(e)
        }

@router.get("/catalog")
async def catalog_health_check():
    """
    Проверяет доступность каталога товаров.
    """
    try:
        print(f"[HEALTH_CATALOG] Начинаем проверку каталога...")
        print(f"[HEALTH_CATALOG] CATALOG_ID: {WHATSAPP_CATALOG_ID}")
        print(f"[HEALTH_CATALOG] TOKEN: {WHATSAPP_TOKEN[:20] if WHATSAPP_TOKEN else 'None'}...")
        
        # Проверяем переменные окружения
        if not WHATSAPP_CATALOG_ID:
            print(f"[HEALTH_CATALOG_ERROR] WHATSAPP_CATALOG_ID не установлен")
            return {
                "status": "unhealthy",
                "service": "catalog",
                "error": "WHATSAPP_CATALOG_ID not set"
            }
        
        if not WHATSAPP_TOKEN:
            print(f"[HEALTH_CATALOG_ERROR] WHATSAPP_TOKEN не установлен")
            return {
                "status": "unhealthy",
                "service": "catalog",
                "error": "WHATSAPP_TOKEN not set"
            }
        
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        
        # Получаем список товаров (синхронный метод)
        print(f"[HEALTH_CATALOG] Вызываем get_products()...")
        products = catalog_service.get_products()
        print(f"[HEALTH_CATALOG] Получено товаров: {len(products) if products else 0}")
        
        if products and len(products) > 0:
            print(f"[HEALTH_CATALOG] ✅ Каталог работает, найдено {len(products)} товаров")
            return {
                "status": "healthy",
                "service": "catalog",
                "products_count": len(products),
                "catalog_id": WHATSAPP_CATALOG_ID
            }
        else:
            print(f"[HEALTH_CATALOG] ❌ Каталог пуст или не работает")
            return {
                "status": "unhealthy",
                "service": "catalog",
                "error": "No products found"
            }
            
    except Exception as e:
        print(f"[HEALTH_CATALOG_ERROR] Ошибка проверки каталога: {e}")
        print(f"[HEALTH_CATALOG_ERROR] Тип ошибки: {type(e).__name__}")
        return {
            "status": "unhealthy",
            "service": "catalog",
            "error": str(e)
        }

@router.get("/files")
async def files_health_check():
    """
    Проверяет доступность важных файлов (промпты, шаблоны, статика).
    """
    try:
        print(f"[HEALTH_FILES] Начинаем проверку файлов...")
        
        # Список важных файлов для проверки
        important_files = [
            "src/services/prompts/ai_system_prompt.prompt",
            "templates/crm_dashboard.html",
            "templates/chat_history.html",
            "static/css/chat_history.css",
            "static/js/chat_history.js"
        ]
        
        files_status = {}
        all_files_exist = True
        
        for file_path in important_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                is_readable = os.access(file_path, os.R_OK)
                
                files_status[file_path] = {
                    "exists": True,
                    "size": file_size,
                    "readable": is_readable,
                    "status": "healthy" if is_readable else "unreadable"
                }
                
                if not is_readable:
                    all_files_exist = False
                    
                print(f"[HEALTH_FILES] ✅ {file_path}: {file_size} bytes, readable: {is_readable}")
            else:
                files_status[file_path] = {
                    "exists": False,
                    "size": 0,
                    "readable": False,
                    "status": "missing"
                }
                all_files_exist = False
                print(f"[HEALTH_FILES] ❌ {file_path}: файл не найден")
        
        # Проверяем директории
        directories = ["static", "templates", "src/services/prompts"]
        dir_status = {}
        
        for dir_path in directories:
            if os.path.exists(dir_path):
                is_readable = os.access(dir_path, os.R_OK)
                dir_status[dir_path] = {
                    "exists": True,
                    "readable": is_readable,
                    "status": "healthy" if is_readable else "unreadable"
                }
                print(f"[HEALTH_FILES] ✅ Директория {dir_path}: readable: {is_readable}")
            else:
                dir_status[dir_path] = {
                    "exists": False,
                    "readable": False,
                    "status": "missing"
                }
                all_files_exist = False
                print(f"[HEALTH_FILES] ❌ Директория {dir_path}: не найдена")
        
        if all_files_exist:
            print(f"[HEALTH_FILES] ✅ Все файлы доступны")
            return {
                "status": "healthy",
                "service": "files",
                "files": files_status,
                "directories": dir_status,
                "summary": "All important files are accessible"
            }
        else:
            print(f"[HEALTH_FILES] ❌ Некоторые файлы недоступны")
            return {
                "status": "unhealthy",
                "service": "files",
                "files": files_status,
                "directories": dir_status,
                "summary": "Some important files are missing or unreadable"
            }
            
    except Exception as e:
        print(f"[HEALTH_FILES_ERROR] Ошибка проверки файлов: {e}")
        return {
            "status": "unhealthy",
            "service": "files",
            "error": str(e)
        }

@router.get("/full")
async def full_health_check():
    """
    Полная проверка всех сервисов.
    """
    try:
        # Запускаем проверки (все асинхронные)
        ai_result = await ai_health_check()
        catalog_result = await catalog_health_check()
        files_result = await files_health_check()
        
        # Определяем общий статус
        all_healthy = (
            ai_result.get("status") == "healthy" and
            catalog_result.get("status") == "healthy" and
            files_result.get("status") == "healthy"
        )
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "service": "auraflora-bot",
            "checks": {
                "ai": ai_result,
                "catalog": catalog_result,
                "files": files_result
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        print(f"[HEALTH_FULL_ERROR] Ошибка полной проверки: {e}")
        return {
            "status": "unhealthy",
            "service": "auraflora-bot",
            "error": str(e)
        } 
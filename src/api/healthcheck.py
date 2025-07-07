from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.catalog_service import CatalogService
from utils.whatsapp_client import WhatsAppClient
from services.session_service import SessionService
from config.settings import LINE_ACCESS_TOKEN, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
import httpx

router = APIRouter()

@router.get("/health/full", summary="Полная проверка состояния")
async def full_health_check():
    results = {}

    # Проверка Firestore
    try:
        session_service = SessionService()
        test = await session_service.get_user_info("healthcheck_test")
        results["firestore"] = "ok"
    except Exception as e:
        results["firestore"] = f"error: {e}"

    # Проверка WABA (WhatsApp)
    try:
        whatsapp_client = WhatsAppClient()
        # Проверяем, что клиент инициализирован корректно
        if whatsapp_client.token and whatsapp_client.phone_id:
            results["waba"] = "ok"
        else:
            results["waba"] = "error: missing token or phone_id"
    except Exception as e:
        results["waba"] = f"error: {e}"

    # Проверка LINE
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.line.me/v2/bot/info", headers={
                "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
            })
            results["line"] = "ok" if resp.status_code == 200 else f"error: {resp.text}"
    except Exception as e:
        results["line"] = f"error: {e}"

    # Проверка каталога WABA
    try:
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        products = await catalog_service.get_catalog_products()
        results["catalog"] = "ok" if products else "empty"
    except Exception as e:
        results["catalog"] = f"error: {e}"

    # Итоговый статус
    results["status"] = "ok" if all(v == "ok" or v == "empty" for v in results.values()) else "error"
    return JSONResponse(results) 
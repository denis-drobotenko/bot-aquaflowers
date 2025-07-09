from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from src.services.error_service import ErrorService
from src.models.error import ErrorStatus, ErrorSeverity

router = APIRouter()
templates = Jinja2Templates(directory="templates")
error_service = ErrorService()


@router.get("/errors", response_class=HTMLResponse)
async def errors_page(request: Request):
    """Страница со списком ошибок"""
    try:
        # Получаем параметры фильтрации
        status_filter = request.query_params.get('status', 'all')
        severity_filter = request.query_params.get('severity', 'all')
        limit = int(request.query_params.get('limit', '50'))
        
        # Получаем ошибки в зависимости от фильтров
        if status_filter != 'all':
            status = ErrorStatus(status_filter)
            errors = await error_service.get_errors_by_status(status, limit)
        elif severity_filter != 'all':
            severity = ErrorSeverity(severity_filter)
            errors = await error_service.get_errors_by_severity(severity, limit)
        else:
            errors = await error_service.get_recent_errors(24, limit)
        
        # Получаем статистику
        stats = await error_service.get_error_stats()
        
        return templates.TemplateResponse("errors.html", {
            "request": request,
            "errors": errors,
            "stats": stats,
            "status_filter": status_filter,
            "severity_filter": severity_filter,
            "limit": limit
        })
        
    except Exception as e:
        print(f"[ERROR_ROUTES] Error loading errors page: {e}")
        raise HTTPException(status_code=500, detail="Error loading errors page")


@router.get("/errors/{error_id}", response_class=HTMLResponse)
async def error_details_page(request: Request, error_id: str):
    """Страница с деталями ошибки"""
    try:
        error = await error_service.get_error(error_id)
        if not error:
            raise HTTPException(status_code=404, detail="Error not found")
        
        return templates.TemplateResponse("error_details.html", {
            "request": request,
            "error": error
        })
        
    except Exception as e:
        print(f"[ERROR_ROUTES] Error loading error details: {e}")
        raise HTTPException(status_code=500, detail="Error loading error details")


@router.post("/errors/{error_id}/status")
async def update_error_status(error_id: str, status: str, resolved_by: Optional[str] = None, notes: Optional[str] = None):
    """Обновляет статус ошибки"""
    try:
        error_status = ErrorStatus(status)
        success = await error_service.update_error_status(error_id, error_status, resolved_by, notes)
        
        if success:
            return {"status": "success", "message": "Error status updated"}
        else:
            raise HTTPException(status_code=404, detail="Error not found")
            
    except Exception as e:
        print(f"[ERROR_ROUTES] Error updating error status: {e}")
        raise HTTPException(status_code=500, detail="Error updating error status")


@router.delete("/errors/{error_id}")
async def delete_error(error_id: str):
    """Удаляет ошибку"""
    try:
        success = await error_service.delete_error(error_id)
        
        if success:
            return {"status": "success", "message": "Error deleted"}
        else:
            raise HTTPException(status_code=404, detail="Error not found")
            
    except Exception as e:
        print(f"[ERROR_ROUTES] Error deleting error: {e}")
        raise HTTPException(status_code=500, detail="Error deleting error")


@router.get("/api/errors")
async def get_errors_api(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50
):
    """API для получения ошибок"""
    try:
        if status:
            status_enum = ErrorStatus(status)
            errors = await error_service.get_errors_by_status(status_enum, limit)
        elif severity:
            severity_enum = ErrorSeverity(severity)
            errors = await error_service.get_errors_by_severity(severity_enum, limit)
        else:
            errors = await error_service.get_recent_errors(24, limit)
        
        # Преобразуем в словари для JSON
        errors_data = []
        for error in errors:
            error_dict = error.to_dict()
            errors_data.append(error_dict)
        
        print(f"[ERROR_ROUTES] API returning {len(errors_data)} errors")
        return errors_data  # Возвращаем массив напрямую, а не в объекте
        
    except Exception as e:
        print(f"[ERROR_ROUTES] API error: {e}")
        raise HTTPException(status_code=500, detail="Error getting errors")


@router.get("/api/errors/stats")
async def get_error_stats_api():
    """API для получения статистики ошибок"""
    try:
        stats = await error_service.get_error_stats()
        return stats
        
    except Exception as e:
        print(f"[ERROR_ROUTES] API stats error: {e}")
        raise HTTPException(status_code=500, detail="Error getting error stats") 
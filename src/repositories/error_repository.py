from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from src.repositories.base_repository import BaseRepository
from src.models.error import Error, ErrorSeverity, ErrorStatus


class ErrorRepository(BaseRepository[Error]):
    """Репозиторий для работы с ошибками"""
    
    def __init__(self):
        super().__init__("errors")
    
    def _model_to_dict(self, model: Error) -> Dict[str, Any]:
        """Преобразует модель в словарь для сохранения"""
        return model.to_dict()
    
    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> Error:
        """Преобразует словарь в модель"""
        return Error.from_dict(data)
    
    async def save_error(self, error: Error) -> str:
        """Сохраняет ошибку в БД"""
        if not error.error_id:
            error.error_id = str(uuid.uuid4())
        
        error.updated_at = datetime.now()
        
        doc_id = await self.create(error)
        return doc_id or error.error_id
    
    async def get_error(self, error_id: str) -> Optional[Error]:
        """Получает ошибку по ID"""
        return await self.get_by_id(error_id)
    
    async def get_errors_by_user(self, sender_id: str, limit: int = 50) -> List[Error]:
        """Получает ошибки пользователя"""
        return await self.find_by_field('sender_id', sender_id, limit)
    
    async def get_errors_by_session(self, session_id: str) -> List[Error]:
        """Получает ошибки сессии"""
        return await self.find_by_field('session_id', session_id)
    
    async def get_recent_errors(self, hours: int = 24, limit: int = 100) -> List[Error]:
        """Получает недавние ошибки"""
        if not self.db:
            return []
        
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            # Получаем все ошибки и фильтруем по времени
            all_errors = await self.list_all(limit * 2)  # Берем больше, чтобы учесть фильтрацию
            
            # Фильтруем ошибки по времени
            recent_errors = []
            for error in all_errors:
                if error.timestamp and error.timestamp >= since:
                    recent_errors.append(error)
                    if len(recent_errors) >= limit:
                        break
            
            return recent_errors
            
        except Exception as e:
            print(f"Error getting recent errors: {e}")
            return []
    
    async def get_errors_by_status(self, status: ErrorStatus, limit: int = 100) -> List[Error]:
        """Получает ошибки по статусу"""
        return await self.find_by_field('status', status.value, limit)
    
    async def get_errors_by_severity(self, severity: ErrorSeverity, limit: int = 100) -> List[Error]:
        """Получает ошибки по важности"""
        return await self.find_by_field('severity', severity.value, limit)
    
    async def get_all_errors(self, limit: int = 200) -> List[Error]:
        """Получает все ошибки"""
        return await self.list_all(limit)
    
    async def update_error_status(self, error_id: str, status: ErrorStatus, resolved_by: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Обновляет статус ошибки"""
        error = await self.get_by_id(error_id)
        if not error:
            return False
        
        error.status = status
        error.updated_at = datetime.now()
        
        if status == ErrorStatus.RESOLVED:
            error.resolved_at = datetime.now()
            error.resolved_by = resolved_by
        
        if notes:
            error.notes = notes
        
        return await self.update(error_id, error)
    
    async def delete_error(self, error_id: str) -> bool:
        """Удаляет ошибку"""
        return await self.delete(error_id)
    
    async def get_error_stats(self) -> Dict[str, Any]:
        """Получает статистику ошибок"""
        # Получаем все ошибки за последние 24 часа
        recent_errors = await self.get_recent_errors(24)
        
        # Статистика по статусам
        status_stats = {}
        for status in ErrorStatus:
            status_stats[status.value] = len([e for e in recent_errors if e.status == status])
        
        # Статистика по важности
        severity_stats = {}
        for severity in ErrorSeverity:
            severity_stats[severity.value] = len([e for e in recent_errors if e.severity == severity])
        
        # Статистика по типам ошибок
        type_stats = {}
        for error in recent_errors:
            error_type = error.error_type or 'unknown'
            type_stats[error_type] = type_stats.get(error_type, 0) + 1
        
        return {
            'total_recent': len(recent_errors),
            'by_status': status_stats,
            'by_severity': severity_stats,
            'by_type': type_stats
        } 
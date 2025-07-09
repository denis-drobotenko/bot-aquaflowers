import traceback
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from src.repositories.error_repository import ErrorRepository
from src.models.error import Error, ErrorSeverity, ErrorStatus


class ErrorService:
    """Сервис для работы с ошибками"""
    
    def __init__(self):
        self.error_repository = ErrorRepository()
    
    async def log_error(
        self,
        error: Exception,
        sender_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_message: Optional[str] = None,
        ai_response: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        module: str = "",
        function: str = ""
    ) -> str:
        """
        Логирует ошибку в БД
        
        Args:
            error: Исключение
            sender_id: ID отправителя
            session_id: ID сессии
            user_message: Сообщение пользователя
            ai_response: Ответ AI
            context_data: Дополнительные данные контекста
            severity: Важность ошибки
            module: Модуль где произошла ошибка
            function: Функция где произошла ошибка
            
        Returns:
            ID сохраненной ошибки
        """
        try:
            # Получаем информацию об ошибке
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            
            # Получаем номер строки
            line_number = None
            if error.__traceback__:
                tb = error.__traceback__
                while tb.tb_next:
                    tb = tb.tb_next
                line_number = tb.tb_lineno
            
            # Создаем объект ошибки
            error_obj = Error(
                timestamp=datetime.now(),
                severity=severity,
                status=ErrorStatus.NEW,
                sender_id=sender_id,
                session_id=session_id,
                error_type=error_type,
                error_message=error_message,
                error_details=error_message,
                stack_trace=stack_trace,
                module=module,
                function=function,
                line_number=line_number,
                context_data=context_data or {},
                user_message=user_message,
                ai_response=ai_response
            )
            
            # Сохраняем в БД
            error_id = await self.error_repository.save_error(error_obj)
            print(f"[ERROR_SERVICE] Logged error {error_id}: {error_type} - {error_message}")
            
            return error_id
            
        except Exception as e:
            print(f"[ERROR_SERVICE] Failed to log error: {e}")
            return ""
    
    async def get_error(self, error_id: str) -> Optional[Error]:
        """Получает ошибку по ID"""
        return await self.error_repository.get_error(error_id)
    
    async def get_errors_by_user(self, sender_id: str, limit: int = 50) -> list[Error]:
        """Получает ошибки пользователя"""
        return await self.error_repository.get_errors_by_user(sender_id, limit)
    
    async def get_errors_by_session(self, session_id: str) -> list[Error]:
        """Получает ошибки сессии"""
        return await self.error_repository.get_errors_by_session(session_id)
    
    async def get_recent_errors(self, hours: int = 24, limit: int = 100) -> list[Error]:
        """Получает недавние ошибки"""
        return await self.error_repository.get_recent_errors(hours, limit)
    
    async def get_errors_by_status(self, status: ErrorStatus, limit: int = 100) -> list[Error]:
        """Получает ошибки по статусу"""
        return await self.error_repository.get_errors_by_status(status, limit)
    
    async def get_errors_by_severity(self, severity: ErrorSeverity, limit: int = 100) -> list[Error]:
        """Получает ошибки по важности"""
        return await self.error_repository.get_errors_by_severity(severity, limit)
    
    async def get_all_errors(self, limit: int = 200) -> list[Error]:
        """Получает все ошибки"""
        return await self.error_repository.get_all_errors(limit)
    
    async def update_error_status(
        self, 
        error_id: str, 
        status: ErrorStatus, 
        resolved_by: Optional[str] = None, 
        notes: Optional[str] = None
    ) -> bool:
        """Обновляет статус ошибки"""
        return await self.error_repository.update_error_status(error_id, status, resolved_by, notes)
    
    async def delete_error(self, error_id: str) -> bool:
        """Удаляет ошибку"""
        return await self.error_repository.delete_error(error_id)
    
    async def get_error_stats(self) -> Dict[str, Any]:
        """Получает статистику ошибок"""
        return await self.error_repository.get_error_stats()
    
    def get_error_messages(self, user_lang: str = 'ru') -> Dict[str, str]:
        """Возвращает сообщения об ошибках на разных языках"""
        if user_lang == 'en':
            return {
                'ru': 'Sorry, an error occurred. Please try again. 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            }
        elif user_lang == 'th':
            return {
                'ru': 'Извините, произошла ошибка. Попробуйте еще раз. 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            }
        else:
            return {
                'ru': 'Извините, произошла ошибка. Попробуйте еще раз. 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            } 
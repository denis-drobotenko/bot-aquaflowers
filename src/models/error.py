from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorStatus(Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    IGNORED = "ignored"


@dataclass
class Error:
    """Модель ошибки для сохранения в БД"""
    
    # Основные поля
    error_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    status: ErrorStatus = ErrorStatus.NEW
    
    # Информация о пользователе
    sender_id: Optional[str] = None
    session_id: Optional[str] = None
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    
    # Информация об ошибке
    error_type: str = ""
    error_message: str = ""
    error_details: str = ""
    stack_trace: Optional[str] = None
    
    # Контекст ошибки
    module: str = ""
    function: str = ""
    line_number: Optional[int] = None
    
    # Дополнительные данные
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_message: Optional[str] = None
    ai_response: Optional[str] = None
    
    # Метаданные
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь для сохранения в БД"""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'status': self.status.value,
            'sender_id': self.sender_id,
            'session_id': self.session_id,
            'user_name': self.user_name,
            'user_phone': self.user_phone,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'stack_trace': self.stack_trace,
            'module': self.module,
            'function': self.function,
            'line_number': self.line_number,
            'context_data': self.context_data,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Error':
        """Создает объект из словаря"""
        return cls(
            error_id=data.get('error_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            severity=ErrorSeverity(data.get('severity', 'medium')),
            status=ErrorStatus(data.get('status', 'new')),
            sender_id=data.get('sender_id'),
            session_id=data.get('session_id'),
            user_name=data.get('user_name'),
            user_phone=data.get('user_phone'),
            error_type=data.get('error_type', ''),
            error_message=data.get('error_message', ''),
            error_details=data.get('error_details', ''),
            stack_trace=data.get('stack_trace'),
            module=data.get('module', ''),
            function=data.get('function', ''),
            line_number=data.get('line_number'),
            context_data=data.get('context_data', {}),
            user_message=data.get('user_message'),
            ai_response=data.get('ai_response'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            resolved_at=datetime.fromisoformat(data['resolved_at']) if data.get('resolved_at') else None,
            resolved_by=data.get('resolved_by'),
            notes=data.get('notes')
        ) 
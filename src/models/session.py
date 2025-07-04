"""
Модель сессии пользователя
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


class SessionStatus(str, Enum):
    """Статусы сессии"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    COMPLETED = "completed"


@dataclass
class Session:
    """Модель сессии пользователя"""
    
    # Основные поля
    session_id: str
    sender_id: str
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Опциональные поля
    last_activity: Optional[datetime] = None
    user_language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.session_id:
            raise ValueError("session_id не может быть пустым")
        if not self.sender_id:
            raise ValueError("sender_id не может быть пустым")
        
        # Устанавливаем last_activity если не задан
        if self.last_activity is None:
            self.last_activity = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует сессию в словарь для сохранения в БД"""
        return {
            'session_id': self.session_id,
            'sender_id': self.sender_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'user_language': self.user_language,
            'metadata': self.metadata or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Создает сессию из словаря"""
        # Парсим timestamps
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now()
        
        last_activity = data.get('last_activity')
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        
        return cls(
            session_id=data['session_id'],
            sender_id=data['sender_id'],
            status=SessionStatus(data.get('status', 'active')),
            created_at=created_at,
            last_activity=last_activity,
            user_language=data.get('user_language'),
            metadata=data.get('metadata')
        )
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now()
    
    def is_active(self, max_inactive_days: int = 7) -> bool:
        """Проверяет, активна ли сессия"""
        if self.status != SessionStatus.ACTIVE:
            return False
        
        if not self.last_activity:
            return False
        
        cutoff_time = datetime.now() - timedelta(days=max_inactive_days)
        return self.last_activity > cutoff_time
    
    def mark_completed(self):
        """Отмечает сессию как завершенную"""
        self.status = SessionStatus.COMPLETED
    
    def mark_inactive(self):
        """Отмечает сессию как неактивную"""
        self.status = SessionStatus.INACTIVE
    
    def set_user_language(self, language: str):
        """Устанавливает язык пользователя"""
        self.user_language = language
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Получает значение из метаданных"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """Устанавливает значение в метаданные"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value 
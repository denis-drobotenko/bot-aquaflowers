"""
Модель сообщения для чата
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class MessageRole(str, Enum):
    """Роли сообщений в диалоге"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Модель сообщения в чате с поддержкой многоязычности"""
    
    # Основные поля
    sender_id: str
    session_id: str
    role: MessageRole
    content: str  # Основной текст на языке пользователя
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Многоязычные поля
    content_en: Optional[str] = None  # Английская версия
    content_thai: Optional[str] = None  # Тайская версия
    
    # Опциональные поля
    id: Optional[str] = None
    wa_message_id: Optional[str] = None
    parts: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.sender_id:
            raise ValueError("sender_id не может быть пустым")
        if not self.session_id:
            raise ValueError("session_id не может быть пустым")
        if not self.content:
            raise ValueError("content не может быть пустым")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует сообщение в словарь для сохранения в БД"""
        return {
            'sender_id': self.sender_id,
            'session_id': self.session_id,
            'role': self.role.value,
            'content': self.content,
            'content_en': self.content_en,
            'content_thai': self.content_thai,
            'timestamp': self.timestamp.isoformat(),
            'wa_message_id': self.wa_message_id,
            'parts': self.parts
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Создает сообщение из словаря"""
        # Парсим timestamp
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif timestamp is None:
            timestamp = datetime.now()
        
        return cls(
            id=data.get('id'),
            sender_id=data['sender_id'],
            session_id=data['session_id'],
            role=MessageRole(data['role']),
            content=data['content'],
            content_en=data.get('content_en'),
            content_thai=data.get('content_thai'),
            timestamp=timestamp,
            wa_message_id=data.get('wa_message_id'),
            parts=data.get('parts')
        )
    
    def is_from_user(self) -> bool:
        """Проверяет, что сообщение от пользователя"""
        return self.role == MessageRole.USER
    
    def is_from_assistant(self) -> bool:
        """Проверяет, что сообщение от ассистента"""
        return self.role == MessageRole.ASSISTANT
    
    def is_system_message(self) -> bool:
        """Проверяет, что это системное сообщение"""
        return self.role == MessageRole.SYSTEM 
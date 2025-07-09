"""
Модель пользователя
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class UserStatus(str, Enum):
    """Статусы пользователя"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"


@dataclass
class User:
    """Модель пользователя"""
    
    # Основные поля
    sender_id: str
    name: Optional[str] = None
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Опциональные поля
    phone: Optional[str] = None
    language: Optional[str] = None
    last_activity: Optional[datetime] = None
    id: Optional[str] = None  # ID документа в Firestore
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.sender_id:
            raise ValueError("sender_id не может быть пустым")
        
        # Устанавливаем phone если не задан
        if not self.phone:
            self.phone = self.sender_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует пользователя в словарь для сохранения в БД"""
        result = {
            'sender_id': self.sender_id,
            'name': self.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'phone': self.phone,
            'language': self.language,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
        }
        # Добавляем ID только если он есть
        if self.id:
            result['id'] = self.id
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Создает пользователя из словаря"""
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
            sender_id=data['sender_id'],
            name=data.get('name'),
            status=UserStatus(data.get('status', 'active')),
            created_at=created_at,
            phone=data.get('phone'),
            language=data.get('language'),
            last_activity=last_activity,
            id=data.get('id'),  # ID документа в Firestore
        )
    
    def update_activity(self):
        """Обновляет время последней активности"""
        self.last_activity = datetime.now()
    
    def set_name(self, name: str):
        """Устанавливает имя пользователя"""
        self.name = name
    
    def set_language(self, language: str):
        """Устанавливает язык пользователя"""
        self.language = language
    
    def set_phone(self, phone: str):
        """Устанавливает телефон пользователя"""
        self.phone = phone
    
    def activate(self):
        """Активирует пользователя"""
        self.status = UserStatus.ACTIVE
    
    def deactivate(self):
        """Деактивирует пользователя"""
        self.status = UserStatus.INACTIVE
    
    def block(self):
        """Блокирует пользователя"""
        self.status = UserStatus.BLOCKED
    
    def is_active(self) -> bool:
        """Проверяет, активен ли пользователь"""
        return self.status == UserStatus.ACTIVE
    
    def is_blocked(self) -> bool:
        """Проверяет, заблокирован ли пользователь"""
        return self.status == UserStatus.BLOCKED
    
    def get_display_name(self) -> str:
        """Получает отображаемое имя пользователя"""
        if self.name:
            return self.name
        return f"Пользователь {self.sender_id[-4:]}"  # Последние 4 цифры 
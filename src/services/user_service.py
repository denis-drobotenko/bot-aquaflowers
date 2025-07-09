"""
Сервис для работы с пользователями
"""

from src.repositories.user_repository import UserRepository
from src.models.user import User, UserStatus
from src.utils.logging_decorator import log_function
from typing import Optional

class UserService:
    def __init__(self):
        self.repo = UserRepository()

    @log_function("user_service")
    async def create_user(self, user: User) -> Optional[str]:
        # Устанавливаем ID пользователя равным sender_id для уникальности
        user.id = user.sender_id
        return await self.repo.create(user)

    @log_function("user_service")
    async def get_user(self, sender_id: str) -> Optional[User]:
        # Сначала пытаемся получить по ID документа (sender_id)
        user = await self.repo.get_by_id(sender_id)
        if user:
            return user
        
        # Если не найден по ID, ищем по полю sender_id (для старых записей)
        users = await self.repo.find_by_field('sender_id', sender_id, limit=1)
        return users[0] if users else None

    @log_function("user_service")
    async def update_user(self, sender_id: str, user: User) -> bool:
        # Сначала находим пользователя по sender_id
        existing_user = await self.get_user(sender_id)
        if not existing_user:
            return False
        
        # Устанавливаем правильный ID для обновления
        user.id = sender_id
        
        # Обновляем по ID документа (sender_id)
        return await self.repo.update(sender_id, user)

    async def block_user(self, sender_id: str) -> bool:
        user = await self.get_user(sender_id)
        if not user:
            return False
        user.block()
        return await self.update_user(sender_id, user)

    async def activate_user(self, sender_id: str) -> bool:
        user = await self.get_user(sender_id)
        if not user:
            return False
        user.activate()
        return await self.update_user(sender_id, user) 
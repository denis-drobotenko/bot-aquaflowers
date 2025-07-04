"""
Сервис для работы с пользователями
"""

from src.repositories.user_repository import UserRepository
from src.models.user import User, UserStatus
from src.utils.logging_utils import ContextLogger
from typing import Optional

class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.logger = ContextLogger("user_service")

    async def create_user(self, user: User) -> Optional[str]:
        return await self.repo.create(user)

    async def get_user(self, sender_id: str) -> Optional[User]:
        return await self.repo.get_by_id(sender_id)

    async def update_user(self, sender_id: str, user: User) -> bool:
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
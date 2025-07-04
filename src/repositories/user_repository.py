"""
Репозиторий для пользователей
"""

from src.repositories.base_repository import BaseRepository
from src.models.user import User
from typing import Dict, Any

class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__('users')

    def _model_to_dict(self, model: User) -> Dict[str, Any]:
        return model.to_dict()

    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> User:
        # id пользователя может быть как поле, так и doc_id
        if 'id' not in data:
            data['id'] = doc_id
        return User.from_dict(data) 
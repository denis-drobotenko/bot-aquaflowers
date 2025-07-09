"""
Репозиторий для пользователей
"""

from src.repositories.base_repository import BaseRepository
from src.models.user import User
from typing import Dict, Any, List, Optional

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
    
    async def create(self, model: User) -> Optional[str]:
        """
        Создает нового пользователя.
        
        Args:
            model: Пользователь для создания
            
        Returns:
            ID созданного документа или None при ошибке
        """
        try:
            # Проверяем, не существует ли уже пользователь с таким sender_id
            existing_users = await self.find_by_field('sender_id', model.sender_id, limit=1)
            if existing_users:
                print(f"User with sender_id {model.sender_id} already exists")
                return existing_users[0].id
            
            doc_data = self._model_to_dict(model)
            # Используем sender_id как ID документа для уникальности
            doc_ref = self._get_collection_ref().document(model.sender_id)
            doc_ref.set(doc_data)
            
            doc_id = doc_ref.id
            print(f"Created user with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
    
    async def get_all_users(self) -> List[User]:
        """Получает всех пользователей из БД"""
        if not self.db:
            return []
        
        try:
            docs = self.db.collection(self.collection_name).stream()
            users = []
            for doc in docs:
                data = doc.to_dict()
                user = self._dict_to_model(data, doc.id)
                users.append(user)
            return users
        except Exception as e:
            print(f"Error getting all users: {e}")
            return [] 
"""
Репозиторий для сессий
"""

from src.repositories.base_repository import BaseRepository
from src.models.session import Session
from typing import Dict, Any

class SessionRepository(BaseRepository[Session]):
    def __init__(self):
        super().__init__('users')  # Используем коллекцию users вместо user_sessions

    def _model_to_dict(self, model: Session) -> Dict[str, Any]:
        return model.to_dict()

    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> Session:
        # session_id может быть как поле, так и doc_id
        if 'session_id' not in data:
            data['session_id'] = doc_id
        return Session.from_dict(data) 
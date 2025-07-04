"""
Сервис для работы с сообщениями
"""

from src.repositories.message_repository import MessageRepository
from src.models.message import Message
from src.utils.logging_utils import ContextLogger
from typing import List, Optional, Dict, Any
from google.cloud import firestore
from datetime import datetime

class MessageService:
    def __init__(self):
        self.repo = MessageRepository()
        self.logger = ContextLogger("message_service")
        self.db = self._get_firestore_client()
    
    def _get_firestore_client(self):
        """Получает клиент Firestore"""
        try:
            return firestore.Client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore client: {e}")
            return None

    async def add_message(self, message: Message) -> Optional[str]:
        """Добавляет сообщение в коллекцию messages (старый метод)"""
        return await self.repo.create(message)

    async def add_message_to_conversation(self, message: Message) -> Optional[str]:
        """
        Добавляет сообщение в правильную структуру conversations.
        Использует репозиторий для работы с БД.
        """
        try:
            success = self.repo.add_message_to_conversation(message)
            if success:
                self.logger.info(f"Message added to conversation: {message.sender_id}/{message.session_id}")
                return "success"
            else:
                self.logger.error(f"Failed to add message to conversation: {message.sender_id}/{message.session_id}")
                return None
        except Exception as e:
            self.logger.error(f"Error adding message to conversation: {e}")
            return None

    async def get_message(self, message_id: str) -> Optional[Message]:
        return await self.repo.get_by_id(message_id)

    async def get_conversation_history(self, session_id: str, limit: int = 100) -> List[Message]:
        """Получает историю из коллекции messages (старый метод)"""
        messages = await self.repo.find_by_field('session_id', session_id, limit=limit)
        # Сортировка по времени
        messages.sort(key=lambda m: m.timestamp)
        return messages

    async def get_conversation_history_for_ai(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю диалога в формате для AI из структуры conversations.
        Возвращает список словарей с полями role и content.
        """
        try:
            # Нужно найти sender_id по session_id
            sender_id = self.repo.find_session_owner(session_id)
            if not sender_id:
                self.logger.warning(f"Session {session_id} not found in conversations")
                return []
            
            # Получаем историю через репозиторий
            history = self.repo.get_conversation_history_by_sender(sender_id, session_id, limit=limit)
            self.logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []

    async def get_conversation_history_for_ai_by_sender(self, sender_id: str, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю диалога по sender_id и session_id.
        Использует репозиторий для работы с БД.
        """
        try:
            history = self.repo.get_conversation_history_by_sender(sender_id, session_id, limit=limit)
            self.logger.info(f"Retrieved {len(history)} messages for sender {sender_id}, session {session_id}")
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []

    async def update_message(self, message_id: str, message: Message) -> bool:
        return await self.repo.update(message_id, message) 
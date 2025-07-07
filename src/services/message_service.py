"""
Сервис для работы с сообщениями
"""

from src.repositories.message_repository import MessageRepository
from src.models.message import Message
from src.utils.logging_decorator import log_function
from typing import List, Optional, Dict, Any, Tuple
from google.cloud import firestore
from datetime import datetime

class MessageService:
    def __init__(self):
        self.repo = MessageRepository()
        self.db = self._get_firestore_client()
    
    def _get_firestore_client(self):
        """Получает клиент Firestore"""
        try:
            return firestore.Client()
        except Exception as e:
            print(f"Failed to initialize Firestore client: {e}")
            return None

    async def add_message(self, message: Message) -> Optional[str]:
        """Добавляет сообщение в коллекцию messages (старый метод)"""
        return await self.repo.create(message)

    @log_function("message_service")
    async def add_message_to_conversation(self, message: Message) -> Optional[str]:
        """
        Добавляет сообщение в правильную структуру conversations.
        Использует репозиторий для работы с БД.
        """
        try:
            success = await self.repo.add_message_to_conversation(message)
            if success:
                print(f"Message added to conversation: {message.sender_id}/{message.session_id}")
                return "success"
            else:
                print(f"Failed to add message to conversation: {message.sender_id}/{message.session_id}")
                return None
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return None

    @log_function("message_service")
    async def add_message_with_transaction(self, message: Message, limit: int = 10) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Добавляет сообщение с использованием транзакции и возвращает обновленную историю диалога.
        Гарантирует атомарность операций сохранения и чтения.
        
        Args:
            message: Сообщение для сохранения
            limit: Лимит сообщений в истории
            
        Returns:
            Tuple[bool, List[Dict]]: (успех_сохранения, история_диалога)
        """
        try:
            success, history = await self.repo.add_message_with_transaction(message, limit)
            if success:
                print(f"Message added with transaction: {message.sender_id}/{message.session_id}")
                print(f"Retrieved {len(history)} messages in transaction")
            else:
                print(f"Failed to add message with transaction: {message.sender_id}/{message.session_id}")
            return success, history
        except Exception as e:
            print(f"Error in transaction: {e}")
            return False, []

    async def get_message(self, message_id: str) -> Optional[Message]:
        return await self.repo.get_by_id(message_id)

    async def get_conversation_history(self, session_id: str, limit: int = 100) -> List[Message]:
        """Получает историю из коллекции messages (старый метод)"""
        messages = await self.repo.find_by_field('session_id', session_id, limit=limit)
        # Сортировка по времени
        messages.sort(key=lambda m: m.timestamp)
        return messages

    @log_function("message_service")
    async def get_conversation_history_for_ai(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю диалога в формате для AI из структуры conversations.
        Возвращает список словарей с полями role и content.
        """
        try:
            # Нужно найти sender_id по session_id
            sender_id = await self.repo.find_session_owner(session_id)
            if not sender_id:
                print(f"Session {session_id} not found in conversations")
                return []
            
            # Получаем историю через репозиторий
            history = await self.repo.get_conversation_history_by_sender(sender_id, session_id, limit=limit)
            print(f"Retrieved {len(history)} messages for session {session_id}")
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def get_conversation_history_for_ai_by_sender(self, sender_id: str, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю диалога по sender_id и session_id.
        Использует репозиторий для работы с БД.
        """
        try:
            history = await self.repo.get_conversation_history_by_sender(sender_id, session_id, limit=limit)
            print(f"Retrieved {len(history)} messages for sender {sender_id}, session {session_id}")
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def get_messages_for_session(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает сообщения для сессии (для совместимости с message_processor).
        Использует get_conversation_history_for_ai.
        """
        return await self.get_conversation_history_for_ai(session_id, limit)

    async def update_message(self, message_id: str, message: Message) -> bool:
        return await self.repo.update(message_id, message)
    
    async def get_message_by_wa_id(self, sender_id: str, session_id: str, wa_message_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает сообщение по WhatsApp message ID.
        Ищет во всех сессиях пользователя, а не только в текущей.
        
        Args:
            sender_id: ID пользователя
            session_id: ID сессии (не используется для поиска)
            wa_message_id: WhatsApp message ID
            
        Returns:
            Dict с данными сообщения или None
        """
        try:
            print(f"[WAID_SEARCH] Начинаем поиск wa_id {wa_message_id} для пользователя {sender_id}")
            
            # Используем новый метод из репозитория с передачей SessionService
            from src.services.session_service import SessionService
            session_service = SessionService()
            message = await self.repo.get_message_by_wa_id(sender_id, wa_message_id, session_service)
            
            if message:
                print(f"[WAID_SEARCH] НАЙДЕНО! wa_id {wa_message_id} в сессии {message.get('session_id')}")
                return message
            else:
                print(f"[WAID_SEARCH] Message with wa_id {wa_message_id} not found for user {sender_id}")
                return None
                
        except Exception as e:
            print(f"[WAID_SEARCH] Error getting message by wa_id: {e}")
            return None

    def add_message_with_transaction_sync(self, message, limit=10):
        """
        Сохраняет сообщение и возвращает историю диалога через sync-транзакцию Firestore.
        """
        return self.repo.add_message_with_transaction_sync(message, limit)

    def add_user_and_ai_messages_with_transaction_sync(self, user_message: Message, ai_message: Message, limit: int = 10):
        """Сохраняет сообщение пользователя и AI в одной транзакции"""
        return self.repo.add_user_and_ai_messages_with_transaction_sync(user_message, ai_message, limit) 
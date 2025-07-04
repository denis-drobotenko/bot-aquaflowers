"""
Репозиторий для сообщений
"""

from src.repositories.base_repository import BaseRepository
from src.models.message import Message
from typing import Dict, Any, List
from google.cloud import firestore
from datetime import datetime

class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__('messages')
        self.db = self._get_firestore_client()

    def _model_to_dict(self, model: Message) -> Dict[str, Any]:
        return model.to_dict()

    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> Message:
        # id сообщения может быть как поле, так и doc_id
        if 'id' not in data:
            data['id'] = doc_id
        return Message.from_dict(data)

    def add_message_to_conversation(self, message: Message) -> bool:
        """
        Добавляет сообщение в структуру conversations.
        Структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
        """
        if not self.db:
            return False
        
        try:
            # Создаем ссылку на документ сессии
            doc_ref = self.db.collection('conversations').document(message.sender_id).collection('sessions').document(message.session_id)
            
            # Данные сообщения
            message_data = {
                'role': message.role.value,
                'content': message.content,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            # Добавляем переводы если есть
            if message.content_en:
                message_data['content_en'] = message.content_en
            if message.content_thai:
                message_data['content_thai'] = message.content_thai
            
            # Добавляем сообщение в подколлекцию messages
            doc_ref.collection('messages').add(message_data)
            
            return True
            
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return False

    def get_conversation_history_by_sender(self, sender_id: str, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает историю диалога по sender_id и session_id из структуры conversations.
        Возвращает список словарей с полями role и content.
        """
        if not self.db:
            return []
        
        try:
            # Прямой путь к сообщениям (не проверяем существование документа сессии)
            messages_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages')
            
            # Получаем сообщения, отсортированные по времени
            query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(limit)
            messages = query.stream()
            
            history = []
            for msg_doc in messages:
                msg_data = msg_doc.to_dict()
                history.append({
                    'role': msg_data.get('role', 'user'),
                    'content': msg_data.get('content', ''),
                    'timestamp': msg_data.get('timestamp'),
                    'content_en': msg_data.get('content_en'),
                    'content_thai': msg_data.get('content_thai')
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    def find_session_owner(self, session_id: str, known_users: List[str] = None) -> str:
        """
        Ищет владельца сессии среди известных пользователей.
        Возвращает sender_id или None если не найден.
        """
        if not self.db:
            return None
        
        if known_users is None:
            known_users = ["79140775712", "79140775713", "79140775714", "79140775715"]
        
        try:
            for user_id in known_users:
                # Проверяем, есть ли сообщения у этого пользователя в данной сессии
                messages_ref = self.db.collection('conversations').document(user_id).collection('sessions').document(session_id).collection('messages')
                docs = list(messages_ref.limit(1).stream())
                if docs:
                    return user_id
            
            return None
            
        except Exception as e:
            print(f"Error finding session owner: {e}")
            return None 
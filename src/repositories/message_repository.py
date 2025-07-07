"""
Репозиторий для сообщений
"""

from src.repositories.base_repository import BaseRepository
from src.models.message import Message
from typing import Dict, Any, List, Optional, Tuple
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

    async def add_message_with_transaction(self, message: Message, limit: int = 10) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Добавляет сообщение в структуру conversations с использованием транзакции
        и сразу возвращает обновленную историю диалога.
        
        Args:
            message: Сообщение для сохранения
            limit: Лимит сообщений в истории
            
        Returns:
            Tuple[bool, List[Dict]]: (успех_сохранения, история_диалога)
        """
        if not self.db:
            return False, []
        
        try:
            # Используем синхронную транзакцию Firestore
            def transaction_callback(transaction):
                # Создаем ссылку на документ сессии
                doc_ref = self.db.collection('conversations').document(message.sender_id).collection('sessions').document(message.session_id)
                
                # Проверяем, существует ли документ сессии
                session_doc = doc_ref.get(transaction=transaction)
                if not session_doc.exists:
                    print(f"Creating session document for {message.sender_id}/{message.session_id}")
                    transaction.set(doc_ref, {
                        'created_at': message.timestamp,
                        'message_count': 1,
                        'last_activity': message.timestamp
                    })
                else:
                    # Обновляем счетчик сообщений в документе сессии
                    transaction.update(doc_ref, {
                        'message_count': firestore.Increment(1),
                        'last_activity': message.timestamp
                    })
                
                # Данные сообщения
                message_data = {
                    'role': message.role.value,
                    'content': message.content,
                    'timestamp': message.timestamp,
                }
                
                # Добавляем переводы если есть
                if message.content_en:
                    message_data['content_en'] = message.content_en
                if message.content_thai:
                    message_data['content_thai'] = message.content_thai
                if message.wa_message_id:
                    message_data['wa_message_id'] = message.wa_message_id
                
                # Сохраняем сообщение
                if message.wa_message_id:
                    message_ref = doc_ref.collection('messages').document(message.wa_message_id)
                    transaction.set(message_ref, message_data)
                else:
                    # Если нет wa_message_id, создаем новый документ
                    message_ref = doc_ref.collection('messages').document()
                    transaction.set(message_ref, message_data)
                
                # Получаем обновленную историю диалога в рамках той же транзакции
                messages_ref = doc_ref.collection('messages')
                query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(limit)
                messages = query.stream(transaction=transaction)
                
                history = []
                for msg_doc in messages:
                    msg_data = msg_doc.to_dict()
                    history.append({
                        'role': msg_data.get('role', 'user'),
                        'content': msg_data.get('content', ''),
                        'timestamp': msg_data.get('timestamp'),
                        'content_en': msg_data.get('content_en'),
                        'content_thai': msg_data.get('content_thai'),
                        'wa_message_id': msg_data.get('wa_message_id')
                    })
                
                return history
            
            # Выполняем транзакцию синхронно
            import asyncio
            loop = asyncio.get_event_loop()
            history = await loop.run_in_executor(None, lambda: self.db.run_in_transaction(transaction_callback))
            
            print(f"Message saved to {message.sender_id}/{message.session_id} with wa_id: {message.wa_message_id}")
            print(f"Retrieved {len(history)} messages in transaction")
            return True, history
            
        except Exception as e:
            print(f"Error in transaction: {e}")
            return False, []

    async def add_message_to_conversation(self, message: Message) -> bool:
        """
        Добавляет сообщение в структуру conversations.
        Структура: conversations/{sender_id}/sessions/{session_id}/messages/{message_id}
        Если есть wa_message_id (wamid) — использовать его как id документа Firestore.
        """
        if not self.db:
            return False
        
        try:
            # Создаем ссылку на документ сессии
            doc_ref = self.db.collection('conversations').document(message.sender_id).collection('sessions').document(message.session_id)
            
            # Проверяем, существует ли документ сессии, если нет - создаем
            session_doc = doc_ref.get()
            if not session_doc.exists:
                print(f"Creating session document for {message.sender_id}/{message.session_id}")
                doc_ref.set({
                    'created_at': message.timestamp,
                    'message_count': 0,
                    'last_activity': message.timestamp
                })
            
            # Данные сообщения
            message_data = {
                'role': message.role.value,
                'content': message.content,
                'timestamp': message.timestamp,
            }
            
            # Добавляем переводы если есть
            if message.content_en:
                message_data['content_en'] = message.content_en
            if message.content_thai:
                message_data['content_thai'] = message.content_thai
            if message.wa_message_id:
                message_data['wa_message_id'] = message.wa_message_id
            
            # Сохраняем с нужным id
            if message.wa_message_id:
                doc_ref.collection('messages').document(message.wa_message_id).set(message_data)
            else:
                doc_ref.collection('messages').add(message_data)
            
            # Обновляем счетчик сообщений в документе сессии
            doc_ref.update({
                'message_count': firestore.Increment(1),
                'last_activity': message.timestamp
            })
            
            print(f"Message saved to {message.sender_id}/{message.session_id} with wa_id: {message.wa_message_id}")
            return True
        
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return False

    async def get_conversation_history_by_sender(self, sender_id: str, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
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
                    'content_thai': msg_data.get('content_thai'),
                    'wa_message_id': msg_data.get('wa_message_id')
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []

    async def find_session_owner(self, session_id: str, known_users: List[str] = None) -> str:
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

    async def get_message_by_wa_id(self, sender_id: str, wa_message_id: str, session_service) -> Optional[Dict[str, Any]]:
        """
        Ищет сообщение по wa_message_id во всех сессиях пользователя.
        Возвращает словарь с данными сообщения или None.
        """
        if not self.db:
            return None
        
        try:
            # Получаем все сессии пользователя через SessionService
            sessions = await session_service.get_all_sessions_by_sender(sender_id)
            
            # Ищем сообщение в каждой сессии
            for session in sessions:
                session_id = session['session_id']
                messages_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id).collection('messages')
                
                # Ищем сообщение по wa_message_id
                message_doc = messages_ref.document(wa_message_id).get()
                
                if message_doc.exists:
                    message_data = message_doc.to_dict()
                    return {
                        'session_id': session_id,
                        'role': message_data.get('role', 'user'),
                        'content': message_data.get('content', ''),
                        'timestamp': message_data.get('timestamp'),
                        'content_en': message_data.get('content_en'),
                        'content_thai': message_data.get('content_thai'),
                        'wa_message_id': wa_message_id
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting message by wa_id: {e}")
            return False

    def add_message_with_transaction_sync(self, message: Message, limit: int = 10):
        """
        Сохраняет сообщение и возвращает историю диалога в рамках sync-транзакции Firestore.
        Возвращает (успех, история)
        """
        if not self.db:
            return False, []
        from google.cloud import firestore
        try:
            @firestore.transactional
            def transaction_callback(transaction, message, limit):
                doc_ref = self.db.collection('conversations').document(message.sender_id).collection('sessions').document(message.session_id)
                # 1. Сначала читаем историю сообщений
                messages_ref = doc_ref.collection('messages')
                query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(limit)
                history = []
                messages = query.stream(transaction=transaction)
                for msg_doc in messages:
                    msg_data = msg_doc.to_dict()
                    history.append({
                        'role': msg_data.get('role', 'user'),
                        'content': msg_data.get('content', ''),
                        'timestamp': msg_data.get('timestamp'),
                        'content_en': msg_data.get('content_en'),
                        'content_thai': msg_data.get('content_thai'),
                        'wa_message_id': msg_data.get('wa_message_id')
                    })
                
                # 2. Добавляем текущее сообщение в историю (если его там еще нет)
                current_message_data = {
                    'role': message.role.value,
                    'content': message.content,
                    'timestamp': message.timestamp,
                    'content_en': message.content_en,
                    'content_thai': message.content_thai,
                    'wa_message_id': message.wa_message_id
                }
                
                # Проверяем, есть ли уже такое сообщение в истории
                message_exists = any(
                    msg.get('content') == message.content and 
                    msg.get('role') == message.role.value and
                    msg.get('timestamp') == message.timestamp 
                    for msg in history
                )
                
                if not message_exists:
                    history.append(current_message_data)
                
                # 3. Потом делаем set/update
                session_doc = doc_ref.get(transaction=transaction)
                if not session_doc.exists:
                    transaction.set(doc_ref, {
                        'created_at': message.timestamp,
                        'message_count': 1,
                        'last_activity': message.timestamp
                    })
                else:
                    transaction.update(doc_ref, {
                        'message_count': firestore.Increment(1),
                        'last_activity': message.timestamp
                    })
                
                # Сохраняем сообщение
                if message.wa_message_id:
                    message_ref = doc_ref.collection('messages').document(message.wa_message_id)
                    transaction.set(message_ref, current_message_data)
                else:
                    message_ref = doc_ref.collection('messages').document()
                    transaction.set(message_ref, current_message_data)
                
                return history
            transaction = self.db.transaction()
            history = transaction_callback(transaction, message, limit)
            print(f"[SYNC] Message saved to {message.sender_id}/{message.session_id} with wa_id: {message.wa_message_id}")
            print(f"[SYNC] Retrieved {len(history)} messages in transaction")
            return True, history
        except Exception as e:
            print(f"[SYNC] Error in transaction: {e}")
            return False, []

    def add_user_and_ai_messages_with_transaction_sync(self, user_message: Message, ai_message: Message, limit: int = 10):
        """
        Сохраняет сообщение пользователя и AI в одной транзакции Firestore.
        Возвращает (успех, история_с_ai)
        """
        if not self.db:
            return False, []
        from google.cloud import firestore
        try:
            @firestore.transactional
            def transaction_callback(transaction, user_message, ai_message, limit):
                doc_ref = self.db.collection('conversations').document(user_message.sender_id).collection('sessions').document(user_message.session_id)
                
                # 1. Сначала читаем существующую историю
                messages_ref = doc_ref.collection('messages')
                query = messages_ref.order_by('timestamp', direction=firestore.Query.ASCENDING).limit(limit)
                history = []
                messages = query.stream(transaction=transaction)
                for msg_doc in messages:
                    msg_data = msg_doc.to_dict()
                    history.append({
                        'role': msg_data.get('role', 'user'),
                        'content': msg_data.get('content', ''),
                        'timestamp': msg_data.get('timestamp'),
                        'content_en': msg_data.get('content_en'),
                        'content_thai': msg_data.get('content_thai')
                    })
                
                # 2. Обновляем сессию
                session_doc = doc_ref.get(transaction=transaction)
                if not session_doc.exists:
                    transaction.set(doc_ref, {
                        'created_at': user_message.timestamp,
                        'message_count': 2,  # Пользователь + AI
                        'last_activity': ai_message.timestamp
                    })
                else:
                    transaction.update(doc_ref, {
                        'message_count': firestore.Increment(2),
                        'last_activity': ai_message.timestamp
                    })
                
                # 3. Сохраняем сообщение пользователя
                user_doc_ref = messages_ref.document()
                transaction.set(user_doc_ref, {
                    'sender_id': user_message.sender_id,
                    'session_id': user_message.session_id,
                    'role': user_message.role.value,
                    'content': user_message.content,
                    'content_en': user_message.content_en,
                    'content_thai': user_message.content_thai,
                    'wa_message_id': user_message.wa_message_id,
                    'timestamp': user_message.timestamp,
                    'created_at': user_message.timestamp
                })
                
                # 4. Сохраняем сообщение AI
                ai_doc_ref = messages_ref.document()
                transaction.set(ai_doc_ref, {
                    'sender_id': ai_message.sender_id,
                    'session_id': ai_message.session_id,
                    'role': ai_message.role.value,
                    'content': ai_message.content,
                    'content_en': ai_message.content_en,
                    'content_thai': ai_message.content_thai,
                    'wa_message_id': ai_message.wa_message_id,
                    'timestamp': ai_message.timestamp,
                    'created_at': ai_message.timestamp
                })
                
                # 5. Добавляем оба сообщения в историю
                history.append({
                    'role': user_message.role.value,
                    'content': user_message.content,
                    'timestamp': user_message.timestamp,
                    'content_en': user_message.content_en,
                    'content_thai': user_message.content_thai
                })
                history.append({
                    'role': ai_message.role.value,
                    'content': ai_message.content,
                    'timestamp': ai_message.timestamp,
                    'content_en': ai_message.content_en,
                    'content_thai': ai_message.content_thai
                })
                
                return history
            
            transaction = self.db.transaction()
            history = transaction_callback(transaction, user_message, ai_message, limit)
            print(f"[SYNC] User and AI messages saved in single transaction, history: {len(history)} messages")
            return True, history
            
        except Exception as e:
            print(f"[SYNC] Error in user+AI transaction: {e}")
            return False, []

    async def get_last_message_by_sender(self, sender_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает последнее сообщение от пользователя
        """
        if not self.db:
            return None
        
        try:
            # Ищем в структуре conversations
            conversations_ref = self.db.collection('conversations').document(sender_id).collection('sessions')
            sessions = conversations_ref.stream()
            
            last_message = None
            last_timestamp = None
            
            for session_doc in sessions:
                messages_ref = session_doc.reference.collection('messages')
                query = messages_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1)
                messages = query.stream()
                
                for msg_doc in messages:
                    msg_data = msg_doc.to_dict()
                    timestamp = msg_data.get('timestamp')
                    
                    if timestamp and (last_timestamp is None or timestamp > last_timestamp):
                        last_timestamp = timestamp
                        last_message = {
                            'sender_id': sender_id,
                            'session_id': session_doc.id,
                            'role': msg_data.get('role', 'user'),
                            'content': msg_data.get('content', ''),
                            'timestamp': timestamp,
                            'content_en': msg_data.get('content_en'),
                            'content_thai': msg_data.get('content_thai'),
                            'wa_message_id': msg_data.get('wa_message_id')
                        }
            
            return last_message
            
        except Exception as e:
            print(f"Error getting last message: {e}")
            return None
    
    async def get_all_messages(self) -> List[Dict[str, Any]]:
        """Получает все сообщения из БД"""
        if not self.db:
            return []
        
        try:
            all_messages = []
            conversations_ref = self.db.collection('conversations')
            conversations = conversations_ref.stream()
            
            for conv_doc in conversations:
                sender_id = conv_doc.id
                sessions_ref = conv_doc.reference.collection('sessions')
                sessions = sessions_ref.stream()
                
                for session_doc in sessions:
                    session_id = session_doc.id
                    messages_ref = session_doc.reference.collection('messages')
                    messages = messages_ref.stream()
                    
                    for msg_doc in messages:
                        msg_data = msg_doc.to_dict()
                        all_messages.append({
                            'sender_id': sender_id,
                            'session_id': session_id,
                            'role': msg_data.get('role', 'user'),
                            'content': msg_data.get('content', ''),
                            'timestamp': msg_data.get('timestamp'),
                            'content_en': msg_data.get('content_en'),
                            'content_thai': msg_data.get('content_thai'),
                            'wa_message_id': msg_data.get('wa_message_id')
                        })
            
            return all_messages
            
        except Exception as e:
            print(f"Error getting all messages: {e}")
            return [] 
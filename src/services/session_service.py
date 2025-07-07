"""
Сервис для работы с сессиями пользователей
"""

from src.repositories.session_repository import SessionRepository
from src.models.session import Session
from src.utils.logging_decorator import log_function
from typing import Optional, List, Dict, Any
from datetime import datetime
import random
from google.cloud import firestore

class SessionService:
    def __init__(self):
        self.repo = SessionRepository()
        self.db = self._get_firestore_client()
    
    def _get_firestore_client(self):
        """Получает клиент Firestore"""
        try:
            return firestore.Client()
        except Exception as e:
            print(f"Failed to initialize Firestore client: {e}")
            return None

    @log_function("session_service")
    async def get_or_create_session_id(self, sender_id: str) -> str:
        """Получает существующий session_id или создает новый"""
        # Проверяем в users
        if self.db:
            try:
                doc_ref = self.db.collection('users').document(sender_id)
                doc = doc_ref.get()
                if doc.exists:
                    user_data = doc.to_dict()
                    session_id = user_data.get('session_id')
                    session_created = user_data.get('session_created')
                    
                    if session_id and session_created:
                        # Проверяем срок сессии (неделя)
                        from datetime import timedelta
                        session_date = session_created
                        if hasattr(session_date, 'timestamp'):
                            session_date = session_date.timestamp()
                        
                        week_ago = datetime.now() - timedelta(days=7)
                        if session_date > week_ago.timestamp():
                            print(f"Found valid session: {session_id} for {sender_id}")
                            return session_id
                        else:
                            print(f"Session expired, creating new one for {sender_id}")
            except Exception as e:
                print(f"Error checking users: {e}")
        
        # Создаём новую сессию
        new_session_id = self._generate_session_id(sender_id)
        await self._save_to_users(sender_id, new_session_id)
        
        print(f"Created new session: {new_session_id} for {sender_id}")
        return new_session_id

    @log_function("session_service")
    async def create_new_session_after_order(self, sender_id: str) -> str:
        """
        Создает новую сессию после заказа (команда /newses).
        Сохраняет только в users.
        """
        new_session_id = self._generate_session_id(sender_id)
        
        # Обновляем users
        await self._save_to_users(sender_id, new_session_id)
        
        print(f"Created new session after order: {new_session_id} for {sender_id}")
        return new_session_id

    async def _save_to_users(self, sender_id: str, session_id: str, user_name: str = None):
        """Сохраняет session_id и имя пользователя в коллекцию users"""
        if not self.db:
            return
        
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            user_data = {
                'session_id': session_id,
                'session_created': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Добавляем имя пользователя если передано
            if user_name:
                user_data['name'] = user_name
            
            doc_ref.set(user_data, merge=True)  # merge=True чтобы не перезаписывать существующие поля
            print(f"Saved to users: {sender_id} -> {session_id}")
        except Exception as e:
            print(f"Error saving to users: {e}")

    async def save_user_info(self, sender_id: str, user_name: str):
        """Сохраняет информацию о пользователе в коллекцию users"""
        if not self.db:
            return
        
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            doc_ref.set({
                'name': user_name,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)  # merge=True чтобы не перезаписывать session_id
            print(f"Saved user info: {sender_id} -> {user_name}")
        except Exception as e:
            print(f"Error saving user info: {e}")

    async def save_user_language(self, sender_id: str, session_id: str, user_language: str):
        """
        Сохраняет язык пользователя в сессию.
        
        Args:
            sender_id: ID пользователя
            session_id: ID сессии
            user_language: Код языка ('ru', 'en', 'th')
        """
        if not self.db:
            return
        
        try:
            # Сохраняем в документ сессии
            session_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
            session_ref.update({
                'user_language': user_language,
                'last_activity': firestore.SERVER_TIMESTAMP
            })
            print(f"Saved user language: {sender_id}/{session_id} -> {user_language}")
        except Exception as e:
            print(f"Error saving user language: {e}")

    async def get_user_language(self, sender_id: str, session_id: str) -> str:
        """
        Получает сохраненный язык пользователя из сессии.
        
        Args:
            sender_id: ID пользователя
            session_id: ID сессии
            
        Returns:
            str: Код языка или 'auto' если не найден
        """
        if not self.db:
            return 'auto'
        
        try:
            # Получаем из документа сессии
            session_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
            doc = session_ref.get()
            
            if doc.exists:
                session_data = doc.to_dict()
                user_language = session_data.get('user_language')
                if user_language:
                    print(f"Retrieved user language: {sender_id}/{session_id} -> {user_language}")
                    return user_language
            
            print(f"User language not found for: {sender_id}/{session_id}")
            return 'auto'
            
        except Exception as e:
            print(f"Error getting user language: {e}")
            return 'auto'

    async def get_user_info(self, sender_id: str) -> dict:
        """Получает информацию о пользователе из коллекции users"""
        if not self.db:
            return {}
        
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                print(f"Retrieved user info: {sender_id} -> {user_data}")
                return user_data
            else:
                print(f"User not found: {sender_id}")
                return {}
                
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {}

    def _generate_session_id(self, sender_id: str) -> str:
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        microseconds = now.microsecond
        random_num = random.randint(100, 999)
        return f"{timestamp_str}_{microseconds}_{random_num}"

    async def get_all_sessions_by_sender(self, sender_id: str) -> List[Dict[str, Any]]:
        """
        Получает все сессии пользователя из структуры conversations.
        Ищет сессии по наличию сообщений, а не по документам сессий.
        Возвращает список словарей с session_id.
        """
        if not self.db:
            return []
        
        try:
            # Получаем все подколлекции (сессии) у пользователя
            sessions_ref = self.db.collection('conversations').document(sender_id).collection('sessions')
            session_docs = list(sessions_ref.stream())
            
            session_list = []
            for session_doc in session_docs:
                session_id = session_doc.id
                session_data = session_doc.to_dict()
                
                # Проверяем, есть ли сообщения в этой сессии
                messages_ref = session_doc.reference.collection('messages')
                messages = list(messages_ref.limit(1).stream())
                
                if messages:  # Если есть хотя бы одно сообщение
                    session_list.append({
                        'session_id': session_id,
                        'created_at': session_data.get('created_at'),
                        'message_count': session_data.get('message_count', len(messages))
                    })
            
            print(f"Found {len(session_list)} sessions with messages for user {sender_id}")
            return session_list
            
        except Exception as e:
            print(f"Error getting sessions by sender: {e}")
            return []

    def save_user_language_sync(self, sender_id: str, session_id: str, user_language: str):
        if not self.db:
            return
        try:
            session_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
            session_ref.update({
                'user_language': user_language,
                'last_activity': firestore.SERVER_TIMESTAMP
            })
            print(f"[SYNC] Saved user language: {sender_id}/{session_id} -> {user_language}")
        except Exception as e:
            print(f"[SYNC] Error saving user language: {e}")

    def get_user_language_sync(self, sender_id: str, session_id: str) -> str:
        if not self.db:
            return 'auto'
        try:
            session_ref = self.db.collection('conversations').document(sender_id).collection('sessions').document(session_id)
            doc = session_ref.get()
            if doc.exists:
                session_data = doc.to_dict()
                user_language = session_data.get('user_language')
                if user_language:
                    print(f"[SYNC] Retrieved user language: {sender_id}/{session_id} -> {user_language}")
                    return user_language
            print(f"[SYNC] User language not found for: {sender_id}/{session_id}")
            return 'auto'
        except Exception as e:
            print(f"[SYNC] Error getting user language: {e}")
            return 'auto'

    def save_user_info_sync(self, sender_id: str, user_name: str):
        if not self.db:
            return
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            doc_ref.set({
                'name': user_name,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            print(f"[SYNC] Saved user info: {sender_id} -> {user_name}")
        except Exception as e:
            print(f"[SYNC] Error saving user info: {e}") 
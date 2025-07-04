"""
Сервис для работы с сессиями пользователей
"""

from src.repositories.session_repository import SessionRepository
from src.models.session import Session
from typing import Optional
from datetime import datetime
import random
from google.cloud import firestore
from src.utils.logging_utils import ContextLogger

class SessionService:
    def __init__(self):
        self.repo = SessionRepository()
        self.logger = ContextLogger("session_service")
        self.db = self._get_firestore_client()
    
    def _get_firestore_client(self):
        """Получает клиент Firestore"""
        try:
            return firestore.Client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore client: {e}")
            return None

    async def get_or_create_session_id(self, sender_id: str) -> str:
        """Получает существующий session_id или создает новый"""
        # Сначала проверяем в users (объединенная коллекция)
        if self.db:
            try:
                doc_ref = self.db.collection('users').document(sender_id)
                doc = doc_ref.get()
                if doc.exists:
                    user_data = doc.to_dict()
                    session_id = user_data.get('session_id')
                    if session_id:
                        self.logger.info(f"Found existing session: {session_id} for {sender_id}")
                        return session_id
            except Exception as e:
                self.logger.error(f"Error checking users: {e}")
        
        # Если нет в users, пробуем найти в sessions
        sessions = await self.repo.find_by_field('sender_id', sender_id, limit=1)
        if sessions:
            session_id = sessions[0].session_id
            # Сохраняем в users для совместимости
            await self._save_to_users(sender_id, session_id)
            return session_id
        
        # Если нет — создаём новую
        new_session_id = self._generate_session_id(sender_id)
        session = Session(
            session_id=new_session_id,
            sender_id=sender_id,
            created_at=datetime.now()
        )
        await self.repo.create(session)
        
        # Сохраняем в users для совместимости
        await self._save_to_users(sender_id, new_session_id)
        
        self.logger.info(f"Created new session: {new_session_id} for {sender_id}")
        return new_session_id

    async def create_new_session_after_order(self, sender_id: str) -> str:
        """
        Создает новую сессию после заказа (команда /newses).
        Сохраняет в users и sessions.
        """
        new_session_id = self._generate_session_id(sender_id)
        
        # Создаем новую сессию в sessions
        session = Session(
            session_id=new_session_id,
            sender_id=sender_id,
            created_at=datetime.now()
        )
        await self.repo.create(session)
        
        # Обновляем users
        await self._save_to_users(sender_id, new_session_id)
        
        self.logger.info(f"Created new session after order: {new_session_id} for {sender_id}")
        return new_session_id

    async def _save_to_users(self, sender_id: str, session_id: str, user_name: str = None):
        """Сохраняет session_id и имя пользователя в коллекцию users"""
        if not self.db:
            return
        
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            user_data = {
                'session_id': session_id,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Добавляем имя пользователя если передано
            if user_name:
                user_data['name'] = user_name
            
            doc_ref.set(user_data, merge=True)  # merge=True чтобы не перезаписывать существующие поля
            self.logger.info(f"Saved to users: {sender_id} -> {session_id}")
        except Exception as e:
            self.logger.error(f"Error saving to users: {e}")

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
            self.logger.info(f"Saved user info: {sender_id} -> {user_name}")
        except Exception as e:
            self.logger.error(f"Error saving user info: {e}")

    async def get_user_info(self, sender_id: str) -> dict:
        """Получает информацию о пользователе из коллекции users"""
        if not self.db:
            return {}
        
        try:
            doc_ref = self.db.collection('users').document(sender_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                self.logger.info(f"Retrieved user info: {sender_id} -> {user_data}")
                return user_data
            else:
                self.logger.warning(f"User not found: {sender_id}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            return {}

    def _generate_session_id(self, sender_id: str) -> str:
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        microseconds = now.microsecond
        random_num = random.randint(100, 999)
        return f"{timestamp_str}_{microseconds}_{random_num}" 
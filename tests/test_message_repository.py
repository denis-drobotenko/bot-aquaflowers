"""
Тесты для MessageRepository
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.repositories.message_repository import MessageRepository
from src.models.message import Message, MessageRole
from google.cloud import firestore
from datetime import datetime

class TestMessageRepository:
    
    @pytest.fixture
    def mock_firestore(self):
        """Мокаем Firestore клиент"""
        with patch('src.repositories.message_repository.firestore.Client') as mock_client:
            mock_db = Mock()
            mock_client.return_value = mock_db
            yield mock_db
    
    @pytest.fixture
    def repository(self, mock_firestore):
        """Создаем репозиторий с моком Firestore"""
        repo = MessageRepository()
        repo.db = mock_firestore
        return repo
    
    @pytest.fixture
    def sample_message(self):
        """Создаем тестовое сообщение"""
        return Message(
            sender_id="test_user",
            session_id="test_session",
            role=MessageRole.USER,
            content="Test message",
            wa_message_id="test_wa_id"
        )
    
    def test_init_with_firestore(self, mock_firestore):
        """Тест инициализации с Firestore"""
        repo = MessageRepository()
        assert repo.db is not None
        assert repo.logger is not None
    
    def test_init_without_firestore(self):
        """Тест инициализации без Firestore"""
        with patch('src.repositories.message_repository.firestore.Client', side_effect=Exception("No Firestore")):
            repo = MessageRepository()
            assert repo.db is None
            assert repo.logger is not None
    
    @pytest.mark.asyncio
    async def test_add_message_to_conversation_success(self, repository, sample_message, mock_firestore):
        """Тест успешного добавления сообщения"""
        # Мокаем операции Firestore для создания документа сессии и сообщения
        mock_session_doc_ref = Mock()
        mock_message_doc_ref = Mock()
        
        # Настраиваем цепочку вызовов для создания документа сессии
        mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_session_doc_ref
        
        # Настраиваем цепочку вызовов для создания сообщения
        mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_message_doc_ref
        
        result = await repository.add_message_to_conversation(sample_message)
        
        assert result is True
        # Проверяем, что set был вызван хотя бы один раз (для документа сессии или сообщения)
        assert mock_session_doc_ref.set.call_count >= 1 or mock_message_doc_ref.set.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_add_message_to_conversation_no_firestore(self, sample_message):
        """Тест добавления сообщения без Firestore"""
        repo = MessageRepository()
        repo.db = None
        
        result = await repo.add_message_to_conversation(sample_message)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_add_message_to_conversation_exception(self, repository, sample_message, mock_firestore):
        """Тест обработки исключения при добавлении сообщения"""
        mock_firestore.collection.side_effect = Exception("Firestore error")
        
        result = await repository.add_message_to_conversation(sample_message)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_success(self, repository, mock_firestore):
        """Тест получения истории сообщений"""
        # Мокаем сообщения
        mock_message1 = Mock()
        mock_message1.to_dict.return_value = {
            'role': 'user',
            'content': 'Hello',
            'timestamp': datetime.now()
        }
        mock_message1.id = 'msg1'
        
        mock_message2 = Mock()
        mock_message2.to_dict.return_value = {
            'role': 'assistant',
            'content': 'Hi there!',
            'timestamp': datetime.now()
        }
        mock_message2.id = 'msg2'
        
        mock_messages = [mock_message1, mock_message2]
        mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_messages
        
        result = await repository.get_conversation_history_by_sender("test_user", "test_session", limit=10)
        
        assert len(result) == 2
        assert result[0]['content'] == 'Hello'
        assert result[1]['content'] == 'Hi there!'
    
    @pytest.mark.asyncio
    async def test_get_message_by_wa_id_success(self, repository, mock_firestore):
        """Тест поиска сообщения по wa_message_id"""
        # Мокаем SessionService
        mock_session_service = Mock()
        mock_session_service.get_all_sessions_by_sender = AsyncMock(return_value=[
            {'session_id': 'session1', 'message_count': 5},
            {'session_id': 'session2', 'message_count': 3}
        ])
        
        # Мокаем сообщение
        mock_message_doc = Mock()
        mock_message_doc.exists = True
        mock_message_doc.to_dict.return_value = {
            'role': 'assistant',
            'content': 'Found message',
            'timestamp': datetime.now(),
            'content_en': 'Found message EN',
            'content_thai': 'Found message TH'
        }
        
        mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_message_doc
        
        result = await repository.get_message_by_wa_id("test_user", "test_wa_id", mock_session_service)
        
        assert result is not None
        assert result['content'] == 'Found message'
        assert result['content_en'] == 'Found message EN'
        assert result['content_thai'] == 'Found message TH'
    
    @pytest.mark.asyncio
    async def test_get_message_by_wa_id_not_found(self, repository, mock_firestore):
        """Тест поиска несуществующего сообщения"""
        mock_session_service = Mock()
        mock_session_service.get_all_sessions_by_sender = AsyncMock(return_value=[
            {'session_id': 'session1', 'message_count': 5}
        ])
        
        # Мокаем несуществующее сообщение
        mock_message_doc = Mock()
        mock_message_doc.exists = False
        
        mock_firestore.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.document.return_value.get.return_value = mock_message_doc
        
        result = await repository.get_message_by_wa_id("test_user", "nonexistent_wa_id", mock_session_service)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_message_by_wa_id_no_sessions(self, repository, mock_firestore):
        """Тест поиска сообщения без сессий"""
        mock_session_service = Mock()
        mock_session_service.get_all_sessions_by_sender = AsyncMock(return_value=[])
        
        result = await repository.get_message_by_wa_id("test_user", "test_wa_id", mock_session_service)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_message_by_wa_id_exception(self, repository, mock_firestore):
        """Тест обработки исключения при поиске сообщения"""
        mock_session_service = Mock()
        mock_session_service.get_all_sessions_by_sender = AsyncMock(side_effect=Exception("Session error"))
        
        result = await repository.get_message_by_wa_id("test_user", "test_wa_id", mock_session_service)
        
        assert result is None

if __name__ == "__main__":
    pytest.main([__file__]) 
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, Mock
from src.services.session_service import SessionService
from src.repositories.session_repository import SessionRepository
from datetime import datetime, timedelta


@pytest.fixture
def session_service():
    with patch('src.services.session_service.firestore.Client') as mock_firestore:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        service = SessionService()
        yield service


def test_init(session_service):
    assert isinstance(session_service.repo, SessionRepository)
    assert session_service.db is not None


def test_init_firestore_error():
    with patch('src.services.session_service.firestore.Client', side_effect=Exception("Firestore error")):
        service = SessionService()
        assert service.db is None


@pytest.mark.asyncio
async def test_get_or_create_session_id_existing_valid(session_service):
    # Мокаем Firestore
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        'session_id': 'existing_session_123',
        'session_created': datetime.now().timestamp()
    }
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Мокаем сохранение
    with patch.object(session_service, '_save_to_users') as mock_save:
        result = await session_service.get_or_create_session_id("user_123")
        
        assert result == "existing_session_123"
        mock_save.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_session_id_expired(session_service):
    # Мокаем Firestore с истекшей сессией
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        'session_id': 'expired_session_123',
        'session_created': (datetime.now() - timedelta(days=8)).timestamp()  # Истекла неделю назад
    }
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Мокаем сохранение
    with patch.object(session_service, '_save_to_users') as mock_save:
        result = await session_service.get_or_create_session_id("user_123")
        
        # Должна быть создана новая сессия
        assert isinstance(result, str)
        assert len(result) > 20
        assert result.count('_') == 3
        assert result != 'expired_session_123'
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_session_id_new_user(session_service):
    # Мокаем Firestore с несуществующим пользователем
    mock_doc = MagicMock()
    mock_doc.exists = False
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Мокаем сохранение
    with patch.object(session_service, '_save_to_users') as mock_save:
        result = await session_service.get_or_create_session_id("new_user_123")
        
        # Должна быть создана новая сессия
        assert isinstance(result, str)
        assert len(result) > 20
        assert result.count('_') == 3
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_session_id_firestore_error(session_service):
    # Мокаем ошибку Firestore
    mock_collection = MagicMock()
    mock_collection.document.side_effect = Exception("Firestore error")
    session_service.db.collection.return_value = mock_collection
    
    # Мокаем сохранение
    with patch.object(session_service, '_save_to_users') as mock_save:
        result = await session_service.get_or_create_session_id("user_123")
        
        # Должна быть создана новая сессия
        assert isinstance(result, str)
        assert len(result) > 20
        assert result.count('_') == 3
        mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_session_after_order(session_service):
    # Мокаем сохранение
    with patch.object(session_service, '_save_to_users') as mock_save:
        result = await session_service.create_new_session_after_order("user_123")
        
        # Должна быть создана новая сессия
        assert isinstance(result, str)
        assert len(result) > 20
        assert result.count('_') == 3
        mock_save.assert_called_once_with("user_123", result)


@pytest.mark.asyncio
async def test_save_to_users_success(session_service):
    # Мокаем Firestore
    mock_doc_ref = MagicMock()
    mock_doc_ref.set = MagicMock()
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    await session_service._save_to_users("user_123", "session_456", "Test User")
    
    mock_doc_ref.set.assert_called_once()
    call_args = mock_doc_ref.set.call_args
    assert call_args[1]['merge'] is True


@pytest.mark.asyncio
async def test_save_to_users_no_db(session_service):
    session_service.db = None
    
    # Не должно вызывать исключение
    await session_service._save_to_users("user_123", "session_456", "Test User")


@pytest.mark.asyncio
async def test_save_to_users_error(session_service):
    # Мокаем Firestore с ошибкой
    mock_doc_ref = MagicMock()
    mock_doc_ref.set.side_effect = Exception("Firestore error")
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Не должно вызывать исключение
    await session_service._save_to_users("user_123", "session_456", "Test User")


@pytest.mark.asyncio
async def test_save_user_info_success(session_service):
    # Мокаем Firestore
    mock_doc_ref = MagicMock()
    mock_doc_ref.set = MagicMock()
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    await session_service.save_user_info("user_123", "Test User")
    
    mock_doc_ref.set.assert_called_once()
    call_args = mock_doc_ref.set.call_args
    assert call_args[1]['merge'] is True


@pytest.mark.asyncio
async def test_save_user_info_no_db(session_service):
    session_service.db = None
    
    # Не должно вызывать исключение
    await session_service.save_user_info("user_123", "Test User")


@pytest.mark.asyncio
async def test_save_user_info_error(session_service):
    # Мокаем Firestore с ошибкой
    mock_doc_ref = MagicMock()
    mock_doc_ref.set.side_effect = Exception("Firestore error")
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Не должно вызывать исключение
    await session_service.save_user_info("user_123", "Test User")


@pytest.mark.asyncio
async def test_get_user_info_success(session_service):
    # Мокаем Firestore
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        'name': 'Test User',
        'session_id': 'session_123',
        'updated_at': datetime.now()
    }
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_user_info("user_123")
    
    assert result['name'] == 'Test User'
    assert result['session_id'] == 'session_123'


@pytest.mark.asyncio
async def test_get_user_info_not_found(session_service):
    # Мокаем Firestore
    mock_doc = MagicMock()
    mock_doc.exists = False
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_user_info("user_123")
    
    assert result == {}


@pytest.mark.asyncio
async def test_get_user_info_no_db(session_service):
    session_service.db = None
    
    result = await session_service.get_user_info("user_123")
    
    assert result == {}


@pytest.mark.asyncio
async def test_get_user_info_error(session_service):
    # Мокаем Firestore с ошибкой
    mock_collection = MagicMock()
    mock_collection.document.side_effect = Exception("Firestore error")
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_user_info("user_123")
    
    assert result == {}


def test_generate_session_id(session_service):
    result = session_service._generate_session_id("user_123")
    
    # Проверяем формат: YYYYMMDD_HHMMSS_microseconds_random
    assert isinstance(result, str)
    assert len(result) > 20
    assert "_" in result
    assert result.count("_") == 3


@pytest.mark.asyncio
async def test_get_all_sessions_by_sender_success(session_service):
    # Мокаем Firestore
    mock_session_doc1 = MagicMock()
    mock_session_doc1.id = "session_1"
    mock_session_doc1.to_dict.return_value = {'created_at': datetime.now(), 'message_count': 5}
    
    mock_session_doc2 = MagicMock()
    mock_session_doc2.id = "session_2"
    mock_session_doc2.to_dict.return_value = {'created_at': datetime.now(), 'message_count': 3}
    
    # Мокаем сообщения для первой сессии
    mock_message1 = MagicMock()
    mock_messages_ref1 = MagicMock()
    mock_messages_ref1.limit.return_value.stream.return_value = [mock_message1]
    
    # Мокаем пустые сообщения для второй сессии
    mock_messages_ref2 = MagicMock()
    mock_messages_ref2.limit.return_value.stream.return_value = []
    
    mock_session_doc1.reference.collection.return_value = mock_messages_ref1
    mock_session_doc2.reference.collection.return_value = mock_messages_ref2
    
    mock_sessions_ref = MagicMock()
    mock_sessions_ref.stream.return_value = [mock_session_doc1, mock_session_doc2]
    
    mock_conversations_doc = MagicMock()
    mock_conversations_doc.collection.return_value = mock_sessions_ref
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_conversations_doc
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_all_sessions_by_sender("user_123")
    
    assert len(result) == 1  # Только сессия с сообщениями
    assert result[0]['session_id'] == "session_1"


@pytest.mark.asyncio
async def test_get_all_sessions_by_sender_no_sessions(session_service):
    # Мокаем Firestore с пустыми сессиями
    mock_sessions_ref = MagicMock()
    mock_sessions_ref.stream.return_value = []
    
    mock_conversations_doc = MagicMock()
    mock_conversations_doc.collection.return_value = mock_sessions_ref
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_conversations_doc
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_all_sessions_by_sender("user_123")
    
    assert result == []


@pytest.mark.asyncio
async def test_get_all_sessions_by_sender_no_db(session_service):
    session_service.db = None
    
    result = await session_service.get_all_sessions_by_sender("user_123")
    
    assert result == []


@pytest.mark.asyncio
async def test_get_all_sessions_by_sender_error(session_service):
    # Мокаем Firestore с ошибкой
    mock_collection = MagicMock()
    mock_collection.document.side_effect = Exception("Firestore error")
    
    session_service.db.collection.return_value = mock_collection
    
    result = await session_service.get_all_sessions_by_sender("user_123")
    
    assert result == []


@pytest.fixture
def mock_firestore():
    with patch('src.services.session_service.firestore') as mock_fs:
        yield mock_fs


@pytest.fixture
def mock_db():
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    return mock_db


class TestSessionService:
    
    @pytest.mark.asyncio
    async def test_save_user_language(self, session_service, mock_db):
        """Тест сохранения языка пользователя"""
        session_service.db = mock_db
        
        # Настройка моков
        mock_session_ref = Mock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_session_ref
        
        # Вызов метода
        await session_service.save_user_language("user123", "session456", "ru")
        
        # Проверка вызовов
        mock_session_ref.update.assert_called_once()
        call_args = mock_session_ref.update.call_args[0][0]
        assert call_args['user_language'] == 'ru'
        assert 'last_activity' in call_args
    
    @pytest.mark.asyncio
    async def test_get_user_language_found(self, session_service, mock_db):
        """Тест получения языка пользователя - язык найден"""
        session_service.db = mock_db
        
        # Настройка моков
        mock_session_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'user_language': 'en'}
        mock_session_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_session_ref
        
        # Вызов метода
        result = await session_service.get_user_language("user123", "session456")
        
        # Проверка результата
        assert result == 'en'
    
    @pytest.mark.asyncio
    async def test_get_user_language_not_found(self, session_service, mock_db):
        """Тест получения языка пользователя - язык не найден"""
        session_service.db = mock_db
        
        # Настройка моков
        mock_session_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = False
        mock_session_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_session_ref
        
        # Вызов метода
        result = await session_service.get_user_language("user123", "session456")
        
        # Проверка результата
        assert result == 'auto'
    
    @pytest.mark.asyncio
    async def test_get_user_language_no_db(self, session_service):
        """Тест получения языка пользователя - нет подключения к БД"""
        session_service.db = None
        
        # Вызов метода
        result = await session_service.get_user_language("user123", "session456")
        
        # Проверка результата
        assert result == 'auto'
    
    @pytest.mark.asyncio
    async def test_save_user_language_no_db(self, session_service):
        """Тест сохранения языка пользователя - нет подключения к БД"""
        session_service.db = None
        
        # Вызов метода не должен вызывать ошибку
        await session_service.save_user_language("user123", "session456", "th")
    
    @pytest.mark.asyncio
    async def test_get_user_language_with_metadata(self, session_service, mock_db):
        """Тест получения языка пользователя с метаданными"""
        session_service.db = mock_db
        
        # Настройка моков
        mock_session_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'user_language': 'th',
            'message_count': 5,
            'created_at': datetime.now()
        }
        mock_session_ref.get.return_value = mock_doc
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value = mock_session_ref
        
        # Вызов метода
        result = await session_service.get_user_language("user123", "session456")
        
        # Проверка результата
        assert result == 'th' 
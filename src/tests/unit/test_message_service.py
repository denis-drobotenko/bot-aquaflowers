import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.message_service import MessageService
from src.models.message import Message, MessageRole


@pytest.fixture
def message_service():
    with patch('src.services.message_service.firestore.Client') as mock_firestore, \
         patch('src.services.message_service.MessageRepository') as mock_repo_class:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        mock_repo = MagicMock()
        mock_repo.create = AsyncMock()
        mock_repo.add_message_to_conversation = AsyncMock()
        mock_repo.get_by_id = AsyncMock()
        mock_repo.find_by_field = AsyncMock()
        mock_repo.find_session_owner = AsyncMock()
        mock_repo.get_conversation_history_by_sender = AsyncMock()
        mock_repo.update = AsyncMock()
        mock_repo.get_message_by_wa_id = AsyncMock()
        mock_repo_class.return_value = mock_repo
        service = MessageService()
        yield service


def test_init(message_service):
    assert isinstance(message_service.repo, MagicMock)
    assert message_service.db is not None


def test_init_firestore_error():
    with patch('src.services.message_service.firestore.Client', side_effect=Exception("Firestore error")):
        service = MessageService()
        assert service.db is None


@pytest.mark.asyncio
async def test_add_message_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = "message_id_123"
        
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Test message"
        )
        
        result = await message_service.add_message(message)
        
        assert result == "message_id_123"
        mock_create.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_add_message_to_conversation_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'add_message_to_conversation', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = True
        
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Test message"
        )
        
        result = await message_service.add_message_to_conversation(message)
        
        assert result == "success"
        mock_add.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_add_message_to_conversation_failure(message_service):
    # Мокаем репозиторий с ошибкой
    with patch.object(message_service.repo, 'add_message_to_conversation', new_callable=AsyncMock) as mock_add:
        mock_add.return_value = False
        
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Test message"
        )
        
        result = await message_service.add_message_to_conversation(message)
        
        assert result is None


@pytest.mark.asyncio
async def test_add_message_to_conversation_error(message_service):
    # Мокаем репозиторий с исключением
    with patch.object(message_service.repo, 'add_message_to_conversation', side_effect=Exception("DB Error")):
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Test message"
        )
        
        result = await message_service.add_message_to_conversation(message)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_message_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
        expected_message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Test message"
        )
        mock_get.return_value = expected_message
        
        result = await message_service.get_message("message_id_123")
        
        assert result == expected_message
        mock_get.assert_called_once_with("message_id_123")


@pytest.mark.asyncio
async def test_get_message_not_found(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        result = await message_service.get_message("nonexistent_id")
        
        assert result is None


@pytest.mark.asyncio
async def test_get_conversation_history_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find:
        expected_messages = [
            Message(sender_id="user_123", session_id="session_456", role=MessageRole.USER, content="Message 1"),
            Message(sender_id="user_123", session_id="session_456", role=MessageRole.ASSISTANT, content="Message 2")
        ]
        mock_find.return_value = expected_messages
        
        result = await message_service.get_conversation_history("session_456", limit=10)
        
        assert len(result) == 2
        mock_find.assert_called_once_with('session_id', 'session_456', limit=10)


@pytest.mark.asyncio
async def test_get_conversation_history_empty(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find:
        mock_find.return_value = []
        
        result = await message_service.get_conversation_history("session_456")
        
        assert result == []


@pytest.mark.asyncio
async def test_get_conversation_history_for_ai_success(message_service):
    # Мокаем поиск владельца сессии
    with patch.object(message_service.repo, 'find_session_owner', new_callable=AsyncMock) as mock_find_owner:
        mock_find_owner.return_value = "user_123"
        
        # Мокаем получение истории
        with patch.object(message_service.repo, 'get_conversation_history_by_sender', new_callable=AsyncMock) as mock_get_history:
            expected_history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
            mock_get_history.return_value = expected_history
            
            result = await message_service.get_conversation_history_for_ai("session_456", limit=10)
            
            assert result == expected_history
            mock_find_owner.assert_called_once_with("session_456")
            mock_get_history.assert_called_once_with("user_123", "session_456", limit=10)


@pytest.mark.asyncio
async def test_get_conversation_history_for_ai_session_not_found(message_service):
    # Мокаем поиск владельца сессии
    with patch.object(message_service.repo, 'find_session_owner', new_callable=AsyncMock) as mock_find_owner:
        mock_find_owner.return_value = None
        
        result = await message_service.get_conversation_history_for_ai("session_456")
        
        assert result == []


@pytest.mark.asyncio
async def test_get_conversation_history_for_ai_error(message_service):
    # Мокаем ошибку
    with patch.object(message_service.repo, 'find_session_owner', side_effect=Exception("DB Error")):
        result = await message_service.get_conversation_history_for_ai("session_456")
        
        assert result == []


@pytest.mark.asyncio
async def test_get_conversation_history_for_ai_by_sender_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'get_conversation_history_by_sender', new_callable=AsyncMock) as mock_get_history:
        expected_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        mock_get_history.return_value = expected_history
        
        result = await message_service.get_conversation_history_for_ai_by_sender("user_123", "session_456", limit=10)
        
        assert result == expected_history
        mock_get_history.assert_called_once_with("user_123", "session_456", limit=10)


@pytest.mark.asyncio
async def test_get_conversation_history_for_ai_by_sender_error(message_service):
    # Мокаем ошибку
    with patch.object(message_service.repo, 'get_conversation_history_by_sender', side_effect=Exception("DB Error")):
        result = await message_service.get_conversation_history_for_ai_by_sender("user_123", "session_456")
        
        assert result == []


@pytest.mark.asyncio
async def test_update_message_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'update', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True
        
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Updated message"
        )
        
        result = await message_service.update_message("message_id_123", message)
        
        assert result is True
        mock_update.assert_called_once_with("message_id_123", message)


@pytest.mark.asyncio
async def test_update_message_failure(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'update', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = False
        
        message = Message(
            sender_id="user_123",
            session_id="session_456",
            role=MessageRole.USER,
            content="Updated message"
        )
        
        result = await message_service.update_message("message_id_123", message)
        
        assert result is False


@pytest.mark.asyncio
async def test_get_message_by_wa_id_success(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'get_message_by_wa_id', new_callable=AsyncMock) as mock_get:
        expected_message = {
            "sender_id": "user_123",
            "session_id": "session_456",
            "wa_message_id": "wa_msg_123",
            "content": "Test message"
        }
        mock_get.return_value = expected_message
        
        result = await message_service.get_message_by_wa_id("user_123", "session_456", "wa_msg_123")
        
        assert result == expected_message
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_message_by_wa_id_not_found(message_service):
    # Мокаем репозиторий
    with patch.object(message_service.repo, 'get_message_by_wa_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        result = await message_service.get_message_by_wa_id("user_123", "session_456", "wa_msg_123")
        
        assert result is None


@pytest.mark.asyncio
async def test_get_message_by_wa_id_error(message_service):
    # Мокаем ошибку
    with patch.object(message_service.repo, 'get_message_by_wa_id', side_effect=Exception("DB Error")):
        result = await message_service.get_message_by_wa_id("user_123", "session_456", "wa_msg_123")
        
        assert result is None 
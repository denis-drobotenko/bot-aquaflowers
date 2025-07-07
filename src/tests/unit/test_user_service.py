import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.user_service import UserService
from src.repositories.user_repository import UserRepository
from src.models.user import User, UserStatus


@pytest.fixture
def user_service():
    return UserService()


def test_init(user_service):
    assert isinstance(user_service.repo, UserRepository)
    assert hasattr(user_service, 'logger')


@pytest.mark.asyncio
async def test_create_user_success(user_service):
    with patch.object(user_service.repo, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = "user_id_123"
        user = User(sender_id="user_123", name="Test User", phone="+1234567890")
        result = await user_service.create_user(user)
        assert result == "user_id_123"
        mock_create.assert_called_once_with(user)


@pytest.mark.asyncio
async def test_create_user_failure(user_service):
    with patch.object(user_service.repo, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = None
        user = User(sender_id="user_123", name="Test User", phone="+1234567890")
        result = await user_service.create_user(user)
        assert result is None


@pytest.mark.asyncio
async def test_get_user_success(user_service):
    with patch.object(user_service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
        expected_user = User(sender_id="user_123", name="Test User", phone="+1234567890", status=UserStatus.ACTIVE)
        mock_get.return_value = expected_user
        result = await user_service.get_user("user_123")
        assert result == expected_user
        mock_get.assert_called_once_with("user_123")


@pytest.mark.asyncio
async def test_get_user_not_found(user_service):
    with patch.object(user_service.repo, 'get_by_id', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        result = await user_service.get_user("nonexistent_id")
        assert result is None


@pytest.mark.asyncio
async def test_update_user_success(user_service):
    with patch.object(user_service.repo, 'update', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = True
        user = User(sender_id="user_123", name="Updated User", phone="+1234567890", status=UserStatus.ACTIVE)
        result = await user_service.update_user("user_123", user)
        assert result is True
        mock_update.assert_called_once_with("user_123", user)


@pytest.mark.asyncio
async def test_update_user_failure(user_service):
    with patch.object(user_service.repo, 'update', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = False
        user = User(sender_id="user_123", name="Updated User", phone="+1234567890")
        result = await user_service.update_user("user_123", user)
        assert result is False


@pytest.mark.asyncio
async def test_block_user_success(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user, \
         patch.object(user_service, 'update_user', new_callable=AsyncMock) as mock_update_user:
        user = User(sender_id="user_123", name="Test User", status=UserStatus.ACTIVE)
        mock_get_user.return_value = user
        mock_update_user.return_value = True
        result = await user_service.block_user("user_123")
        assert result is True
        assert user.status == UserStatus.BLOCKED
        mock_get_user.assert_called_once_with("user_123")
        mock_update_user.assert_called_once_with("user_123", user)


@pytest.mark.asyncio
async def test_block_user_not_found(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None
        result = await user_service.block_user("nonexistent_id")
        assert result is False


@pytest.mark.asyncio
async def test_block_user_already_blocked(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user, \
         patch.object(user_service, 'update_user', new_callable=AsyncMock) as mock_update_user:
        user = User(sender_id="user_123", name="Test User", status=UserStatus.BLOCKED)
        mock_get_user.return_value = user
        mock_update_user.return_value = True
        result = await user_service.block_user("user_123")
        assert result is True
        assert user.status == UserStatus.BLOCKED
        mock_get_user.assert_called_once_with("user_123")
        mock_update_user.assert_called_once_with("user_123", user)


@pytest.mark.asyncio
async def test_activate_user_success(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user, \
         patch.object(user_service, 'update_user', new_callable=AsyncMock) as mock_update_user:
        user = User(sender_id="user_123", name="Test User", status=UserStatus.BLOCKED)
        mock_get_user.return_value = user
        mock_update_user.return_value = True
        result = await user_service.activate_user("user_123")
        assert result is True
        assert user.status == UserStatus.ACTIVE
        mock_get_user.assert_called_once_with("user_123")
        mock_update_user.assert_called_once_with("user_123", user)


@pytest.mark.asyncio
async def test_activate_user_not_found(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None
        result = await user_service.activate_user("nonexistent_id")
        assert result is False


@pytest.mark.asyncio
async def test_activate_user_already_active(user_service):
    with patch.object(user_service, 'get_user', new_callable=AsyncMock) as mock_get_user, \
         patch.object(user_service, 'update_user', new_callable=AsyncMock) as mock_update_user:
        user = User(sender_id="user_123", name="Test User", status=UserStatus.ACTIVE)
        mock_get_user.return_value = user
        mock_update_user.return_value = True
        result = await user_service.activate_user("user_123")
        assert result is True
        assert user.status == UserStatus.ACTIVE
        mock_get_user.assert_called_once_with("user_123")
        mock_update_user.assert_called_once_with("user_123", user) 
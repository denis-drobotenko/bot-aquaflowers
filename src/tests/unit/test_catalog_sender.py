import pytest
from unittest.mock import patch, AsyncMock
from src.services.catalog_sender import CatalogSender


@pytest.fixture
def catalog_sender():
    with patch('src.services.catalog_sender.CatalogService') as mock_catalog_service:
        sender = CatalogSender()
        sender.catalog_service = mock_catalog_service
        return sender


@pytest.mark.asyncio
async def test_get_catalog_messages_success(catalog_sender):
    catalog_sender.catalog_service.get_available_products = AsyncMock(return_value=[
        {
            "name": "Test Bouquet",
            "price": "1000",
            "image_url": "https://example.com/image.jpg",
            "retailer_id": "test_id"
        }
    ])
    messages = await catalog_sender.get_catalog_messages("+1234567890", "user_123", "session_456")
    assert len(messages) == 1
    assert messages[0]["type"] == "image"
    assert messages[0]["image_url"] == "https://example.com/image.jpg"
    assert "Test Bouquet" in messages[0]["caption"]
    assert "1000" in messages[0]["caption"]
    # Эмодзи 🌸 теперь добавляется в MessageProcessor, не в CatalogSender


@pytest.mark.asyncio
async def test_get_catalog_messages_empty(catalog_sender):
    catalog_sender.catalog_service.get_available_products = AsyncMock(return_value=[])
    messages = await catalog_sender.get_catalog_messages("+1234567890", "user_123", "session_456")
    assert len(messages) == 1
    assert messages[0]["type"] == "text"
    assert "нет букетов" in messages[0]["content"]


@pytest.mark.asyncio
async def test_get_catalog_messages_error(catalog_sender):
    catalog_sender.catalog_service.get_available_products = AsyncMock(side_effect=Exception("API Error"))
    messages = await catalog_sender.get_catalog_messages("+1234567890", "user_123", "session_456")
    assert len(messages) == 1
    assert messages[0]["type"] == "text"
    assert "ошибка" in messages[0]["content"] 
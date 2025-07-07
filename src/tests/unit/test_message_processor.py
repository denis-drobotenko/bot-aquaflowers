import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.message_processor import MessageProcessor


@pytest.fixture
def message_processor():
    with patch('src.services.message_processor.WhatsAppClient') as mock_whatsapp_client:
        with patch('src.services.message_processor.MessageService') as mock_message_service:
            processor = MessageProcessor()
            processor.whatsapp_client = mock_whatsapp_client
            processor.message_service = mock_message_service
            return processor


def test_init(message_processor):
    assert isinstance(message_processor.whatsapp_client, MagicMock)
    assert isinstance(message_processor.message_service, MagicMock)


@pytest.mark.asyncio
async def test_send_text_message_success(message_processor):
    # Мокаем отправку текста
    message_processor.whatsapp_client.send_text_message = AsyncMock(return_value="test_message_id")
    
    result = await message_processor.send_message(
        "+1234567890",
        "Привет!",
        "text",
        save_to_db=True,
        session_id="session_123",
        sender_id="user_456"
    )
    
    assert result is True
    message_processor.whatsapp_client.send_text_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_text_message_without_db_save(message_processor):
    # Мокаем отправку текста
    message_processor.whatsapp_client.send_text_message = AsyncMock(return_value="test_message_id")
    
    result = await message_processor.send_message(
        "+1234567890",
        "Привет!",
        "text",
        save_to_db=False
    )
    
    assert result is True
    message_processor.whatsapp_client.send_text_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_text_message_error(message_processor):
    # Мокаем ошибку отправки
    message_processor.whatsapp_client.send_text_message = AsyncMock(return_value=None)
    
    result = await message_processor.send_message(
        "+1234567890",
        "Привет!",
        "text"
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_send_image_message_success(message_processor):
    # Мокаем отправку изображения
    message_processor.whatsapp_client.send_image_with_caption = AsyncMock(return_value="test_message_id")
    
    result = await message_processor.send_message(
        "+1234567890",
        "Красивый букет",
        "image",
        {"image_url": "https://example.com/image.jpg"},
        save_to_db=True,
        session_id="session_123",
        sender_id="user_456"
    )
    
    assert result is True
    message_processor.whatsapp_client.send_image_with_caption.assert_called_once()


@pytest.mark.asyncio
async def test_send_image_message_error_with_fallback(message_processor):
    # Мокаем ошибку отправки изображения
    message_processor.whatsapp_client.send_image_with_caption = AsyncMock(return_value=None)
    # Мокаем успешный fallback на текст
    message_processor.whatsapp_client.send_text_message = AsyncMock(return_value="fallback_message_id")
    
    result = await message_processor.send_message(
        "+1234567890",
        "Красивый букет",
        "image",
        {"image_url": "https://example.com/image.jpg"}
    )
    
    assert result is True
    message_processor.whatsapp_client.send_text_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_image_message_error_without_fallback(message_processor):
    # Мокаем ошибку отправки изображения
    message_processor.whatsapp_client.send_image_with_caption = AsyncMock(return_value=None)
    # Мокаем ошибку fallback
    message_processor.whatsapp_client.send_text_message = AsyncMock(return_value=None)
    
    result = await message_processor.send_message(
        "+1234567890",
        "Красивый букет",
        "image",
        {"image_url": "https://example.com/image.jpg"}
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_send_unknown_message_type(message_processor):
    result = await message_processor.send_message(
        "+1234567890",
        "Тест",
        "unknown_type"
    )
    
    assert result is False


def test_add_flower_emoji():
    processor = MessageProcessor()
    
    # Тест добавления 🌸 если нет
    result = processor._add_flower_emoji("Простой текст")
    assert result == "Простой текст 🌸"
    
    # Тест если уже есть 🌸
    result = processor._add_flower_emoji("Текст 🌸")
    assert result == "Текст 🌸"
    
    # Тест пустого текста
    result = processor._add_flower_emoji("")
    assert result == "🌸"

def test_clean_caption():
    processor = MessageProcessor()
    
    # Тест очистки эмодзи
    result = processor._clean_caption("Красивый букет 💕")
    assert result == "Красивый букет 🌸"
    
    # Тест добавления 🌸 если нет
    result = processor._clean_caption("Простой текст")
    assert result == "Простой текст 🌸"
    
    # Тест если уже есть 🌸
    result = processor._clean_caption("Текст 🌸")
    assert result == "Текст 🌸"


@pytest.mark.asyncio
async def test_process_incoming_message(message_processor):
    # Мокаем сохранение сообщения
    message_processor.message_service.add_message_to_conversation = AsyncMock()
    
    result = await message_processor.process_incoming_message(
        "+1234567890",
        "Привет!",
        save_to_db=True,
        session_id="session_123",
        sender_id="user_456"
    )
    
    assert result == "Привет!"
    message_processor.message_service.add_message_to_conversation.assert_called_once()


@pytest.mark.asyncio
async def test_process_incoming_message_without_db_save(message_processor):
    result = await message_processor.process_incoming_message(
        "+1234567890",
        "Привет!",
        save_to_db=False
    )
    
    assert result == "Привет!"
    # Не должно вызывать сохранение в БД
    message_processor.message_service.add_message_to_conversation.assert_not_called() 
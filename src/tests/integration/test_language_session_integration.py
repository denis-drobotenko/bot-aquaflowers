"""
Интеграционные тесты для работы с языком сессии
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.message_processor import MessageProcessor
from src.services.session_service import SessionService
from src.services.ai_service import AIService
from src.models.message import Message, MessageRole

@pytest.fixture
def mock_ai_service():
    with patch('src.handlers.message_handler.AIService') as mock_ai:
        mock_instance = Mock()
        mock_instance.detect_language.return_value = 'ru'
        mock_instance.translate_user_message.return_value = ('Привет', 'Hello', 'สวัสดี')
        mock_instance.generate_response.return_value = ('Здравствуйте!', 'Hello!', 'สวัสดี!', None)
        mock_ai.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_session_service():
    with patch('src.handlers.message_handler.SessionService') as mock_session:
        mock_instance = Mock()
        mock_instance.get_or_create_session_id.return_value = 'session_123'
        mock_instance.get_user_language.return_value = 'auto'
        mock_instance.save_user_language = AsyncMock()
        mock_instance.save_user_info = AsyncMock()
        mock_session.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_message_service():
    with patch('src.handlers.message_handler.MessageService') as mock_message:
        mock_instance = Mock()
        mock_instance.add_message_to_conversation = AsyncMock()
        mock_instance.get_conversation_history_for_ai_by_sender.return_value = []
        mock_message.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def message_handler(mock_ai_service, mock_session_service, mock_message_service):
    """Создает MessageProcessor с замоканными зависимостями"""
    return MessageProcessor()

class TestLanguageSessionIntegration:
    
    @pytest.mark.asyncio
    async def test_first_message_language_detection(
        self, 
        message_handler, 
        mock_ai_service, 
        mock_session_service, 
        mock_message_service
    ):
        """Тест определения языка при первом сообщении"""
        
        # Настройка моков
        mock_session_service.get_user_language.return_value = 'auto'
        mock_ai_service.detect_language.return_value = 'ru'
        
        # Вызов метода
        result = await message_handler.process_text_message(
            sender_id="user123",
            message_text="Привет, как дела?",
            sender_name="Иван"
        )
        
        # Проверки
        mock_session_service.get_user_language.assert_called_once_with("user123", "session_123")
        mock_ai_service.detect_language.assert_called_once_with("Привет, как дела?")
        mock_session_service.save_user_language.assert_called_once_with("user123", "session_123", "ru")
        
        # Проверка результата
        assert result[0] == 'Здравствуйте!'  # Основной ответ
        assert result[1] == 'Hello!'  # Английский
        assert result[2] == 'สวัสดี!'  # Тайский
    
    @pytest.mark.asyncio
    async def test_subsequent_message_uses_saved_language(
        self, 
        message_handler, 
        mock_ai_service, 
        mock_session_service, 
        mock_message_service
    ):
        """Тест использования сохраненного языка при последующих сообщениях"""
        
        # Настройка моков - язык уже сохранен
        mock_session_service.get_user_language.return_value = 'en'
        mock_ai_service.detect_language.return_value = 'ru'  # Не должен вызываться
        
        # Вызов метода
        result = await message_handler.process_text_message(
            sender_id="user123",
            message_text="Hello, how are you?",
            sender_name="John"
        )
        
        # Проверки
        mock_session_service.get_user_language.assert_called_once_with("user123", "session_123")
        # detect_language не должен вызываться, так как язык уже сохранен
        mock_ai_service.detect_language.assert_not_called()
        # save_user_language не должен вызываться
        mock_session_service.save_user_language.assert_not_called()
        
        # Проверка результата
        assert result[0] == 'Здравствуйте!'
    
    @pytest.mark.asyncio
    async def test_language_persistence_across_messages(
        self, 
        message_handler, 
        mock_ai_service, 
        mock_session_service, 
        mock_message_service
    ):
        """Тест сохранения языка между сообщениями"""
        
        # Первое сообщение - определяем язык
        mock_session_service.get_user_language.return_value = 'auto'
        mock_ai_service.detect_language.return_value = 'th'
        
        await message_handler.process_text_message(
            sender_id="user123",
            message_text="สวัสดี",
            sender_name="สมชาย"
        )
        
        # Проверяем, что язык был сохранен
        mock_session_service.save_user_language.assert_called_once_with("user123", "session_123", "th")
        
        # Второе сообщение - используем сохраненный язык
        mock_session_service.reset_mock()
        mock_ai_service.reset_mock()
        mock_session_service.get_user_language.return_value = 'th'
        
        await message_handler.process_text_message(
            sender_id="user123",
            message_text="ขอบคุณ",
            sender_name="สมชาย"
        )
        
        # Проверяем, что язык не переопределялся
        mock_ai_service.detect_language.assert_not_called()
        mock_session_service.save_user_language.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_language_fallback_to_auto(
        self, 
        message_handler, 
        mock_ai_service, 
        mock_session_service, 
        mock_message_service
    ):
        """Тест fallback на auto при некорректном языке"""
        
        # Настройка моков - некорректный язык
        mock_session_service.get_user_language.return_value = 'invalid_lang'
        mock_ai_service.detect_language.return_value = 'en'
        
        # Вызов метода
        await message_handler.process_text_message(
            sender_id="user123",
            message_text="Hello world",
            sender_name="John"
        )
        
        # Проверки - должен определить новый язык
        mock_ai_service.detect_language.assert_called_once_with("Hello world")
        mock_session_service.save_user_language.assert_called_once_with("user123", "session_123", "en")
    
    @pytest.mark.asyncio
    async def test_empty_language_handling(
        self, 
        message_handler, 
        mock_ai_service, 
        mock_session_service, 
        mock_message_service
    ):
        """Тест обработки пустого языка"""
        
        # Настройка моков - пустой язык
        mock_session_service.get_user_language.return_value = ''
        mock_ai_service.detect_language.return_value = 'ru'
        
        # Вызов метода
        await message_handler.process_text_message(
            sender_id="user123",
            message_text="Привет",
            sender_name="Иван"
        )
        
        # Проверки - должен определить новый язык
        mock_ai_service.detect_language.assert_called_once_with("Привет")
        mock_session_service.save_user_language.assert_called_once_with("user123", "session_123", "ru") 
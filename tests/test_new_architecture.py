"""
Тест новой архитектуры
"""

import pytest
import asyncio
from datetime import datetime
from src.models.message import Message, MessageRole
from src.models.session import Session, SessionStatus
from src.models.order import Order, OrderStatus
from src.models.user import User, UserStatus
from src.services.session_service import SessionService
from src.services.message_service import MessageService
from src.services.order_service import OrderService
from src.services.user_service import UserService
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.services.command_service import CommandService

@pytest.mark.asyncio
async def test_models_creation():
    """Тест создания моделей"""
    
    # Тест Message
    message = Message(
        sender_id="123456789",
        session_id="session_123",
        role=MessageRole.USER,
        content="Привет!"
    )
    assert message.sender_id == "123456789"
    assert message.role == MessageRole.USER
    assert message.is_from_user() == True
    
    # Тест Session
    session = Session(
        session_id="session_123",
        sender_id="123456789"
    )
    assert session.session_id == "session_123"
    assert session.status == SessionStatus.ACTIVE
    assert session.is_active() == True
    
    # Тест Order
    order = Order(
        order_id="order_123",
        session_id="session_123",
        sender_id="123456789"
    )
    assert order.order_id == "order_123"
    assert order.status == OrderStatus.DRAFT
    assert order.is_draft() == True
    
    # Тест User
    user = User(
        sender_id="123456789",
        name="Тестовый пользователь"
    )
    assert user.sender_id == "123456789"
    assert user.name == "Тестовый пользователь"
    assert user.is_active() == True

@pytest.mark.asyncio
async def test_services_initialization():
    """Тест инициализации сервисов"""
    
    # Тест SessionService
    session_service = SessionService()
    assert session_service is not None
    
    # Тест MessageService
    message_service = MessageService()
    assert message_service is not None
    
    # Тест OrderService
    order_service = OrderService()
    assert order_service is not None
    
    # Тест UserService
    user_service = UserService()
    assert user_service is not None
    
    # Тест AIService
    ai_service = AIService("test_api_key")
    assert ai_service is not None
    
    # Тест CatalogService
    catalog_service = CatalogService("test_catalog_id", "test_token")
    assert catalog_service is not None
    
    # Тест CommandService
    command_service = CommandService()
    assert command_service is not None

@pytest.mark.asyncio
async def test_ai_service_language_detection():
    """Тест определения языка в AI сервисе"""
    
    ai_service = AIService("test_api_key")
    
    # Тест русского языка
    russian_text = "Привет, как дела?"
    lang = ai_service.detect_language(russian_text)
    assert lang == "ru"
    
    # Тест английского языка
    english_text = "Hello, how are you?"
    lang = ai_service.detect_language(english_text)
    assert lang == "en"
    
    # Тест пустого текста
    empty_text = ""
    lang = ai_service.detect_language(empty_text)
    assert lang == "auto"

@pytest.mark.asyncio
async def test_command_service():
    """Тест сервиса команд"""
    
    command_service = CommandService()
    
    # Тест пустой команды
    result = await command_service.handle_command("123", "session_123", {})
    assert result["status"] == "success"
    assert result["message"] == "No command to execute"
    
    # Тест неизвестной команды
    result = await command_service.handle_command("123", "session_123", {"type": "unknown"})
    assert result["status"] == "error"
    assert "Unknown command" in result["message"]

if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"]) 
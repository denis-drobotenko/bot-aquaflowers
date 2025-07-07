"""
Общие хелперы для тестов
"""

from typing import List, Dict, Any
from src.models.message import Message, MessageRole
from src.models.order import Order, OrderStatus
from src.models.session import Session
from src.models.user import User, UserStatus
from datetime import datetime
import pytest
import sys
from functools import wraps

def create_test_message(
    sender_id: str = "test_user_123",
    session_id: str = "test_session_456",
    role: MessageRole = MessageRole.USER,
    content: str = "Test message",
    wa_message_id: str = None
) -> Message:
    """Создает тестовое сообщение"""
    return Message(
        sender_id=sender_id,
        session_id=session_id,
        role=role,
        content=content,
        wa_message_id=wa_message_id
    )

def create_test_order(
    order_id: str = "test_order_123",
    sender_id: str = "test_user_123",
    session_id: str = "test_session_456",
    bouquet: str = "Test Bouquet",
    status: OrderStatus = OrderStatus.DRAFT
) -> Order:
    """Создает тестовый заказ"""
    return Order(
        order_id=order_id,
        sender_id=sender_id,
        session_id=session_id,
        bouquet=bouquet,
        status=status
    )

def create_test_session(
    sender_id: str = "test_user_123",
    session_id: str = "test_session_456"
) -> Session:
    """Создает тестовую сессию"""
    return Session(
        sender_id=sender_id,
        session_id=session_id
    )

def create_test_user(
    sender_id: str = "test_user_123",
    name: str = "Test User",
    status: UserStatus = UserStatus.ACTIVE
) -> User:
    """Создает тестового пользователя"""
    return User(
        sender_id=sender_id,
        name=name,
        status=status
    )

def create_mock_ai_response(
    text: str = "Test response",
    text_en: str = "Test response EN",
    text_thai: str = "Test response TH",
    command: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Создает мок ответа AI"""
    return {
        "text": text,
        "text_en": text_en,
        "text_thai": text_thai,
        "command": command
    }

def create_mock_catalog_product(
    product_id: str = "test_id_1",
    name: str = "Test Bouquet",
    price: str = "1 000,00 ฿",
    retailer_id: str = "test_retailer_123"
) -> Dict[str, Any]:
    """Создает мок товара каталога"""
    return {
        "id": product_id,
        "name": name,
        "description": f"Description for {name}",
        "price": price,
        "retailer_id": retailer_id,
        "image_url": f"https://example.com/{product_id}.jpg",
        "availability": "in stock"
    }

def assert_message_equals(actual: Message, expected: Message):
    """Проверяет равенство сообщений"""
    assert actual.sender_id == expected.sender_id
    assert actual.session_id == expected.session_id
    assert actual.role == expected.role
    assert actual.content == expected.content
    if expected.wa_message_id:
        assert actual.wa_message_id == expected.wa_message_id

def assert_order_equals(actual: Order, expected: Order):
    """Проверяет равенство заказов"""
    assert actual.sender_id == expected.sender_id
    assert actual.session_id == expected.session_id
    assert actual.bouquet == expected.bouquet
    assert actual.status == expected.status

def show_progress(test_name):
    """Декоратор для отображения прогресса тестов"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"🔄 Запуск: {test_name}")
            try:
                result = func(*args, **kwargs)
                print(f"✅ Успех: {test_name}")
                return result
            except Exception as e:
                print(f"❌ Ошибка: {test_name} - {str(e)}")
                raise
        return wrapper
    return decorator

def progress_test(test_name):
    """Альтернативный декоратор для pytest тестов"""
    def decorator(func):
        @pytest.mark.progress
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"🔄 Тест: {test_name}")
            result = func(*args, **kwargs)
            print(f"✅ Тест прошел: {test_name}")
            return result
        return wrapper
    return decorator 
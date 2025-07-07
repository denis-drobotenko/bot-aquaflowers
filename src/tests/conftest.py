"""
Конфигурация pytest с базовыми фикстурами
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any
import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Настройки pytest-cov
def pytest_configure(config):
    """Настройка pytest-cov"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Автоматически помечаем тесты как unit или integration"""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для асинхронных тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_firestore_client():
    """Мок для Firestore клиента"""
    mock_client = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    mock_doc = Mock()
    
    # Настройка мока
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {}
    mock_document.get.return_value = mock_doc
    mock_collection.document.return_value = mock_document
    mock_client.collection.return_value = mock_collection
    
    return mock_client

@pytest.fixture
def mock_whatsapp_client():
    """Мок для WhatsApp клиента"""
    mock_client = Mock()
    mock_client.send_text_message = AsyncMock(return_value=True)
    return mock_client

@pytest.fixture
def mock_gemini_model():
    """Мок для Gemini модели"""
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_model.generate_content.return_value = mock_response
    return mock_model

@pytest.fixture
def sample_catalog_data():
    """Тестовые данные каталога"""
    return [
        {
            "id": "test_id_1",
            "name": "Pretty 😍",
            "description": "Beautiful bouquet",
            "price": "2 600,00 ฿",
            "retailer_id": "kie4sy3qsy",
            "image_url": "https://example.com/image1.jpg",
            "availability": "in stock"
        },
        {
            "id": "test_id_2", 
            "name": "Spirit 🌸",
            "description": "Elegant bouquet",
            "price": "1 800,00 ฿",
            "retailer_id": "rl7vdxcifo",
            "image_url": "https://example.com/image2.jpg",
            "availability": "in stock"
        }
    ]

@pytest.fixture
def sample_messages():
    """Тестовые сообщения"""
    return [
        {
            "sender_id": "test_user_123",
            "session_id": "test_session_456",
            "role": "user",
            "content": "Привет! Хочу посмотреть каталог",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        {
            "sender_id": "test_user_123",
            "session_id": "test_session_456", 
            "role": "assistant",
            "content": "Здравствуйте! Конечно, покажу вам наш каталог цветов",
            "timestamp": "2024-01-01T12:01:00Z"
        }
    ]

@pytest.fixture
def sample_order_data():
    """Тестовые данные заказа"""
    return {
        "sender_id": "test_user_123",
        "session_id": "test_session_456",
        "bouquet": "Pretty 😍",
        "retailer_id": "kie4sy3qsy",
        "delivery_needed": True,
        "address": "Rawai, Phuket",
        "date": "2024-01-15",
        "time": "14:00",
        "card_needed": True,
        "card_text": "С днем рождения!",
        "recipient_name": "Анна",
        "recipient_phone": "+79123456789"
    }

@pytest.fixture
def mock_ai_response():
    """Мок ответа AI"""
    return {
        "text": "Здравствуйте! Хотите посмотреть наш каталог цветов?",
        "text_en": "Hello! Would you like to see our flower catalog?",
        "text_thai": "สวัสดี! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?",
        "command": None
    }

@pytest.fixture
def mock_ai_response_with_command():
    """Мок ответа AI с командой"""
    return {
        "text": "Отлично! Сейчас покажу вам каждый букет с фото!",
        "text_en": "Great! I'll show you each bouquet with photo!",
        "text_thai": "เยี่ยม! ฉันจะแสดงช่อดอกไม้แต่ละช่อพร้อมรูปภาพ!",
        "command": {
            "type": "send_catalog"
        }
    }

@pytest.fixture(scope="function")
def mock_firestore():
    """Мок для Firestore"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('firebase_admin.firestore.Client', MagicMock())
        yield

@pytest.fixture(scope="function")
def mock_requests():
    """Мок для HTTP запросов"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('requests.get', MagicMock())
        m.setattr('requests.post', MagicMock())
        yield

@pytest.fixture(scope="function")
def mock_ai_client():
    """Мок для AI клиента"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('google.generativeai.GenerativeModel', MagicMock())
        yield

@pytest.fixture(scope="function")
def mock_whatsapp_client():
    """Мок для WhatsApp клиента"""
    with pytest.MonkeyPatch().context() as m:
        m.setattr('src.utils.whatsapp_client.WhatsAppClient', MagicMock())
        yield

@pytest.fixture(scope="function")
def test_data():
    """Общие тестовые данные"""
    return {
        "user_id": "test_user_123",
        "session_id": "test_session_456",
        "order_id": "test_order_789",
        "message_id": "test_message_101"
    } 
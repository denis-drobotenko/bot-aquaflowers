import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.ai_service import AIService
from src.utils.ai_utils import format_conversation_for_ai, parse_ai_response, format_catalog_for_ai, get_fallback_text
from src.tests.utils.test_helpers import show_progress

@pytest.fixture
def ai_service():
    # Используем тестовый ключ и моки
    with patch('src.services.ai_service.genai.configure'):
        with patch('src.services.ai_service.CatalogService'):
            return AIService("test_api_key")

@show_progress("Инициализация AIService")
def test_init(ai_service):
    assert ai_service.api_key == "test_api_key"
    assert ai_service.logger is not None

@show_progress("Определение языка - русский")
def test_detect_language_ru(ai_service):
    result = ai_service.detect_language("Привет, как дела?")
    assert result == "ru"

@show_progress("Определение языка - английский")
def test_detect_language_en(ai_service):
    result = ai_service.detect_language("Hello, how are you?")
    assert result == "en"

@show_progress("Определение языка - тайский")
def test_detect_language_th(ai_service):
    result = ai_service.detect_language("สวัสดีครับ")
    assert result == "th"

@show_progress("Определение языка - авто")
def test_detect_language_auto(ai_service):
    result = ai_service.detect_language("12345")
    assert result == "auto"

@patch('src.services.ai_service.genai.GenerativeModel')
def test_translate_text_success(mock_model_class, ai_service):
    # Мокаем ответ от Gemini
    mock_response = MagicMock()
    mock_response.text = "Hello"
    mock_model = MagicMock()
    mock_model.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model
    
    result = ai_service.translate_text("Привет", "ru", "en")
    assert result == "Hello"

def test_translate_text_same_language(ai_service):
    result = ai_service.translate_text("Hello", "en", "en")
    assert result == "Hello"

def test_translate_text_empty(ai_service):
    result = ai_service.translate_text("", "ru", "en")
    assert result == ""

@patch('src.services.ai_service.genai.GenerativeModel')
def test_translate_text_error(mock_model_class, ai_service):
    # Мокаем ошибку
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("API Error")
    mock_model_class.return_value = mock_model
    
    result = ai_service.translate_text("Привет", "ru", "en")
    assert result == "Привет"  # Возвращает исходный текст при ошибке

def test_translate_user_message_ru(ai_service):
    with patch.object(ai_service, 'translate_text') as mock_translate:
        mock_translate.return_value = "Hello"
        
        text, text_en, text_thai = ai_service.translate_user_message("Привет", "ru")
        
        assert text == "Привет"
        assert text_en == "Hello"
        assert text_thai == "Hello"

def test_translate_user_message_en(ai_service):
    with patch.object(ai_service, 'translate_text') as mock_translate:
        mock_translate.return_value = "Привет"
        
        text, text_en, text_thai = ai_service.translate_user_message("Hello", "en")
        
        assert text == "Hello"
        assert text_en == "Hello"
        assert text_thai == "Привет"

def test_translate_user_message_auto(ai_service):
    with patch.object(ai_service, 'detect_language') as mock_detect:
        mock_detect.return_value = 'ru'
        with patch.object(ai_service, 'translate_text') as mock_translate:
            mock_translate.return_value = "Hello"
            
            text, text_en, text_thai = ai_service.translate_user_message("Привет", "auto")
            
            mock_detect.assert_called_once_with("Привет")
            assert text == "Привет"

def test_get_system_prompt_with_name(ai_service):
    prompt = ai_service.get_system_prompt("ru", "Анна")
    assert "Анна" in prompt
    assert "Russian" in prompt

def test_get_system_prompt_without_name(ai_service):
    prompt = ai_service.get_system_prompt("en")
    assert "User name unknown" in prompt
    assert "English" in prompt

def test_get_system_prompt_auto_language(ai_service):
    prompt = ai_service.get_system_prompt("auto")
    assert "Respond in English by default" in prompt

@pytest.mark.asyncio
async def test_format_conversation_for_ai():
    from src.models.message import Message, MessageRole
    
    messages = [
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Привет"),
        Message(sender_id="user1", session_id="session1", role=MessageRole.ASSISTANT, content="Здравствуйте!"),
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Как дела?")  # Заменяем пустое на валидное
    ]
    
    result = await format_conversation_for_ai(messages, "session1", "user1")
    
    assert len(result) >= 3  # Может быть больше из-за системных сообщений
    # Проверяем последние сообщения (обычные сообщения)
    assert any("Привет" in msg['content'] for msg in result)
    assert any("Здравствуйте!" in msg['content'] for msg in result)
    assert any("Как дела?" in msg['content'] for msg in result)

@pytest.mark.asyncio
async def test_format_conversation_for_ai_empty():
    result = await format_conversation_for_ai([], None, None)
    assert result == []

def test_parse_ai_response_valid_json():
    response_text = '{"text": "Привет", "text_en": "Hello", "text_thai": "สวัสดี", "command": null}'
    
    text, text_en, text_thai, command = parse_ai_response(response_text)
    
    assert text == "Привет"
    assert text_en == "Hello"
    assert text_thai == "สวัสดี"
    assert command is None

def test_parse_ai_response_markdown():
    response_text = '''```json
{"text": "Привет", "text_en": "Hello", "text_thai": "สวัสดี", "command": {"type": "send_catalog"}}
```'''
    
    text, text_en, text_thai, command = parse_ai_response(response_text)
    
    assert text == "Привет"
    assert text_en == "Hello"
    assert text_thai == "สวัสดี"
    assert command == {"type": "send_catalog"}

def test_parse_ai_response_invalid_json():
    response_text = "Invalid JSON response"
    
    text, text_en, text_thai, command = parse_ai_response(response_text)
    
    # При ошибке парсинга возвращает исходный текст
    assert text == response_text
    assert text_en == response_text
    assert text_thai == response_text
    assert command is None

def test_format_catalog_for_ai():
    products = [
        {"name": "Bouquet 1", "price": "1000", "retailer_id": "id1"},
        {"name": "Bouquet 2", "price": "2000", "retailer_id": "id2"}
    ]
    
    result = format_catalog_for_ai(products)
    
    assert "Bouquet 1" in result
    assert "Bouquet 2" in result
    assert "1000" in result
    assert "2000" in result
    assert "id1" in result
    assert "id2" in result

def test_format_catalog_for_ai_empty():
    result = format_catalog_for_ai([])
    assert "недоступен" in result

def test_get_fallback_text():
    # Тест для русского языка
    result_ru = get_fallback_text("ru")
    assert "Конечно" in result_ru
    
    # Тест для английского языка
    result_en = get_fallback_text("en")
    assert "Of course" in result_en
    
    # Тест для тайского языка
    result_th = get_fallback_text("th")
    assert "แน่นอน" in result_th
    
    # Тест для неизвестного языка (должен вернуть русский)
    result_auto = get_fallback_text("auto")
    assert "Конечно" in result_auto

@pytest.mark.asyncio
async def test_generate_response_success(ai_service):
    from src.models.message import Message, MessageRole
    
    messages = [
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Привет")
    ]
    
    # Мокаем каталог
    with patch.object(ai_service.catalog_service, 'get_products', new_callable=AsyncMock) as mock_get_products:
        mock_get_products.return_value = [{"name": "Test Bouquet", "price": "1000"}]
        
        # Мокаем Gemini
        with patch('src.services.ai_service.genai.GenerativeModel') as mock_model_class:
            mock_response = MagicMock()
            mock_response.text = '{"text": "Здравствуйте!", "text_en": "Hello!", "text_thai": "สวัสดี!", "command": null}'
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            text, text_en, text_thai, command = await ai_service.generate_response(messages, "ru")
            
            assert text == "Здравствуйте!"
            assert text_en == "Hello!"
            assert text_thai == "สวัสดี!"
            assert command is None

@pytest.mark.asyncio
async def test_generate_response_empty_history(ai_service):
    # Мокаем каталог
    with patch.object(ai_service.catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = []
        
        # Мокаем Gemini
        with patch('src.services.ai_service.genai.GenerativeModel') as mock_model_class:
            mock_response = MagicMock()
            mock_response.text = '{"text": "Конечно! Чем могу помочь?", "text_en": "Of course! How can I help?", "text_thai": "แน่นอน! ฉันสามารถช่วยคุณได้อย่างไร?", "command": null}'
            mock_model = MagicMock()
            mock_model.generate_content.return_value = mock_response
            mock_model_class.return_value = mock_model
            
            text, text_en, text_thai, command = await ai_service.generate_response([], "ru")
            
            assert "Конечно" in text or "Of course" in text_en

@pytest.mark.asyncio
async def test_generate_response_error(ai_service):
    from src.models.message import Message, MessageRole
    
    messages = [
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Привет")
    ]
    
    # Мокаем ошибку
    with patch.object(ai_service.catalog_service, 'get_products', side_effect=Exception("API Error")):
        text, text_en, text_thai, command = await ai_service.generate_response(messages, "ru")
        
        # Должен вернуть fallback текст
        assert "Конечно" in text or "Of course" in text_en or "แน่นอน" in text_thai

def test_generate_response_sync(ai_service):
    from src.models.message import Message, MessageRole
    
    messages = [
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Привет")
    ]
    
    # Мокаем Gemini
    with patch.object(ai_service.model, 'generate_content') as mock_generate:
        mock_response = MagicMock()
        mock_response.text = "Здравствуйте! Чем могу помочь?"
        mock_generate.return_value = mock_response
        
        result = ai_service.generate_response_sync(messages, "ru")
        
        assert result == "Здравствуйте! Чем могу помочь?"

def test_generate_response_sync_error(ai_service):
    from src.models.message import Message, MessageRole
    
    messages = [
        Message(sender_id="user1", session_id="session1", role=MessageRole.USER, content="Привет")
    ]
    
    # Мокаем ошибку
    with patch.object(ai_service.model, 'generate_content', side_effect=Exception("API Error")):
        result = ai_service.generate_response_sync(messages, "ru")
        
        assert "Извините" in result or "ошибка" in result 
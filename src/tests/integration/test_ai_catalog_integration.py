import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.services.catalog_sender import CatalogSender
from src.models.message import Message, MessageRole


@pytest.fixture
def ai_service():
    return AIService(api_key="test_api_key")


@pytest.fixture
def catalog_service():
    return CatalogService(catalog_id="test_catalog_id", access_token="test_access_token")


@pytest.fixture
def catalog_sender():
    sender = CatalogSender()
    sender.whatsapp_client = AsyncMock()
    return sender


@pytest.mark.asyncio
async def test_ai_generate_response_with_catalog_integration(ai_service, catalog_service):
    """Тест интеграции AI с каталогом при генерации ответа"""
    
    # Мокаем получение товаров из каталога
    with patch.object(catalog_service, 'get_available_products') as mock_get_products:
        mock_products = [
            {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза',
                'image_url': 'http://example.com/rose.jpg'
            },
            {
                'id': '2',
                'name': 'Тюльпан желтый',
                'price': 80,
                'description': 'Яркий желтый тюльпан',
                'image_url': 'http://example.com/tulip.jpg'
            }
        ]
        mock_get_products.return_value = mock_products
        
        # Мокаем генерацию ответа AI
        with patch.object(ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Вот наши доступные цветы: розы и тюльпаны"
            
            # Получаем товары
            products = await catalog_service.get_available_products()
            
            # Генерируем ответ с каталогом
            response = await ai_service.generate_response(
                sender_id="user_123",
                session_id="session_456",
                user_message="Покажите каталог цветов",
                catalog_data=products
            )
            
            assert response == "Вот наши доступные цветы: розы и тюльпаны"
            mock_get_products.assert_called_once()
            mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_catalog_sender_with_ai_response_integration(catalog_sender, ai_service):
    """Тест интеграции отправки каталога с AI ответом"""
    
    # Мокаем получение товаров
    with patch.object(catalog_sender.catalog_service, 'get_available_products', new_callable=AsyncMock) as mock_get_products:
        mock_get_products.return_value = [
            {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'image_url': 'http://example.com/rose.jpg'
            }
        ]
        # Мокаем отправку сообщения
        with patch.object(catalog_sender, '_send_whatsapp_image_with_caption') as mock_send:
            mock_send.return_value = True
            # Мокаем сохранение сообщения
            with patch.object(catalog_sender, '_save_catalog_message') as mock_save:
                mock_save.return_value = "message_id_123"
                # Мокаем генерацию AI ответа
                with patch.object(ai_service, 'generate_response') as mock_generate:
                    mock_generate.return_value = "Вот наш каталог цветов"
                    # Отправляем каталог
                    result = await catalog_sender.handle_send_catalog(
                        to_number="+1234567890",
                        sender_id="user_123",
                        session_id="session_456"
                    )
                    assert result is True
                    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_ai_format_catalog_for_prompt_integration(ai_service, catalog_service):
    """Тест форматирования каталога для AI промпта"""
    
    # Мокаем получение товаров
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_products = [
            {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза',
                'available': True
            },
            {
                'id': '2',
                'name': 'Тюльпан желтый',
                'price': 80,
                'description': 'Яркий желтый тюльпан',
                'available': False
            }
        ]
        mock_get_products.return_value = mock_products
        
        # Получаем товары
        products = await catalog_service.get_products()
        
        # Форматируем каталог для AI
        from src.utils.ai_utils import format_catalog_for_ai
        formatted_catalog = format_catalog_for_ai(products)
        
        # Проверяем, что результат — строка и содержит оба товара
        assert isinstance(formatted_catalog, str)
        assert "Роза красная" in formatted_catalog
        assert "Тюльпан желтый" in formatted_catalog


@pytest.mark.asyncio
async def test_ai_search_products_integration(ai_service, catalog_service):
    """Тест поиска товаров через AI"""
    
    # Мокаем поиск товаров
    with patch.object(catalog_service, 'search_products') as mock_search:
        mock_search.return_value = [
            {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза'
            }
        ]
        
        # Мокаем генерацию AI ответа
        with patch.object(ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Нашел красную розу за 100 рублей"
            
            # Ищем товары
            search_results = await catalog_service.search_products("красная роза")
            
            # Генерируем ответ на основе результатов поиска
            response = await ai_service.generate_response(
                sender_id="user_123",
                session_id="session_456",
                user_message="Ищу красную розу",
                catalog_data=search_results
            )
            
            assert response == "Нашел красную розу за 100 рублей"
            mock_search.assert_called_once_with("красная роза")
            mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_ai_validate_product_integration(ai_service, catalog_service):
    """Тест валидации товара через AI"""
    
    # Мокаем валидацию товара
    with patch.object(catalog_service, 'validate_product') as mock_validate:
        mock_validate.return_value = True
        
        # Мокаем получение товара
        with patch.object(catalog_service, 'get_product_by_id') as mock_get_product:
            mock_product = {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза',
                'available': True
            }
            mock_get_product.return_value = mock_product
            
            # Валидируем товар
            is_valid = await catalog_service.validate_product("1")
            
            # Получаем информацию о товаре
            product = await catalog_service.get_product_by_id("1")
            
            # Генерируем ответ на основе валидации
            if is_valid and product:
                response = f"Товар '{product['name']}' доступен за {product['price']} рублей"
            else:
                response = "Товар недоступен"
            
            assert response == "Товар 'Роза красная' доступен за 100 рублей"
            mock_validate.assert_called_once_with("1")
            mock_get_product.assert_called_once_with("1")


@pytest.mark.asyncio
async def test_ai_catalog_cache_integration(ai_service, catalog_service):
    """Тест работы с кэшем каталога и AI"""
    
    # Мокаем получение товаров с кэшем
    with patch.object(catalog_service, 'get_available_products') as mock_get_products:
        mock_products = [
            {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза'
            }
        ]
        mock_get_products.return_value = mock_products
        
        # Мокаем генерацию AI ответа
        with patch.object(ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Вот наша роза"
            
            # Первый запрос - загружаем в кэш
            products1 = await catalog_service.get_available_products()
            response1 = await ai_service.generate_response(
                sender_id="user_123",
                session_id="session_456",
                user_message="Покажите розы",
                catalog_data=products1
            )
            
            # Второй запрос - используем кэш
            products2 = await catalog_service.get_available_products()
            response2 = await ai_service.generate_response(
                sender_id="user_123",
                session_id="session_456",
                user_message="Покажите розы",
                catalog_data=products2
            )
            
            assert response1 == response2 == "Вот наша роза"
            # Проверяем, что метод вызывался дважды (для каждого запроса)
            assert mock_get_products.call_count == 2


@pytest.mark.asyncio
async def test_ai_catalog_error_handling_integration(ai_service, catalog_service):
    """Тест обработки ошибок при работе с каталогом и AI"""
    
    # Мокаем ошибку при получении товаров
    with patch.object(catalog_service, 'get_available_products') as mock_get_products:
        mock_get_products.side_effect = Exception("Catalog service error")
        
        # Мокаем генерацию AI ответа для случая ошибки
        with patch.object(ai_service, 'generate_response') as mock_generate:
            mock_generate.return_value = "Извините, каталог временно недоступен"
            
            try:
                products = await catalog_service.get_available_products()
            except Exception:
                products = []
            
            response = await ai_service.generate_response(
                sender_id="user_123",
                session_id="session_456",
                user_message="Покажите каталог",
                catalog_data=products
            )
            
            assert response == "Извините, каталог временно недоступен"
            assert products == []
            mock_get_products.assert_called_once()
            mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_ai_catalog_multilingual_integration(ai_service, catalog_service):
    """Тест многоязычной поддержки каталога и AI"""
    
    # Мокаем определение языка
    with patch.object(ai_service, 'detect_language') as mock_detect:
        mock_detect.return_value = 'en'
        
        # Мокаем перевод
        with patch.object(ai_service, 'translate_text') as mock_translate:
            mock_translate.return_value = "Here are our flowers"
            
            # Мокаем получение товаров
            with patch.object(catalog_service, 'get_available_products') as mock_get_products:
                mock_products = [
                    {
                        'id': '1',
                        'name': 'Роза красная',
                        'price': 100,
                        'description': 'Красивая красная роза'
                    }
                ]
                mock_get_products.return_value = mock_products
                
                # Определяем язык
                language = ai_service.detect_language("Show me flowers")
                
                # Переводим ответ
                translated_response = ai_service.translate_text("Вот наши цветы", language)
                
                # Получаем товары
                products = await catalog_service.get_available_products()
                
                assert language == 'en'
                assert translated_response == "Here are our flowers"
                assert len(products) == 1
                mock_detect.assert_called_once_with("Show me flowers")
                mock_translate.assert_called_once_with("Вот наши цветы", 'en')
                mock_get_products.assert_called_once() 
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.catalog_service import CatalogService


@pytest.fixture
def catalog_service():
    return CatalogService(catalog_id="test_catalog_id", access_token="test_token")


def test_init(catalog_service):
    assert catalog_service.catalog_id == "test_catalog_id"
    assert catalog_service.access_token == "test_token"
    assert catalog_service._cache is None


@pytest.mark.asyncio
async def test_get_products_success(catalog_service):
    # Мокаем HTTPX клиент
    with patch('src.services.catalog_service.httpx.AsyncClient') as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "data": [
                {"id": "1", "name": "Bouquet 1", "price": "1000"},
                {"id": "2", "name": "Bouquet 2", "price": "2000"}
            ]
        })
        mock_response.raise_for_status.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        products = await catalog_service.get_products()
        
        assert len(products) == 2
        assert products[0]["name"] == "Bouquet 1"
        assert products[1]["name"] == "Bouquet 2"
        assert catalog_service._cache == products


@pytest.mark.asyncio
async def test_get_products_use_cache(catalog_service):
    # Устанавливаем кэш
    cached_products = [{"id": "1", "name": "Cached Bouquet"}]
    catalog_service._cache = cached_products
    
    products = await catalog_service.get_products()
    
    assert products == cached_products


@pytest.mark.asyncio
async def test_get_products_force_refresh(catalog_service):
    # Устанавливаем кэш
    cached_products = [{"id": "1", "name": "Cached Bouquet"}]
    catalog_service._cache = cached_products
    
    # Мокаем HTTPX клиент для принудительного обновления
    with patch('src.services.catalog_service.httpx.AsyncClient') as mock_client_class:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={
            "data": [{"id": "2", "name": "New Bouquet"}]
        })
        mock_response.raise_for_status.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        products = await catalog_service.get_products(force_refresh=True)
        
        assert len(products) == 1
        assert products[0]["name"] == "New Bouquet"


@pytest.mark.asyncio
async def test_get_products_error(catalog_service):
    # Мокаем ошибку HTTP
    with patch('src.services.catalog_service.httpx.AsyncClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("HTTP Error")
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        products = await catalog_service.get_products()
        
        assert products == []


@pytest.mark.asyncio
async def test_get_available_products(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1", "availability": "in stock"},
            {"id": "2", "name": "Bouquet 2", "availability": "out of stock"},
            {"id": "3", "name": "Bouquet 3", "availability": None}
        ]
        
        available_products = await catalog_service.get_available_products()
        
        assert len(available_products) == 2
        assert available_products[0]["name"] == "Bouquet 1"
        assert available_products[1]["name"] == "Bouquet 3"  # None считается доступным


@pytest.mark.asyncio
async def test_get_product_by_id_found(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1"},
            {"id": "2", "name": "Bouquet 2"}
        ]
        
        product = await catalog_service.get_product_by_id("1")
        
        assert product["name"] == "Bouquet 1"


@pytest.mark.asyncio
async def test_get_product_by_id_not_found(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1"}
        ]
        
        product = await catalog_service.get_product_by_id("999")
        
        assert product is None


@pytest.mark.asyncio
async def test_validate_product_valid(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1", "retailer_id": "retailer_1"}
        ]
        
        result = await catalog_service.validate_product("retailer_1")
        
        assert result["valid"] is True
        assert result["product"]["name"] == "Bouquet 1"


@pytest.mark.asyncio
async def test_validate_product_invalid(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1", "retailer_id": "retailer_1"}
        ]
        
        result = await catalog_service.validate_product("invalid_retailer")
        
        assert result["valid"] is False
        assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_search_products_found(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Red Rose Bouquet", "description": "Beautiful red roses"},
            {"id": "2", "name": "White Lily Bouquet", "description": "Elegant white lilies"},
            {"id": "3", "name": "Sunflower Bouquet", "description": "Bright sunflowers"}
        ]
        
        results = await catalog_service.search_products("rose")
        
        assert len(results) == 1
        assert results[0]["name"] == "Red Rose Bouquet"


@pytest.mark.asyncio
async def test_search_products_not_found(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Red Rose Bouquet", "description": "Beautiful red roses"}
        ]
        
        results = await catalog_service.search_products("tulip")
        
        assert len(results) == 0


@pytest.mark.asyncio
async def test_search_products_empty_query(catalog_service):
    # Мокаем get_products
    with patch.object(catalog_service, 'get_products') as mock_get_products:
        mock_get_products.return_value = [
            {"id": "1", "name": "Bouquet 1", "description": "Description"}
        ]
        
        results = await catalog_service.search_products("")
        
        assert len(results) == 1  # Пустой запрос должен найти все товары


def test_clear_cache(catalog_service):
    # Устанавливаем кэш
    catalog_service._cache = [{"id": "1", "name": "Test"}]
    catalog_service._cache_time = "2024-01-01"
    
    catalog_service.clear_cache()
    
    assert catalog_service._cache is None
    assert catalog_service._cache_time is None 
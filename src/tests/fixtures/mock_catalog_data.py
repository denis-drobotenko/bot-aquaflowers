"""
Тестовые данные каталога товаров
"""

from typing import List, Dict, Any

def get_sample_catalog_products() -> List[Dict[str, Any]]:
    """Возвращает тестовые товары каталога"""
    return [
        {
            "id": "catalog_id_1",
            "name": "Pretty 😍",
            "description": "Beautiful pink and white bouquet with roses and lilies",
            "price": "2 600,00 ฿",
            "retailer_id": "kie4sy3qsy",
            "image_url": "https://example.com/pretty_bouquet.jpg",
            "availability": "in stock"
        },
        {
            "id": "catalog_id_2",
            "name": "Spirit 🌸",
            "description": "Elegant white bouquet with orchids and baby's breath",
            "price": "1 800,00 ฿",
            "retailer_id": "rl7vdxcifo",
            "image_url": "https://example.com/spirit_bouquet.jpg",
            "availability": "in stock"
        },
        {
            "id": "catalog_id_3",
            "name": "Sunshine ☀️",
            "description": "Bright yellow bouquet with sunflowers and daisies",
            "price": "2 200,00 ฿",
            "retailer_id": "abc123def",
            "image_url": "https://example.com/sunshine_bouquet.jpg",
            "availability": "in stock"
        },
        {
            "id": "catalog_id_4",
            "name": "Romance 💕",
            "description": "Romantic red roses bouquet with baby's breath",
            "price": "3 000,00 ฿",
            "retailer_id": "xyz789uvw",
            "image_url": "https://example.com/romance_bouquet.jpg",
            "availability": "out of stock"
        },
        {
            "id": "catalog_id_5",
            "name": "Spring 🌺",
            "description": "Colorful spring bouquet with tulips and daffodils",
            "price": "1 500,00 ฿",
            "retailer_id": "def456ghi",
            "image_url": "https://example.com/spring_bouquet.jpg",
            "availability": "in stock"
        }
    ]

def get_available_products() -> List[Dict[str, Any]]:
    """Возвращает только доступные товары"""
    all_products = get_sample_catalog_products()
    return [p for p in all_products if p.get('availability') == 'in stock']

def get_unavailable_products() -> List[Dict[str, Any]]:
    """Возвращает только недоступные товары"""
    all_products = get_sample_catalog_products()
    return [p for p in all_products if p.get('availability') != 'in stock']

def get_product_by_retailer_id(retailer_id: str) -> Dict[str, Any]:
    """Возвращает товар по retailer_id"""
    products = get_sample_catalog_products()
    for product in products:
        if product.get('retailer_id') == retailer_id:
            return product
    return None

def get_products_by_name_pattern(pattern: str) -> List[Dict[str, Any]]:
    """Возвращает товары по паттерну в названии"""
    products = get_sample_catalog_products()
    pattern_lower = pattern.lower()
    return [p for p in products if pattern_lower in p.get('name', '').lower()]

def get_empty_catalog() -> List[Dict[str, Any]]:
    """Возвращает пустой каталог"""
    return []

def get_catalog_with_one_product() -> List[Dict[str, Any]]:
    """Возвращает каталог с одним товаром"""
    return [get_sample_catalog_products()[0]]

def get_catalog_api_response() -> Dict[str, Any]:
    """Возвращает мок ответа API каталога"""
    return {
        "data": get_sample_catalog_products(),
        "paging": {
            "cursors": {
                "before": "cursor_before",
                "after": "cursor_after"
            },
            "next": "https://graph.facebook.com/v23.0/catalog_id/products?after=cursor_after"
        }
    }

def get_catalog_api_error_response() -> Dict[str, Any]:
    """Возвращает мок ошибки API каталога"""
    return {
        "error": {
            "message": "Invalid access token",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 1234567,
            "fbtrace_id": "AbCdEfGhIjKlMnOpQrStUvWxYz"
        }
    } 
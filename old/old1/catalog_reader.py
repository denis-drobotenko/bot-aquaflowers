"""
Чтение реального каталога цветов из WhatsApp Business API
"""

import logging
from .config import WHATSAPP_TOKEN, WHATSAPP_CATALOG_ID

logger = logging.getLogger(__name__)

def get_catalog_products():
    """
    Получает список всех товаров из каталога WABA.
    """
    try:
        import requests
        url = f"https://graph.facebook.com/v23.0/{WHATSAPP_CATALOG_ID}/products"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        
        params = {
            "fields": "id,name,description,price,retailer_id,image_url,availability"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"[CATALOG] Retrieved {len(data.get('data', []))} products from catalog")
        
        return data.get('data', [])
        
    except Exception as e:
        logger.error(f"Failed to get catalog products: {e}")
        return []

def format_catalog_for_ai(products):
    """
    Форматирует каталог для передачи в AI (оставляем ID только для AI, но не для пользователя)
    """
    if not products:
        return "Каталог временно недоступен."
    catalog_text = "АКТУАЛЬНЫЙ КАТАЛОГ ЦВЕТОВ ИЗ WABA\n\n"
    for i, product in enumerate(products, 1):
        name = product.get('name', 'Без названия')
        price = product.get('price', 'Цена не указана')
        catalog_text += f"{i}. {name}\n   Цена: {price}\n"
    catalog_text += "ВАЖНО: Используй ТОЛЬКО эти товары! Не выдумывай названия!"
    return catalog_text

def get_catalog_summary():
    """
    Получает краткую сводку каталога для AI.
    """
    products = get_catalog_products()
    
    if not products:
        return "Каталог временно недоступен."
    
    summary = "Доступные товары:\n"
    for product in products:
        name = product.get('name', 'Без названия')
        retailer_id = product.get('retailer_id', '')
        summary += f"- {name} (ID: {retailer_id})\n"
    
    return summary

def get_product_by_retailer_id(products, retailer_id):
    """
    Находит товар по retailer_id.
    """
    for product in products:
        if product.get('retailer_id') == retailer_id:
            return product
    return None

def get_product_by_name(products, product_name):
    """
    Находит товар по названию (без учета регистра и эмоджи).
    """
    # Очищаем название от эмоджи и приводим к нижнему регистру
    clean_name = product_name.replace('🌸', '').strip().lower()
    
    for product in products:
        product_clean_name = product.get('name', '').replace('🌸', '').strip().lower()
        if product_clean_name == clean_name:
            return product
    return None

def validate_product_selection(retailer_id):
    """
    Проверяет, существует ли товар с данным retailer_id в каталоге.
    """
    products = get_catalog_products()
    product = get_product_by_retailer_id(products, retailer_id)
    
    if product:
        return {
            "valid": True,
            "product": product
        }
    else:
        return {
            "valid": False,
            "available_products": [p.get('retailer_id') for p in products]
        }

def validate_product_by_name(product_name):
    """
    Проверяет, существует ли товар с данным названием в каталоге.
    """
    products = get_catalog_products()
    product = get_product_by_name(products, product_name)
    
    if product:
        return {
            "valid": True,
            "product": product
        }
    else:
        return {
            "valid": False,
            "available_products": [p.get('name', 'Без названия') for p in products]
        }

def filter_available_products(products):
    """
    Оставляет только товары, которые есть в наличии (availability == 'in stock').
    Если поле отсутствует, считаем товар доступным.
    """
    available = []
    for p in products:
        avail = p.get('availability')
        if avail is None or avail.lower() == 'in stock':
            available.append(p)
    return available 
"""
Сервис для работы с каталогом товаров
"""

import requests
from typing import List, Dict, Any, Optional
import os

class CatalogService:
    def __init__(self, catalog_id: str, access_token: str):
        self.catalog_id = catalog_id
        self.access_token = access_token
        self._cache = None
        self._cache_time = None

    def get_products(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получает список товаров из каталога"""
        if not force_refresh and self._cache:
            return self._cache
        
        try:
            url = f"https://graph.facebook.com/v23.0/{self.catalog_id}/products"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Используем синхронный requests как в старой версии
            params = {
                "fields": "id,name,description,price,retailer_id,image_url,availability"
            }
            
            print(f"[CATALOG_DEBUG] Загружаем товары из каталога {self.catalog_id}...")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('data', [])
            
            print(f"[CATALOG_DEBUG] Получено {len(products)} товаров из каталога")
            if products:
                print(f"[CATALOG_DEBUG] Первый товар: {products[0]}")
            
            self._cache = products
            self._cache_time = None
            
            return products
            
        except Exception as e:
            print(f"[CATALOG_ERROR] Ошибка получения товаров: {e}")
            return []

    def filter_available_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    def get_available_products(self) -> List[Dict[str, Any]]:
        """Получает только доступные товары"""
        products = self.get_products()
        print(f"[CATALOG_DEBUG] Всего товаров получено: {len(products)}")
        
        available = self.filter_available_products(products)
        print(f"[CATALOG_DEBUG] Доступных товаров: {len(available)}")
        
        if available:
            print(f"[CATALOG_DEBUG] Первый доступный товар: {available[0]}")
        else:
            print(f"[CATALOG_DEBUG] Нет доступных товаров!")
            
        return available

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Получает товар по ID"""
        products = self.get_products()
        for product in products:
            if product.get('id') == product_id:
                return product
        return None

    def validate_product(self, retailer_id: str) -> Dict[str, Any]:
        """Валидирует товар по retailer_id"""
        products = self.get_products()
        for product in products:
            if product.get('retailer_id') == retailer_id:
                return {"valid": True, "product": product}
        return {"valid": False, "error": "Product not found"}

    def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Ищет товары по запросу"""
        products = self.get_products()
        query_lower = query.lower()
        
        results = []
        for product in products:
            name = product.get('name', '').lower()
            description = product.get('description', '').lower()
            
            if query_lower in name or query_lower in description:
                results.append(product)
        
        return results

    def clear_cache(self):
        """Очищает кэш товаров"""
        self._cache = None
        self._cache_time = None 
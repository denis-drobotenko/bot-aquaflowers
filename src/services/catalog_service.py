"""
Сервис для работы с каталогом товаров
"""

import httpx
from src.utils.logging_utils import ContextLogger
from typing import List, Dict, Any, Optional
import os

class CatalogService:
    def __init__(self, catalog_id: str, access_token: str):
        self.catalog_id = catalog_id
        self.access_token = access_token
        self.logger = ContextLogger("catalog_service")
        self._cache = None
        self._cache_time = None

    async def get_products(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получает список товаров из каталога"""
        if not force_refresh and self._cache:
            return self._cache
        
        try:
            url = f"https://graph.facebook.com/v23.0/{self.catalog_id}/products"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Добавляем параметры как в catalog_reader.py
            params = {
                "fields": "id,name,description,price,retailer_id,image_url,availability"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                products = data.get('data', [])
                
                self._cache = products
                self._cache_time = None
                
                self.logger.info(f"Retrieved {len(products)} products from catalog")
                return products
                
        except Exception as e:
            self.logger.error(f"Error fetching catalog products: {e}")
            return []

    async def get_available_products(self) -> List[Dict[str, Any]]:
        """Получает только доступные товары"""
        products = await self.get_products()
        # Используем логику из catalog_reader.py
        available = []
        for p in products:
            avail = p.get('availability')
            if avail is None or avail.lower() == 'in stock':
                available.append(p)
        return available

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Получает товар по ID"""
        products = await self.get_products()
        for product in products:
            if product.get('id') == product_id:
                return product
        return None

    async def validate_product(self, retailer_id: str) -> Dict[str, Any]:
        """Валидирует товар по retailer_id"""
        products = await self.get_products()
        for product in products:
            if product.get('retailer_id') == retailer_id:
                return {"valid": True, "product": product}
        return {"valid": False, "error": "Product not found"}

    async def search_products(self, query: str) -> List[Dict[str, Any]]:
        """Ищет товары по запросу"""
        products = await self.get_products()
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
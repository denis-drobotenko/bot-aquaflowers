"""
Обработчик интерактивных сообщений
"""

from typing import Dict, Any
from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

class InteractiveHandler:
    """Обработчик интерактивных сообщений (кнопки, каталог товаров)"""
    
    def __init__(self):
        self.catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
    
    async def process_interactive_message(self, sender_id: str, interactive_data: Dict[str, Any]) -> str:
        """
        Обрабатывает интерактивные сообщения (кнопки, каталог товаров).
        
        Типы интерактивных сообщений:
        - button: нажатие кнопки
        - catalog_message: выбор товара из каталога
        - list_reply: выбор из списка
        
        Args:
            sender_id: ID пользователя WhatsApp
            interactive_data: Данные интерактивного сообщения
            
        Returns:
            str: Ответ для отправки пользователю
        """
        interactive_type = interactive_data.get('type')
        print(f"[INTERACTIVE] Обработка {interactive_type} от {sender_id}")
        
        if interactive_type == 'button':
            return await self._handle_button_click(interactive_data)
        
        elif interactive_type == 'catalog_message':
            return await self._handle_catalog_selection(interactive_data)
        
        else:
            print(f"[INTERACTIVE] Неизвестный тип: {interactive_type}")
            return "Спасибо за взаимодействие! 🌸"
    
    async def _handle_button_click(self, interactive_data: Dict[str, Any]) -> str:
        """Обрабатывает нажатие кнопки"""
        button_id = interactive_data.get('button_reply', {}).get('id')
        print(f"[BUTTON] Нажата кнопка: {button_id}")
        
        # Здесь можно добавить логику для разных кнопок
        if button_id == 'catalog':
            return "Вот наш каталог товаров! 🌸"
        elif button_id == 'help':
            return "Чем могу помочь? 🌸"
        else:
            return "Спасибо за выбор! 🌸"
    
    async def _handle_catalog_selection(self, interactive_data: Dict[str, Any]) -> str:
        """Обрабатывает выбор товара из каталога"""
        catalog_data = interactive_data.get('catalog_message', {})
        retailer_id = catalog_data.get('retailer_id')  # Используем retailer_id
        print(f"[CATALOG] Выбран товар: {retailer_id}")
        
        # Валидируем товар в каталоге
        validation = await self.catalog_service.validate_product(retailer_id)
        if validation['valid']:
            product = validation['product']
            return f"Отличный выбор! {product.get('name')} - {product.get('price')} 🌸"
        else:
            return "Извините, этот товар временно недоступен 🌸" 
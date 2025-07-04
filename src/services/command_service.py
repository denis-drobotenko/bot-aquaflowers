"""
Сервис для обработки команд от AI
"""

from src.utils.logging_utils import ContextLogger
from src.services.catalog_service import CatalogService
from src.services.order_service import OrderService
from src.services.session_service import SessionService
from src.models.order import Order, OrderItem, OrderStatus
from src.config import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
from typing import Dict, Any, Optional
import json

class CommandService:
    def __init__(self):
        self.logger = ContextLogger("command_service")
        self.catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        self.order_service = OrderService()
        self.session_service = SessionService()

    async def handle_command(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду от AI"""
        try:
            if not isinstance(command, dict):
                return {"status": "error", "message": "Invalid command format"}
            
            if not command:
                return {"status": "success", "message": "No command to execute"}
            
            command_type = command.get('type')
            if not command_type:
                return {"status": "error", "message": "No command type found"}
            
            self.logger.info(f"Processing command: {command_type}")
            
            # Выполняем команду в зависимости от типа
            if command_type == 'send_catalog':
                return await self._handle_send_catalog(sender_id, session_id, command)
            elif command_type == 'save_order_info':
                return await self._handle_save_order_info(sender_id, session_id, command)
            elif command_type == 'confirm_order':
                return await self._handle_confirm_order(sender_id, session_id, command)
            elif command_type == 'clarify_request':
                return await self._handle_clarify_request(sender_id, session_id, command)
            else:
                return {"status": "error", "message": f"Unknown command: {command_type}"}
                
        except Exception as e:
            self.logger.error(f"Error handling command: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_send_catalog(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду отправки каталога"""
        try:
            # Получаем доступные товары
            available_products = await self.catalog_service.get_available_products()
            
            if not available_products:
                return {
                    "status": "error", 
                    "message": "Извините, сейчас нет букетов в наличии. Попробуйте позже. 🌸"
                }
            
            # TODO: Отправить каталог через WhatsApp
            self.logger.info(f"Catalog requested for session {session_id}")
            
            return {
                "status": "success", 
                "action": "catalog_sent",
                "products_count": len(available_products)
            }
            
        except Exception as e:
            self.logger.error(f"Error sending catalog: {e}")
            return {"status": "error", "message": "Ошибка при отправке каталога"}

    async def _handle_save_order_info(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду сохранения информации о заказе"""
        try:
            # Извлекаем данные из команды
            order_data = {}
            for key in ['bouquet', 'date', 'time', 'delivery_needed', 'address', 'card_needed', 'card_text']:
                if key in command:
                    order_data[key] = command[key]
            
            # Если указан букет, валидируем его
            if 'bouquet' in order_data:
                retailer_id = command.get('retailer_id')
                if retailer_id:
                    validation = await self.catalog_service.validate_product(retailer_id)
                    if not validation['valid']:
                        available_products = await self.catalog_service.get_products()
                        product_names = [p.get('name', 'Без названия') for p in available_products[:5]]
                        
                        return {
                            "status": "error",
                            "action": "invalid_product",
                            "message": f"Такого букета нет в каталоге. Вот что у нас есть: {', '.join(product_names)}",
                            "available_products": product_names
                        }
                    else:
                        # Сохраняем информацию о реальном товаре
                        product = validation['product']
                        order_data['product_name'] = product.get('name', order_data['bouquet'])
                        order_data['product_price'] = product.get('price', 'Цена не указана')
                        order_data['retailer_id'] = retailer_id
            
            # TODO: Сохранить данные заказа
            self.logger.info(f"Order info saved for session {session_id}: {order_data}")
            
            return {
                "status": "success", 
                "action": "data_saved", 
                "data": order_data
            }
            
        except Exception as e:
            self.logger.error(f"Error saving order info: {e}")
            return {"status": "error", "message": "Ошибка при сохранении данных заказа"}

    async def _handle_confirm_order(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду подтверждения заказа"""
        try:
            # TODO: Логика подтверждения заказа
            self.logger.info(f"Order confirmed for session {session_id}")
            
            return {
                "status": "success",
                "action": "order_confirmed"
            }
            
        except Exception as e:
            self.logger.error(f"Error confirming order: {e}")
            return {"status": "error", "message": "Ошибка при подтверждении заказа"}

    async def _handle_clarify_request(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду уточнения запроса"""
        try:
            clarification = command.get('clarification', '')
            self.logger.info(f"Clarification requested for session {session_id}: {clarification}")
            
            return {
                "status": "success",
                "action": "clarification_sent",
                "clarification": clarification
            }
            
        except Exception as e:
            self.logger.error(f"Error handling clarification: {e}")
            return {"status": "error", "message": "Ошибка при обработке уточнения"} 
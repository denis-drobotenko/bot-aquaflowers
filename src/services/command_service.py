"""
Сервис для обработки команд от AI
"""

from src.utils.logging_decorator import log_function
from src.services.catalog_service import CatalogService
from src.services.order_service import OrderService
from src.services.session_service import SessionService
from src.models.order import Order, OrderItem, OrderStatus
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
from typing import Dict, Any, Optional
import json

class CommandService:
    def __init__(self):
        self.catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        self.order_service = OrderService()
        self.session_service = SessionService()

    @log_function("command_service")
    async def handle_command(self, command: Dict[str, Any], session_id: str, sender_id: str) -> Dict[str, Any]:
        """Обрабатывает команду от AI"""
        try:
            if not command or not isinstance(command, dict):
                return {"status": "error", "message": "Invalid command format"}

            command_type = command.get('type')
            if not command_type:
                return {"status": "error", "message": "No command type found"}

            print(f"Handling command: {command_type} for session {session_id}")

            # Выполняем команду в зависимости от типа
            if command_type == 'send_catalog':
                return await self._handle_send_catalog(sender_id, session_id, command)
            elif command_type == 'save_order_info':
                return await self._handle_save_order_info(sender_id, session_id, command)
            elif command_type == 'add_order_item':
                return await self._handle_add_order_item(sender_id, session_id, command)
            elif command_type == 'remove_order_item':
                return await self._handle_remove_order_item(sender_id, session_id, command)
            elif command_type == 'update_order_delivery':
                return await self._handle_update_order_delivery(sender_id, session_id, command)
            elif command_type == 'confirm_order':
                return await self._handle_confirm_order(sender_id, session_id, command)
            elif command_type == 'clarify_request':
                return await self._handle_clarify_request(sender_id, session_id, command)
            else:
                return {"status": "error", "message": f"Unknown command: {command_type}"}

        except Exception as e:
            print(f"Error handling command: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_send_catalog(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду отправки каталога"""
        try:
            products = self.catalog_service.get_available_products()
            
            if not products:
                return {
                    "status": "error",
                    "message": "К сожалению, наш каталог сейчас временно недоступен. Приносим извинения за неудобства! Пожалуйста, попробуйте немного позже. 🌸"
                }

            # Отправляем каталог через CatalogSender
            from src.services.catalog_sender import catalog_sender
            success = await catalog_sender.send_catalog(sender_id, session_id)
            
            if success:
                return {
                    "status": "success",
                    "action": "catalog_sent",
                    "products_count": len(products)
                }
            else:
                return {
                    "status": "error",
                    "message": "Ошибка при отправке каталога."
                }

        except Exception as e:
            print(f"Error sending catalog: {e}")
            return {"status": "error", "message": "Ошибка при отправке каталога"}

    async def _handle_save_order_info(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду сохранения данных заказа (товары и общие данные)"""
        try:
            order_data = {}
            
            # 1. Обрабатываем товар если есть
            if 'bouquet' in command and 'retailer_id' in command:
                # Валидируем товар через каталог
                validation = self.catalog_service.validate_product(command['retailer_id'])
                if validation['valid']:
                    product = validation['product']
                    item_data = {
                        'bouquet': command['bouquet'],
                        'quantity': command.get('quantity', 1),
                        'price': product.get('price'),
                        'notes': command.get('notes'),
                        'product_id': command['retailer_id']
                    }
                    # Обновляем или добавляем товар в заказ
                    await self.order_service.update_order_item(session_id, sender_id, item_data)
                    print(f"Item updated in order: {item_data}")
                else:
                    print(f"Invalid product: {command['retailer_id']}")
            
            # 2. Обрабатываем общие данные заказа
            general_fields = ['date', 'time', 'delivery_needed', 'address', 'card_needed', 
                             'card_text', 'recipient_name', 'recipient_phone']
            
            for field in general_fields:
                if field in command:
                    order_data[field] = command[field]

            # 3. Обновляем общие данные заказа
            if order_data:
                order_id = await self.order_service.update_order_data(session_id, sender_id, order_data)
                print(f"Order info updated for session {session_id}: {order_data}, order_id: {order_id}")
            
            return {
                "status": "success", 
                "action": "order_data_updated", 
                "data": order_data
            }
        except Exception as e:
            print(f"Error saving order info: {e}")
            return {"status": "error", "message": "Ошибка при сохранении данных заказа"}

    async def _handle_add_order_item(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду добавления товара в заказ"""
        try:
            # Валидируем товар через каталог
            if 'retailer_id' in command:
                validation = self.catalog_service.validate_product(command['retailer_id'])
                if not validation['valid']:
                    return {
                        "status": "error",
                        "action": "invalid_product",
                        "message": "Такого товара нет в каталоге"
                    }
                else:
                    # Добавляем информацию о товаре из каталога
                    product = validation['product']
                    command['price'] = product.get('price')
                    command['product_id'] = command['retailer_id']

            # Подготавливаем данные товара
            item_data = {
                'bouquet': command['bouquet'],
                'quantity': command.get('quantity', 1),
                'price': command.get('price'),
                'notes': command.get('notes'),
                'product_id': command.get('product_id')
            }

            order_id = await self.order_service.add_item(session_id, sender_id, item_data)
            
            return {
                "status": "success",
                "action": "item_added",
                "item_data": item_data,
                "order_id": order_id
            }
        except Exception as e:
            print(f"Error adding order item: {e}")
            return {"status": "error", "message": "Ошибка при добавлении товара"}

    async def _handle_remove_order_item(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду удаления товара из заказа"""
        try:
            product_id = command.get('product_id')
            if not product_id:
                return {"status": "error", "message": "Не указан ID товара для удаления"}

            success = await self.order_service.remove_item(session_id, sender_id, product_id)
            
            if success:
                return {
                    "status": "success",
                    "action": "item_removed",
                    "product_id": product_id
                }
            else:
                return {
                    "status": "error",
                    "message": "Товар не найден в заказе"
                }
        except Exception as e:
            print(f"Error removing order item: {e}")
            return {"status": "error", "message": "Ошибка при удалении товара"}

    async def _handle_update_order_delivery(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду обновления данных доставки"""
        try:
            delivery_data = {}
            delivery_fields = ['date', 'time', 'delivery_needed', 'address', 'card_needed', 
                              'card_text', 'recipient_name', 'recipient_phone']
            
            for field in delivery_fields:
                if field in command:
                    delivery_data[field] = command[field]

            order_id = await self.order_service.update_order_data(session_id, sender_id, delivery_data)
            
            return {
                "status": "success",
                "action": "delivery_updated",
                "delivery_data": delivery_data,
                "order_id": order_id
            }
        except Exception as e:
            print(f"Error updating delivery: {e}")
            return {"status": "error", "message": "Ошибка при обновлении данных доставки"}

    async def _handle_confirm_order(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду подтверждения заказа"""
        try:
            order_result = await self.order_service.process_order_for_operator(session_id, sender_id)
            
            if order_result['is_ready_for_operator']:
                # Заказ готов - обновляем статус
                await self.order_service.update_order_status(session_id, sender_id, OrderStatus.CONFIRMED)
                
                # Отправляем заказ в LINE
                line_result = await self.order_service.send_order_to_line(session_id, sender_id)
                if line_result != "ok":
                    print(f"[COMMAND_SERVICE] Ошибка отправки в LINE: {line_result}")
                
                # Заказ подтвержден - оставляем текущую сессию
                print(f"[COMMAND_SERVICE] Заказ подтвержден, оставляем текущую сессию: {session_id}")
                
                return {
                    "status": "success",
                    "action": "order_confirmed",
                    "order_data": order_result['order_data'],
                    "validation": order_result['validation'],
                    "summary_for_ai": order_result['summary_for_ai'],
                    "is_ready_for_operator": True,
                    "line_sent": line_result == "ok"
                }
            else:
                # Заказ не готов
                return {
                    "status": "error",
                    "action": "incomplete_order",
                    "order_data": order_result['order_data'],
                    "validation": order_result['validation'],
                    "summary_for_ai": order_result['summary_for_ai'],
                    "is_ready_for_operator": False
                }
        except Exception as e:
            print(f"Error confirming order: {e}")
            return {"status": "error", "message": "Ошибка при подтверждении заказа"}

    async def _handle_clarify_request(self, sender_id: str, session_id: str, command: Dict[str, Any]) -> Dict[str, Any]:
        """Обрабатывает команду уточнения запроса"""
        try:
            clarification = command.get('clarification', '')
            print(f"Clarification request: {clarification}")
            
            return {
                "status": "success",
                "action": "clarification_sent",
                "clarification": clarification
            }
        except Exception as e:
            print(f"Error processing clarification: {e}")
            return {"status": "error", "message": "Ошибка при обработке уточнения"} 
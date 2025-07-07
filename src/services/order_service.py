"""
Сервис для работы с заказами (один заказ на сессию с несколькими товарами)
"""

from src.utils.logging_decorator import log_function
from src.repositories.order_repository import OrderRepository
from src.models.order import Order, OrderItem, OrderStatus
from typing import List, Optional, Dict, Any
from datetime import datetime

class OrderService:
    def __init__(self):
        self.repo = OrderRepository()

    @log_function("order_service")
    async def get_or_create_order(self, session_id: str, sender_id: str) -> Order:
        """
        Получает существующий заказ для сессии или создает новый.
        Один заказ на сессию.
        Структура: orders/{sender_id}/sessions/{session_id}
        """
        # Пытаемся получить существующий заказ
        existing_order = await self.repo.get_order_by_session(sender_id, session_id)
        if existing_order:
            return existing_order
        else:
            # Создаем новый заказ
            order = Order(
                order_id=session_id,  # Используем session_id как order_id
                session_id=session_id,
                sender_id=sender_id,
                status=OrderStatus.DRAFT
            )
            await self.repo.create_order_for_session(order)
            return order

    @log_function("order_service")
    async def update_order_data(self, session_id: str, sender_id: str, order_data: Dict[str, Any]) -> str:
        """
        Обновляет данные заказа (доставка, получатель и т.д.).
        Возвращает order_id.
        """
        order = await self.get_or_create_order(session_id, sender_id)
        
        # Обновляем только общие поля (не товары)
        general_fields = ['date', 'time', 'delivery_needed', 'address', 'card_needed', 
                         'card_text', 'recipient_name', 'recipient_phone', 'customer_name', 'customer_phone']
        
        for field in general_fields:
            if field in order_data:
                setattr(order, field, order_data[field])
        
        order.updated_at = datetime.now()
        
        await self.repo.update_order_by_session(sender_id, session_id, order)
        return order.order_id

    @log_function("order_service")
    async def add_item(self, session_id: str, sender_id: str, item_data: Dict[str, Any]) -> str:
        """
        Добавляет новый товар в заказ.
        """
        order = await self.get_or_create_order(session_id, sender_id)
        
        product_id = item_data.get('product_id', f"item_{len(order.items) + 1}")
        
        # Добавляем новый товар
        item = OrderItem(
            product_id=product_id,
            bouquet=item_data['bouquet'],
            quantity=item_data.get('quantity', 1),
            price=item_data.get('price'),
            notes=item_data.get('notes')
        )
        order.items.append(item)
        print(f"Added new item {product_id}: {item_data['bouquet']}")
        
        order.updated_at = datetime.now()
        await self.repo.update_order_by_session(sender_id, session_id, order)
        return order.order_id

    async def update_order_item(self, session_id: str, sender_id: str, item_data: Dict[str, Any]) -> str:
        """
        Обновляет существующий товар в заказе. Если товара нет, создает новый.
        """
        order = await self.get_or_create_order(session_id, sender_id)
        
        product_id = item_data.get('product_id')
        
        if not product_id:
            # Если product_id не указан, добавляем новый товар
            return await self.add_item(session_id, sender_id, item_data)
        
        # Ищем существующий товар
        existing_item = None
        for item in order.items:
            if item.product_id == product_id:
                existing_item = item
                break
        
        if existing_item:
            # Обновляем существующий товар
            existing_item.bouquet = item_data['bouquet']
            existing_item.quantity = item_data.get('quantity', 1)
            if 'price' in item_data:
                existing_item.price = item_data['price']
            if 'notes' in item_data:
                existing_item.notes = item_data['notes']
            print(f"Updated existing item {product_id}: {item_data['bouquet']}")
        else:
            # Товар не найден, добавляем новый
            return await self.add_item(session_id, sender_id, item_data)
        
        order.updated_at = datetime.now()
        await self.repo.update_order_by_session(sender_id, session_id, order)
        return order.order_id

    async def remove_item(self, session_id: str, sender_id: str, product_id: str) -> bool:
        """
        Удаляет товар из заказа.
        """
        order = await self.get_or_create_order(session_id, sender_id)
        
        original_count = len(order.items)
        order.items = [item for item in order.items if item.product_id != product_id]
        
        if len(order.items) < original_count:
            order.updated_at = datetime.now()
            await self.repo.update_order_by_session(sender_id, session_id, order)
            return True
        return False



    @log_function("order_service")
    async def update_order_status(self, session_id: str, sender_id: str, status: OrderStatus) -> bool:
        """
        Обновляет статус заказа.
        """
        order = await self.get_or_create_order(session_id, sender_id)
        order.status = status
        order.updated_at = datetime.now()
        
        await self.repo.update_order_by_session(sender_id, session_id, order)
        return True

    async def get_order_data(self, session_id: str, sender_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Получает данные заказа для сессии.
        """
        if not sender_id:
            # Извлекаем sender_id из session_id (первая часть до первого подчеркивания)
            sender_id = session_id.split('_')[0] if '_' in session_id else session_id
        
        try:
            order = await self.repo.get_order_by_session(sender_id, session_id)
            if order:
                print(f"Order retrieved successfully: {order.order_id}")
                print(f"Order type: {type(order)}")
                print(f"Order attributes: {dir(order)}")
                
                # Безопасная обработка items
                items = []
                if hasattr(order, 'items'):
                    print(f"order.items type: {type(order.items)}")
                    print(f"order.items value: {order.items}")
                    if order.items:
                        if isinstance(order.items, list):
                            items = [item.to_dict() for item in order.items]
                            print(f"Processed {len(items)} items")
                        else:
                            print(f"Warning: order.items is not a list: {type(order.items)}")
                else:
                    print("order.items attribute not found")
                
                result = {
                    'order_id': order.order_id,
                    'sender_id': order.sender_id,
                    'status': order.status.value,
                    'date': order.date,
                    'time': order.time,
                    'delivery_needed': order.delivery_needed,
                    'address': order.address,
                    'card_needed': order.card_needed,
                    'card_text': order.card_text,
                    'recipient_name': order.recipient_name,
                    'recipient_phone': order.recipient_phone,
                    'customer_name': getattr(order, 'customer_name', None),
                    'customer_phone': getattr(order, 'customer_phone', None),
                    'items': items,
                    'created_at': order.created_at.isoformat(),
                    'updated_at': order.updated_at.isoformat()
                }
                print(f"Returning order data with {len(items)} items")
                return result
            else:
                print(f"Order not found for session_id: {session_id}, sender_id: {sender_id}")
                return None
        except Exception as e:
            print(f"Error in get_order_data: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def get_user_order_history(self, sender_id: str, limit: int = 10) -> List[Order]:
        """
        Получает историю заказов пользователя.
        """
        return await self.repo.get_user_orders(sender_id, limit)

    def validate_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидирует данные заказа.
        """
        required_fields = {
            'date': 'Дата доставки',
            'time': 'Время доставки'
        }
        
        optional_fields = {
            'address': 'Адрес доставки',
            'recipient_name': 'Имя получателя',
            'recipient_phone': 'Телефон получателя',
            'card_text': 'Текст открытки'
        }
        
        missing_required = []
        missing_optional = []
        warnings = []
        
        # Проверяем обязательные поля
        for field, field_name in required_fields.items():
            if not order_data.get(field):
                missing_required.append(field_name)
        
        # Проверяем опциональные поля
        for field, field_name in optional_fields.items():
            if not order_data.get(field):
                missing_optional.append(field_name)
        
        # Проверяем товары
        items = order_data.get('items', [])
        if not items:
            missing_required.append('Товары в заказе')
        
        # Проверяем логику доставки
        if order_data.get('delivery_needed') and not order_data.get('address'):
            warnings.append("Указана доставка, но не указан адрес")
        
        # Проверяем логику открытки
        if order_data.get('card_needed') and not order_data.get('card_text'):
            warnings.append("Указана открытка, но не указан текст")
        
        is_complete = len(missing_required) == 0
        
        return {
            'is_complete': is_complete,
            'missing_required': missing_required,
            'missing_optional': missing_optional,
            'warnings': warnings,
            'order_data': order_data
        }

    def get_order_summary_for_ai(self, order_data: Dict[str, Any]) -> str:
        """
        Формирует резюме заказа для ИИ.
        """
        summary_parts = []
        
        # Заказчик
        if order_data.get('customer_name'):
            summary_parts.append(f"Заказчик: {order_data['customer_name']}")
        
        if order_data.get('customer_phone'):
            summary_parts.append(f"Телефон заказчика: {order_data['customer_phone']}")
        
        # Товары
        items = order_data.get('items', [])
        if items:
            summary_parts.append("Товары:")
            for i, item in enumerate(items, 1):
                item_summary = f"{i}. {item['bouquet']}"
                if item.get('quantity', 1) > 1:
                    item_summary += f" - {item['quantity']} шт."
                if item.get('notes'):
                    item_summary += f" ({item['notes']})"
                summary_parts.append(item_summary)
        
        # Дата и время
        if order_data.get('date') and order_data.get('time'):
            summary_parts.append(f"Дата и время: {order_data['date']} в {order_data['time']}")
        
        # Доставка
        if order_data.get('delivery_needed'):
            summary_parts.append("Доставка: Да")
            if order_data.get('address'):
                summary_parts.append(f"Адрес: {order_data['address']}")
        else:
            summary_parts.append("Доставка: Нет")
        
        # Открытка
        if order_data.get('card_needed'):
            summary_parts.append("Открытка: Да")
            if order_data.get('card_text'):
                summary_parts.append(f"Текст открытки: \"{order_data['card_text']}\"")
        else:
            summary_parts.append("Открытка: Нет")
        
        # Получатель
        if order_data.get('recipient_name'):
            summary_parts.append(f"Получатель: {order_data['recipient_name']}")
        
        if order_data.get('recipient_phone'):
            summary_parts.append(f"Телефон: {order_data['recipient_phone']}")
        
        return "\n".join(summary_parts)

    async def process_order_for_operator(self, session_id: str, sender_id: str) -> Dict[str, Any]:
        """
        Полный процесс обработки заказа для передачи оператору.
        """
        try:
            order_data = await self.get_order_data(session_id, sender_id) or {}
            validation = self.validate_order_data(order_data)
            summary_for_ai = self.get_order_summary_for_ai(order_data)
            
            return {
                'order_data': order_data,
                'validation': validation,
                'summary_for_ai': summary_for_ai,
                'is_ready_for_operator': validation['is_complete']
            }
            
        except Exception as e:
            return {
                'order_data': {},
                'validation': {'is_complete': False, 'missing_required': ['Ошибка обработки']},
                'summary_for_ai': "Ошибка при обработке заказа",
                'is_ready_for_operator': False
            }

    async def send_order_to_line(self, session_id: str, sender_id: str) -> str:
        """
        Отправляет заказ оператору в LINE.
        """
        try:
            order_data = await self.get_order_data(session_id, sender_id)
            if not order_data:
                return "error: order not found"
            
            # Формируем список букетов из items
            items = order_data.get('items', [])
            if items:
                bouquet_names = []
                for item in items:
                    bouquet_name = item.get('bouquet', 'Unknown')
                    quantity = item.get('quantity', 1)
                    if quantity > 1:
                        bouquet_names.append(f"{bouquet_name} x{quantity}")
                    else:
                        bouquet_names.append(bouquet_name)
                bouquet = ", ".join(bouquet_names)
            else:
                bouquet = "No items"
            
            address = order_data.get('address', '-')
            date = order_data.get('date', '-')
            time = order_data.get('time', '-')
            card_text = order_data.get('card_text', 'None')
            recipient_name = order_data.get('recipient_name', '-')
            recipient_phone = order_data.get('recipient_phone', '-')
            customer_name = order_data.get('customer_name', '-')
            customer_phone = order_data.get('customer_phone', '-')
            
            # Определяем базовый URL в зависимости от окружения
            import os
            base_url = os.getenv('BASE_URL', 'http://localhost:8080')
            if base_url == 'http://localhost:8080':
                # Локальная разработка
                chat_url = f"{base_url}/chat/{session_id}"
            else:
                # Продакшн
                chat_url = f"https://auraflora-bot-xicvc2y5hq-as.a.run.app/chat/{session_id}"
            
            # ENGLISH
            order_en = f"NEW ORDER CONFIRMED!\n\nBouquet: {bouquet}\nDelivery address: {address}\nDelivery date: {date}\nDelivery time: {time}\nCard text: {card_text}\nRecipient name: {recipient_name}\nRecipient phone: {recipient_phone}\nCustomer: {customer_name} ({customer_phone})\n"
            
            # THAI
            order_th = f"\nคำสั่งซื้อใหม่ได้รับการยืนยัน!\n\nช่อดอกไม้: {bouquet}\nที่อยู่จัดส่ง: {address}\nวันที่จัดส่ง: {date}\nเวลาจัดส่ง: {time}\nข้อความการ์ด: {card_text}\nชื่อผู้รับ: {recipient_name}\nเบอร์โทรศัพท์ผู้รับ: {recipient_phone}\nลูกค้า: {customer_name} ({customer_phone})\n"
            
            from datetime import datetime
            now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            status = f"Status: Order confirmed by customer\nTime: {now}"
            status_th = f"สถานะ: ลูกค้ายืนยันคำสั่งซื้อแล้ว\nเวลา: {now}"
            
            chat_link = f"Conversation link: {chat_url}"
            chat_link_th = f"ลิงก์การสนทนา: {chat_url}"
            
            order_summary = f"{order_en}\n{order_th}\n{status}\n{status_th}\n\n{chat_link}\n{chat_link_th}"
            
            # Отправляем в LINE
            from src.config.settings import LINE_ACCESS_TOKEN, LINE_GROUP_ID
            if not LINE_ACCESS_TOKEN or not LINE_GROUP_ID:
                return "error: LINE configuration missing"
            
            from linebot import LineBotApi
            from linebot.models import TextSendMessage
            from linebot.exceptions import LineBotApiError
            
            line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
            line_bot_api.push_message(LINE_GROUP_ID, TextSendMessage(text=order_summary))
            
            print(f"[ORDER_SERVICE] Заказ отправлен в LINE для сессии {session_id}")
            return "ok"
            
        except LineBotApiError as e:
            print(f"[ORDER_SERVICE] Ошибка LINE API: {e}")
            return f"error: LINE API error - {str(e)}"
        except Exception as e:
            print(f"[ORDER_SERVICE] Ошибка отправки в LINE: {e}")
            return f"error: {str(e)}"

    async def get_all_orders_for_crm(self) -> List[Dict[str, Any]]:
        """
        Получает все заказы для CRM с дополнительной информацией.
        """
        orders = await self.repo.get_all_orders()
        result = []
        
        for order in orders:
            order_dict = order.to_dict()
            # Добавляем дополнительную информацию
            order_dict['total_items'] = sum(item.quantity for item in order.items)
            # Безопасный парсинг цены
            total_price = 0
            for item in order.items:
                if item.price:
                    try:
                        # Убираем символы валюты, пробелы и неразрывные пробелы
                        price_str = item.price.replace('฿', '').replace(',', '').replace('\xa0', '').strip()
                        total_price += float(price_str)
                    except (ValueError, AttributeError):
                        print(f"Warning: Could not parse price '{item.price}' for item {item.product_id}")
                        continue
            order_dict['total_price'] = total_price
            result.append(order_dict)
        
        return result

    async def get_orders_by_time_period(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Получает заказы за определенный период времени.
        """
        all_orders = await self.get_all_orders_for_crm()
        filtered_orders = []
        
        for order in all_orders:
            created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
            if start_date <= created_at <= end_date:
                filtered_orders.append(order)
        
        return filtered_orders

    async def get_orders_by_status(self, status: OrderStatus) -> List[Dict[str, Any]]:
        """
        Получает заказы по статусу.
        """
        all_orders = await self.get_all_orders_for_crm()
        return [order for order in all_orders if order['status'] == status.value]

    async def get_customer_orders_summary(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получает сводку по клиентам и их заказам.
        """
        all_orders = await self.get_all_orders_for_crm()
        customers = {}
        
        for order in all_orders:
            sender_id = order['sender_id']
            if sender_id not in customers:
                customers[sender_id] = {
                    'sender_id': sender_id,
                    'name': order.get('customer_name', 'Неизвестный клиент'),
                    'phone': order.get('customer_phone', sender_id),
                    'orders': [],
                    'total_orders': 0,
                    'completed_orders': 0
                }
            
            customers[sender_id]['orders'].append(order)
            customers[sender_id]['total_orders'] += 1
            
            # Завершённые заказы: confirmed, cancelled и другие финальные статусы
            if order['status'] in ['confirmed', 'cancelled']:
                customers[sender_id]['completed_orders'] += 1
        
        # Разделяем на клиентов с заказами и без
        with_orders = []
        without_orders = []
        
        for customer in customers.values():
            if customer['total_orders'] > 0:
                with_orders.append(customer)
            else:
                without_orders.append(customer)
        
        # Сортируем по имени
        with_orders.sort(key=lambda x: x['name'].lower())
        without_orders.sort(key=lambda x: x['name'].lower())
        
        return {
            'with_orders': with_orders,
            'without_orders': without_orders
        } 
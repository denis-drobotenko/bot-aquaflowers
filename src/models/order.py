"""
Модель заказа
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class OrderStatus(Enum):
    """Статусы заказа"""
    DRAFT = "draft"                    # Данные собираются
    INCOMPLETE = "incomplete"          # Собрали, но не хватает обязательных данных
    READY = "ready"                   # Готов к подтверждению (все обязательные данные есть)
    CONFIRMED = "confirmed"           # Подтвержден пользователем
    SENT_TO_OPERATOR = "sent_to_operator"  # Отправлен оператору
    CANCELLED = "cancelled"           # Отменен


@dataclass
class OrderItem:
    """Модель товара в заказе"""
    
    product_id: str
    bouquet: str  # название букета
    quantity: int = 1
    price: Optional[str] = None
    notes: Optional[str] = None  # "для мамы", "для подруги" и т.д.
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует товар в словарь для сохранения в БД"""
        return {
            'product_id': self.product_id,
            'bouquet': self.bouquet,
            'quantity': self.quantity,
            'price': self.price,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        """Создает товар из словаря"""
        return cls(
            product_id=data['product_id'],
            bouquet=data['bouquet'],
            quantity=data.get('quantity', 1),
            price=data.get('price'),
            notes=data.get('notes')
        )


@dataclass
class Order:
    """Модель заказа"""
    
    # Основные поля
    order_id: str
    session_id: str
    sender_id: str
    status: OrderStatus = OrderStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Общие данные доставки (для всех товаров в заказе)
    date: Optional[str] = None
    time: Optional[str] = None
    delivery_needed: bool = False
    address: Optional[str] = None
    card_needed: bool = False
    card_text: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    
    # Данные заказчика (из WABA)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    
    # Связи с другими заказами
    parent_order_id: Optional[str] = None  # Связь с предыдущим заказом
    related_orders: List[str] = field(default_factory=list)  # Связанные заказы
    
    # Товары в заказе
    items: List[OrderItem] = field(default_factory=list)
    
    # Метаданные - УДАЛЕНО
    # metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None  # Заметки оператора
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if not self.order_id:
            raise ValueError("order_id не может быть пустым")
        if not self.session_id:
            raise ValueError("session_id не может быть пустым")
        if not self.sender_id:
            raise ValueError("sender_id не может быть пустым")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует заказ в словарь для сохранения в БД"""
        return {
            'order_id': self.order_id,
            'session_id': self.session_id,
            'sender_id': self.sender_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'date': self.date,
            'time': self.time,
            'delivery_needed': self.delivery_needed,
            'address': self.address,
            'card_needed': self.card_needed,
            'card_text': self.card_text,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'parent_order_id': self.parent_order_id,
            'related_orders': self.related_orders,
            'items': [item.to_dict() for item in self.items],
            # 'metadata': self.metadata or {},  # УДАЛЕНО
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Создает заказ из словаря"""
        # Парсим timestamp
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.now()
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        elif updated_at is None:
            updated_at = datetime.now()
        
        # Парсим items
        items = []
        items_data = data.get('items', [])
        if isinstance(items_data, list):
            for item_data in items_data:
                if isinstance(item_data, dict):
                    items.append(OrderItem.from_dict(item_data))
                else:
                    print(f"Warning: item_data is not a dict: {type(item_data)}")
        else:
            print(f"Warning: items_data is not a list: {type(items_data)}")
        
        return cls(
            order_id=data['order_id'],
            session_id=data['session_id'],
            sender_id=data['sender_id'],
            status=OrderStatus(data.get('status', 'draft')),
            created_at=created_at,
            updated_at=updated_at,
            date=data.get('date'),
            time=data.get('time'),
            delivery_needed=data.get('delivery_needed', False),
            address=data.get('address'),
            card_needed=data.get('card_needed', False),
            card_text=data.get('card_text'),
            recipient_name=data.get('recipient_name'),
            recipient_phone=data.get('recipient_phone'),
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            parent_order_id=data.get('parent_order_id'),
            related_orders=data.get('related_orders', []),
            items=items,
            # metadata=data.get('metadata'),  # УДАЛЕНО
            notes=data.get('notes')
        )
    
    def add_item(self, item: OrderItem):
        """Добавляет товар в заказ"""
        self.items.append(item)
    
    def remove_item(self, product_id: str):
        """Удаляет товар из заказа"""
        self.items = [item for item in self.items if item.product_id != product_id]
    
    def get_item(self, product_id: str) -> Optional[OrderItem]:
        """Получает товар по ID"""
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None
    
    def confirm(self):
        """Подтверждает заказ"""
        self.status = OrderStatus.CONFIRMED
    
    def process(self):
        """Переводит заказ в обработку"""
        self.status = OrderStatus.PROCESSING
    
    def complete(self):
        """Завершает заказ"""
        self.status = OrderStatus.COMPLETED
    
    def cancel(self):
        """Отменяет заказ"""
        self.status = OrderStatus.CANCELLED
    
    def is_draft(self) -> bool:
        """Проверяет, что заказ в черновике"""
        return self.status == OrderStatus.DRAFT
    
    def is_confirmed(self) -> bool:
        """Проверяет, что заказ подтвержден"""
        return self.status == OrderStatus.CONFIRMED
    
    def has_delivery(self) -> bool:
        """Проверяет, нужна ли доставка"""
        return self.delivery_needed and self.address
    
    def has_card(self) -> bool:
        """Проверяет, нужна ли открытка"""
        return self.card_needed and self.card_text
    
    def get_total_items(self) -> int:
        """Получает общее количество товаров"""
        return sum(item.quantity for item in self.items)
    
    # Методы get_metadata, set_metadata - УДАЛИТЬ 
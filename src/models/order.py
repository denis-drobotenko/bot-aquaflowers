"""
Модель заказа
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class OrderStatus(str, Enum):
    """Статусы заказа"""
    DRAFT = "draft"           # Черновик
    CONFIRMED = "confirmed"   # Подтвержден
    PROCESSING = "processing" # В обработке
    COMPLETED = "completed"   # Завершен
    CANCELLED = "cancelled"   # Отменен


@dataclass
class OrderItem:
    """Элемент заказа"""
    product_id: str
    product_name: str
    quantity: int = 1
    price: Optional[str] = None
    retailer_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price,
            'retailer_id': self.retailer_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OrderItem':
        return cls(
            product_id=data['product_id'],
            product_name=data['product_name'],
            quantity=data.get('quantity', 1),
            price=data.get('price'),
            retailer_id=data.get('retailer_id')
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
    
    # Информация о заказе
    bouquet: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    delivery_needed: bool = False
    address: Optional[str] = None
    card_needed: bool = False
    card_text: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_phone: Optional[str] = None
    
    # Товары
    items: List[OrderItem] = field(default_factory=list)
    
    # Метаданные
    metadata: Optional[Dict[str, Any]] = None
    
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
            'bouquet': self.bouquet,
            'date': self.date,
            'time': self.time,
            'delivery_needed': self.delivery_needed,
            'address': self.address,
            'card_needed': self.card_needed,
            'card_text': self.card_text,
            'recipient_name': self.recipient_name,
            'recipient_phone': self.recipient_phone,
            'items': [item.to_dict() for item in self.items],
            'metadata': self.metadata or {}
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
        
        # Парсим items
        items = []
        for item_data in data.get('items', []):
            items.append(OrderItem.from_dict(item_data))
        
        return cls(
            order_id=data['order_id'],
            session_id=data['session_id'],
            sender_id=data['sender_id'],
            status=OrderStatus(data.get('status', 'draft')),
            created_at=created_at,
            bouquet=data.get('bouquet'),
            date=data.get('date'),
            time=data.get('time'),
            delivery_needed=data.get('delivery_needed', False),
            address=data.get('address'),
            card_needed=data.get('card_needed', False),
            card_text=data.get('card_text'),
            recipient_name=data.get('recipient_name'),
            recipient_phone=data.get('recipient_phone'),
            items=items,
            metadata=data.get('metadata')
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
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Получает значение из метаданных"""
        if not self.metadata:
            return default
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any):
        """Устанавливает значение в метаданные"""
        if not self.metadata:
            self.metadata = {}
        self.metadata[key] = value 
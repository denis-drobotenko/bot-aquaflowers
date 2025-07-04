"""
Сервис для работы с заказами
"""

from src.utils.logging_utils import ContextLogger
from src.repositories.order_repository import OrderRepository
from src.models.order import Order, OrderStatus, OrderItem
from typing import List, Optional

class OrderService:
    def __init__(self):
        self.repo = OrderRepository()
        self.logger = ContextLogger("order_service")

    async def create_order(self, order: Order) -> Optional[str]:
        return await self.repo.create(order)

    async def get_order(self, order_id: str) -> Optional[Order]:
        return await self.repo.get_by_id(order_id)

    async def update_order(self, order_id: str, order: Order) -> bool:
        return await self.repo.update(order_id, order)

    async def confirm_order(self, order_id: str) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        order.confirm()
        return await self.update_order(order_id, order)

    async def complete_order(self, order_id: str) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        order.complete()
        return await self.update_order(order_id, order)

    async def cancel_order(self, order_id: str) -> bool:
        order = await self.get_order(order_id)
        if not order:
            return False
        order.cancel()
        return await self.update_order(order_id, order)

    async def get_orders_by_session(self, session_id: str, limit: int = 10) -> List[Order]:
        return await self.repo.find_by_field('session_id', session_id, limit=limit) 
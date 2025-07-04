"""
Репозиторий для заказов
"""

from src.repositories.base_repository import BaseRepository
from src.models.order import Order
from typing import Dict, Any

class OrderRepository(BaseRepository[Order]):
    def __init__(self):
        super().__init__('orders')

    def _model_to_dict(self, model: Order) -> Dict[str, Any]:
        return model.to_dict()

    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> Order:
        # id заказа может быть как поле, так и doc_id
        if 'id' not in data:
            data['id'] = doc_id
        return Order.from_dict(data) 
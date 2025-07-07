"""
Репозиторий для заказов с иерархической структурой orders/{user_id}/sessions/{session_id}
"""

from src.repositories.base_repository import BaseRepository
from src.models.order import Order
from typing import Dict, Any, Optional, List
from google.cloud import firestore

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
    
    def _get_user_session_collection_ref(self, sender_id: str, session_id: str):
        """
        Получает ссылку на подколлекцию сессии пользователя.
        Структура: orders/{sender_id}/sessions/{session_id}
        """
        if not self.db:
            raise RuntimeError("Firestore client not available")
        return self.db.collection(self.collection_name).document(sender_id).collection('sessions').document(session_id)
    
    def _get_user_collection_ref(self, sender_id: str):
        """
        Получает ссылку на коллекцию пользователя.
        Структура: orders/{sender_id}
        """
        if not self.db:
            raise RuntimeError("Firestore client not available")
        return self.db.collection(self.collection_name).document(sender_id)
    
    async def create_order_for_session(self, order: Order) -> Optional[str]:
        """
        Создает заказ для конкретной сессии пользователя.
        Структура: orders/{sender_id}/sessions/{session_id}
        """
        try:
            doc_data = self._model_to_dict(order)
            doc_ref = self._get_user_session_collection_ref(order.sender_id, order.session_id)
            doc_ref.set(doc_data)
            
            doc_id = doc_ref.id
            print(f"Created order document: orders/{order.sender_id}/sessions/{order.session_id}")
            return doc_id
            
        except Exception as e:
            print(f"Error creating order document: {e}")
            return None
    
    async def get_order_by_session(self, sender_id: str, session_id: str) -> Optional[Order]:
        """
        Получает заказ по сессии пользователя.
        """
        try:
            doc_ref = self._get_user_session_collection_ref(sender_id, session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                model = self._dict_to_model(data, doc.id)
                print(f"Retrieved order: orders/{sender_id}/sessions/{session_id}")
                return model
            else:
                print(f"Order not found: orders/{sender_id}/sessions/{session_id}")
                return None
                
        except Exception as e:
            print(f"Error getting order {sender_id}/{session_id}: {e}")
            return None
    
    async def update_order_by_session(self, sender_id: str, session_id: str, order: Order) -> bool:
        """
        Обновляет заказ по сессии пользователя.
        """
        try:
            doc_data = self._model_to_dict(order)
            doc_ref = self._get_user_session_collection_ref(sender_id, session_id)
            doc_ref.update(doc_data)
            
            print(f"Updated order: orders/{sender_id}/sessions/{session_id}")
            return True
            
        except Exception as e:
            print(f"Error updating order {sender_id}/{session_id}: {e}")
            return False
    
    async def get_user_orders(self, sender_id: str, limit: Optional[int] = None) -> List[Order]:
        """
        Получает все заказы пользователя.
        """
        try:
            user_ref = self._get_user_collection_ref(sender_id)
            sessions_ref = user_ref.collection('sessions')
            
            if limit:
                docs = sessions_ref.limit(limit).stream()
            else:
                docs = sessions_ref.stream()
            
            orders = []
            for doc in docs:
                data = doc.to_dict()
                model = self._dict_to_model(data, doc.id)
                orders.append(model)
            
            print(f"Retrieved {len(orders)} orders for user {sender_id}")
            return orders
            
        except Exception as e:
            print(f"Error getting user orders {sender_id}: {e}")
            return []
    
    async def order_exists(self, sender_id: str, session_id: str) -> bool:
        """
        Проверяет существование заказа для сессии.
        """
        try:
            doc_ref = self._get_user_session_collection_ref(sender_id, session_id)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            print(f"Error checking order existence {sender_id}/{session_id}: {e}")
            return False

    async def get_all_orders(self) -> List[Order]:
        """
        Получает все заказы из всех пользователей через collection_group('sessions').
        """
        try:
            if not self.db:
                raise RuntimeError("Firestore client not available")
            orders = []
            session_docs = self.db.collection_group('sessions').stream()
            for session_doc in session_docs:
                data = session_doc.to_dict()
                try:
                    model = self._dict_to_model(data, session_doc.id)
                    orders.append(model)
                except Exception as e:
                    print(f"[WARN] Ошибка парсинга заказа {session_doc.id}: {e}\n  Данные: {data}")
                    continue
            print(f"Retrieved {len(orders)} orders from all sessions (collection_group)")
            return orders
        except Exception as e:
            print(f"Error getting all orders (collection_group): {e}")
            return [] 
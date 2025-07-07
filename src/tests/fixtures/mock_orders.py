"""
Тестовые заказы для сервисов
"""

from typing import List, Dict, Any

def get_sample_orders() -> List[Dict[str, Any]]:
    return [
        {
            "order_id": "order_1",
            "sender_id": "user_1",
            "session_id": "session_1",
            "bouquet": "Pretty 😍",
            "retailer_id": "kie4sy3qsy",
            "delivery_needed": True,
            "address": "Rawai, Phuket",
            "date": "2024-01-15",
            "time": "14:00",
            "card_needed": True,
            "card_text": "С днем рождения!",
            "recipient_name": "Анна",
            "recipient_phone": "+79123456789",
            "status": "pending"
        },
        {
            "order_id": "order_2",
            "sender_id": "user_2",
            "session_id": "session_2",
            "bouquet": "Spirit 🌸",
            "retailer_id": "rl7vdxcifo",
            "delivery_needed": False,
            "address": "",
            "date": "2024-01-20",
            "time": "16:00",
            "card_needed": False,
            "card_text": "",
            "recipient_name": "John",
            "recipient_phone": "+66812345678",
            "status": "confirmed"
        }
    ]

def get_empty_orders() -> List[Dict[str, Any]]:
    return [] 
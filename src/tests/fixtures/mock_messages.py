"""
Тестовые сообщения для сервисов
"""

from typing import List, Dict, Any

def get_sample_messages() -> List[Dict[str, Any]]:
    return [
        {
            "sender_id": "user_1",
            "session_id": "session_1",
            "role": "user",
            "content": "Привет! Хочу посмотреть каталог",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        {
            "sender_id": "user_1",
            "session_id": "session_1",
            "role": "assistant",
            "content": "Здравствуйте! Конечно, покажу вам наш каталог цветов",
            "timestamp": "2024-01-01T12:01:00Z"
        },
        {
            "sender_id": "user_2",
            "session_id": "session_2",
            "role": "user",
            "content": "Hello! Show me the catalog, please",
            "timestamp": "2024-01-02T10:00:00Z"
        },
        {
            "sender_id": "user_2",
            "session_id": "session_2",
            "role": "assistant",
            "content": "Hello! Would you like to see our flower catalog?",
            "timestamp": "2024-01-02T10:01:00Z"
        }
    ]

def get_empty_messages() -> List[Dict[str, Any]]:
    return [] 
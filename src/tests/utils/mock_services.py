"""
Моки внешних сервисов для тестов
"""

from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List
import json

class MockGeminiModel:
    """Мок для Gemini модели"""
    
    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Test response"]
        self.response_index = 0
    
    def generate_content(self, prompt: str):
        """Мок генерации контента"""
        response = Mock()
        response.text = self.responses[self.response_index % len(self.responses)]
        self.response_index += 1
        return response

class MockWhatsAppClient:
    """Мок для WhatsApp клиента"""
    
    def __init__(self):
        self.sent_messages = []
        self.sent_images = []
    
    async def send_text_message(self, to_number: str, text: str) -> bool:
        """Мок отправки текстового сообщения"""
        self.sent_messages.append({
            "to": to_number,
            "text": text,
            "type": "text"
        })
        return True
    
    async def send_image_message(self, to_number: str, image_url: str, caption: str) -> bool:
        """Мок отправки изображения"""
        self.sent_images.append({
            "to": to_number,
            "image_url": image_url,
            "caption": caption,
            "type": "image"
        })
        return True

class MockFirestoreClient:
    """Мок для Firestore клиента"""
    
    def __init__(self):
        self.collections = {}
        self.documents = {}
    
    def collection(self, collection_name: str):
        """Мок коллекции"""
        if collection_name not in self.collections:
            self.collections[collection_name] = MockFirestoreCollection(collection_name)
        return self.collections[collection_name]

class MockFirestoreCollection:
    """Мок Firestore коллекции"""
    
    def __init__(self, name: str):
        self.name = name
        self.documents = {}
    
    def document(self, doc_id: str):
        """Мок документа"""
        if doc_id not in self.documents:
            self.documents[doc_id] = MockFirestoreDocument(doc_id)
        return self.documents[doc_id]
    
    def stream(self):
        """Мок стрима документов"""
        return [doc for doc in self.documents.values()]

class MockFirestoreDocument:
    """Мок Firestore документа"""
    
    def __init__(self, doc_id: str):
        self.id = doc_id
        self.exists = True
        self.data = {}
        self.collections = {}
    
    def get(self):
        """Мок получения документа"""
        return self
    
    def set(self, data: Dict[str, Any], merge: bool = False):
        """Мок установки данных"""
        if merge:
            self.data.update(data)
        else:
            self.data = data
    
    def to_dict(self):
        """Мок преобразования в словарь"""
        return self.data
    
    def collection(self, collection_name: str):
        """Мок подколлекции"""
        if collection_name not in self.collections:
            self.collections[collection_name] = MockFirestoreCollection(collection_name)
        return self.collections[collection_name]

class MockHTTPXClient:
    """Мок для HTTPX клиента"""
    
    def __init__(self):
        self.requests = []
        self.responses = {}
    
    def add_response(self, url: str, method: str, status_code: int, response_data: Dict[str, Any]):
        """Добавляет мок ответ"""
        key = f"{method}:{url}"
        self.responses[key] = {
            "status_code": status_code,
            "json": response_data
        }
    
    async def get(self, url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None):
        """Мок GET запроса"""
        self.requests.append({
            "method": "GET",
            "url": url,
            "headers": headers,
            "params": params
        })
        
        key = f"GET:{url}"
        if key in self.responses:
            response = Mock()
            response.status_code = self.responses[key]["status_code"]
            response.json.return_value = self.responses[key]["json"]
            response.raise_for_status = Mock()
            return response
        
        # Дефолтный ответ
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        response.raise_for_status = Mock()
        return response
    
    async def post(self, url: str, headers: Dict[str, str] = None, json: Dict[str, Any] = None):
        """Мок POST запроса"""
        self.requests.append({
            "method": "POST",
            "url": url,
            "headers": headers,
            "json": json
        })
        
        key = f"POST:{url}"
        if key in self.responses:
            response = Mock()
            response.status_code = self.responses[key]["status_code"]
            response.json.return_value = self.responses[key]["json"]
            response.raise_for_status = Mock()
            return response
        
        # Дефолтный ответ
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"messages": [{"id": "test_message_id"}]}
        response.raise_for_status = Mock()
        return response

def create_mock_ai_json_response(text: str, text_en: str, text_thai: str, command: Dict[str, Any] = None) -> str:
    """Создает JSON ответ AI в строковом формате"""
    response_data = {
        "text": text,
        "text_en": text_en,
        "text_thai": text_thai
    }
    if command:
        response_data["command"] = command
    
    return json.dumps(response_data, ensure_ascii=False)

def create_mock_ai_markdown_response(text: str, text_en: str, text_thai: str, command: Dict[str, Any] = None) -> str:
    """Создает ответ AI в markdown формате"""
    json_response = create_mock_ai_json_response(text, text_en, text_thai, command)
    return f"```json\n{json_response}\n```" 
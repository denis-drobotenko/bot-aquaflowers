"""
Базовый репозиторий для работы с Firestore
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, TypeVar, Generic
from google.cloud import firestore
from src.utils.logging_utils import ContextLogger

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Базовый класс для репозиториев Firestore.
    
    Generic T - тип модели данных
    """
    
    def __init__(self, collection_name: str):
        """
        Инициализирует репозиторий.
        
        Args:
            collection_name: Имя коллекции в Firestore
        """
        self.collection_name = collection_name
        self.db = self._get_firestore_client()
        self.logger = ContextLogger(f"{collection_name}_repository")
    
    def _get_firestore_client(self) -> Optional[firestore.Client]:
        """
        Получает клиент Firestore.
        
        Returns:
            Firestore клиент или None если не удалось инициализировать
        """
        try:
            return firestore.Client()
        except Exception as e:
            self.logger.error(f"Failed to initialize Firestore client: {e}")
            return None
    
    def _get_collection_ref(self):
        """
        Получает ссылку на коллекцию.
        
        Returns:
            Ссылка на коллекцию Firestore
        """
        if not self.db:
            raise RuntimeError("Firestore client not available")
        return self.db.collection(self.collection_name)
    
    @abstractmethod
    def _model_to_dict(self, model: T) -> Dict[str, Any]:
        """
        Преобразует модель в словарь для сохранения.
        
        Args:
            model: Модель данных
            
        Returns:
            Словарь для сохранения в БД
        """
        pass
    
    @abstractmethod
    def _dict_to_model(self, data: Dict[str, Any], doc_id: str) -> T:
        """
        Преобразует словарь в модель.
        
        Args:
            data: Данные из БД
            doc_id: ID документа
            
        Returns:
            Модель данных
        """
        pass
    
    async def create(self, model: T) -> Optional[str]:
        """
        Создает новый документ.
        
        Args:
            model: Модель для создания
            
        Returns:
            ID созданного документа или None при ошибке
        """
        try:
            doc_data = self._model_to_dict(model)
            doc_ref = self._get_collection_ref().document()
            doc_ref.set(doc_data)
            
            doc_id = doc_ref.id
            self.logger.info(f"Created document with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Error creating document: {e}")
            return None
    
    async def get_by_id(self, doc_id: str) -> Optional[T]:
        """
        Получает документ по ID.
        
        Args:
            doc_id: ID документа
            
        Returns:
            Модель данных или None если не найдено
        """
        try:
            doc_ref = self._get_collection_ref().document(doc_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                model = self._dict_to_model(data, doc_id)
                self.logger.info(f"Retrieved document: {doc_id}")
                return model
            else:
                self.logger.warning(f"Document not found: {doc_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting document {doc_id}: {e}")
            return None
    
    async def update(self, doc_id: str, model: T) -> bool:
        """
        Обновляет документ.
        
        Args:
            doc_id: ID документа
            model: Обновленная модель
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            doc_data = self._model_to_dict(model)
            doc_ref = self._get_collection_ref().document(doc_id)
            doc_ref.update(doc_data)
            
            self.logger.info(f"Updated document: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating document {doc_id}: {e}")
            return False
    
    async def delete(self, doc_id: str) -> bool:
        """
        Удаляет документ.
        
        Args:
            doc_id: ID документа
            
        Returns:
            True если успешно, False при ошибке
        """
        try:
            doc_ref = self._get_collection_ref().document(doc_id)
            doc_ref.delete()
            
            self.logger.info(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    async def list_all(self, limit: Optional[int] = None) -> List[T]:
        """
        Получает все документы из коллекции.
        
        Args:
            limit: Максимальное количество документов
            
        Returns:
            Список моделей
        """
        try:
            query = self._get_collection_ref()
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            models = []
            
            for doc in docs:
                data = doc.to_dict()
                model = self._dict_to_model(data, doc.id)
                models.append(model)
            
            self.logger.info(f"Retrieved {len(models)} documents")
            return models
            
        except Exception as e:
            self.logger.error(f"Error listing documents: {e}")
            return []
    
    async def find_by_field(self, field: str, value: Any, limit: Optional[int] = None) -> List[T]:
        """
        Ищет документы по полю.
        
        Args:
            field: Имя поля для поиска
            value: Значение поля
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных моделей
        """
        try:
            query = self._get_collection_ref().where(field, "==", value)
            
            if limit:
                query = query.limit(limit)
            
            docs = query.stream()
            models = []
            
            for doc in docs:
                data = doc.to_dict()
                model = self._dict_to_model(data, doc.id)
                models.append(model)
            
            self.logger.info(f"Found {len(models)} documents with {field}={value}")
            return models
            
        except Exception as e:
            self.logger.error(f"Error finding documents by {field}={value}: {e}")
            return []
    
    async def exists(self, doc_id: str) -> bool:
        """
        Проверяет существование документа.
        
        Args:
            doc_id: ID документа
            
        Returns:
            True если документ существует
        """
        try:
            doc_ref = self._get_collection_ref().document(doc_id)
            doc = doc_ref.get()
            return doc.exists
            
        except Exception as e:
            self.logger.error(f"Error checking document existence {doc_id}: {e}")
            return False 
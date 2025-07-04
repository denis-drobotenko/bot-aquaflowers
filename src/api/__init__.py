"""
API модуль - роуты FastAPI
"""

from .webhook_routes import router as webhook_router
from .chat_routes import router as chat_router

__all__ = ['webhook_router', 'chat_router'] 
"""
FastAPI роуты
"""

from .chat_routes import router as chat_router
from .healthcheck import router as healthcheck_router

__all__ = [
    'chat_router', 
    'healthcheck_router'
] 
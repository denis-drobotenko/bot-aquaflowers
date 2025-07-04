#!/usr/bin/env python3
"""
Точка входа для Cloud Run
"""

import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем и запускаем приложение
from src.main import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 
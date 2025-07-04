#!/usr/bin/env python3
"""
Быстрый тест работоспособности для деплоя (без ai_manager)
"""

import asyncio
import sys
import os
import time
from datetime import datetime

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.models.message import Message, MessageRole
from src.config.settings import GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

async def test_quick():
    print("=== БЫСТРЫЙ ТЕСТ РАБОТОСПОСОБНОСТИ (НОВЫЙ) ===")
    sender_id = f"test_user_quick_{int(time.time())}"
    session_id = f"test_session_quick_{int(time.time())}"

    # Тест 1: Проверка AI
    print("\n1. Тест: AI отвечает на простое сообщение")
    try:
        ai_service = AIService(GEMINI_API_KEY)
        test_message = [
            Message(
                sender_id=sender_id,
                session_id=session_id,
                role=MessageRole.USER,
                content="Привет"
            )
        ]
        ai_text = await ai_service.generate_response(test_message)
        if ai_text and len(ai_text) > 10:
            print("✅ AI отвечает корректно!")
        else:
            print("❌ AI не отвечает или отвечает слишком коротко")
            return False
    except Exception as e:
        print(f"❌ Ошибка в AI: {e}")
        return False

    # Тест 2: Проверка каталога
    print("\n2. Тест: Чтение каталога")
    try:
        catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
        products = await catalog_service.get_available_products()
        if products and len(products) > 0:
            print(f"✅ Каталог загружается корректно! Найдено товаров: {len(products)}")
        else:
            print("❌ Каталог не загружается или слишком короткий")
            return False
    except Exception as e:
        print(f"❌ Ошибка в каталоге: {e}")
        return False

    # Тест 3: Проверка валидации товара
    print("\n3. Тест: Валидация товара")
    try:
        if products:
            test_product = products[0]
            retailer_id = test_product.get('retailer_id')
            if retailer_id:
                validation = await catalog_service.validate_product(retailer_id)
                if validation["valid"]:
                    print("✅ Валидация товара работает!")
                else:
                    print("❌ Валидация товара не работает")
                    return False
    except Exception as e:
        print(f"❌ Ошибка в валидации: {e}")
        return False

    print("\n✅ Все быстрые тесты пройдены! Система готова к деплою.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_quick())
    if not success:
        sys.exit(1) 
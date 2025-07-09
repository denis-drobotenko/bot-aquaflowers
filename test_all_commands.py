#!/usr/bin/env python3
"""
Тесты для всех команд AI
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.command_service import CommandService
from src.services.message_processor import MessageProcessor
from src.services.ai_service import AIService
from src.config.settings import GEMINI_API_KEY

async def test_send_catalog():
    """Тест команды send_catalog"""
    print("\n=== ТЕСТ: send_catalog ===")
    
    command_service = CommandService()
    
    # Тестируем отправку каталога
    result = await command_service.handle_command(
        command={"type": "send_catalog"},
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'success':
        print("✅ send_catalog работает")
    else:
        print(f"❌ send_catalog ошибка: {result.get('message')}")

async def test_save_order_info():
    """Тест команды save_order_info"""
    print("\n=== ТЕСТ: save_order_info ===")
    
    command_service = CommandService()
    
    # Тестируем сохранение букета
    result = await command_service.handle_command(
        command={
            "type": "save_order_info",
            "bouquet": "Spirit",
            "retailer_id": "test_product_123"
        },
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'success':
        print("✅ save_order_info работает")
    else:
        print(f"❌ save_order_info ошибка: {result.get('message')}")

async def test_add_order_item():
    """Тест команды add_order_item"""
    print("\n=== ТЕСТ: add_order_item ===")
    
    command_service = CommandService()
    
    # Тестируем добавление товара
    result = await command_service.handle_command(
        command={
            "type": "add_order_item",
            "bouquet": "Rose Garden",
            "retailer_id": "test_product_456",
            "quantity": 2
        },
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'success':
        print("✅ add_order_item работает")
    else:
        print(f"❌ add_order_item ошибка: {result.get('message')}")

async def test_remove_order_item():
    """Тест команды remove_order_item"""
    print("\n=== ТЕСТ: remove_order_item ===")
    
    command_service = CommandService()
    
    # Тестируем удаление товара
    result = await command_service.handle_command(
        command={
            "type": "remove_order_item",
            "product_id": "test_product_123"
        },
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'success':
        print("✅ remove_order_item работает")
    else:
        print(f"❌ remove_order_item ошибка: {result.get('message')}")



async def test_confirm_order():
    """Тест команды confirm_order"""
    print("\n=== ТЕСТ: confirm_order ===")
    
    command_service = CommandService()
    
    # Тестируем подтверждение заказа
    result = await command_service.handle_command(
        command={"type": "confirm_order"},
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'success':
        print("✅ confirm_order работает")
    else:
        print(f"❌ confirm_order ошибка: {result.get('message')}")

async def test_unknown_command():
    """Тест неизвестной команды"""
    print("\n=== ТЕСТ: unknown_command ===")
    
    command_service = CommandService()
    
    # Тестируем неизвестную команду
    result = await command_service.handle_command(
        command={"type": "unknown_command"},
        session_id="test_session_123",
        sender_id="test_user_456"
    )
    
    print(f"Результат: {result}")
    
    if result.get('status') == 'error':
        print("✅ unknown_command правильно отклонена")
    else:
        print("❌ unknown_command должна быть отклонена")

async def test_supported_commands():
    """Тест списка поддерживаемых команд"""
    print("\n=== ТЕСТ: SUPPORTED_COMMANDS ===")
    
    message_processor = MessageProcessor()
    
    expected_commands = {
        'send_catalog',
        'save_order_info', 
        'add_order_item',
        'remove_order_item',
        'confirm_order'
    }
    
    actual_commands = message_processor.SUPPORTED_COMMANDS
    
    print(f"Ожидаемые команды: {expected_commands}")
    print(f"Фактические команды: {actual_commands}")
    
    if expected_commands == actual_commands:
        print("✅ SUPPORTED_COMMANDS соответствуют ожиданиям")
    else:
        missing = expected_commands - actual_commands
        extra = actual_commands - expected_commands
        print(f"❌ Несоответствие:")
        if missing:
            print(f"   Отсутствуют: {missing}")
        if extra:
            print(f"   Лишние: {extra}")

async def test_ai_response_parsing():
    """Тест парсинга ответов AI"""
    print("\n=== ТЕСТ: AI Response Parsing ===")
    
    ai_service = AIService(GEMINI_API_KEY)
    
    # Тестируем парсинг правильного JSON
    test_response = '''
    {
      "text": "Привет! Покажу каталог.",
      "text_en": "Hello! I'll show the catalog.",
      "text_thai": "สวัสดี! ฉันจะแสดงแคตตาล็อก",
      "command": {
        "type": "send_catalog"
      }
    }
    '''
    
    from src.utils.ai_utils import parse_ai_response
    result = parse_ai_response(test_response)
    
    print(f"Результат парсинга: {result}")
    
    if result[0] and result[3] and result[3].get('type') == 'send_catalog':
        print("✅ AI response parsing работает")
    else:
        print("❌ AI response parsing ошибка")

async def main():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ТЕСТОВ КОМАНД AI")
    print("=" * 50)
    
    try:
        # Тесты команд
        await test_send_catalog()
        await test_save_order_info()
        await test_add_order_item()
        await test_remove_order_item()
        await test_confirm_order()
        await test_unknown_command()
        
        # Тесты системы
        await test_supported_commands()
        await test_ai_response_parsing()
        
        print("\n" + "=" * 50)
        print("✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТАХ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 
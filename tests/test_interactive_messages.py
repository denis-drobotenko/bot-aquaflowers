#!/usr/bin/env python3
"""
Тест обработки интерактивных сообщений
"""

import sys
import os

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем src в путь
# Добавляем src в путь
current_dir = os.path.dirname(__file__)
# Всегда добавляем путь к src относительно текущего файла
src_path = os.path.join(current_dir, '..', 'src')
sys.path.insert(0, src_path)

from src.webhook_handlers import get_button_reply, get_list_reply, get_product, get_order

def test_interactive_messages():
    """Тестируем обработку интерактивных сообщений"""
    print("=== ТЕСТ ИНТЕРАКТИВНЫХ СООБЩЕНИЙ ===")
    
    # Тест 1: Button Reply
    print("\n1. Тест: Button Reply")
    button_webhook = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "interactive": {
                            "type": "button_reply",
                            "button_reply": {
                                "id": "btn_catalog",
                                "title": "Показать каталог"
                            }
                        }
                    }]
                }
            }]
        }]
    }
    
    result = get_button_reply(button_webhook)
    print(f"Button reply: {result}")
    if result and result['title'] == "Показать каталог":
        print("✅ Button reply обрабатывается правильно!")
    else:
        print("❌ Button reply не обрабатывается")
    
    # Тест 2: Product Selection
    print("\n2. Тест: Product Selection")
    product_webhook = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "product": {
                            "id": "prod_123",
                            "catalog_id": "cat_456",
                            "product_retailer_id": "rl7vdxcifo"
                        }
                    }]
                }
            }]
        }]
    }
    
    result = get_product(product_webhook)
    print(f"Product selection: {result}")
    if result and result['product_retailer_id'] == "rl7vdxcifo":
        print("✅ Product selection обрабатывается правильно!")
    else:
        print("❌ Product selection не обрабатывается")
    
    # Тест 3: Order Placement
    print("\n3. Тест: Order Placement")
    order_webhook = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "order": {
                            "id": "order_789",
                            "catalog_id": "cat_456",
                            "product_items": [
                                {"product_retailer_id": "rl7vdxcifo", "quantity": 1}
                            ]
                        }
                    }]
                }
            }]
        }]
    }
    
    result = get_order(order_webhook)
    print(f"Order placement: {result}")
    if result and result['order_id'] == "order_789":
        print("✅ Order placement обрабатывается правильно!")
    else:
        print("❌ Order placement не обрабатывается")
    
    # Тест 4: List Reply
    print("\n4. Тест: List Reply")
    list_webhook = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "interactive": {
                            "type": "list_reply",
                            "list_reply": {
                                "id": "list_123",
                                "title": "Розовые розы",
                                "description": "25 роз"
                            }
                        }
                    }]
                }
            }]
        }]
    }
    
    result = get_list_reply(list_webhook)
    print(f"List reply: {result}")
    if result and result['title'] == "Розовые розы":
        print("✅ List reply обрабатывается правильно!")
    else:
        print("❌ List reply не обрабатывается")

if __name__ == "__main__":
    test_interactive_messages() 
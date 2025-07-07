#!/usr/bin/env python3
"""
Тестовый скрипт для проверки CRM
"""

import requests
import json
from datetime import datetime, timedelta

def test_crm():
    base_url = "http://localhost:8080"
    
    print("🌺 Тестирование AquaFlora CRM")
    print("=" * 50)
    
    # Тест 1: Корневой роут (должен перенаправлять на CRM)
    print("\n1. Тест корневого роута...")
    try:
        response = requests.get(f"{base_url}/", allow_redirects=True)
        if response.status_code == 200 and "AquaFlora CRM" in response.text:
            print("✅ Корневой роут перенаправляет на CRM")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тест 2: CRM главная страница
    print("\n2. Тест CRM главной страницы...")
    try:
        response = requests.get(f"{base_url}/crm/")
        if response.status_code == 200:
            print("✅ CRM главная страница загружается")
            if "По времени" in response.text:
                print("✅ Табы отображаются")
            if "Сегодня" in response.text:
                print("✅ Секции времени отображаются")
        else:
            print(f"❌ Ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тест 3: Страница заказа (с несуществующим заказом)
    print("\n3. Тест страницы заказа...")
    try:
        response = requests.get(f"{base_url}/crm/order/test_order_123")
        if response.status_code == 404:
            print("✅ Страница заказа возвращает 404 для несуществующего заказа")
        else:
            print(f"❌ Неожиданный статус: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тест 4: API заказов
    print("\n4. Тест API заказов...")
    try:
        response = requests.get(f"{base_url}/crm/api/orders")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API заказов работает, возвращает {len(data.get('orders', []))} заказов")
        else:
            print(f"❌ Ошибка API: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    # Тест 5: Статические файлы
    print("\n5. Тест статических файлов...")
    try:
        response = requests.get(f"{base_url}/test-static")
        if response.status_code == 200:
            print("✅ Статические файлы доступны")
        else:
            print(f"❌ Ошибка статических файлов: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")

if __name__ == "__main__":
    test_crm() 
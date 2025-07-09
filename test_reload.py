#!/usr/bin/env python3
import requests
import time

def test_server():
    """Тестирует работу сервера"""
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ Сервер работает!")
            return True
        else:
            print(f"❌ Сервер вернул статус: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения к серверу: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Проверяем работу сервера...")
    test_server() 
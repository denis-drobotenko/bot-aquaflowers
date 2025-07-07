#!/usr/bin/env python3
"""
Скрипт для создания тестовых логов с разными временными метками
"""

import os
import json
import datetime
import random

# Создаем папку logs если её нет
os.makedirs("logs", exist_ok=True)

# Функции для генерации логов
def create_test_logs():
    """Создает тестовые логи с разными временными метками"""
    
    # Базовое время (сейчас)
    base_time = datetime.datetime.now()
    
    # Модули и функции для разнообразия
    modules = ["order_service", "ai_service", "message_service", "session_service", "user_service"]
    functions = ["create_order", "process_message", "get_user", "update_session", "send_notification"]
    
    logs = []
    
    # Создаем логи за последние 24 часа
    for i in range(50):
        # Время от 24 часов назад до сейчас
        hours_ago = random.uniform(0, 24)
        log_time = base_time - datetime.timedelta(hours=hours_ago)
        
        # Случайный модуль и функция
        module = random.choice(modules)
        function = random.choice(functions)
        
        # Создаем запись о начале функции
        start_log = {
            "event": "function_start",
            "module": module,
            "function": function,
            "timestamp": log_time.isoformat(),
            "parameters": {
                "user_id": f"user_{random.randint(1000, 9999)}",
                "data": {"test": "value", "count": random.randint(1, 100)}
            }
        }
        logs.append(start_log)
        
        # Создаем запись о завершении функции (через 1-100мс)
        execution_time = random.uniform(1, 100)
        end_time = log_time + datetime.timedelta(milliseconds=execution_time)
        
        end_log = {
            "event": "function_end",
            "module": module,
            "function": function,
            "timestamp": end_time.isoformat(),
            "execution_time_ms": round(execution_time, 2),
            "result": f"Success: processed {random.randint(1, 10)} items"
        }
        logs.append(end_log)
        
        # Иногда добавляем ошибку (10% случаев)
        if random.random() < 0.1:
            error_time = end_time + datetime.timedelta(milliseconds=random.uniform(1, 50))
            error_log = {
                "event": "function_error",
                "module": module,
                "function": function,
                "timestamp": error_time.isoformat(),
                "error_type": "ValidationError",
                "error_message": f"Invalid data for user {random.randint(1000, 9999)}"
            }
            logs.append(error_log)
    
    # Сортируем по времени
    logs.sort(key=lambda x: x["timestamp"])
    
    return logs

if __name__ == "__main__":
    print("📝 Создаем тестовые логи...")
    
    logs = create_test_logs()
    
    # Сохраняем в файл
    log_file = "logs/app.json"
    with open(log_file, "w", encoding="utf-8") as f:
        for log in logs:
            f.write(json.dumps(log, ensure_ascii=False) + "\n")
    
    print(f"✅ Создано {len(logs)} записей логов")
    print(f"📄 Файл сохранен: {log_file}")
    
    # Показываем временной диапазон
    if logs:
        first_time = datetime.datetime.fromisoformat(logs[0]["timestamp"])
        last_time = datetime.datetime.fromisoformat(logs[-1]["timestamp"])
        print(f"⏰ Временной диапазон: {first_time.strftime('%Y-%m-%d %H:%M:%S')} - {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Статистика по событиям
    events = {}
    for log in logs:
        event = log["event"]
        events[event] = events.get(event, 0) + 1
    
    print("📊 Статистика по событиям:")
    for event, count in events.items():
        print(f"   {event}: {count}") 
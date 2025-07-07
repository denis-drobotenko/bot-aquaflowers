import subprocess
import json
import os
import glob
from datetime import datetime, timedelta
import time
import re

def cleanup_old_log_files():
    """Удаляет все старые файлы логов кроме logs.log"""
    patterns = [
        "logs_*.log",
        "quick_logs.json",
        "gcloud_logs.json",
        "fresh_logs.json"
    ]
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                os.remove(file_path)
                print(f"Удален файл: {file_path}")
            except Exception as e:
                print(f"Не удалось удалить {file_path}: {e}")

def get_logs_from_gcloud():
    print("Собираю логи...")
    print("Время: последние 30 минут")
    
    # Удаляем старые файлы логов
    cleanup_old_log_files()
    
    # Команда для получения логов
    filter_query = 'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot"'
    cmd = [
        "gcloud", "logging", "read", filter_query,
        "--limit=2000",
        "--format=json"
    ]
    
    print(f"Фильтр: {filter_query}")
    print("Выполняю команду gcloud...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs_data = json.loads(result.stdout)
        
        print(f"\nКоманда выполнена за {result.returncode} секунд")
        print(f"Найдено {len(logs_data)} записей логов")
        
        # Сохраняем только в logs.log
        with open('logs.log', 'w', encoding='utf-8') as f:
            for i, log_entry in enumerate(logs_data):
                if i % 50 == 0 and i > 0:
                    print(f"Обработано записей: {i}")
                
                # Извлекаем текст лога
                if 'textPayload' in log_entry:
                    log_text = log_entry['textPayload']
                elif 'jsonPayload' in log_entry:
                    log_text = json.dumps(log_entry['jsonPayload'], ensure_ascii=False, indent=2)
                else:
                    log_text = str(log_entry)
                
                # Добавляем временную метку
                timestamp = log_entry.get('timestamp', '')
                f.write(f"[{timestamp}] {log_text}\n")
        
        print(f"Готово! Сохранено {len(logs_data)} записей в logs.log")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

def quick_logs():
    print("Быстрый сбор логов...")
    
    # Удаляем старые файлы логов
    cleanup_old_log_files()
    
    filter_query = 'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot"'
    cmd = [
        "gcloud", "logging", "read", filter_query,
        "--limit=100",
        "--format=json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs_data = json.loads(result.stdout)
        
        # Сохраняем только в logs.log
        with open('logs.log', 'w', encoding='utf-8') as f:
            for log_entry in logs_data:
                if 'textPayload' in log_entry:
                    log_text = log_entry['textPayload']
                elif 'jsonPayload' in log_entry:
                    log_text = json.dumps(log_entry['jsonPayload'], ensure_ascii=False, indent=2)
                else:
                    log_text = str(log_entry)
                
                timestamp = log_entry.get('timestamp', '')
                f.write(f"[{timestamp}] {log_text}\n")
        
        print(f"Сохранено {len(logs_data)} записей в logs.log")
        
    except Exception as e:
        print(f"Ошибка: {e}")

def save_logs_from_gcloud():
    print("Собираю логи...")
    print("Время: последние 15 минут")
    
    # Удаляем старые файлы логов
    cleanup_old_log_files()
    
    # Формируем команду для получения логов за последние 15 минут
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=15)
    
    # Форматируем время для gcloud
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Команда для получения логов
    filter_query = f'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot" timestamp>="{start_str}" timestamp<="{end_str}"'
    cmd = [
        "gcloud", "logging", "read", filter_query,
        "--limit=2000",
        "--format=json"
    ]
    
    print(f"Фильтр: {filter_query}")
    print(f"Время: {start_str} - {end_str}")
    print("Выполняю команду gcloud...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs_data = json.loads(result.stdout)
        
        print(f"\nКоманда выполнена за {result.returncode} секунд")
        print(f"Найдено {len(logs_data)} записей логов")
        
        # Сохраняем только в logs.log
        with open('logs.log', 'w', encoding='utf-8') as f:
            for i, log_entry in enumerate(logs_data):
                if i % 50 == 0 and i > 0:
                    print(f"Обработано записей: {i}")
                
                # Извлекаем текст лога
                if 'textPayload' in log_entry:
                    log_text = log_entry['textPayload']
                elif 'jsonPayload' in log_entry:
                    log_text = json.dumps(log_entry['jsonPayload'], ensure_ascii=False, indent=2)
                else:
                    log_text = str(log_entry)
                
                # Добавляем временную метку
                timestamp = log_entry.get('timestamp', '')
                f.write(f"[{timestamp}] {log_text}\n")
        
        print(f"Готово! Сохранено {len(logs_data)} записей в logs.log")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

def filter_useful_logs(logs_data):
    """Фильтрует только полезные логи для отладки диалогов"""
    useful_logs = []
    
    # Ключевые слова для полезных логов
    useful_keywords = [
        'webhook', 'message', 'ai', 'session', 'user', 'bot', 'response',
        'dialog', 'conversation', 'whatsapp', 'send', 'receive',
        'catalog', 'order', 'product', 'flower', 'bouquet',
        'error', 'exception', 'warning'
    ]
    
    # Исключаем технические логи
    exclude_keywords = [
        'shutting down', 'startup', 'application startup',
        'uvicorn', 'fastapi', 'middleware', 'cors',
        'health check', 'root endpoint', 'static files'
    ]
    
    for log in logs_data:
        text = log.get('textPayload', '').lower()
        
        # Пропускаем технические логи
        if any(exclude in text for exclude in exclude_keywords):
            continue
            
        # Включаем только полезные логи
        if any(keyword in text for keyword in useful_keywords):
            useful_logs.append(log)
    
    return useful_logs

def get_logs_via_api(period_min=20):
    """Получает логи за указанный период через Google Cloud Logging API"""
    try:
        from google.cloud import logging
        print("Подключаюсь к Google Cloud Logging API...")
        client = logging.Client()
        
        # Вычисляем временной диапазон
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=period_min)
        
        # Формируем фильтр
        filter_str = f'''
        resource.type="cloud_run_revision"
        resource.labels.service_name="auraflora-bot"
        timestamp >= "{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        timestamp < "{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        '''
        print(f"Получаю логи с {start_time} по {end_time}...")
        entries = client.list_entries(
            filter_=filter_str,
            page_size=5000,
            max_results=5000
        )
        logs_data = []
        for entry in entries:
            log_entry = {
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else '',
                'textPayload': str(entry.payload) if entry.payload else '',
            }
            logs_data.append(log_entry)
        
        print(f"✅ Получено {len(logs_data)} сырых логов")
        
        # Фильтруем только полезные логи
        useful_logs = filter_useful_logs(logs_data)
        print(f"✅ Отфильтровано {len(useful_logs)} полезных логов")
        
        return True, useful_logs
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return False, None

def get_logs_last_5_minutes():
    """Получает логи за последние 5 минут"""
    print("Собираю логи за последние 5 минут...")
    
    # Удаляем старые файлы логов
    cleanup_old_log_files()
    
    # Формируем команду для получения логов за последние 5 минут
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=5)
    
    # Форматируем время для gcloud
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Команда для получения логов
    filter_query = f'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot" timestamp>="{start_str}" timestamp<="{end_str}"'
    cmd = [
        "gcloud", "logging", "read", filter_query,
        "--limit=2000",
        "--format=json"
    ]
    
    print(f"Фильтр: {filter_query}")
    print(f"Время: {start_str} - {end_str}")
    print("Выполняю команду gcloud...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs_data = json.loads(result.stdout)
        
        print(f"\nКоманда выполнена успешно")
        print(f"Найдено {len(logs_data)} записей логов")
        
        # Сохраняем только в logs.log
        with open('logs.log', 'w', encoding='utf-8') as f:
            for i, log_entry in enumerate(logs_data):
                if i % 50 == 0 and i > 0:
                    print(f"Обработано записей: {i}")
                
                # Извлекаем текст лога
                if 'textPayload' in log_entry:
                    log_text = log_entry['textPayload']
                elif 'jsonPayload' in log_entry:
                    log_text = json.dumps(log_entry['jsonPayload'], ensure_ascii=False, indent=2)
                else:
                    log_text = str(log_entry)
                
                # Добавляем временную метку
                timestamp = log_entry.get('timestamp', '')
                f.write(f"[{timestamp}] {log_text}\n")
        
        print(f"Готово! Сохранено {len(logs_data)} записей в logs.log")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_logs()
        elif sys.argv[1] == "--minutes" and len(sys.argv) > 2:
            minutes = int(sys.argv[2])
            if minutes == 5:
                get_logs_last_5_minutes()
            else:
                print(f"Поддерживается только 5 минут. Используйте: python3 {sys.argv[0]} --minutes 5")
        else:
            print(f"Использование: python3 {sys.argv[0]} [quick|--minutes 5]")
    else:
        get_logs_from_gcloud() 
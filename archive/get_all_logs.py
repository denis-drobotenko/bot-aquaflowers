import subprocess
import json
import os
import glob
from datetime import datetime, timedelta
import time

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

def get_all_logs():
    print("Собираю все доступные логи...")
    
    # Удаляем старые файлы логов
    cleanup_old_log_files()
    
    # Команда для получения всех логов
    cmd = [
        "gcloud", "logging", "read",
        "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"",
        "--limit=1000",
        "--format=json"
    ]
    
    print(f"Фильтр: resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"")
    print("Выполняю команду gcloud...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logs_data = json.loads(result.stdout)
        
        print(f"\nКоманда выполнена успешно")
        print(f"Найдено {len(logs_data)} записей логов")
        
        if len(logs_data) == 0:
            print("Логи не найдены. Попробуем другой фильтр...")
            
            # Попробуем более широкий фильтр
            cmd2 = [
                "gcloud", "logging", "read",
                "resource.type=\"cloud_run_revision\"",
                "--limit=100",
                "--format=json"
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, check=True, shell=True)
            logs_data2 = json.loads(result2.stdout)
            
            print(f"Найдено {len(logs_data2)} записей с широким фильтром")
            
            if len(logs_data2) > 0:
                print("Первые записи:")
                for i, log in enumerate(logs_data2[:3]):
                    print(f"  {i+1}. {log}")
        
        # Сохраняем логи
        with open('logs.log', 'w', encoding='utf-8') as f:
            for i, log_entry in enumerate(logs_data):
                if i % 100 == 0 and i > 0:
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
    get_all_logs() 
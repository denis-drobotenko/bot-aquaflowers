import subprocess
import json
import os
import glob
import re
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

def remove_emojis(text):
    # Удаляем эмодзи и другие проблемные Unicode символы
    emoji_pattern = re.compile("["
                               "\U0001F600-\U0001F64F"  # emoticons
                               "\U0001F300-\U0001F5FF"  # symbols & pictographs
                               "\U0001F680-\U0001F6FF"  # transport & map symbols
                               "\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "\U00002500-\U00002BEF"  # chinese char
                               "\U00002702-\U000027B0"
                               "\U00002702-\U000027B0"
                               "\U000024C2-\U0001F251"
                               "\U0001f926-\U0001f937"
                               "\U00010000-\U0010ffff"
                               "\u2640-\u2642" 
                               "\u2600-\u2B55"
                               "\u200d"
                               "\u23cf"
                               "\u23e9"
                               "\u231a"
                               "\ufe0f"  # dingbats
                               "\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def clean_text(text):
    try:
        # Удаляем эмодзи
        cleaned = remove_emojis(text)
        # Убираем лишние escape символы
        cleaned = cleaned.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
        return cleaned
    except Exception:
        return text

def get_json_logs_5000():
    print("Скачиваю 5000 логов с сервера и ищу JSON-ответы AI...")
    cleanup_old_log_files()
    
    cmd = [
        "gcloud", "logging", "read",
        "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"",
        "--limit=5000",
        "--format=json"
    ]
    
    print("Выполняю команду gcloud для скачивания 5000 логов...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logs_data = json.loads(result.stdout)
        
        print(f"\nСкачано {len(logs_data)} записей логов с сервера")
        
        json_responses = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            # Ищем в textPayload
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                # Ищем строки с JSON, русским текстом или ключевыми словами
                if any(keyword in text for keyword in ['json', 'JSON', 'Добрый', 'Отлично', 'confirm_order', 'send_catalog', 'text":', 'command":']):
                    # Убираем только пустые строки или строки из одних знаков вопроса
                    if text.strip() and not re.match(r'^[?\s]*$', text):
                        json_responses.append(f"[{timestamp}] {text}\n")
            
            # Ищем в jsonPayload
            elif 'jsonPayload' in log_entry:
                payload = log_entry['jsonPayload']
                payload_str = str(payload)
                # Ищем полезные данные в jsonPayload
                if any(keyword in payload_str for keyword in ['text', 'message', 'json', 'command']):
                    if payload_str.strip() and not re.match(r'^[?\s]*$', payload_str):
                        json_responses.append(f"[{timestamp}] {payload_str}\n")
        
        print(f"Найдено {len(json_responses)} потенциальных JSON-ответов")
        
        # Берем последние 100
        last_100 = json_responses[-100:] if len(json_responses) >= 100 else json_responses
        
        # Записываем с обработкой ошибок кодировки
        with open('last_100_json.log', 'w', encoding='utf-8', errors='replace') as f:
            f.writelines(last_100)
        
        print(f"Готово! Сохранено {len(last_100)} записей в last_100_json.log")
        
        if last_100:
            print("\nПервые 3 записи:")
            for i, line in enumerate(last_100[:3]):
                print(f"{i+1}. {line.strip()[:150]}...")
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")
        print(f"stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")

if __name__ == "__main__":
    get_json_logs_5000() 
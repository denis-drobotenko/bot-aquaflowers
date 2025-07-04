import os
from google.cloud import logging
import ftfy
from unidecode import unidecode
import re
from datetime import datetime, timedelta

def fix_encoding(text):
    """Исправляем проблемы с кодировкой разными способами"""
    try:
        # 1. Используем ftfy для исправления mojibake
        fixed = ftfy.fix_text(text)
        if fixed != text and any(ord(c) > 127 for c in fixed):
            return fixed
        
        # 2. Если ftfy не помог, пробуем другие методы
        if '?' in text or any(ord(c) == 65533 for c in text):  # replacement character
            # Пробуем декодировать как cp1251
            try:
                bytes_text = text.encode('latin-1')
                decoded = bytes_text.decode('cp1251')
                return decoded
            except:
                pass
        
        return text
    except Exception:
        return text

def extract_ai_logs_via_api():
    """Извлекаем логи через Google Cloud API с правильной обработкой кодировки"""
    print("Подключаюсь к Google Cloud Logging API...")
    
    try:
        # Инициализируем клиент
        client = logging.Client()
        
        # Фильтр для наших логов
        filter_str = '''
        resource.type="cloud_run_revision"
        resource.labels.service_name="auraflora-bot"
        (textPayload:"AI response" OR textPayload:"[AI_DEBUG]" OR textPayload:"PARSE_RESPONSE")
        '''
        
        print("Получаю последние 1000 записей с AI ответами...")
        
        # Получаем логи за последние 24 часа
        from datetime import datetime, timezone, timedelta
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        
        entries = client.list_entries(
            filter_=filter_str,
            page_size=1000,
            max_results=1000
        )
        
        ai_responses = []
        
        print("Обрабатываю записи...")
        for entry in entries:
            timestamp = entry.timestamp.isoformat() if entry.timestamp else 'Unknown'
            
            if hasattr(entry, 'payload') and entry.payload:
                text = str(entry.payload)
                
                # Исправляем кодировку
                fixed_text = fix_encoding(text)
                
                # Ищем AI ответы
                if 'AI response:' in fixed_text:
                    response_match = re.search(r'AI response:\s*(.+)', fixed_text)
                    if response_match:
                        response_text = response_match.group(1).strip()
                        ai_responses.append(f"[{timestamp}]\nAI: {response_text}\n---\n")
                
                elif '"text":' in fixed_text and any(c.isalpha() for c in fixed_text):
                    # Извлекаем JSON текст
                    json_match = re.search(r'"text":\s*"([^"]*)"', fixed_text)
                    if json_match:
                        text_content = json_match.group(1)
                        decoded_content = fix_encoding(text_content)
                        ai_responses.append(f"[{timestamp}]\nAI JSON: {decoded_content}\n---\n")
        
        print(f"Найдено {len(ai_responses)} AI ответов")
        
        if ai_responses:
            # Сохраняем
            with open('ai_logs_api_fixed.log', 'w', encoding='utf-8') as f:
                f.writelines(ai_responses)
            
            print("Сохранено в ai_logs_api_fixed.log")
            
            # Показываем примеры
            print("\nПоследние 5 AI ответов:")
            for i, response in enumerate(ai_responses[-5:]):
                lines = response.split('\n')
                if len(lines) >= 2 and lines[1].strip():
                    ai_text = lines[1]
                    # Показываем только если получился нормальный текст
                    if not '?????' in ai_text and any(c.isalpha() for c in ai_text):
                        print(f"{i+1}. {ai_text}")
        else:
            print("AI ответы не найдены")
            
    except Exception as e:
        print(f"Ошибка API: {e}")
        print("Попробуем альтернативный метод...")
        
        # Fallback на gcloud CLI с улучшенной обработкой
        fallback_extract()

def fallback_extract():
    """Альтернативный метод через gcloud CLI с ftfy"""
    import subprocess
    import json
    
    print("Используем gcloud CLI с ftfy...")
    
    cmd = [
        "gcloud", "logging", "read",
        'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot"',
        "--limit=1000",
        "--format=json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logs_data = json.loads(result.stdout)
        
        print(f"Получено {len(logs_data)} записей")
        
        ai_responses = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                
                if any(keyword in text for keyword in ['AI response:', '[AI_DEBUG]', 'PARSE_RESPONSE']):
                    # Применяем ftfy для исправления кодировки
                    fixed_text = ftfy.fix_text(text)
                    
                    # Если ftfy не помог, пробуем другие методы
                    if fixed_text == text and '????' in text:
                        try:
                            # Пробуем через разные кодировки
                            for encoding in ['cp1251', 'cp866', 'koi8-r']:
                                try:
                                    temp_bytes = text.encode('latin-1')
                                    decoded = temp_bytes.decode(encoding)
                                    if any(ord(c) > 127 and c != '?' for c in decoded):
                                        fixed_text = decoded
                                        break
                                except:
                                    continue
                        except:
                            pass
                    
                    if 'AI response:' in fixed_text:
                        response_match = re.search(r'AI response:\s*(.+)', fixed_text)
                        if response_match:
                            response_text = response_match.group(1).strip()
                            ai_responses.append(f"[{timestamp}]\nAI: {response_text}\n---\n")
        
        print(f"Найдено {len(ai_responses)} AI ответов")
        
        if ai_responses:
            with open('ai_logs_fallback_fixed.log', 'w', encoding='utf-8') as f:
                f.writelines(ai_responses)
            
            print("Сохранено в ai_logs_fallback_fixed.log")
            
            print("\nПоследние 3 AI ответа:")
            for i, response in enumerate(ai_responses[-3:]):
                lines = response.split('\n')
                if len(lines) >= 2:
                    print(f"{i+1}. {lines[1]}")
        
    except Exception as e:
        print(f"Ошибка fallback: {e}")

if __name__ == "__main__":
    extract_ai_logs_via_api() 
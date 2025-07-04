import subprocess
import json
import re
import codecs

def decode_unicode_string(s):
    """Декодируем Unicode escape последовательности"""
    try:
        # Декодируем Unicode escape последовательности
        decoded = codecs.decode(s, 'unicode_escape')
        return decoded
    except Exception:
        return s

def extract_ai_responses():
    print("Скачиваю 5000 логов и ищу ответы AI...")
    
    cmd = [
        "gcloud", "logging", "read",
        "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"",
        "--limit=5000",
        "--format=json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logs_data = json.loads(result.stdout)
        
        print(f"Скачано {len(logs_data)} записей с сервера")
        
        ai_responses = []
        all_ai_lines = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                
                # Расширенный поиск AI-связанных строк
                if any(keyword in text.lower() for keyword in ['ai response', 'parse_response', 'ai_manager', 'processing ai', 'json_processor']):
                    all_ai_lines.append(f"[{timestamp}] {text}")
                    
                    # Ищем конкретные JSON ответы
                    if '"text":' in text and ('"command":' in text or 'Processing' in text):
                        # Попробуем извлечь и декодировать JSON
                        json_matches = re.findall(r'\{[^}]*"text"[^}]*\}', text)
                        for json_str in json_matches:
                            decoded_json = decode_unicode_string(json_str)
                            try:
                                json_obj = json.loads(decoded_json)
                                if 'text' in json_obj:
                                    ai_text = json_obj['text']
                                    command = json_obj.get('command', 'нет команды')
                                    
                                    ai_responses.append(f"[{timestamp}]\n")
                                    ai_responses.append(f"Текст AI: {ai_text}\n")
                                    ai_responses.append(f"Команда: {command}\n")
                                    ai_responses.append(f"---\n\n")
                            except:
                                ai_responses.append(f"[{timestamp}] {decoded_json}\n\n")
        
        print(f"Найдено {len(all_ai_lines)} AI-связанных строк")
        print(f"Найдено {len(ai_responses)//4} декодированных ответов AI")
        
        # Показываем примеры найденных AI строк
        if all_ai_lines:
            print("\nПримеры найденных AI строк:")
            for i, line in enumerate(all_ai_lines[:5]):
                print(f"{i+1}. {line[:150]}...")
        
        # Сохраняем декодированные ответы
        if ai_responses:
            with open('ai_responses.log', 'w', encoding='utf-8') as f:
                f.writelines(ai_responses)
            print(f"\nДекодированные ответы сохранены в ai_responses.log")
        
        # Сохраняем все AI строки для анализа
        with open('all_ai_lines.log', 'w', encoding='utf-8') as f:
            for line in all_ai_lines:
                f.write(line + '\n')
        print(f"Все AI строки сохранены в all_ai_lines.log")
        
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    extract_ai_responses() 
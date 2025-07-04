import subprocess
import json
import re
import codecs
import unicodedata

def decode_unicode_escapes(text):
    """Декодируем Unicode escape последовательности типа \\u0410"""
    try:
        # Заменяем \\u на \u для правильного декодирования
        text = text.replace('\\\\u', '\\u')
        # Декодируем Unicode escape последовательности
        decoded = codecs.decode(text, 'unicode_escape')
        return decoded
    except Exception:
        return text

def fix_encoding(text):
    """Исправляем проблемы с кодировкой"""
    try:
        # Попробуем разные варианты декодирования
        if '??????' in text or '???' in text:
            # Возможно, это UTF-8 интерпретируется как cp1251
            try:
                # Кодируем как latin-1, затем декодируем как utf-8
                fixed = text.encode('latin-1').decode('utf-8')
                return fixed
            except:
                pass
        
        return text
    except Exception:
        return text

def extract_ai_responses():
    print("Скачиваю 5000 логов с сервера...")
    
    # Используем PowerShell команду напрямую
    cmd = "gcloud logging read \"resource.type=\\\"cloud_run_revision\\\" resource.labels.service_name=\\\"auraflora-bot\\\"\" --limit=5000 --format=json"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logs_data = json.loads(result.stdout)
        
        print(f"Скачано {len(logs_data)} записей с сервера")
        
        ai_responses = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                
                # Ищем строки с AI ответами
                if any(keyword in text for keyword in ['AI response:', '[AI_DEBUG]', 'PARSE_RESPONSE']):
                    
                    # Попробуем извлечь JSON или обычный текст ответа
                    if 'AI response:' in text:
                        # Извлекаем текст после "AI response:"
                        response_match = re.search(r'AI response:\s*(.+)', text)
                        if response_match:
                            response_text = response_match.group(1)
                            
                            # Декодируем Unicode и исправляем кодировку
                            decoded_text = decode_unicode_escapes(response_text)
                            fixed_text = fix_encoding(decoded_text)
                            
                            ai_responses.append(f"[{timestamp}]\n")
                            ai_responses.append(f"AI Ответ: {fixed_text}\n")
                            ai_responses.append(f"---\n\n")
                    
                    # Также ищем JSON в PARSE_RESPONSE
                    elif 'PARSE_RESPONSE' in text and '"text":' in text:
                        json_match = re.search(r'\{"text"[^}]*\}', text)
                        if json_match:
                            json_str = json_match.group(0)
                            try:
                                # Декодируем JSON
                                decoded_json = decode_unicode_escapes(json_str)
                                json_obj = json.loads(decoded_json)
                                
                                if 'text' in json_obj:
                                    ai_text = json_obj['text']
                                    fixed_text = fix_encoding(ai_text)
                                    command = json_obj.get('command', 'нет команды')
                                    
                                    ai_responses.append(f"[{timestamp}]\n")
                                    ai_responses.append(f"AI Текст: {fixed_text}\n")
                                    ai_responses.append(f"Команда: {command}\n")
                                    ai_responses.append(f"---\n\n")
                            except Exception as e:
                                pass
        
        print(f"Найдено {len(ai_responses)//4} ответов AI")
        
        # Берем последние 100 ответов
        last_responses = ai_responses[-400:] if len(ai_responses) >= 400 else ai_responses
        
        # Сохраняем в файл с правильной кодировкой
        with open('ai_responses_fixed.log', 'w', encoding='utf-8', errors='ignore') as f:
            f.writelines(last_responses)
        
        print(f"Сохранено в ai_responses_fixed.log")
        
        # Показываем последние несколько ответов
        if last_responses:
            print("\nПоследние 3 ответа AI:")
            lines = ''.join(last_responses).split('---\n\n')
            for i, response in enumerate(lines[-4:-1]):
                if response.strip():
                    print(f"\n{i+1}. {response.strip()}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_ai_responses() 
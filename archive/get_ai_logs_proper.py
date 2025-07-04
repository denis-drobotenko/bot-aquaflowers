import subprocess
import json
import codecs
import re
import chardet

def detect_and_decode(text):
    """Определяем кодировку и декодируем текст"""
    try:
        # Если есть Unicode escape последовательности
        if '\\u0' in text:
            # Исправляем двойное экранирование
            fixed = text.replace('\\\\u', '\\u')
            try:
                decoded = codecs.decode(fixed, 'unicode_escape')
                return decoded
            except:
                pass
        
        # Если есть знаки вопроса, пробуем разные кодировки
        if '?' in text and any(ord(c) > 127 for c in text):
            try:
                # Пробуем через bytes
                text_bytes = text.encode('latin-1')
                detected = chardet.detect(text_bytes)
                if detected['encoding']:
                    return text_bytes.decode(detected['encoding'])
            except:
                pass
        
        return text
    except:
        return text

def extract_ai_logs():
    print("Извлекаю ответы AI с сервера...")
    
    # Сначала сохраняем raw данные в JSON файл
    cmd = [
        "gcloud", "logging", "read",
        "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"",
        "--limit=2000",
        "--format=json"
    ]
    
    print("Скачиваю логи...")
    try:
        # Сохраняем в файл с binary режимом
        with open('temp_logs.json', 'wb') as f:
            result = subprocess.run(cmd, stdout=f, shell=True, check=True)
        
        # Читаем файл с автоопределением кодировки
        with open('temp_logs.json', 'rb') as f:
            raw_data = f.read()
            
        # Определяем кодировку
        detected = chardet.detect(raw_data)
        encoding = detected['encoding'] if detected['encoding'] else 'utf-8'
        print(f"Определена кодировка: {encoding}")
        
        # Декодируем с найденной кодировкой
        text_data = raw_data.decode(encoding, errors='replace')
        logs_data = json.loads(text_data)
        
        print(f"Загружено {len(logs_data)} записей")
        
        ai_logs = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                
                # Ищем AI ответы
                if any(keyword in text for keyword in ['AI response:', '[AI_DEBUG]', 'PARSE_RESPONSE']):
                    
                    # Декодируем текст
                    decoded_text = detect_and_decode(text)
                    
                    # Извлекаем только ответ
                    if 'AI response:' in decoded_text:
                        response_match = re.search(r'AI response:\s*(.+)', decoded_text)
                        if response_match:
                            response_text = response_match.group(1).strip()
                            ai_logs.append(f"[{timestamp}]\nAI: {response_text}\n---\n")
                    
                    elif '"text":' in decoded_text:
                        # Извлекаем JSON с текстом
                        json_match = re.search(r'\{"text":\s*"([^"]+)"', decoded_text)
                        if json_match:
                            text_content = json_match.group(1)
                            decoded_content = detect_and_decode(text_content)
                            ai_logs.append(f"[{timestamp}]\nAI: {decoded_content}\n---\n")
        
        print(f"Найдено {len(ai_logs)} AI ответов")
        
        # Берем последние 100
        recent_logs = ai_logs[-100:] if len(ai_logs) >= 100 else ai_logs
        
        # Сохраняем с UTF-8 BOM
        with open('ai_logs_decoded.log', 'w', encoding='utf-8-sig') as f:
            f.writelines(recent_logs)
        
        print("Сохранено в ai_logs_decoded.log")
        
        # Показываем несколько примеров
        if recent_logs:
            print("\nПоследние 3 AI ответа:")
            for i, log in enumerate(recent_logs[-3:]):
                lines = log.split('\n')
                if len(lines) >= 2:
                    print(f"{i+1}. {lines[1][:150]}...")
        
        # Удаляем временный файл
        import os
        try:
            os.remove('temp_logs.json')
        except:
            pass
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_ai_logs() 
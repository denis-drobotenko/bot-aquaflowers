import subprocess
import json
import codecs
import sys
import os

def extract_ai_responses():
    print("Скачиваю логи с правильной кодировкой...")
    
    # Устанавливаем UTF-8 для Python
    if sys.platform == "win32":
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    cmd = [
        "gcloud", "logging", "read",
        "resource.type=\"cloud_run_revision\" resource.labels.service_name=\"auraflora-bot\"",
        "--limit=1000",
        "--format=json"
    ]
    
    try:
        # Запускаем с указанием кодировки
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            errors='replace',
            shell=True
        )
        
        if result.returncode != 0:
            print(f"Ошибка команды: {result.stderr}")
            return
            
        logs_data = json.loads(result.stdout)
        print(f"Скачано {len(logs_data)} записей")
        
        ai_responses = []
        
        for log_entry in logs_data:
            timestamp = log_entry.get('timestamp', '')
            
            if 'textPayload' in log_entry:
                text = log_entry['textPayload']
                
                # Ищем AI ответы
                if 'AI response:' in text or '[AI_DEBUG]' in text:
                    
                    # Попробуем разные способы декодирования
                    decoded_text = text
                    
                    # 1. Если есть Unicode escape последовательности
                    if '\\u' in text:
                        try:
                            # Заменяем двойные слеши на одинарные для правильного декодирования
                            fixed_text = text.replace('\\\\u', '\\u')
                            decoded_text = codecs.decode(fixed_text, 'unicode_escape')
                        except:
                            pass
                    
                    # 2. Пробуем разные кодировки если есть знаки вопроса
                    if '???' in decoded_text or '??????' in decoded_text:
                        try:
                            # Пробуем cp1251 -> utf-8
                            decoded_text = text.encode('cp1251').decode('utf-8')
                        except:
                            try:
                                # Пробуем latin-1 -> utf-8  
                                decoded_text = text.encode('latin-1').decode('utf-8')
                            except:
                                pass
                    
                    ai_responses.append(f"[{timestamp}]\n{decoded_text}\n---\n\n")
        
        print(f"Найдено {len(ai_responses)} AI ответов")
        
        # Берем последние 50
        recent_responses = ai_responses[-50:] if len(ai_responses) >= 50 else ai_responses
        
        # Сохраняем с BOM для правильного отображения в Windows
        with open('ai_responses_utf8.log', 'w', encoding='utf-8-sig') as f:
            f.writelines(recent_responses)
        
        print("Сохранено в ai_responses_utf8.log")
        
        # Показываем последние 2 ответа
        if recent_responses:
            print("\nПоследние 2 AI ответа:")
            responses_text = ''.join(recent_responses)
            parts = responses_text.split('---\n\n')
            for i, part in enumerate(parts[-3:-1]):
                if part.strip():
                    print(f"\n{i+1}. {part.strip()[:200]}...")
                    
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_ai_responses() 
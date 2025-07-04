import re
import codecs
import json

def decode_unicode_sequences(text):
    """Декодируем Unicode escape последовательности"""
    try:
        # Находим все Unicode escape последовательности
        unicode_pattern = r'\\u[0-9a-fA-F]{4}'
        
        def replace_unicode(match):
            unicode_str = match.group(0)
            try:
                # Декодируем Unicode
                char = codecs.decode(unicode_str, 'unicode_escape')
                return char
            except:
                return unicode_str
        
        # Заменяем все найденные последовательности
        decoded = re.sub(unicode_pattern, replace_unicode, text)
        return decoded
    except:
        return text

def process_existing_logs():
    print("Обрабатываю существующие логи...")
    
    try:
        with open('last_100_json.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"Читаю {len(lines)} строк из last_100_json.log")
        
        ai_responses = []
        
        for line in lines:
            # Ищем строки с Unicode escape последовательностями
            if '\\u0' in line:
                decoded_line = decode_unicode_sequences(line)
                
                # Ищем текстовые ответы AI
                if '"text":' in decoded_line:
                    # Извлекаем JSON
                    json_match = re.search(r'"text":\s*"([^"]*)"', decoded_line)
                    if json_match:
                        text_content = json_match.group(1)
                        # Декодируем и текст внутри JSON
                        final_text = decode_unicode_sequences(text_content)
                        
                        # Извлекаем timestamp если есть
                        timestamp_match = re.search(r'\[([\d\-T:.Z]+)\]', line)
                        timestamp = timestamp_match.group(1) if timestamp_match else 'Unknown time'
                        
                        ai_responses.append(f"[{timestamp}]\nAI: {final_text}\n---\n")
        
        print(f"Найдено {len(ai_responses)} декодированных ответов AI")
        
        # Сохраняем декодированные ответы
        with open('ai_responses_decoded.log', 'w', encoding='utf-8') as f:
            f.writelines(ai_responses)
        
        print("Сохранено в ai_responses_decoded.log")
        
        # Показываем первые несколько
        if ai_responses:
            print("\nПервые 5 декодированных ответов:")
            for i, response in enumerate(ai_responses[:5]):
                lines = response.split('\n')
                if len(lines) >= 2:
                    print(f"{i+1}. {lines[1]}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_existing_logs() 
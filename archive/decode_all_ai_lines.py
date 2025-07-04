import re
import codecs

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

def fix_surrogates(text):
    """Исправляем проблемы с суррогатными парами"""
    try:
        # Кодируем с игнорированием суррогатов, затем декодируем
        return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    except:
        return text

def process_ai_lines():
    print("Декодирую файл all_ai_lines.log...")
    
    try:
        with open('all_ai_lines.log', 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        print(f"Читаю {len(lines)} строк из all_ai_lines.log")
        
        decoded_responses = []
        
        for line_num, line in enumerate(lines, 1):
            try:
                # Извлекаем timestamp
                timestamp_match = re.search(r'\[([\d\-T:.Z]+)\]', line)
                timestamp = timestamp_match.group(1) if timestamp_match else f'Line {line_num}'
                
                # Ищем AI response
                if 'AI response:' in line:
                    # Извлекаем текст после "AI response:"
                    response_match = re.search(r'AI response:\s*(.+)', line)
                    if response_match:
                        response_text = response_match.group(1).strip()
                        
                        # Декодируем Unicode escape последовательности
                        decoded_text = decode_unicode_sequences(response_text)
                        
                        # Исправляем суррогатные пары
                        fixed_text = fix_surrogates(decoded_text)
                        
                        # Убираем знаки вопроса, если получился нормальный текст
                        if any(ord(c) > 127 and c != '?' for c in fixed_text):
                            decoded_responses.append(f"[{timestamp}]\nAI: {fixed_text}\n---\n")
                        elif '????' not in response_text:  # Если изначально не было много вопросов
                            decoded_responses.append(f"[{timestamp}]\nAI: {response_text}\n---\n")
                
                # Также проверяем другие типы логов
                elif any(keyword in line for keyword in ['[AI_DEBUG]', 'PARSE_RESPONSE']):
                    # Декодируем всю строку
                    decoded_line = decode_unicode_sequences(line)
                    fixed_line = fix_surrogates(decoded_line)
                    
                    if any(ord(c) > 127 and c != '?' for c in fixed_line):
                        decoded_responses.append(f"[{timestamp}]\nДекодировано: {fixed_line.strip()}\n---\n")
                        
            except Exception as e:
                print(f"Ошибка в строке {line_num}: {e}")
                continue
        
        print(f"Найдено {len(decoded_responses)} декодированных записей")
        
        # Сохраняем с обработкой ошибок
        with open('all_ai_lines_decoded.log', 'w', encoding='utf-8', errors='replace') as f:
            for response in decoded_responses:
                try:
                    f.write(response)
                except UnicodeEncodeError:
                    # Если все еще проблемы, сохраняем с заменой проблемных символов
                    safe_response = response.encode('utf-8', errors='replace').decode('utf-8')
                    f.write(safe_response)
        
        print("Сохранено в all_ai_lines_decoded.log")
        
        # Показываем первые несколько успешно декодированных
        if decoded_responses:
            print("\nПервые 5 декодированных записей:")
            for i, response in enumerate(decoded_responses[:5]):
                lines = response.split('\n')
                if len(lines) >= 2:
                    ai_line = lines[1]
                    if 'AI:' in ai_line and not '??????' in ai_line:
                        print(f"{i+1}. {ai_line}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    process_ai_lines() 
import re
import codecs

def find_and_decode_unicode():
    print("Ищу Unicode последовательности в all_ai_lines.log...")
    
    with open('all_ai_lines.log', 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    print(f"Прочитано {len(lines)} строк")
    
    decoded_lines = []
    unicode_count = 0
    
    for i, line in enumerate(lines):
        # Ищем строки с Unicode escape последовательностями  
        if '\\u04' in line or '\\u05' in line:  # Кириллица
            unicode_count += 1
            print(f"\nСтрока {i+1} содержит Unicode:")
            print(f"Исходная: {line.strip()[:150]}...")
            
            try:
                # Декодируем
                decoded = codecs.decode(line, 'unicode_escape')
                print(f"Декодированная: {decoded.strip()[:150]}...")
                decoded_lines.append((i+1, decoded))
            except Exception as e:
                print(f"Ошибка декодирования: {e}")
    
    print(f"\nНайдено {unicode_count} строк с Unicode")
    
    if decoded_lines:
        print(f"\nУспешно декодировано {len(decoded_lines)} строк")
        
        # Сохраняем декодированные строки
        with open('unicode_decoded_results.txt', 'w', encoding='utf-8') as f:
            for line_num, decoded_line in decoded_lines:
                f.write(f"Строка {line_num}:\n{decoded_line}\n---\n")
        
        print("Результаты сохранены в unicode_decoded_results.txt")

if __name__ == "__main__":
    find_and_decode_unicode() 
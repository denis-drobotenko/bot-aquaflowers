#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для получения логов из Google Cloud через API с правильной обработкой кириллицы
"""

import os
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Устанавливаем UTF-8 как основную кодировку
os.environ['PYTHONIOENCODING'] = 'utf-8'

def fix_cyrillic_encoding(text):
    """Исправляет различные проблемы с кодировкой кириллицы"""
    if not text:
        return text
    
    try:
        import ftfy
        import codecs
        
        # Сначала пробуем ftfy - исправляет mojibake
        fixed_text = ftfy.fix_text(text)
        
        # Обрабатываем Unicode escape последовательности
        if '\\u04' in text or '\\u05' in text:  # Кириллица в Unicode
            try:
                fixed_text = codecs.decode(text, 'unicode_escape')
            except:
                # Пробуем по частям
                unicode_pattern = r'\\u[0-9a-fA-F]{4}'
                def replace_unicode(match):
                    try:
                        return codecs.decode(match.group(0), 'unicode_escape')
                    except:
                        return match.group(0)
                fixed_text = re.sub(unicode_pattern, replace_unicode, text)
        
        return fixed_text
        
    except Exception as e:
        print(f"Ошибка при исправлении кодировки: {e}")
        return text

def get_logs_via_api():
    """Получает логи за 2 июля 2025 через Google Cloud Logging API"""
    try:
        from google.cloud import logging
        print("Подключаюсь к Google Cloud Logging API...")
        
        client = logging.Client()
        
        # Фильтр для получения логов только за 2 июля 2025
        filter_str = '''
        resource.type="cloud_run_revision"
        resource.labels.service_name="auraflora-bot"
        timestamp >= "2025-07-02T00:00:00Z"
        timestamp < "2025-07-03T00:00:00Z"
        '''
        
        print("Получаю логи за 2 июля 2025...")
        
        entries = client.list_entries(
            filter_=filter_str,
            page_size=5000,
            max_results=5000
        )
        
        logs_data = []
        for entry in entries:
            log_entry = {
                'timestamp': entry.timestamp.isoformat() if entry.timestamp else '',
                'textPayload': str(entry.payload) if entry.payload else '',
            }
            logs_data.append(log_entry)
        
        print(f"✅ Получено {len(logs_data)} записей")
        return logs_data, True
        
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return None, False

def extract_ai_responses(logs_data):
    """Извлекает AI ответы как есть, без обработки кодировки"""
    ai_responses = []
    
    print("🔍 Извлекаю AI ответы...")
    
    for i, log_entry in enumerate(logs_data):
        if i % 500 == 0 and i > 0:
            print(f"  Обработано: {i} записей")
            
        text = log_entry.get('textPayload', '')
        if not text:
            continue
        
        # Ищем AI ответы (расширенный поиск)
        keywords = [
            'ai response:', 'parse_response', '"text":',
            '[ai_debug]', 'gemini response', 'ai_manager',
            'response:', 'ai:', 'ответ:'
        ]
        
        if any(keyword in text.lower() for keyword in keywords):
            # Извлекаем ответ КАК ЕСТЬ без обработки кодировки
            ai_text = None
            
            # Паттерны поиска
            patterns = [
                r'AI response:\s*(.+)',
                r'ai response:\s*(.+)',
                r'"text":\s*"([^"]*)"',
                r'"text":\s*`([^`]*)`',
                r'PARSE_RESPONSE[:\s]*(.+)',
                r'\[AI_DEBUG\]\s*(.+)',
                r'response:\s*(.+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    ai_text = match.group(1).strip()
                    # Ограничиваем длину
                    if len(ai_text) > 1000:
                        ai_text = ai_text[:1000] + "..."
                    break
            
            if ai_text and len(ai_text) > 2:
                ai_responses.append({
                    'timestamp': log_entry.get('timestamp', ''),
                    'response': ai_text,
                    'original_log': text[:200] + "..." if len(text) > 200 else text
                })
    
    return ai_responses

def save_results(ai_responses):
    """Сохраняет результаты за 2 июля"""
    logs_dir = Path("fixed_logs")
    logs_dir.mkdir(exist_ok=True)
    
    # JSON файл
    json_file = logs_dir / "ai_responses_july_02_raw.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(ai_responses, f, ensure_ascii=False, indent=2)
    
    # Читаемый файл
    txt_file = logs_dir / "ai_responses_july_02_raw.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("🤖 AI ОТВЕТЫ ЗА 2 ИЮЛЯ 2025 (КАК ЕСТЬ)\n")
        f.write("=" * 70 + "\n")
        f.write(f"Всего найдено: {len(ai_responses)} ответов\n")
        f.write(f"Дата извлечения: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")
        
        for i, ai_entry in enumerate(ai_responses, 1):
            # Форматируем время
            timestamp = ai_entry['timestamp']
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%d.%m.%Y %H:%M:%S')
                except:
                    time_str = timestamp
            else:
                time_str = 'Неизвестно'
            
            f.write(f"{i}. [{time_str}]\n")
            f.write(f"AI: {ai_entry['response']}\n")
            f.write("-" * 100 + "\n\n")
    
    print(f"📁 Сохранено:")
    print(f"  📄 JSON: {json_file}")
    print(f"  📖 Текст: {txt_file}")
    
    return txt_file

def main():
    """Основная функция"""
    print("🚀 ПОЛУЧЕНИЕ AI ОТВЕТОВ ЗА 2 ИЮЛЯ 2025")
    print("=" * 60)
    print("📅 Дата: 2 июля 2025")
    print("📋 Формат: как есть, без обработки кодировки")
    print()
    
    # Получаем логи за 2 июля
    logs_data, success = get_logs_via_api()
    
    if not success:
        print("❌ Не удалось получить логи!")
        return
    
    # Извлекаем AI ответы
    ai_responses = extract_ai_responses(logs_data)
    print(f"🤖 Найдено {len(ai_responses)} AI ответов за 2 июля")
    
    if not ai_responses:
        print("⚠️ AI ответы за 2 июля не найдены")
        return
    
    # Сохраняем
    result_file = save_results(ai_responses)
    
    # Показываем примеры
    print(f"\n📝 ПЕРВЫЕ 5 AI ОТВЕТОВ:")
    print("-" * 70)
    for i, ai_entry in enumerate(ai_responses[:5], 1):
        preview = ai_entry['response'][:120]
        if len(ai_entry['response']) > 120:
            preview += "..."
        
        # Время
        try:
            dt = datetime.fromisoformat(ai_entry['timestamp'].replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = 'N/A'
        
        print(f"{i}. [{time_str}] {preview}")
    
    print(f"\n🎉 Готово! Все AI ответы за 2 июля сохранены в: {result_file}")

if __name__ == "__main__":
    main() 
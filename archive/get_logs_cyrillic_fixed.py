#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для получения логов из Google Cloud с правильной обработкой кириллицы
"""

import os
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Устанавливаем UTF-8 как основную кодировку
os.environ['PYTHONIOENCODING'] = 'utf-8'

def install_required_packages():
    """Устанавливает необходимые пакеты если их нет"""
    try:
        import ftfy
        import unidecode
        import charset_normalizer
    except ImportError:
        print("Устанавливаю необходимые пакеты для работы с кириллицей...")
        subprocess.run([sys.executable, "-m", "pip", "install", "ftfy", "unidecode", "charset-normalizer"], check=True)
        print("Пакеты установлены!")

def fix_cyrillic_encoding(text):
    """
    Исправляет различные проблемы с кодировкой кириллицы
    """
    if not text:
        return text
    
    try:
        # Импортируем библиотеки
        import ftfy
        import charset_normalizer
        
        # Сначала пробуем ftfy - исправляет mojibake
        fixed_text = ftfy.fix_text(text)
        
        # Если ftfy не помог, пробуем другие методы
        if fixed_text == text and ('?' in text or '???' in text):
            # Пробуем определить реальную кодировку
            detected = charset_normalizer.detect(text.encode('utf-8', errors='ignore'))
            if detected and detected.get('confidence', 0) > 0.7:
                encoding = detected['encoding']
                try:
                    # Перекодируем
                    fixed_text = text.encode('latin-1').decode(encoding, errors='ignore')
                except:
                    pass
        
        # Дополнительная обработка Unicode escape последовательностей
        if '\\u04' in fixed_text or '\\u05' in fixed_text:  # Кириллица
            try:
                import codecs
                fixed_text = codecs.decode(fixed_text, 'unicode_escape')
            except:
                pass
        
        return fixed_text
        
    except Exception as e:
        print(f"Ошибка при исправлении кодировки: {e}")
        return text

def get_logs_via_gcloud():
    """
    Получает логи через gcloud CLI с правильной обработкой кодировки
    """
    print("Используем gcloud CLI...")
    
    # Формируем команду
    cmd = [
        "gcloud", "logging", "read",
        'resource.type="cloud_run_revision" resource.labels.service_name="auraflora-bot"',
        "--limit=2000",
        "--format=json"
    ]
    
    try:
        # Запускаем команду БЕЗ shell=True для избежания проблем с кодировкой
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        
        if result.returncode != 0:
            print(f"Ошибка gcloud: {result.stderr}")
            return None, False
        
        # Парсим JSON
        logs_data = json.loads(result.stdout)
        print(f"Получено {len(logs_data)} записей через gcloud CLI")
        return logs_data, True
        
    except subprocess.CalledProcessError as e:
        print(f"Ошибка команды gcloud: {e}")
        print(f"stderr: {e.stderr}")
        return None, False
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return None, False
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None, False

def extract_and_fix_logs(logs_data):
    """
    Извлекает и исправляет кодировку логов
    """
    fixed_logs = []
    ai_responses = []
    
    print("Обрабатываю логи и исправляю кодировку...")
    
    for i, log_entry in enumerate(logs_data):
        if i % 100 == 0 and i > 0:
            print(f"Обработано: {i} записей")
        
        timestamp = log_entry.get('timestamp', '')
        
        # Извлекаем текст лога
        log_text = ""
        if 'textPayload' in log_entry and log_entry['textPayload']:
            log_text = str(log_entry['textPayload'])
        elif 'jsonPayload' in log_entry and log_entry['jsonPayload']:
            log_text = json.dumps(log_entry['jsonPayload'], ensure_ascii=False, indent=2)
        
        if not log_text:
            continue
        
        # Исправляем кодировку
        fixed_text = fix_cyrillic_encoding(log_text)
        
        # Добавляем в общий список
        fixed_logs.append({
            'timestamp': timestamp,
            'text': fixed_text,
            'original': log_text
        })
        
        # Ищем AI ответы
        if any(keyword in fixed_text for keyword in ['AI response:', '[AI_DEBUG]', 'PARSE_RESPONSE', '"text":']):
            # Извлекаем AI ответ
            ai_text = extract_ai_response(fixed_text)
            if ai_text:
                ai_responses.append({
                    'timestamp': timestamp,
                    'response': ai_text,
                    'original': log_text
                })
    
    return fixed_logs, ai_responses

def extract_ai_response(text):
    """
    Извлекает AI ответ из текста лога
    """
    # Ищем прямой AI response
    ai_match = re.search(r'AI response:\s*(.+)', text)
    if ai_match:
        return ai_match.group(1).strip()
    
    # Ищем JSON с текстом
    json_match = re.search(r'"text":\s*"([^"]*)"', text)
    if json_match:
        return json_match.group(1).strip()
    
    # Ищем другие паттерны
    if '[AI_DEBUG]' in text:
        debug_match = re.search(r'\[AI_DEBUG\]\s*(.+)', text)
        if debug_match:
            return debug_match.group(1).strip()
    
    return None

def save_logs(fixed_logs, ai_responses):
    """
    Сохраняет обработанные логи в файлы
    """
    # Создаем папку для логов если её нет
    logs_dir = Path("fixed_logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Текущее время для имени файла
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Сохраняем все логи
    all_logs_file = logs_dir / f"all_logs_fixed_{now}.json"
    with open(all_logs_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_logs, f, ensure_ascii=False, indent=2)
    
    # Сохраняем только AI ответы
    ai_logs_file = logs_dir / f"ai_responses_fixed_{now}.json"
    with open(ai_logs_file, 'w', encoding='utf-8') as f:
        json.dump(ai_responses, f, ensure_ascii=False, indent=2)
    
    # Сохраняем читаемый формат AI ответов
    ai_readable_file = logs_dir / f"ai_responses_readable_{now}.txt"
    with open(ai_readable_file, 'w', encoding='utf-8') as f:
        f.write("AI ОТВЕТЫ С ИСПРАВЛЕННОЙ КИРИЛЛИЦЕЙ\n")
        f.write("=" * 50 + "\n\n")
        
        for i, ai_entry in enumerate(ai_responses[-50:]):  # Последние 50
            f.write(f"{i+1}. [{ai_entry['timestamp']}]\n")
            f.write(f"AI: {ai_entry['response']}\n")
            f.write("-" * 50 + "\n\n")
    
    print(f"\nЛоги сохранены:")
    print(f"  - Все логи: {all_logs_file}")
    print(f"  - AI ответы (JSON): {ai_logs_file}")
    print(f"  - AI ответы (читаемый): {ai_readable_file}")
    
    return ai_readable_file

def main():
    """
    Основная функция
    """
    print("СКРИПТ ПОЛУЧЕНИЯ ЛОГОВ С ИСПРАВЛЕНИЕМ КИРИЛЛИЦЫ")
    print("=" * 60)
    
    # Устанавливаем пакеты если нужно
    install_required_packages()
    
    # Получаем логи через CLI
    logs_data, success = get_logs_via_gcloud()
    
    if not success or not logs_data:
        print("❌ Не удалось получить логи!")
        return
    
    print(f"✅ Получено {len(logs_data)} записей логов")
    
    # Обрабатываем логи
    fixed_logs, ai_responses = extract_and_fix_logs(logs_data)
    
    print(f"✅ Обработано {len(fixed_logs)} записей")
    print(f"✅ Найдено {len(ai_responses)} AI ответов")
    
    # Сохраняем
    readable_file = save_logs(fixed_logs, ai_responses)
    
    # Показываем примеры
    if ai_responses:
        print(f"\n📝 ПОСЛЕДНИЕ 5 AI ОТВЕТОВ:")
        print("-" * 40)
        for i, ai_entry in enumerate(ai_responses[-5:]):
            print(f"{i+1}. {ai_entry['response'][:100]}...")
    
    print(f"\n✅ Готово! Проверьте файл: {readable_file}")

if __name__ == "__main__":
    main() 
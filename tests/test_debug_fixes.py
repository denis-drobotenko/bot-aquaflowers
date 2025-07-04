#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений debug интерфейса
"""

import json
import re
from datetime import datetime

def test_session_grouping():
    """Тестирует группировку сессий по sender_id"""
    print("🧪 ТЕСТ ГРУППИРОВКИ СЕССИЙ")
    print("=" * 50)
    
    # Симулируем логи с разными session_id для одного пользователя
    test_logs = [
        {
            "timestamp": "2024-12-19T10:00:00Z",
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Привет'",
            "session_id": "1234567890_20241219-100000"
        },
        {
            "timestamp": "2024-12-19T10:05:00Z", 
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Как дела?'",
            "session_id": "1234567890_20241219-100500"
        },
        {
            "timestamp": "2024-12-19T10:10:00Z",
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Пока'",
            "session_id": "1234567890_20241219-101000"
        }
    ]
    
    # Симулируем логику группировки из debug_clean.html
    sessions = {}
    
    for log in test_logs:
        message = log.get('message', '')
        
        # Извлекаем sender_id
        webhook_match = re.search(r"from['\"]?\s*:\s*['\"]([^'\"]+)['\"]", message)
        if webhook_match:
            sender_id = webhook_match.group(1)
            
            if sender_id not in sessions:
                sessions[sender_id] = {
                    'session_id': sender_id,
                    'sender_id': sender_id,
                    'message_count': 0,
                    'last_message_time': log['timestamp'],
                    'unique_messages': set()
                }
            
            # Подсчитываем уникальные сообщения
            if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
                # Извлекаем текст сообщения - исправляем регулярное выражение
                text_match = re.search(r"text['\"]?\s*:\s*['\"]([^'\"]+)['\"]", message)
                if text_match:
                    content = text_match.group(1)
                    sessions[sender_id]['unique_messages'].add(content)
                    sessions[sender_id]['message_count'] = len(sessions[sender_id]['unique_messages'])
                    print(f"Добавлено сообщение: '{content}' для {sender_id}")
            
            if log['timestamp'] > sessions[sender_id]['last_message_time']:
                sessions[sender_id]['last_message_time'] = log['timestamp']
    
    # Преобразуем в список
    sessions_list = []
    for session in sessions.values():
        session_copy = session.copy()
        del session_copy['unique_messages']
        sessions_list.append(session_copy)
    
    print(f"Найдено сессий: {len(sessions_list)}")
    for session in sessions_list:
        print(f"  - {session['sender_id']}: {session['message_count']} сообщений")
    
    # Проверяем, что все сообщения одного пользователя сгруппированы
    if len(sessions_list) == 1 and sessions_list[0]['message_count'] == 3:
        print("✅ Группировка работает правильно - все сообщения одного пользователя объединены")
    else:
        print("❌ Проблема с группировкой")
    
    return sessions_list

def test_reply_extraction():
    """Тестирует извлечение reply из логов"""
    print("\n🧪 ТЕСТ ИЗВЛЕЧЕНИЯ REPLY")
    print("=" * 50)
    
    # Тестовые логи с reply
    test_logs = [
        {
            "message": "[WEBHOOK_REPLY] Reply to message ID: wamid.1234567890",
            "expected_reply": "wamid.1234567890"
        },
        {
            "message": '{"context": {"id": "wamid.9876543210"}}',
            "expected_reply": "wamid.9876543210"
        },
        {
            "message": "{'context': {'id': 'wamid.1111111111'}}",
            "expected_reply": "wamid.1111111111"
        }
    ]
    
    for i, test_log in enumerate(test_logs):
        message = test_log['message']
        expected = test_log['expected_reply']
        
        # Симулируем логику извлечения reply из debug_clean.html
        reply_to = None
        
        # Поиск WEBHOOK_REPLY
        reply_match = re.search(r'\[WEBHOOK_REPLY\] Reply to message ID: ([^\s,]+)', message)
        if reply_match:
            reply_to = reply_match.group(1)
        else:
            # Поиск context.id в JSON
            context_match = re.search(r'"context":\s*{\s*"id":\s*"([^"]+)"', message)
            if context_match:
                reply_to = context_match.group(1)
            else:
                # Поиск в одинарных кавычках
                single_quote_match = re.search(r"'context':\s*\{'id':\s*'([^']+)'", message)
                if single_quote_match:
                    reply_to = single_quote_match.group(1)
        
        if reply_to == expected:
            print(f"✅ Тест {i+1}: Reply извлечен правильно - {reply_to}")
        else:
            print(f"❌ Тест {i+1}: Ожидался {expected}, получен {reply_to}")

def test_message_deduplication():
    """Тестирует устранение дублирования сообщений"""
    print("\n🧪 ТЕСТ УСТРАНЕНИЯ ДУБЛИРОВАНИЯ")
    print("=" * 50)
    
    # Симулируем логи с дублирующимися сообщениями
    test_logs = [
        {
            "timestamp": "2024-12-19T10:00:00Z",
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Привет'"
        },
        {
            "timestamp": "2024-12-19T10:00:01Z", 
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Привет'"
        },
        {
            "timestamp": "2024-12-19T10:00:02Z",
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Привет'"
        },
        {
            "timestamp": "2024-12-19T10:05:00Z",
            "message": "[WEBHOOK_RAW_MESSAGE] from: '1234567890' text: 'Как дела?'"
        }
    ]
    
    # Симулируем логику устранения дублирования
    messages = []
    seen_messages = set()
    
    for log in test_logs:
        message = log['message']
        
        if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
            # Извлекаем текст сообщения - исправляем регулярное выражение
            text_match = re.search(r"text['\"]?\s*:\s*['\"]([^'\"]+)['\"]", message)
            if text_match:
                content = text_match.group(1)
                print(f"Найдено сообщение: '{content}'")
                
                if content not in seen_messages:
                    seen_messages.add(content)
                    messages.append({
                        'content': content,
                        'timestamp': log['timestamp']
                    })
                    print(f"  -> Добавлено как новое")
                else:
                    print(f"  -> Пропущено как дубликат")
    
    print(f"Найдено уникальных сообщений: {len(messages)}")
    for msg in messages:
        print(f"  - {msg['content']} ({msg['timestamp']})")
    
    # Проверяем, что дубликаты устранены
    if len(messages) == 2:  # "Привет" и "Как дела?"
        print("✅ Дублирование устранено правильно")
    else:
        print("❌ Проблема с устранением дублирования")

def main():
    """Основная функция тестирования"""
    print("🔧 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ DEBUG ИНТЕРФЕЙСА")
    print("=" * 60)
    
    test_session_grouping()
    test_reply_extraction()
    test_message_deduplication()
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("\nТеперь можно проверить debug интерфейс на http://localhost:8080/debug_clean.html")

if __name__ == "__main__":
    main() 
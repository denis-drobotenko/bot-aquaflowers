"""
Тесты для системы переводов чатов
"""

import pytest
import asyncio
from src.chat_translation_manager import (
    translate_chat_batch, 
    parse_translated_chat, 
    extract_translated_content,
    format_timestamp,
    extract_order_summary
)

def test_format_timestamp():
    """Тест форматирования timestamp"""
    from datetime import datetime
    
    # Тест с datetime объектом
    dt = datetime(2024, 1, 15, 10, 30)
    assert format_timestamp(dt) == "10:30"
    
    # Тест со строкой
    assert format_timestamp("2024-01-15 10:30:00") == "10:30"
    assert format_timestamp("10:30") == "10:30"
    
    # Тест с короткой строкой
    assert format_timestamp("10") == "10"

def test_extract_translated_content():
    """Тест извлечения переведенного контента"""
    # Тест с двоеточием
    assert extract_translated_content("Сообщение 1 (👤 Пользователь): Привет!") == "Привет!"
    assert extract_translated_content("Message 1 (User): Hello!") == "Hello!"
    
    # Тест без двоеточия
    assert extract_translated_content("Просто текст") == "Просто текст"

def test_extract_order_summary():
    """Тест извлечения сводки заказа"""
    conversation_history = [
        {
            'role': 'system',
            'content': 'order_info:bouquet=Spirit 🌸'
        },
        {
            'role': 'system', 
            'content': 'order_info:date=завтра'
        },
        {
            'role': 'system',
            'content': 'order_info:address=ул. Пушкина, 10'
        },
        {
            'role': 'user',
            'content': 'Привет'
        }
    ]
    
    summary = extract_order_summary(conversation_history)
    
    assert summary['bouquet'] == 'Spirit 🌸'
    assert summary['date'] == 'завтра'
    assert summary['address'] == 'ул. Пушкина, 10'
    assert len(summary) == 3

def test_parse_translated_chat():
    """Тест парсинга переведенного чата"""
    original_messages = [
        {'role': 'user', 'content': 'Привет', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    translated_text = """Сообщение 1 (👤 Пользователь): Hello!
Сообщение 2 (🤖 Бот): Hello!"""
    
    result = parse_translated_chat(translated_text, original_messages, 'en')
    
    assert len(result) == 2
    assert result[0]['role'] == 'user'
    assert result[0]['content'] == 'Hello!'
    assert result[0]['lang'] == 'en'
    assert result[1]['role'] == 'model'
    assert result[1]['content'] == 'Hello!'

def test_chat_translation_integration():
    """Интеграционный тест системы переводов"""
    # Тест полного цикла (без реального AI)
    messages = [
        {'role': 'user', 'content': 'Привет!', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    # Проверяем, что функции не падают
    assert format_timestamp('10:30') == '10:30'
    assert extract_translated_content('test: content') == 'content'
    
    # Проверяем извлечение сводки заказа
    history = [{'role': 'system', 'content': 'order_info:bouquet=Test'}]
    summary = extract_order_summary(history)
    assert summary.get('bouquet') == 'Test'

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
Тесты для системы переводов чатов
"""

import pytest
import asyncio
from src.chat_translation_manager import (
    translate_chat_batch, 
    parse_translated_chat, 
    extract_translated_content,
    format_timestamp,
    extract_order_summary
)

def test_format_timestamp():
    """Тест форматирования timestamp"""
    from datetime import datetime
    
    # Тест с datetime объектом
    dt = datetime(2024, 1, 15, 10, 30)
    assert format_timestamp(dt) == "10:30"
    
    # Тест со строкой
    assert format_timestamp("2024-01-15 10:30:00") == "10:30"
    assert format_timestamp("10:30") == "10:30"
    
    # Тест с короткой строкой
    assert format_timestamp("10") == "10"

def test_extract_translated_content():
    """Тест извлечения переведенного контента"""
    # Тест с двоеточием
    assert extract_translated_content("Сообщение 1 (👤 Пользователь): Привет!") == "Привет!"
    assert extract_translated_content("Message 1 (User): Hello!") == "Hello!"
    
    # Тест без двоеточия
    assert extract_translated_content("Просто текст") == "Просто текст"

def test_extract_order_summary():
    """Тест извлечения сводки заказа"""
    conversation_history = [
        {
            'role': 'system',
            'content': 'order_info:bouquet=Spirit 🌸'
        },
        {
            'role': 'system', 
            'content': 'order_info:date=завтра'
        },
        {
            'role': 'system',
            'content': 'order_info:address=ул. Пушкина, 10'
        },
        {
            'role': 'user',
            'content': 'Привет'
        }
    ]
    
    summary = extract_order_summary(conversation_history)
    
    assert summary['bouquet'] == 'Spirit 🌸'
    assert summary['date'] == 'завтра'
    assert summary['address'] == 'ул. Пушкина, 10'
    assert len(summary) == 3

def test_parse_translated_chat():
    """Тест парсинга переведенного чата"""
    original_messages = [
        {'role': 'user', 'content': 'Привет', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    translated_text = """Сообщение 1 (👤 Пользователь): Hello!
Сообщение 2 (🤖 Бот): Hello!"""
    
    result = parse_translated_chat(translated_text, original_messages, 'en')
    
    assert len(result) == 2
    assert result[0]['role'] == 'user'
    assert result[0]['content'] == 'Hello!'
    assert result[0]['lang'] == 'en'
    assert result[1]['role'] == 'model'
    assert result[1]['content'] == 'Hello!'

def test_chat_translation_integration():
    """Интеграционный тест системы переводов"""
    # Тест полного цикла (без реального AI)
    messages = [
        {'role': 'user', 'content': 'Привет!', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    # Проверяем, что функции не падают
    assert format_timestamp('10:30') == '10:30'
    assert extract_translated_content('test: content') == 'content'
    
    # Проверяем извлечение сводки заказа
    history = [{'role': 'system', 'content': 'order_info:bouquet=Test'}]
    summary = extract_order_summary(history)
    assert summary.get('bouquet') == 'Test'

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
Тесты для системы переводов чатов
"""

import pytest
import asyncio
from src.chat_translation_manager import (
    translate_chat_batch, 
    parse_translated_chat, 
    extract_translated_content,
    format_timestamp,
    extract_order_summary
)

def test_format_timestamp():
    """Тест форматирования timestamp"""
    from datetime import datetime
    
    # Тест с datetime объектом
    dt = datetime(2024, 1, 15, 10, 30)
    assert format_timestamp(dt) == "10:30"
    
    # Тест со строкой
    assert format_timestamp("2024-01-15 10:30:00") == "10:30"
    assert format_timestamp("10:30") == "10:30"
    
    # Тест с короткой строкой
    assert format_timestamp("10") == "10"

def test_extract_translated_content():
    """Тест извлечения переведенного контента"""
    # Тест с двоеточием
    assert extract_translated_content("Сообщение 1 (👤 Пользователь): Привет!") == "Привет!"
    assert extract_translated_content("Message 1 (User): Hello!") == "Hello!"
    
    # Тест без двоеточия
    assert extract_translated_content("Просто текст") == "Просто текст"

def test_extract_order_summary():
    """Тест извлечения сводки заказа"""
    conversation_history = [
        {
            'role': 'system',
            'content': 'order_info:bouquet=Spirit 🌸'
        },
        {
            'role': 'system', 
            'content': 'order_info:date=завтра'
        },
        {
            'role': 'system',
            'content': 'order_info:address=ул. Пушкина, 10'
        },
        {
            'role': 'user',
            'content': 'Привет'
        }
    ]
    
    summary = extract_order_summary(conversation_history)
    
    assert summary['bouquet'] == 'Spirit 🌸'
    assert summary['date'] == 'завтра'
    assert summary['address'] == 'ул. Пушкина, 10'
    assert len(summary) == 3

def test_parse_translated_chat():
    """Тест парсинга переведенного чата"""
    original_messages = [
        {'role': 'user', 'content': 'Привет', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    translated_text = """Сообщение 1 (👤 Пользователь): Hello!
Сообщение 2 (🤖 Бот): Hello!"""
    
    result = parse_translated_chat(translated_text, original_messages, 'en')
    
    assert len(result) == 2
    assert result[0]['role'] == 'user'
    assert result[0]['content'] == 'Hello!'
    assert result[0]['lang'] == 'en'
    assert result[1]['role'] == 'model'
    assert result[1]['content'] == 'Hello!'

def test_chat_translation_integration():
    """Интеграционный тест системы переводов"""
    # Тест полного цикла (без реального AI)
    messages = [
        {'role': 'user', 'content': 'Привет!', 'timestamp': '10:30'},
        {'role': 'model', 'content': 'Здравствуйте!', 'timestamp': '10:31'}
    ]
    
    # Проверяем, что функции не падают
    assert format_timestamp('10:30') == '10:30'
    assert extract_translated_content('test: content') == 'content'
    
    # Проверяем извлечение сводки заказа
    history = [{'role': 'system', 'content': 'order_info:bouquet=Test'}]
    summary = extract_order_summary(history)
    assert summary.get('bouquet') == 'Test'

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
import json
import re
from datetime import datetime

def extract_dialogs():
    # Читаем самый свежий лог
    with open('logs_20250702_125730.log', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Извлекаем диалог Petr
    print("=== ДИАЛОГ С PETR (79084634603) ===")
    print()
    
    # Находим все сообщения Petr
    petr_messages = re.findall(r"'from': '79084634603'.*?'text': {'body': '(.*?)'}", content)
    petr_responses = re.findall(r"'to': '79084634603'.*?'text': {'body': '(.*?)'}", content)
    
    print("Сообщения от Petr:")
    for i, msg in enumerate(petr_messages, 1):
        print(f"{i}. Petr: {msg}")
    
    print("\nОтветы бота:")
    for i, resp in enumerate(petr_responses, 1):
        print(f"{i}. Bot: {resp}")
    
    print("\n" + "="*50)
    print("=== ДИАЛОГ С DENIS (79140775712) ===")
    print()
    
    # Находим все сообщения Denis
    denis_messages = re.findall(r"'from': '79140775712'.*?'text': {'body': '(.*?)'}", content)
    denis_responses = re.findall(r"'to': '79140775712'.*?'text': {'body': '(.*?)'}", content)
    
    # Также ищем в других форматах
    denis_messages_alt = re.findall(r"'from': '79140775712'.*?'body': '(.*?)'", content)
    denis_responses_alt = re.findall(r"'to': '79140775712'.*?'body': '(.*?)'", content)
    
    denis_messages.extend(denis_messages_alt)
    denis_responses.extend(denis_responses_alt)
    
    print("Сообщения от Denis:")
    for i, msg in enumerate(denis_messages, 1):
        print(f"{i}. Denis: {msg}")
    
    print("\nОтветы бота:")
    for i, resp in enumerate(denis_responses, 1):
        print(f"{i}. Bot: {resp}")

if __name__ == "__main__":
    extract_dialogs() 
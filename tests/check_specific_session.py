#!/usr/bin/env python3
"""
Тест: перевод и сохранение перевода для сессии 79140775712_20250703_201756_765601_479
"""
import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import database
from src.chat_translation_manager import save_completed_chat_with_translations

def print_translations(completed_chat):
    translations = completed_chat.get('translations', {})
    for lang, msgs in translations.items():
        print(f"\n--- Перевод ({lang}) ---")
        for i, msg in enumerate(msgs, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            print(f"{i:02d}. [{role}] {content}")
        print(f"--- Конец перевода ({lang}) ---\n")

def list_all_completed_chats():
    """Выводит все session_id из коллекции completed_chats"""
    try:
        if not database.db:
            print("❌ Firestore client not available")
            return []
        
        docs = database.db.collection('completed_chats').stream()
        session_ids = []
        for doc in docs:
            session_ids.append(doc.id)
            data = doc.to_dict()
            sender_id = data.get('sender_id', 'unknown')
            print(f"📄 Found: session_id={doc.id}, sender_id={sender_id}")
        
        print(f"📊 Total completed_chats: {len(session_ids)}")
        return session_ids
    except Exception as e:
        print(f"❌ Error listing completed_chats: {e}")
        return []

def run():
    print("=== ПРОВЕРКА КОНКРЕТНОЙ СЕССИИ ===")
    
    full_session_id = "79140775712_20250703_201756_765601_479"
    
    # Извлекаем sender_id из session_id
    if '_' in full_session_id and full_session_id.split('_')[0].isdigit() and len(full_session_id.split('_')[0]) >= 10:
        # Формат: {sender_id}_{session_id}
        sender_id = full_session_id.split('_')[0]
        actual_session_id = '_'.join(full_session_id.split('_')[1:])
    else:
        # Формат: {session_id} - нужно найти владельца
        actual_session_id = full_session_id
        sender_id = None
    
    print(f"1. Full Session ID: {full_session_id}")
    print(f"   Sender ID: {sender_id}")
    print(f"   Actual Session ID: {actual_session_id}")
    
    # Получаем историю диалога
    print("2. Получаем историю диалога")
    conversation_history = database.get_conversation_history(sender_id, actual_session_id)
    print(f"   Сообщений в истории: {len(conversation_history)}")
    
    if conversation_history:
        print("\n--- ВСЕ СООБЩЕНИЯ ---")
        for i, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            print(f"{i:02d}. [{role}] {timestamp}")
            print(f"    {content}")
        print("--- КОНЕЦ СООБЩЕНИЙ ---")
    
    # Формируем ссылку
    print("3. Формируем ссылку")
    url = f"http://localhost:8080/chat/{full_session_id}"
    print(f"   URL: {url}")
    
    if conversation_history:
        print(f"\n✅ УСПЕХ! Найдена реальная сессия с историей")
        print(f"🔗 Ссылка: {url}")
        print(f"📊 Сообщений: {len(conversation_history)}")
        print(f"🆔 Session ID: {full_session_id}")
        
        # Запускаем перевод и сохранение
        print(f"Запускаю перевод и сохранение для: {full_session_id}")
        
        try:
            # Создаем новый event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем перевод
            result = loop.run_until_complete(save_completed_chat_with_translations(sender_id, actual_session_id))
            
            print("Переводы сохранены. Ждем 3 секунды для синхронизации Firestore...")
            time.sleep(3)  # Пауза для синхронизации
            
            print("Читаю из базы...")
            
            # Показываем все completed_chats
            print("\n📋 Все completed_chats в базе:")
            all_session_ids = list_all_completed_chats()
            
            # Пытаемся найти наш чат
            completed_chat = database.get_completed_chat(actual_session_id)
            if completed_chat:
                print(f"✅ Найден completed_chat: {actual_session_id}")
                print_translations(completed_chat)
            else:
                print(f"❌ Не найден completed_chat в базе!")
                print(f"   Искали по session_id: {actual_session_id}")
                print(f"   Доступные session_id: {all_session_ids}")
            
        except Exception as e:
            print(f"❌ Ошибка при переводе: {e}")
        finally:
            loop.close()
    else:
        print(f"❌ Не найдена сессия: {full_session_id}")

if __name__ == "__main__":
    run() 
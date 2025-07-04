import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.ai_manager import get_ai_response
from src.json_processor import parse_ai_response

# Тестовые сообщения пользователя
TEST_MESSAGES = [
    "Привет!",
    "Покажи каталог цветов, пожалуйста!",
    "Мне нужен букет для мамы. Можно с открыткой?\n\nТекст открытки: Любимой маме!",
    "Сделай список:\n- Розы\n- Тюльпаны\n- Лилии\n\nСпасибо!",
    "Расскажи подробно про доставку и оплату.",
    "/getchat"  # Добавляем тест команды /getchat
]

SENDER_ID = "79140775712"
SESSION_ID = "test_manual_session"
SENDER_NAME = "Тестовый пользователь"
USER_LANG = "ru"

print("=== Ручной тест AI-диалога и парсинга JSON ===\n")

for i, msg in enumerate(TEST_MESSAGES, 1):
    print(f"\n--- Тест {i} ---")
    print(f"Пользователь: {repr(msg)}")
    
    try:
        # Получаем ответ AI
        print("Отправляем в AI...")
        ai_text, ai_command = get_ai_response(SESSION_ID, [{'role': 'user', 'parts': [{'text': msg}]}], SENDER_NAME, USER_LANG)
        print(f"\nОтвет AI (текст):\n{repr(ai_text)}")
        print(f"Команда: {ai_command}")
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("-----------------------------")

print("\n=== Тест завершён ===") 
 
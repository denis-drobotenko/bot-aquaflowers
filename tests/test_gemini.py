import sys
import os

# Добавляем путь к src
sys.path.append('src')

from src.ai_manager import get_ai_response

print("Testing full AI response function...")

try:
    # Тестируем с простым сообщением
    response_text, response_command = get_ai_response(
        "test_session_123",
        [
            {"role": "user", "content": "Здравствуйте"}
        ],
        "Test User"
    )
    print('AI Response Text:', response_text)
    print('AI Response Command:', response_command)
    print('✅ Full AI function works!')
except Exception as e:
    print('❌ Error in full AI function:', e) 
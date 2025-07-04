import requests
import json
import re

# Получаем логи
url = "https://auraflora-bot-75152239022.asia-southeast1.run.app/api/debug/logs"
response = requests.get(url)
data = response.json()
logs = data['logs']

print(f"Загружено {len(logs)} логов")

# Тестируем функции из debug_clean.html
def extractUserMessageFromLog(logMessage):
    try:
        # Извлекаем из структуры: 'text': {'body': 'Привет'}
        jsonMatch = re.search(r"'text':\s*\{'body':\s*'([^']+)'", logMessage)
        if jsonMatch:
            return jsonMatch.group(1).strip()
        
        # Альтернативный паттерн с двойными кавычками
        jsonMatch2 = re.search(r'"text":\s*{\s*"body":\s*"([^"]+)"', logMessage)
        if jsonMatch2:
            return jsonMatch2.group(1).strip()
        
    except Exception as e:
        print(f"Error: {e}")
    return ""

def extractBotResponseFromLog(logMessage):
    try:
        # [AI_FINAL_RESULT] Text: Доброй ночи, Denis! Рада снова вас видеть! 🌸
        aiMatch = re.search(r'\[AI_FINAL_RESULT\] Text:\s*(.+)', logMessage)
        if aiMatch:
            return aiMatch.group(1).strip()
        
        # [WEBHOOK_AI_RESPONSE_TEXT] Доброй ночи, Denis! Рада снова вас видеть! 🌸
        responseMatch = re.search(r'\[WEBHOOK_AI_RESPONSE_TEXT\]\s*(.+)', logMessage)
        if responseMatch:
            return responseMatch.group(1).strip()
        
        # [MESSAGE_SEND_INPUT] Original message: Доброй ночи, Denis! Рада снова вас видеть! 🌸
        sendMatch = re.search(r'\[MESSAGE_SEND_INPUT\] Original message:\s*(.+)', logMessage)
        if sendMatch:
            return sendMatch.group(1).strip()
        
    except Exception as e:
        print(f"Error: {e}")
    return ""

# Ищем логи с AI ответами
ai_logs = []
for log in logs:
    message = log.get('message', '')
    if any(pattern in message for pattern in ['[AI_FINAL_RESULT]', '[AI_RESPONSE]', '[AI_TEXT]', '[AI_RESULT]', '[PARSE_RESPONSE]', '[JSON_EXTRACT_RESULT]']):
        ai_logs.append(log)

print(f"\nНайдено {len(ai_logs)} логов с AI ответами:")
for i, log in enumerate(ai_logs[:10]):  # Показываем первые 10
    print(f"\nAI лог {i+1}:")
    print(f"Logger: {log.get('logger_name')}")
    print(f"Message: {log.get('message')}")
    
    # Тестируем извлечение ответа
    content = extractBotResponseFromLog(log.get('message', ''))
    if content:
        print(f"Извлеченный ответ: {content}")
    else:
        print("Ответ не извлечен")

# Ищем логи с входящими сообщениями
incoming_logs = []
for log in logs:
    message = log.get('message', '')
    if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
        incoming_logs.append(log)

print(f"\nНайдено {len(incoming_logs)} логов с входящими сообщениями:")
for i, log in enumerate(incoming_logs[:5]):  # Показываем первые 5
    print(f"\nВходящий лог {i+1}:")
    print(f"Logger: {log.get('logger_name')}")
    print(f"Message: {log.get('message')}")
    
    # Тестируем извлечение сообщения
    content = extractUserMessageFromLog(log.get('message', ''))
    if content:
        print(f"Извлеченное сообщение: {content}")
    else:
        print("Сообщение не извлечено") 
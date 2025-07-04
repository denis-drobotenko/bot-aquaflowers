import requests
import json
import re
from datetime import datetime

# Получаем логи
url = "https://auraflora-bot-75152239022.asia-southeast1.run.app/api/debug/logs"
response = requests.get(url)
data = response.json()
logs = data['logs']

print(f"Загружено {len(logs)} логов")

# Функции из debug_clean.html
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
        # [AI_FINAL_RESULT] Text: Доброй ночи, Denis! Рада снова вас видеть! 🌸, Command: None
        aiMatch = re.search(r'\[AI_FINAL_RESULT\] Text:\s*(.+?)(?:,\s*Command:|$)', logMessage)
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

def buildSessionsFromLogs(logs):
    sessions = {}
    
    # Ищем session_id в логах
    for log in logs:
        message = log.get('message', '')
        
        # Извлекаем session_id из разных паттернов
        sessionId = log.get('session_id')
        if not sessionId:
            # Ищем в тексте лога
            sessionMatch = re.search(r'Session[:\s]+([^\s,]+)', message)
            if sessionMatch:
                sessionId = sessionMatch.group(1)
            else:
                # Ищем в webhook данных
                webhookMatch = re.search(r'from[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]', message)
                if webhookMatch:
                    sessionId = webhookMatch.group(1) + '_' + datetime.fromisoformat(log.get('timestamp')).strftime('%Y%m%d')
        
        if not sessionId:
            continue
        
        if sessionId not in sessions:
            senderId = sessionId.split('_')[0] if '_' in sessionId else sessionId
            sessions[sessionId] = {
                'session_id': sessionId,
                'sender_id': senderId,
                'message_count': 0,
                'last_message_time': log.get('timestamp')
            }
        
        # Подсчитываем сообщения
        if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
            sessions[sessionId]['message_count'] += 1
        
        if log.get('timestamp') > sessions[sessionId]['last_message_time']:
            sessions[sessionId]['last_message_time'] = log.get('timestamp')
    
    sessionsList = list(sessions.values())
    sessionsList.sort(key=lambda x: x['last_message_time'], reverse=True)
    
    return sessionsList

def buildMessagesFromLogs(sessionId, logs):
    messages = []
    
    # Ищем логи для этой сессии (по session_id или по паттернам)
    sessionLogs = []
    for log in logs:
        message = log.get('message', '')
        
        # Проверяем session_id
        if log.get('session_id') == sessionId:
            sessionLogs.append(log)
            continue
        
        # Ищем session_id в тексте лога
        sessionMatch = re.search(r'Session[:\s]+([^\s,]+)', message)
        if sessionMatch and sessionMatch.group(1) == sessionId:
            sessionLogs.append(log)
            continue
        
        # Ищем по sender_id (первая часть session_id)
        senderId = sessionId.split('_')[0]
        webhookMatch = re.search(r'from[\'"]?\s*:\s*[\'"]([^\'"]+)[\'"]', message)
        if webhookMatch and webhookMatch.group(1) == senderId:
            sessionLogs.append(log)
            continue
    
    print(f'Анализирую {len(sessionLogs)} логов для сессии {sessionId}')
    
    # Ищем логи с AI ответами во всех логах
    allAiLogs = [log for log in logs if '[AI_FINAL_RESULT]' in log.get('message', '')]
    print(f'Найдено {len(allAiLogs)} логов с AI ответами во всех логах')
    
    for log in sessionLogs:
        message = log.get('message', '')
        timestamp = log.get('timestamp')
        logger = log.get('logger_name', '')
        
        # Входящие сообщения пользователя
        if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
            print(f'Найден входящий лог: {message[:100]}...')
            content = extractUserMessageFromLog(message)
            print(f'Извлеченный контент: {content}')
            if content:
                messages.append({
                    'role': 'user',
                    'content': content,
                    'timestamp': timestamp
                })
        
        # Исходящие сообщения бота
        elif '[AI_FINAL_RESULT]' in message or '[WEBHOOK_AI_RESPONSE_TEXT]' in message or '[MESSAGE_SEND_INPUT] Original message:' in message:
            print(f'Найден исходящий лог: {message[:100]}...')
            content = extractBotResponseFromLog(message)
            print(f'Извлеченный контент: {content}')
            if content:
                messages.append({
                    'role': 'assistant',
                    'content': content,
                    'timestamp': timestamp
                })
    
    messages.sort(key=lambda x: x['timestamp'])
    print(f'Построено {len(messages)} сообщений')
    return messages

# Тестируем построение сессий
print("\n=== ТЕСТ ПОСТРОЕНИЯ СЕССИЙ ===")
sessions = buildSessionsFromLogs(logs)
print(f"Найдено {len(sessions)} сессий:")
for session in sessions:
    print(f"  {session['session_id']} - {session['sender_id']} ({session['message_count']} сообщений)")

# Тестируем построение сообщений для первой сессии
if sessions:
    print(f"\n=== ТЕСТ ПОСТРОЕНИЯ СООБЩЕНИЙ ДЛЯ СЕССИИ {sessions[0]['session_id']} ===")
    messages = buildMessagesFromLogs(sessions[0]['session_id'], logs)
    
    print(f"\nРезультат - {len(messages)} сообщений:")
    for i, msg in enumerate(messages):
        print(f"  {i+1}. [{msg['role']}] {msg['content'][:50]}...")

print("\n=== ВСЕ AI-ОТВЕТЫ С sessionId ===")
for log in logs:
    msg = log.get('message', '')
    if '[AI_FINAL_RESULT]' in msg:
        # Пытаемся найти sessionId в тексте
        session_match = re.search(r'Session[:\s]+([^\s,]+)', msg)
        session_id_in_log = session_match.group(1) if session_match else None
        print(f"AI_LOG: session_id_in_log={session_id_in_log}, msg={msg[:100]}...") 
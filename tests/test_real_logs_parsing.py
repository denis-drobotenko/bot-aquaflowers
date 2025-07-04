#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import re

def extractBotResponseFromLog(logMessage):
    try:
        # [AI_FINAL_RESULT] Text: Доброй ночи, Denis! Рада снова вас видеть! 🌸, Command: None
        aiMatch = re.search(r'\[AI_FINAL_RESULT\] Text:\s*(.+?)(?:,\s*Command:|$)', logMessage)
        if aiMatch:
            return aiMatch.group(1).strip()
        
        # [AI_RESPONSE_GENERATED] Session: 79140775712_20250703-022437 | Text: Конечно! Чем могу помочь? 🌸 | Command: None
        aiGeneratedMatch = re.search(r'\[AI_RESPONSE_GENERATED\].*?Text:\s*(.+?)(?:\s*\|\s*Command:|$)', logMessage)
        if aiGeneratedMatch:
            return aiGeneratedMatch.group(1).strip()
        
        # [AI_RESPONSE_SAVED] Session: 79140775712_20250703-022437 | Message ID: wamid.HBgLNzkxNDA3NzU3MTIVAgASGBQzQTY5RUI1MEU5MzY3QzUxMENDMQA= | Text: Конечно! Чем могу помочь? 🌸
        aiSavedMatch = re.search(r'\[AI_RESPONSE_SAVED\].*?Text:\s*(.+?)(?:\s*\|\s*Message ID:|$)', logMessage)
        if aiSavedMatch:
            return aiSavedMatch.group(1).strip()
        
        # [WEBHOOK_AI_RESPONSE_TEXT] Доброй ночи, Denis! Рада снова вас видеть! 🌸
        responseMatch = re.search(r'\[WEBHOOK_AI_RESPONSE_TEXT\]\s*(.+)', logMessage)
        if responseMatch:
            return responseMatch.group(1).strip()
        
        # [MESSAGE_SEND_INPUT] Original message: Доброй ночи, Denis! Рада снова вас видеть! 🌸
        sendMatch = re.search(r'\[MESSAGE_SEND_INPUT\] Original message:\s*(.+)', logMessage)
        if sendMatch:
            return sendMatch.group(1).strip()
        
    except Exception as e:
        print(f'Error: {e}')
    return ''

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
        print(f'Error: {e}')
    return ''

def test_real_logs():
    print("Загружаю логи с сервера...")
    
    try:
        response = requests.get('http://localhost:8000/api/debug/logs')
        if response.status_code == 200:
            logs = response.json()
            print(f"Загружено {len(logs)} логов")
            
            # Ищем AI ответы
            ai_logs = []
            user_logs = []
            
            for log in logs:
                message = log.get('message', '')
                
                # AI ответы
                if any(pattern in message for pattern in [
                    '[AI_FINAL_RESULT]',
                    '[AI_RESPONSE_GENERATED]',
                    '[AI_RESPONSE_SAVED]',
                    '[WEBHOOK_AI_RESPONSE_TEXT]',
                    '[MESSAGE_SEND_INPUT]'
                ]):
                    ai_logs.append(log)
                
                # Входящие сообщения
                if '[WEBHOOK_RAW_MESSAGE]' in message and ('"text"' in message or "'text'" in message):
                    user_logs.append(log)
            
            print(f"\nНайдено {len(ai_logs)} AI логов:")
            for i, log in enumerate(ai_logs[:5], 1):  # Показываем первые 5
                message = log.get('message', '')
                extracted = extractBotResponseFromLog(message)
                print(f"  {i}. {message[:100]}...")
                print(f"     Извлечено: '{extracted}'")
                print()
            
            print(f"\nНайдено {len(user_logs)} входящих сообщений:")
            for i, log in enumerate(user_logs[:5], 1):  # Показываем первые 5
                message = log.get('message', '')
                extracted = extractUserMessageFromLog(message)
                print(f"  {i}. {message[:100]}...")
                print(f"     Извлечено: '{extracted}'")
                print()
                
        else:
            print(f"Ошибка загрузки логов: {response.status_code}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    test_real_logs() 
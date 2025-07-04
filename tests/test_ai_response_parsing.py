#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

# Тестовые логи из вашего вывода
test_logs = [
    "[AI_RESPONSE_GENERATED] Session: 79140775712_20250703-022437 | Text: Конечно! Чем могу помочь? 🌸 | Command: None",
    "[AI_RESPONSE_SAVED] Session: 79140775712_20250703-022437 | Message ID: wamid.HBgLNzkxNDA3NzU3MTIVAgASGBQzQTY5RUI1MEU5MzY3QzUxMENDMQA= | Text: Конечно! Чем могу помочь? 🌸",
    "[AI_FINAL_RESULT] Text: Доброй ночи, Denis! Рада снова вас видеть! 🌸, Command: None",
    "[WEBHOOK_AI_RESPONSE_TEXT] Доброй ночи, Denis! Рада снова вас видеть! 🌸",
    "[MESSAGE_SEND_INPUT] Original message: Доброй ночи, Denis! Рада снова вас видеть! 🌸"
]

print("Тестирую парсинг AI ответов:")
print("=" * 50)

for i, log in enumerate(test_logs, 1):
    result = extractBotResponseFromLog(log)
    print(f"Тест {i}:")
    print(f"  Лог: {log}")
    print(f"  Результат: '{result}'")
    print(f"  Успех: {'✅' if result else '❌'}")
    print()

print("=" * 50)
print("Тест завершен!") 
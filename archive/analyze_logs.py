import requests
import json

def analyze_logs():
    print("Анализирую структуру логов...")
    
    # Получаем логи
    url = "https://auraflora-bot-75152239022.asia-southeast1.run.app/api/debug/logs?period_min=5"
    response = requests.get(url)
    data = response.json()
    
    logs = data.get('logs', [])
    print(f"Всего логов: {len(logs)}")
    
    if not logs:
        print("Логи не найдены")
        return
    
    # Анализируем первый лог
    first_log = logs[0]
    print("\nСтруктура первого лога:")
    print(f"Ключи: {list(first_log.keys())}")
    
    # Показываем содержимое textPayload
    text_payload = first_log.get('textPayload', '')
    print(f"\ntextPayload (первые 500 символов):")
    print(text_payload[:500])
    
    # Ищем логи с полезной информацией
    useful_logs = []
    for log in logs:
        text = log.get('textPayload', '')
        if any(keyword in text.lower() for keyword in [
            'webhook', 'message', 'ai', 'session', 'user', 'bot', 'response'
        ]):
            useful_logs.append(log)
    
    print(f"\nНайдено {len(useful_logs)} логов с полезной информацией")
    
    if useful_logs:
        print("\nПримеры полезных логов:")
        for i, log in enumerate(useful_logs[:3]):
            text = log.get('textPayload', '')[:200]
            print(f"{i+1}. {text}")

if __name__ == "__main__":
    analyze_logs() 
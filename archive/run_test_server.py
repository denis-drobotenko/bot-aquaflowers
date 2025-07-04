#!/usr/bin/env python3
"""
Скрипт для запуска тестового сервера
"""

import sys
import os
import uvicorn

# Добавляем src в путь для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Запускает тестовый сервер"""
    
    print("🚀 Запуск тестового сервера AuraFlora Bot")
    print("=" * 50)
    
    # Настройки сервера
    host = "127.0.0.1"  # localhost
    port = 8081
    reload = True  # Автоперезагрузка при изменениях
    
    print(f"📍 Сервер будет доступен по адресу: http://{host}:{port}")
    print(f"🔄 Автоперезагрузка: {'Включена' if reload else 'Отключена'}")
    print(f"📁 Рабочая директория: {os.getcwd()}")
    
    print("\n📋 Доступные эндпоинты:")
    print(f"  🌐 Главная страница: http://{host}:{port}/")
    print(f"  ❤️ Проверка состояния: http://{host}:{port}/health")
    print(f"  📨 Webhook: http://{host}:{port}/webhook")
    print(f"  💬 История переписки: http://{host}:{port}/chat/{{session_id}}")
    
    print("\n🧪 Для тестирования:")
    print(f"  1. Сначала запустите: python test_chat_history.py")
    print(f"  2. Затем откройте браузер и перейдите по ссылкам выше")
    print(f"  3. Для остановки сервера нажмите Ctrl+C")
    
    print("\n" + "=" * 50)
    print("🚀 Запуск сервера...")
    
    try:
        # Запускаем сервер
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Ошибка запуска сервера: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
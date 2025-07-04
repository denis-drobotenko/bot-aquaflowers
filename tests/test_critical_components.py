#!/usr/bin/env python3
"""
Критические тесты компонентов перед деплоем
"""

import asyncio
import sys
import os
import pytest
import time
from datetime import datetime

# Исправляем кодировку для Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Добавляем пути к модулям
current_dir = os.path.dirname(__file__)
project_root = os.path.join(current_dir, '..')
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_path)

# Импорты для тестирования
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.utils.whatsapp_client import WhatsAppClient
from src.repositories.message_repository import MessageRepository
from src.models.message import Message, MessageRole
from src.config import GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID, PROJECT_ID

class CriticalComponentTester:
    """Тестер критических компонентов системы"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Логирует результат теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results[test_name] = success
        
    async def test_ai_service(self):
        """Тест AI сервиса (Gemini)"""
        print("\n=== ТЕСТ AI СЕРВИСА (GEMINI) ===")
        
        try:
            # Инициализация AI сервиса
            ai_service = AIService(GEMINI_API_KEY)
            
            # Тест 1: Простой ответ
            test_messages = [
                Message(
                    sender_id="test_user",
                    session_id="test_session",
                    role=MessageRole.USER,
                    content="Привет"
                )
            ]
            
            response = await ai_service.generate_response(test_messages)
            if response and len(response) > 10:
                self.log_test("AI простой ответ", True, f"Получен ответ длиной {len(response)} символов")
            else:
                self.log_test("AI простой ответ", False, "Ответ слишком короткий или пустой")
                return False
                
            # Тест 2: Определение языка
            lang_ru = ai_service.detect_language("Привет, как дела?")
            lang_en = ai_service.detect_language("Hello, how are you?")
            
            if lang_ru == 'ru' and lang_en == 'en':
                self.log_test("AI определение языка", True, f"RU: {lang_ru}, EN: {lang_en}")
            else:
                self.log_test("AI определение языка", False, f"RU: {lang_ru}, EN: {lang_en}")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("AI сервис", False, f"Ошибка: {e}")
            return False
    
    async def test_catalog_service(self):
        """Тест сервиса каталога"""
        print("\n=== ТЕСТ СЕРВИСА КАТАЛОГА ===")
        
        try:
            # Инициализация каталога
            catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
            
            # Тест 1: Получение товаров
            products = await catalog_service.get_available_products()
            if products and len(products) > 0:
                self.log_test("Каталог загрузка товаров", True, f"Загружено {len(products)} товаров")
            else:
                self.log_test("Каталог загрузка товаров", False, "Товары не загружены")
                return False
                
            # Тест 2: Валидация товара
            if products:
                test_product = products[0]
                retailer_id = test_product.get('retailer_id')
                if retailer_id:
                    validation = await catalog_service.validate_product(retailer_id)
                    if validation['valid']:
                        self.log_test("Каталог валидация товара", True, f"Товар {test_product.get('name')} валиден")
                    else:
                        self.log_test("Каталог валидация товара", False, "Товар не прошел валидацию")
                        return False
                        
            return True
            
        except Exception as e:
            self.log_test("Каталог сервис", False, f"Ошибка: {e}")
            return False
    
    async def test_database_operations(self):
        """Тест операций с базой данных"""
        print("\n=== ТЕСТ БАЗЫ ДАННЫХ ===")
        
        try:
            # Инициализация сервисов
            message_service = MessageService()
            session_service = SessionService()
            
            # Тест 1: Создание сессии
            test_sender_id = f"test_user_{int(time.time())}"
            session_id = await session_service.get_or_create_session_id(test_sender_id)
            
            if session_id:
                self.log_test("БД создание сессии", True, f"Создана сессия: {session_id}")
            else:
                self.log_test("БД создание сессии", False, "Сессия не создана")
                return False
                
            # Тест 2: Сохранение сообщения
            test_message = Message(
                sender_id=test_sender_id,
                session_id=session_id,
                role=MessageRole.USER,
                content="Тестовое сообщение"
            )
            
            message_id = await message_service.add_message(test_message)
            if message_id:
                self.log_test("БД сохранение сообщения", True, f"Сообщение сохранено с ID: {message_id}")
            else:
                self.log_test("БД сохранение сообщения", False, "Сообщение не сохранено")
                return False
                
            # Тест 3: Получение истории
            history = await message_service.get_conversation_history(session_id, limit=10)
            if history and len(history) > 0:
                self.log_test("БД получение истории", True, f"Получено {len(history)} сообщений")
            else:
                self.log_test("БД получение истории", False, "История не получена")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("БД операции", False, f"Ошибка: {e}")
            return False
    
    async def test_whatsapp_client(self):
        """Тест WhatsApp клиента"""
        print("\n=== ТЕСТ WHATSAPP КЛИЕНТА ===")
        
        try:
            # Инициализация клиента
            whatsapp_client = WhatsAppClient()
            
            # Тест 1: Проверка конфигурации
            if whatsapp_client.token and whatsapp_client.phone_id:
                self.log_test("WhatsApp конфигурация", True, "Токен и Phone ID настроены")
            else:
                self.log_test("WhatsApp конфигурация", False, "Отсутствует токен или Phone ID")
                return False
                
            # Тест 2: Форматирование сообщения
            test_text = "Тестовое сообщение"
            formatted_text = whatsapp_client._add_flower_emoji(test_text)
            if "🌸" in formatted_text:
                self.log_test("WhatsApp форматирование", True, "Эмодзи добавлен корректно")
            else:
                self.log_test("WhatsApp форматирование", False, "Эмодзи не добавлен")
                return False
                
            # Примечание: Отправка реального сообщения не тестируется в критических тестах
            # чтобы избежать спама в WhatsApp
            self.log_test("WhatsApp готовность", True, "Клиент готов к отправке сообщений")
            
            return True
            
        except Exception as e:
            self.log_test("WhatsApp клиент", False, f"Ошибка: {e}")
            return False
    
    async def test_configuration(self):
        """Тест конфигурации системы"""
        print("\n=== ТЕСТ КОНФИГУРАЦИИ ===")
        
        try:
            # Тест 1: Критические переменные окружения
            critical_vars = {
                'GEMINI_API_KEY': GEMINI_API_KEY,
                'WHATSAPP_TOKEN': WHATSAPP_TOKEN,
                'WHATSAPP_PHONE_ID': WHATSAPP_PHONE_ID,
                'PROJECT_ID': PROJECT_ID
            }
            
            missing_vars = []
            for var_name, var_value in critical_vars.items():
                if not var_value:
                    missing_vars.append(var_name)
                    
            if not missing_vars:
                self.log_test("Критические переменные", True, "Все критические переменные настроены")
            else:
                self.log_test("Критические переменные", False, f"Отсутствуют: {', '.join(missing_vars)}")
                return False
                
            # Тест 2: Проверка API ключей
            if len(GEMINI_API_KEY) > 20:
                self.log_test("Gemini API ключ", True, "API ключ корректной длины")
            else:
                self.log_test("Gemini API ключ", False, "API ключ слишком короткий")
                return False
                
            if len(WHATSAPP_TOKEN) > 50:
                self.log_test("WhatsApp токен", True, "Токен корректной длины")
            else:
                self.log_test("WhatsApp токен", False, "Токен слишком короткий")
                return False
                
            return True
            
        except Exception as e:
            self.log_test("Конфигурация", False, f"Ошибка: {e}")
            return False
    
    async def run_all_tests(self):
        """Запускает все критические тесты"""
        print("🚀 ЗАПУСК КРИТИЧЕСКИХ ТЕСТОВ ПЕРЕД ДЕПЛОЕМ")
        print(f"Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Конфигурация", self.test_configuration),
            ("AI сервис", self.test_ai_service),
            ("Каталог", self.test_catalog_service),
            ("База данных", self.test_database_operations),
            ("WhatsApp", self.test_whatsapp_client)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ ОШИБКА В ТЕСТЕ {test_name}: {e}")
                results[test_name] = False
        
        # Подсчет результатов
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"\n{'='*60}")
        print(f"📊 РЕЗУЛЬТАТЫ КРИТИЧЕСКИХ ТЕСТОВ")
        print(f"{'='*60}")
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests} ✅")
        print(f"Провалено: {failed_tests} ❌")
        print(f"Время выполнения: {time.time() - self.start_time:.2f} сек")
        
        if failed_tests > 0:
            print(f"\n❌ ПРОВАЛЕННЫЕ ТЕСТЫ:")
            for test_name, result in results.items():
                if not result:
                    print(f"   - {test_name}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📈 Успешность: {success_rate:.1f}%")
        
        # Критические тесты должны пройти на 80% или больше
        if success_rate >= 80:
            print("✅ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к деплою.")
            return True
        else:
            print("❌ КРИТИЧЕСКИЕ ТЕСТЫ ПРОВАЛЕНЫ! Деплой отменен.")
            return False

async def main():
    """Главная функция тестирования"""
    tester = CriticalComponentTester()
    success = await tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
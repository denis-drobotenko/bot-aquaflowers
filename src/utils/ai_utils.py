import re
import json
from typing import List, Optional, Dict, Any, Tuple
from src.models.message import Message

async def format_conversation_for_ai(messages: List, session_id: str = None, sender_id: str = None) -> List[Dict[str, str]]:
    """
    Форматирует историю диалога для AI в формат с ролями для Gemini.
    Возвращает список словарей с полями 'role' и 'content'.
    Поддерживает как объекты Message, так и dict.
    Включает информацию о сохраненных данных заказа.
    """
    formatted = []
    
    # Добавляем информацию о сохраненных данных заказа в начало истории
    if session_id and sender_id:
        try:
            from src.services.order_service import OrderService
            
            order_service = OrderService()
            order_data = await order_service.get_order_data(session_id, sender_id)
            
            if order_data and (order_data.get('items') or order_data.get('delivery_needed') or order_data.get('address')):
                # Формируем сводку сохраненных данных
                saved_info = []
                
                # Информация о товарах
                if order_data.get('items'):
                    for item in order_data['items']:
                        saved_info.append(f"Выбран букет: {item.get('bouquet', 'Неизвестно')} (цена: {item.get('price', 'Не указана')})")
                
                # Информация о доставке
                if order_data.get('delivery_needed'):
                    saved_info.append("Доставка: нужна")
                    if order_data.get('address'):
                        saved_info.append(f"Адрес: {order_data['address']}")
                    if order_data.get('date'):
                        saved_info.append(f"Дата: {order_data['date']}")
                    if order_data.get('time'):
                        saved_info.append(f"Время: {order_data['time']}")
                
                # Информация об открытке
                if order_data.get('card_needed'):
                    saved_info.append("Открытка: нужна")
                    if order_data.get('card_text'):
                        saved_info.append(f"Текст открытки: {order_data['card_text']}")
                
                # Информация о получателе
                if order_data.get('recipient_name'):
                    saved_info.append(f"Получатель: {order_data['recipient_name']}")
                if order_data.get('recipient_phone'):
                    saved_info.append(f"Телефон получателя: {order_data['recipient_phone']}")
                
                if saved_info:
                    saved_content = "[СОХРАНЕННЫЕ ДАННЫЕ ЗАКАЗА]\n" + "\n".join(saved_info)
                    formatted.append({
                        'role': 'system',
                        'content': saved_content
                    })
        except Exception as e:
            print(f"[AI_UTILS] Ошибка получения данных заказа: {e}")
    
    # Добавляем обычные сообщения
    for message in messages:
        if isinstance(message, dict):
            role = message.get('role', 'assistant')
            content = message.get('content', '')
            if hasattr(role, 'value'):
                role = role.value
        else:
            role = message.role.value if hasattr(message.role, 'value') else str(message.role)
            content = message.content
        formatted.append({
            'role': role,
            'content': content
        })
    return formatted

def validate_ai_response(response_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Валидирует ответ AI и возвращает (is_valid, error_message).
    """
    # Проверяем обязательные поля
    if 'text' not in response_data:
        return False, "Missing 'text' field"
    
    # ВАЖНО: Текст обязателен всегда, даже с командами
    if not response_data.get('text'):
        return False, "Missing or empty 'text' field - text is always required"
    
    # Проверяем переводы (делаем необязательными)
    if 'text_en' not in response_data:
        response_data['text_en'] = str(response_data.get('text', ''))
    if 'text_thai' not in response_data:
        response_data['text_thai'] = str(response_data.get('text', ''))
    
    # Проверяем формат команды
    command = response_data.get('command')
    if command is not None:
        if isinstance(command, str):
            return False, f"Command should be object with 'type' field, got string: '{command}'"
        elif isinstance(command, dict):
            if 'type' not in command:
                return False, "Command object missing 'type' field"
            if not isinstance(command['type'], str):
                return False, "Command 'type' should be string"
        else:
            return False, f"Command should be object or null, got: {type(command)}"
    
    return True, ""

def parse_ai_response(response_text: str) -> Tuple[str, str, str, Optional[Dict[str, Any]]]:
    """
    Парсит ответ AI и извлекает текст на трех языках и команду.
    Всегда возвращает все три поля. Все переносы строк заменяет на двойной слэш (\\n).
    Returns:
        Tuple[str, str, str, Optional[Dict]]: (text, text_en, text_thai, command)
    """
    def fix_newlines(s: str) -> str:
        if not s:
            return ''
        # Заменяем все реальные переносы на \\n
        s = s.replace('\r\n', '\\n').replace('\r', '\\n')
        s = s.replace('\n', '\\n')
        s = s.replace('\u2028', '\\n').replace('\u2029', '\\n')
        return s
    
    def preprocess_json_string(json_str: str) -> str:
        """
        Предобрабатывает JSON строку, экранируя реальные переносы строк в строковых значениях
        """
        import re
        # Находим все строковые значения в JSON и экранируем в них переносы строк
        def replace_newlines_in_string(match):
            content = match.group(1)
            # Заменяем все реальные переносы на \\n
            content = content.replace('\n', '\\n').replace('\r', '\\r')
            return f'"{content}"'
        
        # Паттерн для поиска строковых значений в JSON (улучшенный)
        pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"'
        return re.sub(pattern, replace_newlines_in_string, json_str)
    
    try:
        response_text = response_text.strip()
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                fixed = fix_newlines(response_text)
                return fixed, fixed, fixed, None
        
        json_str = json_str.strip()
        # Предобрабатываем JSON, экранируя переносы строк в строковых значениях
        json_str = preprocess_json_string(json_str)
        
        response_data = json.loads(json_str)
        
        # Валидируем ответ
        is_valid, error_msg = validate_ai_response(response_data)
        if not is_valid:
            print(f"[AI_VALIDATION] Invalid response: {error_msg}")
            print(f"[AI_VALIDATION] Response data: {response_data}")
            # Возвращаем None для команды, чтобы вызвать повторный запрос
            text = fix_newlines(response_data.get('text', ''))
            text_en = fix_newlines(response_data.get('text_en', text))
            text_thai = fix_newlines(response_data.get('text_thai', text))
            return text, text_en, text_thai, None
        
        text = fix_newlines(response_data.get('text', ''))
        text_en = fix_newlines(response_data.get('text_en', text))
        text_thai = fix_newlines(response_data.get('text_thai', text))
        command = response_data.get('command')
        
        print(f"[AI_PARSE] Parsed text: '{text}'")
        print(f"[AI_PARSE] Parsed text_en: '{text_en}'")
        print(f"[AI_PARSE] Parsed text_thai: '{text_thai}'")
        print(f"[AI_PARSE] Parsed command: {command}")
        
        # Возвращаем результат даже если text пустой (для команд)
        return text, text_en, text_thai, command
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"JSON string: {json_str}")
        fixed = fix_newlines(response_text)
        return fixed, fixed, fixed, None
    except Exception as e:
        print(f"Parse error: {e}")
        fixed = fix_newlines(response_text)
        return fixed, fixed, fixed, None

def get_fallback_text(user_lang: str) -> str:
    """
    Возвращает fallback-ответ в зависимости от языка.
    """
    if user_lang == 'en':
        return "How can I help you today? 🌸"
    elif user_lang == 'th':
        return "ฉันสามารถช่วยคุณได้อย่างไรวันนี้? 🌸"
    return "Чем могу помочь сегодня? 🌸"

def get_contextual_fallback_text(user_lang: str, context: str = None) -> str:
    """
    Возвращает контекстный fallback-ответ в зависимости от ситуации.
    """
    if context == "catalog_requested":
        if user_lang == 'en':
            return "Let me show you our flower catalog! 🌸"
        elif user_lang == 'th':
            return "ให้ฉันแสดงแคตตาล็อกดอกไม้ของเรา! 🌸"
        return "Покажу вам наш каталог цветов! 🌸"
    
    elif context == "order_info":
        if user_lang == 'en':
            return "I'll help you with your order! 🌸"
        elif user_lang == 'th':
            return "ฉันจะช่วยคุณกับคำสั่งซื้อ! 🌸"
        return "Помогу вам с заказом! 🌸"
    
    # Общий fallback
    return get_fallback_text(user_lang)

def format_catalog_for_ai(products: List[Dict[str, Any]]) -> str:
    """
    Форматирует каталог для передачи в AI.
    """
    if not products:
        return "Каталог временно недоступен."
    
    catalog_text = "АКТУАЛЬНЫЙ КАТАЛОГ ЦВЕТОВ ИЗ WABA\n\n"
    for i, product in enumerate(products, 1):
        name = product.get('name', 'Без названия')
        price = product.get('price', 'Цена не указана')
        retailer_id = product.get('retailer_id', '')
        catalog_text += f"{i}. {name} (ID: {retailer_id})\n   Цена: {price}\n"
    
    catalog_text += "ВАЖНО: Используй ТОЛЬКО эти товары! Не выдумывай названия!"
    return catalog_text 
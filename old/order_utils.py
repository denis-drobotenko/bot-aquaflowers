"""
Утилиты для обработки заказов
"""

import logging
import re
import httpx
from .config import WHATSAPP_TOKEN, WHATSAPP_CATALOG_ID
from typing import List, Dict, Any, Tuple
# Удален импорт catalog_utils - теперь используется только WABA каталог
from . import config
from . import database
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
import os
from datetime import datetime

logger = logging.getLogger(__name__)

line_bot_api = LineBotApi(config.LINE_ACCESS_TOKEN)

def validate_order_completeness(order_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Проверяет, все ли необходимые поля для заказа заполнены."""
    
    required_fields = ["bouquet", "date", "time"]
    missing_fields = [field for field in required_fields if not order_data.get(field)]
    
    return not missing_fields, missing_fields

def extract_order_summary_from_history(history):
    """Извлекает данные заказа из истории диалога"""
    order_data = {
        'bouquet': '-',
        'date': '-',
        'time': '-',
        'address': '-',
        'card': '-',
        'recipient_name': '-',
        'recipient_phone': '-',
        'paid': 'No',
        'retailer_id': '-',
    }
    wa_name = None
    last_bouquet_info = None  # Сохраняем последнюю информацию о букете
    
    for message in history:
        content = message.get('content', '')
        role = message.get('role', '')
        
        # Имя клиента из системного сообщения
        if role == 'system' and '[INFO] Имя клиента:' in content:
            wa_name = content.split(':', 1)[-1].strip()
        
        # Выбранный букет из системного сообщения (приоритет)
        if role == 'system' and '[INFO] выбранный букет:' in content:
            bouquet_match = re.search(r'выбранный букет:\s*([^(]+)', content)
            if bouquet_match:
                order_data['bouquet'] = bouquet_match.group(1).strip()
                last_bouquet_info = order_data['bouquet']
            retailer_match = re.search(r'retailer_id:\s*([^)]+)', content)
            if retailer_match:
                order_data['retailer_id'] = retailer_match.group(1).strip()
        
        # Букет из текстовых сообщений пользователя (если нет системного)
        if role == 'user' and order_data['bouquet'] == '-':
            # Ищем "Я выбираю: название букета"
            choose_match = re.search(r'я выбираю:\s*([^.]+)', content, re.IGNORECASE)
            if choose_match:
                order_data['bouquet'] = choose_match.group(1).strip()
                last_bouquet_info = order_data['bouquet']
            else:
                # Ищем просто название букета
                bouquet = re.search(r'букет[\s:]*([\w\s\-]+)', content, re.IGNORECASE) or re.search(r'Bouquet[\s:]*([\w\s\-]+)', content)
                if bouquet:
                    order_data['bouquet'] = bouquet.group(1).strip()
                    last_bouquet_info = order_data['bouquet']
        
        # Адрес - улучшенный поиск
        address = re.search(r'адрес[\s:]*([\w\s,\-]+)', content, re.IGNORECASE) or re.search(r'Delivery address[\s:]*([\w\s,\-]+)', content) or re.search(r'по адресу\s+([\w\s,\-]+)', content, re.IGNORECASE)
        if address:
            order_data['address'] = address.group(1).strip()
        
        # Дата - улучшенный поиск
        date = re.search(r'(\d{1,2}\.\d{1,2}\.\d{4})', content) or re.search(r'(\d{4}-\d{2}-\d{2})', content) or re.search(r'к\s+(\d{1,2}\.\d{1,2}\.\d{4})', content)
        if date:
            order_data['date'] = date.group(1).strip()
        
        # Время - улучшенный поиск
        time = re.search(r'(\d{1,2}:\d{2})', content) or re.search(r'(\d{1,2}\s+\d{1,2})', content)
        if time:
            order_data['time'] = time.group(1).strip()
        
        # Текст открытки - улучшенный поиск
        card = re.search(r'открытка[\s:]*"([^"]+)"', content, re.IGNORECASE) or re.search(r'Открытка[\s:]*"([^"]+)"', content) or re.search(r'"([^"]+)"', content)
        if card and card.group(1).strip() and order_data['card'] == '-':
            order_data['card'] = card.group(1).strip()
        
        # Имя получателя - улучшенный поиск (приоритет получателю, а не клиенту)
        name = re.search(r'Получатель[\s:]*([\w\s\-]+)', content) or re.search(r'имя[\s:]*([\w\s\-]+)', content, re.IGNORECASE) or re.search(r'Recipient name[\s:]*([\w\s\-]+)', content)
        if name:
            order_data['recipient_name'] = name.group(1).strip()
        
        # Телефон получателя - улучшенный поиск
        phone = re.search(r'(\d{10,15})', content) or re.search(r'(\+?\d[\d\s\-\(\)]+)', content)
        if phone:
            phone_val = phone.group(1).strip()
            if len(re.sub(r'[\s\-\(\)]', '', phone_val)) >= 7:
                order_data['recipient_phone'] = phone_val
        
        # Оплата
        paid = re.search(r'оплачен[\s:]*([\w]+)', content, re.IGNORECASE) or re.search(r'Order paid[\s:]*([\w]+)', content)
        if paid:
            val = paid.group(1).lower()
            order_data['paid'] = 'Yes' if val in ['да', 'yes', 'paid'] else 'No'
    
    # Форматируем телефон
    if order_data['recipient_phone'] != '-':
        phone_clean = re.sub(r'[\s\-\(\)]', '', order_data['recipient_phone'])
        order_data['recipient_phone'] = phone_clean
    
    # Подставляем имя клиента только если нет имени получателя
    if wa_name and order_data['recipient_name'] == '-':
        order_data['recipient_name'] = wa_name
    
    # Если букет не найден, но есть последняя информация о букете, используем её
    if order_data['bouquet'] == '-' and last_bouquet_info:
        order_data['bouquet'] = last_bouquet_info
    
    return order_data

def extract_order_data_from_history(history: List[Dict]) -> Dict:
    """Извлекает данные заказа из истории диалога для function calling"""
    
    order_data = {
        "bouquet": None,
        "date": None,
        "time": None,
        "address": None,
        "recipient_name": None,
        "recipient_phone": None,
        "card": None,
        "delivery_needed": None,
        "card_needed": None
    }
    
    try:
        for message in history:
            if message.get("role") == "system":
                content = message.get("content", "")
                
                # Извлекаем данные из системных сообщений
                if "[INFO] выбранный букет:" in content:
                    bouquet_match = re.search(r'выбранный букет:\s*([^(]+)', content)
                    if bouquet_match:
                        order_data["bouquet"] = bouquet_match.group(1).strip()
                elif "[INFO] дата заказа:" in content:
                    order_data["date"] = content.split(":", 1)[-1].strip()
                elif "[INFO] время заказа:" in content:
                    order_data["time"] = content.split(":", 1)[-1].strip()
                elif "[INFO] адрес доставки:" in content:
                    order_data["address"] = content.split(":", 1)[-1].strip()
                elif "[INFO] имя получателя:" in content:
                    order_data["recipient_name"] = content.split(":", 1)[-1].strip()
                elif "[INFO] телефон получателя:" in content:
                    order_data["recipient_phone"] = content.split(":", 1)[-1].strip()
                elif "[INFO] текст открытки:" in content:
                    order_data["card"] = content.split(":", 1)[-1].strip()
                elif "[INFO] доставка нужна:" in content:
                    order_data["delivery_needed"] = content.split(":", 1)[-1].strip().lower() == "true"
                elif "[INFO] открытка нужна:" in content:
                    order_data["card_needed"] = content.split(":", 1)[-1].strip().lower() == "true"
        
        # Убираем None значения
        order_data = {k: v for k, v in order_data.items() if v is not None}
        
        logger.info(f"[ORDER_DATA] Extracted: {order_data}")
        return order_data
        
    except Exception as e:
        logger.error(f"Error extracting order data: {e}", exc_info=True)
        return {}

def get_conversation_state(history: List[Dict]) -> Dict:
    """Определяет состояние диалога на основе истории."""
    
    state = {
        "client_name_known": False,
        "catalog_sent": False,
        "bouquet_selected": False,
        "date_time_confirmed": False,
        "delivery_info_complete": False,
        "card_info_complete": False,
        "order_confirmed": False
    }
    
    for msg in history:
        content = msg.get("content", "")
        if "Имя клиента:" in content:
            state["client_name_known"] = True
        if "Каталог был отправлен" in content:
            state["catalog_sent"] = True
        if "выбранный букет:" in content:
            state["bouquet_selected"] = True
        if "дата заказа:" in content and "время заказа:" in content:
            state["date_time_confirmed"] = True
        if "адрес доставки:" in content:
            state["delivery_info_complete"] = True
        if "текст открытки:" in content:
            state["card_info_complete"] = True
        if "заказ подтвержден" in content:
            state["order_confirmed"] = True
            
    return state

def determine_next_action(history: list, user_message: str) -> str:
    """Определяет следующее действие на основе истории и сообщения пользователя"""
    
    try:
        state = get_conversation_state(history)
        user_message_lower = user_message.lower()
        
        # Если каталог не отправлен и пользователь спрашивает про букеты
        if not state["catalog_sent"] and any(word in user_message_lower for word in ["букет", "каталог", "что есть", "показать"]):
            return "send_catalog"
        
        # Если букет выбран, но не задан вопрос о дате
        if state["bouquet_selected"] and not state["date_time_confirmed"]:
            return "ask_for_date"
        
        # Если дата указана, но не задан вопрос о времени
        if state["date_time_confirmed"] and not state["date_time_confirmed"]:
            return "ask_for_time"
        
        # Если время указано, но не задан вопрос об адресе
        if state["date_time_confirmed"] and not state["delivery_info_complete"]:
            return "ask_for_address"
        
        # Если адрес указан, но не задан вопрос о получателе
        if state["delivery_info_complete"] and not state["card_info_complete"]:
            return "ask_for_recipient"
        
        # Если получатель указан, но не задан вопрос об открытке
        if state["card_info_complete"] and not state["order_confirmed"]:
            return "ask_for_card"
        
        # Если все данные собраны, предлагаем подтвердить заказ
        if all([state["bouquet_selected"], state["date_time_confirmed"], state["delivery_info_complete"], state["card_info_complete"]]):
            return "confirm_order"
        
        return "continue_conversation"
        
    except Exception as e:
        logger.error(f"Error determining next action: {e}", exc_info=True)
        return "continue_conversation"

async def get_bouquet_photo_url(retailer_id):
    """Получает URL фото букета по retailer_id"""
    if not retailer_id:
        return None
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    product_url = f"https://graph.facebook.com/v20.0/{WHATSAPP_CATALOG_ID}/products"
    filter_str = f'{{"retailer_id":{{"eq":"{retailer_id}"}}}}'
    params = {"fields": "image_url", "filter": filter_str}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(product_url, headers=headers, params=params)
            response.raise_for_status()
            products = response.json().get("data", [])
            if products and products[0].get("image_url"):
                return products[0]["image_url"]
    except Exception as e:
        logger.error(f"Не удалось получить фото букета: {e}")
    return None

async def get_product_details_by_retailer_id(retailer_id: str):
    """Получает детали продукта из каталога по retailer_id"""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    product_url = f"https://graph.facebook.com/v20.0/{WHATSAPP_CATALOG_ID}/products"
    # The filter needs to be a JSON string
    filter_str = f'{{"retailer_id":{{"eq":"{retailer_id}"}}}}'
    params = {"fields": "name,retailer_id", "filter": filter_str}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(product_url, headers=headers, params=params)
            response.raise_for_status()
            products = response.json().get("data", [])
            
            if products:
                product = products[0]
                logger.info(f"Found product match for retailer_id {retailer_id}: {product.get('name')}")
                return product
            else:
                logger.warning(f"No product found for retailer_id: {retailer_id}")
                return None
    except Exception as e:
        logger.error(f"Error getting product details: {e}")
        return None

def validate_order_completeness_new(session_id: str) -> dict:
    """
    Проверяет полноту данных заказа и возвращает статус валидации.
    
    Returns:
        dict: {
            'complete': bool,
            'missing_fields': list,
            'order_data': dict,
            'warnings': list
        }
    """
    from . import database
    
    # Получаем историю сообщений
    # Извлекаем sender_id из session_id
    sender_id = session_id.split('_')[0] if '_' in session_id else session_id
    history = database.get_conversation_history(sender_id, session_id)
    
    # Извлекаем данные заказа из системных сообщений
    order_data = {}
    for msg in history:
        if msg.get('role') == 'system' and msg.get('content', '').startswith('order_info:'):
            try:
                key, value = msg['content'].split(':', 1)[1].split('=', 1)
                order_data[key] = value
            except ValueError:
                continue
    
    # Определяем обязательные поля
    required_fields = {
        'bouquet': 'Букет',
        'date': 'Дата доставки', 
        'time': 'Время доставки',
        'delivery_needed': 'Нужна ли доставка',
        'address': 'Адрес доставки',
        'card_needed': 'Нужна ли открытка',
        'card_text': 'Текст открытки'
    }
    
    missing_fields = []
    warnings = []
    
    # Проверяем обязательные поля
    for field, field_name in required_fields.items():
        if field not in order_data or not order_data[field]:
            missing_fields.append(field_name)
    
    # Проверяем дату доставки
    if 'date' in order_data:
        try:
            # Пытаемся парсить дату
            delivery_date = parse_delivery_date_new(order_data['date'])
            if delivery_date:
                # Проверяем, не слишком ли далеко в будущем
                from datetime import datetime
                days_diff = (delivery_date - datetime.now()).days
                if days_diff > 30:
                    warnings.append(f"Дата доставки {order_data['date']} очень далеко в будущем ({days_diff} дней)")
                elif days_diff < 0:
                    warnings.append(f"Дата доставки {order_data['date']} в прошлом")
        except Exception as e:
            warnings.append(f"Не удалось проверить дату доставки: {e}")
    
    # Проверяем адрес доставки
    if order_data.get('delivery_needed') == 'True' and not order_data.get('address'):
        missing_fields.append('Адрес доставки')
    
    # Проверяем открытку
    if order_data.get('card_needed') == 'True' and not order_data.get('card_text'):
        missing_fields.append('Текст открытки')
    
    return {
        'complete': len(missing_fields) == 0,
        'missing_fields': missing_fields,
        'order_data': order_data,
        'warnings': warnings
    }

def parse_delivery_date_new(date_str: str):
    """
    Парсит строку даты доставки в datetime объект.
    
    Args:
        date_str: Строка с датой (например, "15 декабря", "завтра", "1 июля")
    
    Returns:
        datetime | None: Объект даты или None если не удалось распарсить
    """
    try:
        # Текущая дата
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # Обработка относительных дат
        if date_str.lower() == 'завтра':
            return now + timedelta(days=1)
        elif date_str.lower() == 'послезавтра':
            return now + timedelta(days=2)
        elif 'через' in date_str.lower() and 'день' in date_str.lower():
            # Извлекаем количество дней
            days_match = re.search(r'(\d+)', date_str)
            if days_match:
                days = int(days_match.group(1))
                return now + timedelta(days=days)
        
        # Обработка конкретных дат
        # Пытаемся парсить даты вида "15 декабря", "1 июля" и т.д.
        month_names = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }
        
        for month_name, month_num in month_names.items():
            if month_name in date_str.lower():
                # Извлекаем день
                day_match = re.search(r'(\d+)', date_str)
                if day_match:
                    day = int(day_match.group(1))
                    year = now.year
                    
                    # Если месяц уже прошел в этом году, берем следующий год
                    if month_num < now.month:
                        year += 1
                    
                    return datetime(year, month_num, day)
        
        return None
        
    except Exception as e:
        logger.error(f"Error parsing date '{date_str}': {e}")
        return None

def get_order_summary_new(order_data: dict) -> str:
    """
    Формирует читаемое резюме заказа для пользователя.
    
    Args:
        order_data: Словарь с данными заказа
    
    Returns:
        str: Текстовое резюме заказа
    """
    summary_parts = []
    
    # Букет
    if order_data.get('bouquet'):
        summary_parts.append(f"**Букет:** {order_data['bouquet']}")
    
    # Дата и время
    if order_data.get('date') and order_data.get('time'):
        summary_parts.append(f"**Дата доставки:** {order_data['date']}")
        summary_parts.append(f"**Время доставки:** {order_data['time']}")
    
    # Доставка
    if order_data.get('delivery_needed') == 'True':
        summary_parts.append("**Доставка:** Да")
        if order_data.get('address'):
            summary_parts.append(f"**Адрес:** {order_data['address']}")
    else:
        summary_parts.append("**Доставка:** Нет")
    
    # Открытка
    if order_data.get('card_needed') == 'True':
        summary_parts.append("**Открытка:** Да")
        if order_data.get('card_text'):
            summary_parts.append(f"**Текст:** \"{order_data['card_text']}\"")
    else:
        summary_parts.append("**Открытка:** Нет")
    
    return "\n".join(summary_parts)

def get_next_required_field(order_data: dict) -> str | None:
    """
    Определяет следующее обязательное поле для заполнения.
    
    Args:
        order_data: Словарь с данными заказа
    
    Returns:
        str | None: Название следующего поля или None если все заполнено
    """
    if not order_data.get('bouquet'):
        return 'bouquet'
    if not order_data.get('date') or not order_data.get('time'):
        return 'date_time'
    if not order_data.get('delivery_needed'):
        return 'delivery_needed'
    if order_data.get('delivery_needed') == 'True' and not order_data.get('address'):
        return 'address'
    if not order_data.get('card_needed'):
        return 'card_needed'
    if order_data.get('card_needed') == 'True' and not order_data.get('card_text'):
        return 'card_text'
    
    return None

async def send_order_to_line(sender_id: str, session_id: str, order_details: dict) -> str:
    """
    Отправляет заказ в Line в формате: английский и тайский текст, без HTML.
    """
    try:
        bouquet = order_details.get('bouquet', '-')
        address = order_details.get('address', '-')
        date = order_details.get('date', '-')
        time = order_details.get('time', '-')
        card_text = order_details.get('card_text', '-')
        recipient_name = order_details.get('recipient_name', '-')
        recipient_phone = order_details.get('recipient_phone', '-')
        paid = order_details.get('paid', 'No')
        # ENGLISH
        order_en = f"NEW ORDER CONFIRMED!\n\nBouquet: {bouquet.replace('🌸', '')}\nDelivery address: {address}\nDelivery date: {date}\nDelivery time: {time}\nCard text: {card_text}\nRecipient name: {recipient_name}\nRecipient phone: {recipient_phone}\nOrder paid: {paid}\n"
        # THAI (пример перевода, можно заменить на актуальный)
        order_th = f"\nคำสั่งซื้อใหม่ได้รับการยืนยัน!\n\nช่อดอกไม้: {bouquet.replace('🌸', '')}\nที่อยู่จัดส่ง: {address}\nวันที่จัดส่ง: {date}\nเวลาจัดส่ง: {time}\nข้อความการ์ด: {card_text}\nชื่อผู้รับ: {recipient_name}\nเบอร์โทรศัพท์ผู้รับ: {recipient_phone}\nชำระเงินแล้ว: {'ใช่' if paid.lower() == 'yes' else 'ไม่'}\n"
        now = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        status = f"Status: Order confirmed by customer\nTime: {now}"
        status_th = f"สถานะ: ลูกค้ายืนยันคำสั่งซื้อแล้ว\nเวลา: {now}"
        chat_link = f"Conversation link: https://auraflora-bot-xicvc2y5hq-as.a.run.app/chat/{session_id}"
        chat_link_th = f"ลิงก์การสนทนา: https://auraflora-bot-xicvc2y5hq-as.a.run.app/chat/{session_id}"
        order_summary = f"{order_en}\n{order_th}\n{status}\n{status_th}\n\n{chat_link}\n{chat_link_th}"
        
        # Проверяем, что сообщение не пустое
        if order_summary.strip():
            line_bot_api.push_message(config.LINE_GROUP_ID, TextSendMessage(text=order_summary))
            logger.info(f"Order notification sent to LINE successfully")
            return "ok"
        else:
            logger.error("Order summary is empty, not sending to LINE")
            return "error: empty order summary"
        
    except LineBotApiError as e:
        logger.error(f"LINE API error: {e}")
        return f"Ошибка LINE API: {str(e)}"
    except Exception as e:
        logger.error(f"Failed to send order notification to LINE: {e}")
        return f"Ошибка отправки в LINE: {str(e)}"
        
async def notify_user_order_sent(sender_id: str, session_id: str):
    """Отправляет уведомление пользователю о том, что заказ отправлен"""
    from .whatsapp_utils import send_whatsapp_message
    
    # Проверяем, не было ли уже отправлено уведомление для этой сессии
    notification_key = f"order_notification_sent_{session_id}"
    
    # Используем простую проверку через логирование
    logger.info(f"[ORDER_NOTIFICATION] Sending notification to {sender_id} for session {session_id}")
    
    message = "Ваш заказ отправлен! Ожидайте, менеджер свяжется с вами для оплаты. 🌸"
    await send_whatsapp_message(sender_id, message, sender_id, session_id)
    
    logger.info(f"[ORDER_NOTIFICATION] Notification sent successfully to {sender_id}")

def format_chat_history_html(chat_history: dict, language: str) -> str:
    """Форматирует историю чата в HTML для указанного языка"""
    if not chat_history or 'messages' not in chat_history:
        return "<p>История переписки недоступна</p>"
    
    messages = chat_history['messages']
    html_parts = []
    
    for msg in messages:
        # Получаем текст на нужном языке
        content = msg.get(f'content_{language}', msg.get('content_original', 'Текст недоступен'))
        role = msg.get('role', 'unknown')
        timestamp = msg.get('timestamp', '')
        
        # Форматируем время
        try:
            if timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            else:
                time_str = ''
        except:
            time_str = ''
        
        # Определяем класс сообщения
        message_class = 'user' if role == 'user' else 'bot'
        
        html_parts.append(f"""
            <div class="message {message_class}">
                <div>{escape_html(content)}</div>
                {f'<div class="message-time">{time_str}</div>' if time_str else ''}
            </div>
        """)
    
    return ''.join(html_parts) if html_parts else "<p>Нет сообщений</p>"

def escape_html(text: str) -> str:
    """Экранирует HTML символы"""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')

def format_order_details(order_details: dict, language: str) -> str:
    """Форматирует детали заказа на указанном языке"""
    if language == 'ru':
        summary_parts = []
        
        # Букет
        if order_details.get('bouquet'):
            summary_parts.append(f"**Букет:** {order_details['bouquet']}")
        
        # Дата и время
        if order_details.get('date') and order_details.get('time'):
            summary_parts.append(f"**Дата доставки:** {order_details['date']}")
            summary_parts.append(f"**Время доставки:** {order_details['time']}")
        
        # Доставка
        if order_details.get('delivery_needed') == 'True':
            summary_parts.append("**Доставка:** Да")
            if order_details.get('address'):
                summary_parts.append(f"**Адрес:** {order_details['address']}")
        else:
            summary_parts.append("**Доставка:** Нет")
        
        # Открытка
        if order_details.get('card_needed') == 'True':
            summary_parts.append("**Открытка:** Да")
            if order_details.get('card_text'):
                summary_parts.append(f"**Текст:** \"{order_details['card_text']}\"")
        else:
            summary_parts.append("**Открытка:** Нет")
        
        return "\n".join(summary_parts)
    
    elif language == 'en':
        summary_parts = []
        
        # Bouquet
        if order_details.get('bouquet'):
            summary_parts.append(f"**Bouquet:** {order_details['bouquet']}")
        
        # Date and time
        if order_details.get('date') and order_details.get('time'):
            summary_parts.append(f"**Delivery date:** {order_details['date']}")
            summary_parts.append(f"**Delivery time:** {order_details['time']}")
        
        # Delivery
        if order_details.get('delivery_needed') == 'True':
            summary_parts.append("**Delivery:** Yes")
            if order_details.get('address'):
                summary_parts.append(f"**Address:** {order_details['address']}")
        else:
            summary_parts.append("**Delivery:** No")
        
        # Card
        if order_details.get('card_needed') == 'True':
            summary_parts.append("**Card:** Yes")
            if order_details.get('card_text'):
                summary_parts.append(f"**Text:** \"{order_details['card_text']}\"")
        else:
            summary_parts.append("**Card:** No")
        
        return "\n".join(summary_parts)
    
    elif language == 'th':
        summary_parts = []
        
        # ช่อดอกไม้
        if order_details.get('bouquet'):
            summary_parts.append(f"**ช่อดอกไม้:** {order_details['bouquet']}")
        
        # วันที่และเวลา
        if order_details.get('date') and order_details.get('time'):
            summary_parts.append(f"**วันที่จัดส่ง:** {order_details['date']}")
            summary_parts.append(f"**เวลาจัดส่ง:** {order_details['time']}")
        
        # การจัดส่ง
        if order_details.get('delivery_needed') == 'True':
            summary_parts.append("**การจัดส่ง:** ใช่")
            if order_details.get('address'):
                summary_parts.append(f"**ที่อยู่:** {order_details['address']}")
        else:
            summary_parts.append("**การจัดส่ง:** ไม่")
        
        # การ์ด
        if order_details.get('card_needed') == 'True':
            summary_parts.append("**การ์ด:** ใช่")
            if order_details.get('card_text'):
                summary_parts.append(f"**ข้อความ:** \"{order_details['card_text']}\"")
        else:
            summary_parts.append("**การ์ด:** ไม่")
        
        return "\n".join(summary_parts)
    
    else:
        # Fallback to Russian
        return format_order_details(order_details, 'ru') 
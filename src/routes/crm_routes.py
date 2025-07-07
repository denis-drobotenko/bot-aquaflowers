"""
Роуты для мини CRM системы
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from src.services.order_service import OrderService
from src.services.session_service import SessionService
from src.services.user_service import UserService
from src.models.order import OrderStatus
from datetime import datetime, timedelta
from typing import Dict, List, Any
import html
from google.cloud import firestore

def get_status_text(status: str) -> str:
    """Returns order status text in English"""
    status_map = {
        'draft': 'Draft',
        'incomplete': 'Incomplete',
        'ready': 'Ready',
        'confirmed': 'Confirmed',
        'sent_to_operator': 'Sent to Operator',
        'cancelled': 'Cancelled'
    }
    return status_map.get(status, status)

def format_date(date_str: str) -> str:
    """Форматирует дату для отображения"""
    if not date_str:
        return 'Не указана'
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return date_str

def get_time_periods() -> Dict[str, Dict[str, datetime]]:
    """Возвращает временные периоды для группировки"""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=7)
    
    return {
        "today": {"start": today_start, "end": now},
        "yesterday": {"start": yesterday_start, "end": today_start},
        "last_week": {"start": week_start, "end": yesterday_start}
    }

def group_orders_by_time(orders: List[Dict]) -> Dict[str, Dict[str, List[Dict]]]:
    """Группирует заказы по времени и статусу"""
    periods = get_time_periods()
    grouped = {
        "today": {"incomplete": [], "completed": []},
        "yesterday": {"incomplete": [], "completed": []},
        "last_week": {"incomplete": [], "completed": []}
    }
    
    for order in orders:
        created_at = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
        
        # Определяем период
        period = None
        if periods["today"]["start"] <= created_at <= periods["today"]["end"]:
            period = "today"
        elif periods["yesterday"]["start"] <= created_at <= periods["yesterday"]["end"]:
            period = "yesterday"
        elif periods["last_week"]["start"] <= created_at <= periods["last_week"]["end"]:
            period = "last_week"
        
        if period:
            # Определяем статус
            status = order['status']
            if status in ['draft', 'incomplete', 'ready', 'sent_to_operator']:
                grouped[period]["incomplete"].append(order)
            elif status in ['confirmed', 'cancelled']:
                grouped[period]["completed"].append(order)
    
    return grouped

def group_orders_by_status(orders: List[Dict]) -> Dict[str, List[Dict]]:
    """Группирует заказы по статусам"""
    grouped = {}
    
    for order in orders:
        status = order['status']
        if status not in grouped:
            grouped[status] = []
        grouped[status].append(order)
    
    return grouped

router = APIRouter(prefix="/crm", tags=["crm"])

# Инициализируем сервисы
order_service = OrderService()
session_service = SessionService()
user_service = UserService()

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def crm_dashboard(request: Request):
    """Главная страница мини CRM"""
    try:
        # Получаем все заказы через правильные методы OrderService
        try:
            all_orders = await order_service.get_all_orders_for_crm()
        except Exception as e:
            print(f"Ошибка при получении заказов: {e}")
            all_orders = []
        
        # Группируем по времени
        time_grouped = group_orders_by_time(all_orders)
        
        # Группируем по клиентам через правильный метод
        try:
            customer_grouped = await order_service.get_customer_orders_summary()
        except Exception as e:
            print(f"Ошибка при получении сводки клиентов: {e}")
            customer_grouped = {"with_orders": [], "without_orders": []}
        
        # Группируем по статусам
        status_grouped = group_orders_by_status(all_orders)
        
        return templates.TemplateResponse(
            "crm_dashboard.html",
            {
                "request": request,
                "time_grouped": time_grouped,
                "customer_grouped": customer_grouped,
                "status_grouped": status_grouped,
                "total_orders": len(all_orders),
                "createOrderCard": createOrderCard,
                "createCustomerCard": createCustomerCard,
                "getStatusText": get_status_text
            }
        )
    except Exception as e:
        print(f"Ошибка в CRM dashboard: {e}")
        # Возвращаем страницу с пустыми данными
        return templates.TemplateResponse(
            "crm_dashboard.html",
            {
                "request": request,
                "time_grouped": {
                    "today": {"incomplete": [], "completed": []},
                    "yesterday": {"incomplete": [], "completed": []},
                    "last_week": {"incomplete": [], "completed": []}
                },
                "customer_grouped": {"with_orders": [], "without_orders": []},
                "status_grouped": {},
                "total_orders": 0,
                "createOrderCard": createOrderCard,
                "createCustomerCard": createCustomerCard,
                "getStatusText": get_status_text
            }
        )

@router.get("/order/{sender_id}/{session_id}", response_class=HTMLResponse)
async def order_details(request: Request, sender_id: str, session_id: str):
    """Страница с подробностями заказа"""
    try:
        # Получаем данные заказа
        print(f"Getting order data for session_id: {session_id}, sender_id: {sender_id}")
        order_data = await order_service.get_order_data(session_id, sender_id)
        
        if not order_data:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Получаем информацию о пользователе
        try:
            user_info = await session_service.get_user_info(order_data['sender_id'])
        except Exception:
            # Если не удалось получить информацию о пользователе, используем данные из заказа
            user_info = {
                'name': order_data.get('customer_name', 'Unknown Customer'),
                'phone': order_data.get('customer_phone', order_data['sender_id'])
            }
        
        return templates.TemplateResponse(
            "order_details.html",
            {
                "request": request,
                "order": order_data,
                "user_info": user_info,
                "get_status_text": get_status_text,
                "format_date": format_date
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading order {session_id} for {sender_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@router.get("/api/orders")
async def get_orders_api():
    """API для получения всех заказов"""
    try:
        # Здесь нужно реализовать получение всех заказов
        # Пока возвращаем пустой список
        return {"orders": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def createOrderCard(order: Dict) -> str:
    """Creates HTML order card in one line"""
    status_class = 'completed' if order['status'] in ['confirmed', 'cancelled'] else 'incomplete'
    
    customer_name = order.get('customer_name', 'Unknown Customer')
    customer_phone = order.get('customer_phone', order['sender_id'])
    status_text = get_status_text(order['status'])
    
    return f"""
        <div class="order-card {status_class}">
            <div class="order-header">
                <div class="customer-info">
                    <div class="customer-name">{customer_name} • {customer_phone}</div>
                </div>
                <div class="order-status status-{order['status']}">{status_text}</div>
                <div class="order-actions">
                    <a href="/crm/order/{order['sender_id']}/{order['session_id']}" class="btn-icon" title="View Order" style="width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; text-decoration: none; transition: all 0.2s;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                    </a>
                    <a href="/chat/history/{order['sender_id']}/{order['session_id']}" class="btn-icon" title="Chat History" style="width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; text-decoration: none; transition: all 0.2s;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    """

def createCustomerCard(customer: Dict) -> str:
    """Creates HTML customer section with collapsible orders like Incomplete Orders section"""
    customer_id = customer['sender_id'].replace('+', '').replace('-', '')
    customer_name = customer.get('name', 'Unknown Customer')
    customer_phone = customer.get('phone', customer['sender_id'])
    total_orders = customer.get('total_orders', 0)
    
    orders_html = ""
    if customer.get('orders'):
        for order in customer['orders']:
            status_class = 'completed' if order['status'] in ['confirmed', 'cancelled'] else 'incomplete'
            status_text = get_status_text(order['status'])
            orders_html += f"""
                <div class="order-card {status_class}">
                    <div class="order-header">
                        <div class="customer-info">
                            <div class="customer-name">Order #{order['order_id'][-8:]}</div>
                        </div>
                        <div class="order-status status-{order['status']}">{status_text}</div>
                        <div class="order-actions">
                            <a href="/crm/order/{order['sender_id']}/{order['session_id']}" class="btn-icon" title="View Order" style="width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; text-decoration: none; transition: all 0.2s;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                                    <circle cx="12" cy="12" r="3"/>
                                </svg>
                            </a>
                            <a href="/chat/history/{order['sender_id']}/{order['session_id']}" class="btn-icon" title="Chat History" style="width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; text-decoration: none; transition: all 0.2s;">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                                </svg>
                            </a>
                        </div>
                    </div>
                </div>
            """
    
    return f"""
        <div class="collapsible-section">
            <div class="collapsible-header" onclick="toggleSection('customer-{customer_id}')">
                <h3>{customer_name} • {customer_phone} • {total_orders} orders</h3>
                <svg class="collapse-icon expanded" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6,9 12,15 18,9"></polyline>
                </svg>
            </div>
            <div id="customer-{customer_id}" class="collapsible-content expanded">
                {orders_html}
            </div>
        </div>
    """ 
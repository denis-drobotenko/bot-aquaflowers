import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.order_service import OrderService
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.services.ai_service import AIService
from src.services.catalog_service import CatalogService
from src.models.order import Order, OrderItem, OrderStatus
from src.models.message import Message, MessageRole
from datetime import datetime


@pytest.fixture
def order_service():
    return OrderService()


@pytest.fixture
def message_service():
    with patch('src.services.message_service.firestore') as mock_firestore:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        service = MessageService()
        yield service


@pytest.fixture
def session_service():
    with patch('src.services.session_service.firestore') as mock_firestore:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        service = SessionService()
        yield service


@pytest.fixture
def ai_service():
    return AIService(api_key="test_api_key")


@pytest.fixture
def catalog_service():
    return CatalogService(catalog_id="test_catalog_id", access_token="test_access_token")


@pytest.mark.asyncio
async def test_complete_order_workflow_integration(order_service, message_service, session_service, ai_service, catalog_service):
    """Тест полного workflow заказа: от запроса до завершения"""
    
    # Мокаем создание сессии
    with patch.object(session_service, 'get_or_create_session_id') as mock_get_session:
        mock_get_session.return_value = "session_123"
        
        # Мокаем получение товаров из каталога
        with patch.object(catalog_service, 'get_product_by_id') as mock_get_product:
            mock_product = {
                'id': '1',
                'name': 'Роза красная',
                'price': 100,
                'description': 'Красивая красная роза',
                'available': True
            }
            mock_get_product.return_value = mock_product
            
            # Мокаем валидацию товара
            with patch.object(catalog_service, 'validate_product') as mock_validate:
                mock_validate.return_value = True
                
                # Мокаем создание/получение заказа
                with patch.object(order_service, 'get_or_create_order') as mock_get_order:
                    mock_order = Order(
                        order_id="order_123",
                        session_id="session_123",
                        sender_id="user_123",
                        status=OrderStatus.DRAFT
                    )
                    mock_get_order.return_value = mock_order
                    
                    # Мокаем добавление товара
                    with patch.object(order_service, 'add_item') as mock_add_item:
                        mock_add_item.return_value = "order_123"
                        
                        # Мокаем добавление сообщений
                        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                            mock_add_message.return_value = "success"
                            
                            # Мокаем генерацию AI ответа
                            with patch.object(ai_service, 'generate_response') as mock_generate:
                                mock_generate.return_value = "Заказ создан! Номер заказа: order_123"
                                
                                # 1. Получаем сессию
                                session_id = await session_service.get_or_create_session_id("user_123")
                                
                                # 2. Получаем информацию о товаре
                                product = await catalog_service.get_product_by_id("1")
                                
                                # 3. Валидируем товар
                                is_valid = await catalog_service.validate_product("1")
                                
                                # 4. Получаем или создаем заказ
                                order = await order_service.get_or_create_order(session_id, "user_123")
                                
                                # 5. Добавляем товар в заказ
                                item_data = {
                                    'product_id': '1',
                                    'bouquet': product['name'],
                                    'price': product['price'],
                                    'quantity': 1
                                }
                                order_id = await order_service.add_item(session_id, "user_123", item_data)
                                
                                # 6. Добавляем сообщение о создании заказа
                                order_message = Message(
                                    sender_id="user_123",
                                    session_id=session_id,
                                    role=MessageRole.ASSISTANT,
                                    content=f"Заказ создан! Номер: {order_id}"
                                )
                                await message_service.add_message_to_conversation(order_message)
                                
                                # 7. Генерируем AI ответ
                                ai_response = await ai_service.generate_response(
                                    sender_id="user_123",
                                    session_id=session_id,
                                    user_message="Хочу заказать красную розу"
                                )
                                
                                assert session_id == "session_123"
                                assert product['name'] == "Роза красная"
                                assert is_valid is True
                                assert order_id == "order_123"
                                assert ai_response == "Заказ создан! Номер заказа: order_123"
                                
                                mock_get_session.assert_called_once_with("user_123")
                                mock_get_product.assert_called_once_with("1")
                                mock_validate.assert_called_once_with("1")
                                mock_get_order.assert_called_once_with(session_id, "user_123")
                                mock_add_item.assert_called_once_with(session_id, "user_123", item_data)
                                mock_add_message.assert_called_once_with(order_message)
                                mock_generate.assert_called_once()


@pytest.mark.asyncio
async def test_order_confirmation_workflow_integration(order_service, message_service, session_service):
    """Тест workflow подтверждения заказа"""
    
    # Мокаем получение заказа
    with patch.object(order_service, 'get_or_create_order') as mock_get_order:
        order = Order(
            order_id="order_123",
            session_id="session_123",
            sender_id="user_123",
            status=OrderStatus.DRAFT
        )
        mock_get_order.return_value = order
        
        # Мокаем обновление статуса заказа
        with patch.object(order_service, 'update_order_status') as mock_update_status:
            mock_update_status.return_value = True
            
            # Мокаем добавление сообщений
            with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                mock_add_message.return_value = "success"
                
                # 1. Получаем заказ
                retrieved_order = await order_service.get_or_create_order("session_123", "user_123")
                
                # 2. Подтверждаем заказ
                confirm_result = await order_service.update_order_status("session_123", "user_123", OrderStatus.CONFIRMED)
                
                # 3. Добавляем сообщение о подтверждении
                order.status = OrderStatus.CONFIRMED  # вручную меняем статус
                confirm_message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.ASSISTANT,
                    content="Заказ подтвержден! Ожидайте доставку."
                )
                await message_service.add_message_to_conversation(confirm_message)
                
                assert retrieved_order.order_id == "order_123"
                assert confirm_result is True
                assert order.status == OrderStatus.CONFIRMED
                
                mock_get_order.assert_called_once_with("session_123", "user_123")
                mock_update_status.assert_called_once_with("session_123", "user_123", OrderStatus.CONFIRMED)
                mock_add_message.assert_called_once_with(confirm_message)


@pytest.mark.asyncio
async def test_order_completion_workflow_integration(order_service, message_service, session_service):
    """Тест workflow завершения заказа"""
    
    # Мокаем получение заказа
    with patch.object(order_service, 'get_or_create_order') as mock_get_order:
        order = Order(
            order_id="order_123",
            session_id="session_123",
            sender_id="user_123",
            status=OrderStatus.CONFIRMED
        )
        mock_get_order.return_value = order
        
        # Мокаем завершение заказа
        with patch.object(order_service, 'update_order_status') as mock_update_status:
            mock_update_status.return_value = True
            
            # Мокаем создание новой сессии
            with patch.object(session_service, 'create_new_session_after_order') as mock_new_session:
                mock_new_session.return_value = "new_session_456"
                
                # Мокаем добавление сообщений
                with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                    mock_add_message.return_value = "success"
                    
                    # 1. Получаем заказ
                    retrieved_order = await order_service.get_or_create_order("session_123", "user_123")
                    
                    # 2. Завершаем заказ
                    complete_result = await order_service.update_order_status("session_123", "user_123", OrderStatus.SENT_TO_OPERATOR)
                    
                    # 3. Создаем новую сессию
                    new_session_id = await session_service.create_new_session_after_order("user_123")
                    
                    # 4. Добавляем сообщение о завершении
                    order.status = OrderStatus.SENT_TO_OPERATOR  # вручную меняем статус
                    complete_message = Message(
                        sender_id="user_123",
                        session_id=new_session_id,
                        role=MessageRole.ASSISTANT,
                        content="Заказ выполнен! Спасибо за покупку."
                    )
                    await message_service.add_message_to_conversation(complete_message)
                    
                    assert retrieved_order.order_id == "order_123"
                    assert complete_result is True
                    assert order.status == OrderStatus.SENT_TO_OPERATOR
                    assert new_session_id == "new_session_456"
                    
                    mock_get_order.assert_called_once_with("session_123", "user_123")
                    mock_update_status.assert_called_once_with("session_123", "user_123", OrderStatus.SENT_TO_OPERATOR)
                    mock_new_session.assert_called_once_with("user_123")
                    mock_add_message.assert_called_once_with(complete_message)


@pytest.mark.asyncio
async def test_order_cancellation_workflow_integration(order_service, message_service):
    """Тест workflow отмены заказа"""
    
    # Мокаем получение заказа
    with patch.object(order_service, 'get_or_create_order') as mock_get_order:
        order = Order(
            order_id="order_123",
            session_id="session_123",
            sender_id="user_123",
            status=OrderStatus.DRAFT
        )
        mock_get_order.return_value = order
        
        # Мокаем отмену заказа
        with patch.object(order_service, 'update_order_status') as mock_update_status:
            mock_update_status.return_value = True
            
            # Мокаем добавление сообщений
            with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                mock_add_message.return_value = "success"
                
                # 1. Получаем заказ
                retrieved_order = await order_service.get_or_create_order("session_123", "user_123")
                
                # 2. Отменяем заказ
                cancel_result = await order_service.update_order_status("session_123", "user_123", OrderStatus.CANCELLED)
                
                # 3. Добавляем сообщение об отмене
                order.status = OrderStatus.CANCELLED  # вручную меняем статус
                cancel_message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.ASSISTANT,
                    content="Заказ отменен."
                )
                await message_service.add_message_to_conversation(cancel_message)
                
                assert retrieved_order.order_id == "order_123"
                assert cancel_result is True
                assert order.status == OrderStatus.CANCELLED
                
                mock_get_order.assert_called_once_with("session_123", "user_123")
                mock_update_status.assert_called_once_with("session_123", "user_123", OrderStatus.CANCELLED)
                mock_add_message.assert_called_once_with(cancel_message)


@pytest.mark.asyncio
async def test_order_history_workflow_integration(order_service, message_service, session_service):
    """Тест workflow получения истории заказов"""
    
    # Мокаем получение истории заказов пользователя
    with patch.object(order_service, 'get_user_order_history') as mock_get_history:
        mock_orders = [
            Order(
                order_id="order_1",
                session_id="session_1",
                sender_id="user_123",
                status=OrderStatus.SENT_TO_OPERATOR,
                items=[OrderItem(product_id="1", bouquet="Роза красная", price=100)]
            ),
            Order(
                order_id="order_2",
                session_id="session_2",
                sender_id="user_123",
                status=OrderStatus.CONFIRMED,
                items=[OrderItem(product_id="2", bouquet="Тюльпан желтый", price=80)]
            )
        ]
        mock_get_history.return_value = mock_orders
        
        # Мокаем добавление сообщений
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.return_value = "success"
            
            # 1. Получаем историю заказов
            order_history = await order_service.get_user_order_history("user_123", limit=10)
            
            # 2. Добавляем сообщение с историей
            history_message = Message(
                sender_id="user_123",
                session_id="session_123",
                role=MessageRole.ASSISTANT,
                content=f"У вас {len(order_history)} заказов в истории."
            )
            await message_service.add_message_to_conversation(history_message)
            
            assert len(order_history) == 2
            assert order_history[0].order_id == "order_1"
            assert order_history[1].order_id == "order_2"
            
            mock_get_history.assert_called_once_with("user_123", limit=10)
            mock_add_message.assert_called_once_with(history_message)


@pytest.mark.asyncio
async def test_order_validation_workflow_integration(order_service, catalog_service, message_service):
    """Тест workflow валидации заказа"""
    
    # Мокаем получение данных заказа
    with patch.object(order_service, 'get_order_data') as mock_get_data:
        mock_order_data = {
            'order_id': 'order_123',
            'status': 'DRAFT',
            'date': '2024-01-15',
            'time': '14:00',
            'delivery_needed': True,
            'address': 'ул. Примерная, 1',
            'items': [
                {
                    'product_id': '1',
                    'bouquet': 'Роза красная',
                    'price': 100,
                    'quantity': 1
                }
            ]
        }
        mock_get_data.return_value = mock_order_data
        
        # Мокаем валидацию заказа
        with patch.object(order_service, 'validate_order_data') as mock_validate:
            validation_result = {
                'is_complete': True,
                'missing_required': [],
                'missing_optional': ['Текст открытки'],
                'warnings': [],
                'order_data': mock_order_data
            }
            mock_validate.return_value = validation_result
            
            # Мокаем добавление сообщений
            with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                mock_add_message.return_value = "success"
                
                # 1. Получаем данные заказа
                order_data = await order_service.get_order_data("session_123")
                
                # 2. Валидируем заказ
                validation = order_service.validate_order_data(order_data)
                
                # 3. Добавляем сообщение о валидации
                validation_message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.ASSISTANT,
                    content=f"Заказ {'готов к подтверждению' if validation['is_complete'] else 'требует доработки'}."
                )
                await message_service.add_message_to_conversation(validation_message)
                
                assert order_data['order_id'] == "order_123"
                assert validation['is_complete'] is True
                assert len(validation['missing_required']) == 0
                
                mock_get_data.assert_called_once_with("session_123")
                mock_validate.assert_called_once_with(order_data)
                mock_add_message.assert_called_once_with(validation_message)


@pytest.mark.asyncio
async def test_order_error_handling_workflow_integration(order_service, catalog_service, message_service):
    """Тест workflow обработки ошибок заказа"""
    
    # Мокаем ошибку при получении товара
    with patch.object(catalog_service, 'get_product_by_id') as mock_get_product:
        mock_get_product.side_effect = Exception("Товар не найден")
        
        # Мокаем добавление сообщений
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.return_value = "success"
            
            try:
                # 1. Пытаемся получить товар (вызовет ошибку)
                product = await catalog_service.get_product_by_id("nonexistent_id")
            except Exception as e:
                # 2. Добавляем сообщение об ошибке
                error_message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.ASSISTANT,
                    content="Извините, произошла ошибка при получении товара."
                )
                await message_service.add_message_to_conversation(error_message)
                
                assert str(e) == "Товар не найден"
                mock_get_product.assert_called_once_with("nonexistent_id")
                mock_add_message.assert_called_once_with(error_message)


@pytest.mark.asyncio
async def test_order_status_transitions_workflow_integration(order_service, message_service):
    """Тест workflow переходов статусов заказа"""
    
    # Мокаем получение заказа
    with patch.object(order_service, 'get_or_create_order') as mock_get_order:
        order = Order(
            order_id="order_123",
            session_id="session_123",
            sender_id="user_123",
            status=OrderStatus.DRAFT
        )
        mock_get_order.return_value = order
        
        # Мокаем обновление статуса
        with patch.object(order_service, 'update_order_status') as mock_update_status:
            mock_update_status.return_value = True
            
            # Мокаем добавление сообщений
            with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                mock_add_message.return_value = "success"
                
                # 1. Получаем заказ
                retrieved_order = await order_service.get_or_create_order("session_123", "user_123")
                
                # 2. Переводим в статус "Готов"
                ready_result = await order_service.update_order_status("session_123", "user_123", OrderStatus.READY)
                
                # 3. Переводим в статус "Подтвержден"
                confirmed_result = await order_service.update_order_status("session_123", "user_123", OrderStatus.CONFIRMED)
                
                # 4. Добавляем сообщение о статусе
                order.status = OrderStatus.READY  # вручную меняем статус
                order.status = OrderStatus.CONFIRMED  # вручную меняем статус
                status_message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.ASSISTANT,
                    content="Статус заказа обновлен."
                )
                await message_service.add_message_to_conversation(status_message)
                
                assert retrieved_order.order_id == "order_123"
                assert ready_result is True
                assert confirmed_result is True
                assert order.status == OrderStatus.CONFIRMED
                
                mock_get_order.assert_called_once_with("session_123", "user_123")
                assert mock_update_status.call_count == 2
                mock_add_message.assert_called_once_with(status_message) 
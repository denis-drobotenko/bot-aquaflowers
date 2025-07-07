import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.command_service import CommandService
from src.models.order import OrderStatus


@pytest.fixture
def command_service():
    with patch('src.services.command_service.CatalogService') as mock_catalog_class, \
         patch('src.services.command_service.OrderService') as mock_order_class, \
         patch('src.services.command_service.SessionService') as mock_session_class, \
         patch('src.services.command_service.MessageProcessor') as mock_message_processor_class:
        
        mock_catalog = MagicMock()
        mock_order = MagicMock()
        mock_session = MagicMock()
        mock_message_processor = MagicMock()
        
        # Асинхронные методы мокать через AsyncMock
        mock_message_processor.send_message = AsyncMock()
        mock_catalog.get_available_products = AsyncMock()
        mock_catalog.validate_product = AsyncMock()
        mock_catalog.send_catalog_to_user = AsyncMock()
        mock_order.update_order_data = AsyncMock()
        mock_order.add_item = AsyncMock()
        mock_order.remove_item = AsyncMock()
        mock_order.process_order_for_operator = AsyncMock()
        mock_order.update_order_status = AsyncMock()
        
        mock_catalog_class.return_value = mock_catalog
        mock_order_class.return_value = mock_order
        mock_session_class.return_value = mock_session
        mock_message_processor_class.return_value = mock_message_processor
        
        service = CommandService()
        yield service


def test_init(command_service):
    """Тест инициализации CommandService"""
    assert hasattr(command_service, 'catalog_service')
    assert hasattr(command_service, 'order_service')
    assert hasattr(command_service, 'session_service')
    assert hasattr(command_service, 'logger')


@pytest.mark.asyncio
async def test_handle_command_send_catalog(command_service):
    """Тест обработки команды отправки каталога"""
    
    # Мокаем получение доступных товаров
    with patch.object(command_service.catalog_service, 'get_available_products') as mock_get_products:
        mock_get_products.return_value = [
            {'name': 'Розы', 'price': 100},
            {'name': 'Тюльпаны', 'price': 80}
        ]
        
        # Мокаем отправку каталога
        with patch.object(command_service.catalog_service, 'send_catalog_to_user') as mock_send:
            mock_send.return_value = True
            
            result = await command_service.handle_command(
                sender_id="user_123",
                session_id="session_456",
                command={'type': 'send_catalog'}
            )
            
            assert result['status'] == 'success'
            assert result['action'] == 'catalog_sent'
            assert result['products_count'] == 2
            mock_get_products.assert_called_once()
            mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_send_catalog_no_products(command_service):
    """Тест обработки команды отправки каталога когда нет товаров"""
    
    # Мокаем пустой список товаров
    with patch.object(command_service.catalog_service, 'get_available_products') as mock_get_products:
        mock_get_products.return_value = []
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={'type': 'send_catalog'}
        )
        
        assert result['status'] == 'error'
        assert 'нет букетов в наличии' in result['message']
        mock_get_products.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_save_order_info(command_service):
    """Тест обработки команды сохранения общих данных заказа"""
    
    # Мокаем обновление данных заказа
    with patch.object(command_service.order_service, 'update_order_data') as mock_update:
        mock_update.return_value = "order_123"
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={
                'type': 'save_order_info',
                'date': '2024-01-01',
                'time': '12:00',
                'address': 'Москва'
            }
        )
        
        assert result['status'] == 'success'
        assert result['action'] == 'order_data_updated'
        assert result['data']['date'] == '2024-01-01'
        assert result['order_id'] == "order_123"
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_add_order_item(command_service):
    """Тест обработки команды добавления товара в заказ"""
    
    # Мокаем валидацию товара
    with patch.object(command_service.catalog_service, 'validate_product') as mock_validate:
        mock_validate.return_value = {
            'valid': True,
            'product': {'name': 'Розы', 'price': 100}
        }
        
        # Мокаем добавление товара
        with patch.object(command_service.order_service, 'add_item') as mock_add:
            mock_add.return_value = "order_123"
            
            result = await command_service.handle_command(
                sender_id="user_123",
                session_id="session_456",
                command={
                    'type': 'add_order_item',
                    'bouquet': 'Розы',
                    'quantity': 1,
                    'notes': 'для мамы',
                    'retailer_id': 'prod_123'
                }
            )
            
            assert result['status'] == 'success'
            assert result['action'] == 'item_added'
            assert result['item_data']['bouquet'] == 'Розы'
            assert result['order_id'] == "order_123"
            mock_validate.assert_called_once_with('prod_123')
            mock_add.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_add_order_item_invalid_product(command_service):
    """Тест добавления невалидного товара"""
    
    # Мокаем невалидный товар
    with patch.object(command_service.catalog_service, 'validate_product') as mock_validate:
        mock_validate.return_value = {'valid': False}
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={
                'type': 'add_order_item',
                'bouquet': 'Несуществующий букет',
                'retailer_id': 'invalid_id'
            }
        )
        
        assert result['status'] == 'error'
        assert result['action'] == 'invalid_product'
        assert 'Такого товара нет в каталоге' in result['message']
        mock_validate.assert_called_once_with('invalid_id')


@pytest.mark.asyncio
async def test_handle_command_remove_order_item(command_service):
    """Тест обработки команды удаления товара из заказа"""
    
    # Мокаем удаление товара
    with patch.object(command_service.order_service, 'remove_item') as mock_remove:
        mock_remove.return_value = True
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={
                'type': 'remove_order_item',
                'product_id': 'prod_123'
            }
        )
        
        assert result['status'] == 'success'
        assert result['action'] == 'item_removed'
        assert result['product_id'] == 'prod_123'
        mock_remove.assert_called_once_with('session_456', 'user_123', 'prod_123')


@pytest.mark.asyncio
async def test_handle_command_remove_order_item_not_found(command_service):
    """Тест удаления несуществующего товара"""
    
    # Мокаем неудачное удаление
    with patch.object(command_service.order_service, 'remove_item') as mock_remove:
        mock_remove.return_value = False
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={
                'type': 'remove_order_item',
                'product_id': 'nonexistent_id'
            }
        )
        
        assert result['status'] == 'error'
        assert 'Товар не найден в заказе' in result['message']


@pytest.mark.asyncio
async def test_handle_command_update_order_delivery(command_service):
    """Тест обработки команды обновления данных доставки"""
    
    # Мокаем обновление данных доставки
    with patch.object(command_service.order_service, 'update_order_data') as mock_update:
        mock_update.return_value = "order_123"
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={
                'type': 'update_order_delivery',
                'date': '2024-01-01',
                'time': '12:00',
                'address': 'Москва',
                'delivery_needed': True
            }
        )
        
        assert result['status'] == 'success'
        assert result['action'] == 'delivery_updated'
        assert result['delivery_data']['date'] == '2024-01-01'
        assert result['order_id'] == "order_123"
        mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_confirm_order_success(command_service):
    """Тест успешного подтверждения заказа"""
    
    mock_result = {
        'order_data': {
            'items': [{'bouquet': 'Розы', 'quantity': 1}],
            'date': '2024-01-01',
            'time': '12:00'
        },
        'validation': {'is_complete': True, 'missing_required': [], 'missing_optional': [], 'warnings': []},
        'summary_for_ai': 'Товары:\n1. Розы\nДата и время: 2024-01-01 в 12:00',
        'is_ready_for_operator': True
    }
    
    with patch.object(command_service.order_service, 'process_order_for_operator') as mock_process, \
         patch.object(command_service.order_service, 'update_order_status') as mock_update_status:
        mock_process.return_value = mock_result
        mock_update_status.return_value = True
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={'type': 'confirm_order'}
        )
        
        assert result['status'] == 'success'
        assert result['action'] == 'order_confirmed'
        assert result['is_ready_for_operator'] is True
        assert 'summary_for_ai' in result
        mock_process.assert_called_once()
        mock_update_status.assert_called_once_with('session_456', 'user_123', OrderStatus.CONFIRMED)


@pytest.mark.asyncio
async def test_handle_command_confirm_order_incomplete(command_service):
    """Тест подтверждения заказа с неполными данными"""
    
    mock_result = {
        'order_data': {'items': []},
        'validation': {'is_complete': False, 'missing_required': ['Товары в заказе'], 'missing_optional': [], 'warnings': []},
        'summary_for_ai': '',
        'is_ready_for_operator': False
    }
    
    with patch.object(command_service.order_service, 'process_order_for_operator') as mock_process:
        mock_process.return_value = mock_result
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={'type': 'confirm_order'}
        )
        
        assert result['status'] == 'error'
        assert result['action'] == 'incomplete_order'
        assert result['is_ready_for_operator'] is False
        assert 'summary_for_ai' in result
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_handle_command_clarify_request(command_service):
    """Тест обработки команды уточнения запроса"""
    
    result = await command_service.handle_command(
        sender_id="user_123",
        session_id="session_456",
        command={
            'type': 'clarify_request',
            'clarification': 'Уточните, пожалуйста, какие цветы вы хотите?'
        }
    )
    
    assert result['status'] == 'success'
    assert result['action'] == 'clarification_sent'
    assert result['clarification'] == 'Уточните, пожалуйста, какие цветы вы хотите?'


@pytest.mark.asyncio
async def test_handle_command_unknown(command_service):
    """Тест обработки неизвестной команды"""
    
    result = await command_service.handle_command(
        sender_id="user_123",
        session_id="session_456",
        command={'type': 'unknown_command'}
    )
    
    assert result['status'] == 'error'
    assert 'Unknown command' in result['message']


@pytest.mark.asyncio
async def test_handle_command_with_empty_dict(command_service):
    """Тест обработки команды с пустым словарем"""
    
    result = await command_service.handle_command(
        sender_id="user_123",
        session_id="session_456",
        command={}
    )
    
    assert result['status'] == 'error'
    assert 'Invalid command format' in result['message']


@pytest.mark.asyncio
async def test_handle_command_with_none(command_service):
    """Тест обработки команды с None"""
    
    result = await command_service.handle_command(
        sender_id="user_123",
        session_id="session_456",
        command=None
    )
    
    assert result['status'] == 'error'
    assert 'Invalid command format' in result['message']


@pytest.mark.asyncio
async def test_handle_command_without_type(command_service):
    """Тест обработки команды без типа"""
    
    result = await command_service.handle_command(
        sender_id="user_123",
        session_id="session_456",
        command={'data': 'some_data'}
    )
    
    assert result['status'] == 'error'
    assert 'No command type found' in result['message']


@pytest.mark.asyncio
async def test_handle_command_error_handling(command_service):
    """Тест обработки ошибок в командах"""
    
    # Мокаем ошибку в catalog_service
    with patch.object(command_service.catalog_service, 'get_available_products') as mock_get_products:
        mock_get_products.side_effect = Exception("Database error")
        
        result = await command_service.handle_command(
            sender_id="user_123",
            session_id="session_456",
            command={'type': 'send_catalog'}
        )
        
        assert result['status'] == 'error'
        assert 'Ошибка при отправке каталога' in result['message'] 
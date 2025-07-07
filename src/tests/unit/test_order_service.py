import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.order_service import OrderService
from src.models.order import Order, OrderStatus, OrderItem


@pytest.fixture
def order_service():
    with patch('src.services.order_service.OrderRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo.find_by_session_and_user = AsyncMock()
        mock_repo.find_by_field = AsyncMock()
        mock_repo.update = AsyncMock()
        mock_repo.create = AsyncMock()
        mock_repo_class.return_value = mock_repo
        service = OrderService()
        yield service


def test_init(order_service):
    assert isinstance(order_service.repo, MagicMock)
    assert hasattr(order_service, 'logger')


@pytest.mark.asyncio
async def test_update_order_data_create_new(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        mock_find.return_value = None
        mock_find_by_field.return_value = []
        with patch.object(order_service.repo, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "new_order_123"
            order_data = {'date': '2024-01-01', 'time': '12:00'}
            result = await order_service.update_order_data("session_456", "user_123", order_data)
            assert result.startswith("order_session_456_")
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_update_order_data_update_existing(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[])
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        with patch.object(order_service.repo, 'update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            order_data = {'date': '2024-01-01', 'time': '12:00', 'address': 'Москва'}
            result = await order_service.update_order_data("session_456", "user_123", order_data)
            assert result == "order_123"
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_add_item_success(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[])
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        with patch.object(order_service.repo, 'update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            item_data = {'bouquet': 'Розы', 'quantity': 1, 'price': 100, 'notes': 'для мамы'}
            result = await order_service.add_item("session_456", "user_123", item_data)
            assert result == "order_123"
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_remove_item_success(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[OrderItem(product_id="prod_1", bouquet="Розы", quantity=1), OrderItem(product_id="prod_2", bouquet="Тюльпаны", quantity=2)])
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        with patch.object(order_service.repo, 'update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            result = await order_service.remove_item("session_456", "user_123", "prod_1")
            assert result is True
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_remove_item_not_found(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[OrderItem(product_id="prod_1", bouquet="Розы", quantity=1)])
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        result = await order_service.remove_item("session_456", "user_123", "nonexistent_prod")
        assert result is False


@pytest.mark.asyncio
async def test_update_order_status_success(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[])
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        with patch.object(order_service.repo, 'update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            result = await order_service.update_order_status("session_456", "user_123", OrderStatus.CONFIRMED)
            assert result is True
            mock_update.assert_called_once()


def test_validate_order_data_complete(order_service):
    order_data = {"items": [{"bouquet": "Розы", "quantity": 1}], "date": "15.07.2024", "time": "14:00", "address": "Москва", "recipient_name": "Иван"}
    result = order_service.validate_order_data(order_data)
    assert result["is_complete"] is True
    assert len(result["missing_required"]) == 0
    assert len(result["warnings"]) == 0


def test_validate_order_data_incomplete(order_service):
    order_data = {"items": [{"bouquet": "Розы", "quantity": 1}], "date": "15.07.2024"}
    result = order_service.validate_order_data(order_data)
    assert result["is_complete"] is False
    assert "Время доставки" in result["missing_required"]


def test_validate_order_data_with_warnings(order_service):
    order_data = {"items": [{"bouquet": "Розы", "quantity": 1}], "date": "15.07.2024", "time": "14:00", "address": "Москва", "recipient_name": "Иван", "card_text": "С днем рождения!"}
    result = order_service.validate_order_data(order_data)
    assert result["is_complete"] is True
    assert len(result["missing_required"]) == 0
    assert len(result["warnings"]) == 0


def test_get_order_summary_for_ai(order_service):
    order_data = {
        "items": [
            {"bouquet": "Розы красные", "quantity": 1, "notes": "для мамы"},
            {"bouquet": "Тюльпаны", "quantity": 2}
        ],
        "date": "15.07.2024",
        "time": "14:00",
        "recipient_name": "Иван Петров",
        "card_text": "С днем рождения!",
        "card_needed": True
    }
    summary = order_service.get_order_summary_for_ai(order_data)
    assert "Товары:" in summary
    assert "1. Розы красные" in summary
    assert "2. Тюльпаны" in summary
    assert "Дата и время: 15.07.2024 в 14:00" in summary
    assert "Получатель: Иван Петров" in summary
    assert 'Текст открытки: "С днем рождения!"' in summary


@pytest.mark.asyncio
async def test_process_order_for_operator_ready(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find, \
         patch.object(order_service.repo, 'find_by_field', new_callable=AsyncMock) as mock_find_by_field:
        existing_order = Order(
            order_id="order_123",
            sender_id="user_123",
            session_id="session_456",
            status=OrderStatus.DRAFT,
            items=[OrderItem(product_id="prod_1", bouquet="Розы", quantity=1)],
            date="15.07.2024",
            time="14:00",
            address="Москва",
            card_needed=True,
            card_text="С днем рождения!"
        )
        mock_find.return_value = existing_order
        mock_find_by_field.return_value = [existing_order]
        result = await order_service.process_order_for_operator("session_456", "user_123")
        assert result["is_ready_for_operator"] is True
        assert "summary_for_ai" in result
        assert "order_data" in result
        assert "validation" in result
        assert result["validation"]["is_complete"]


@pytest.mark.asyncio
async def test_process_order_for_operator_incomplete(order_service):
    with patch.object(order_service.repo, 'find_by_session_and_user', new_callable=AsyncMock) as mock_find:
        existing_order = Order(order_id="order_123", sender_id="user_123", session_id="session_456", status=OrderStatus.DRAFT, items=[])
        mock_find.return_value = existing_order
        result = await order_service.process_order_for_operator("session_456", "user_123")
        assert result["is_ready_for_operator"] is False
        assert "summary_for_ai" in result
        assert "order_data" in result
        assert "validation" in result
        assert not result["validation"]["is_complete"] 
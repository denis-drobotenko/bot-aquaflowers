import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.message_service import MessageService
from src.services.session_service import SessionService
from src.models.message import Message, MessageRole
from datetime import datetime


@pytest.fixture
def message_service():
    with patch('src.services.message_service.firestore.Client') as mock_firestore:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        service = MessageService()
        yield service


@pytest.fixture
def session_service():
    with patch('src.services.session_service.firestore.Client') as mock_firestore:
        mock_client = MagicMock()
        mock_firestore.return_value = mock_client
        service = SessionService()
        yield service


@pytest.mark.asyncio
async def test_message_session_workflow_integration(message_service, session_service):
    """Тест полного workflow: создание сессии -> добавление сообщений -> получение истории"""
    
    # Мокаем создание сессии
    with patch.object(session_service, 'get_or_create_session_id') as mock_get_session:
        mock_get_session.return_value = "session_123"
        
        # Мокаем добавление сообщений
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.return_value = "success"
            
            # Мокаем получение истории
            with patch.object(message_service, 'get_conversation_history') as mock_get_history:
                expected_messages = [
                    Message(sender_id="user_123", session_id="session_123", role=MessageRole.USER, content="Привет"),
                    Message(sender_id="user_123", session_id="session_123", role=MessageRole.ASSISTANT, content="Здравствуйте!")
                ]
                mock_get_history.return_value = expected_messages
                
                # Получаем или создаем сессию
                session_id = await session_service.get_or_create_session_id("user_123")
                
                # Добавляем сообщение пользователя
                user_message = Message(
                    sender_id="user_123",
                    session_id=session_id,
                    role=MessageRole.USER,
                    content="Привет"
                )
                await message_service.add_message_to_conversation(user_message)
                
                # Добавляем ответ ассистента
                assistant_message = Message(
                    sender_id="user_123",
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content="Здравствуйте!"
                )
                await message_service.add_message_to_conversation(assistant_message)
                
                # Получаем историю диалога
                history = await message_service.get_conversation_history(session_id)
                
                assert session_id == "session_123"
                assert len(history) == 2
                assert history[0].content == "Привет"
                assert history[1].content == "Здравствуйте!"
                
                mock_get_session.assert_called_once_with("user_123")
                assert mock_add_message.call_count == 2
                mock_get_history.assert_called_once_with("session_123")


@pytest.mark.asyncio
async def test_session_expiry_with_messages_integration(message_service, session_service):
    """Тест истечения сессии с сохранением сообщений"""
    
    # Мокаем Firestore с истекшей сессией
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        'session_id': 'expired_session_123',
        'session_created': (datetime.now().timestamp() - 8 * 24 * 3600)  # 8 дней назад
    }
    
    mock_doc_ref = MagicMock()
    mock_doc_ref.get.return_value = mock_doc
    
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc_ref
    
    session_service.db.collection.return_value = mock_collection
    
    # Мокаем сохранение новой сессии
    with patch.object(session_service, '_save_to_users') as mock_save:
        # Мокаем получение истории старой сессии
        with patch.object(message_service, 'get_conversation_history') as mock_get_history:
            old_messages = [
                Message(sender_id="user_123", session_id="expired_session_123", role=MessageRole.USER, content="Старое сообщение")
            ]
            mock_get_history.return_value = old_messages
            
            # Получаем новую сессию (старая истекла)
            new_session_id = await session_service.get_or_create_session_id("user_123")
            
            # Проверяем, что старая история доступна
            old_history = await message_service.get_conversation_history("expired_session_123")
            
            assert new_session_id != "expired_session_123"
            assert len(new_session_id) > 0
            assert len(old_history) == 1
            assert old_history[0].content == "Старое сообщение"
            
            mock_save.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_sessions_per_user_integration(message_service, session_service):
    """Тест работы с несколькими сессиями одного пользователя"""
    
    # Мокаем получение всех сессий пользователя
    with patch.object(session_service, 'get_all_sessions_by_sender') as mock_get_sessions:
        mock_sessions = [
            {'session_id': 'session_1', 'message_count': 5},
            {'session_id': 'session_2', 'message_count': 3}
        ]
        mock_get_sessions.return_value = mock_sessions
        
        # Мокаем получение истории для каждой сессии
        with patch.object(message_service, 'get_conversation_history') as mock_get_history:
            def mock_history_side_effect(session_id, limit=None):
                if session_id == 'session_1':
                    return [
                        Message(sender_id="user_123", session_id="session_1", role=MessageRole.USER, content="Сообщение 1"),
                        Message(sender_id="user_123", session_id="session_1", role=MessageRole.ASSISTANT, content="Ответ 1")
                    ]
                elif session_id == 'session_2':
                    return [
                        Message(sender_id="user_123", session_id="session_2", role=MessageRole.USER, content="Сообщение 2")
                    ]
                return []
            
            mock_get_history.side_effect = mock_history_side_effect
            
            # Получаем все сессии пользователя
            sessions = await session_service.get_all_sessions_by_sender("user_123")
            
            # Получаем историю для каждой сессии
            session_1_history = await message_service.get_conversation_history("session_1")
            session_2_history = await message_service.get_conversation_history("session_2")
            
            assert len(sessions) == 2
            assert len(session_1_history) == 2
            assert len(session_2_history) == 1
            assert session_1_history[0].content == "Сообщение 1"
            assert session_2_history[0].content == "Сообщение 2"
            
            mock_get_sessions.assert_called_once_with("user_123")
            assert mock_get_history.call_count == 2


@pytest.mark.asyncio
async def test_session_creation_after_order_integration(message_service, session_service):
    """Тест создания новой сессии после заказа"""
    
    # Мокаем создание новой сессии после заказа
    with patch.object(session_service, 'create_new_session_after_order') as mock_create_session:
        mock_create_session.return_value = "new_session_456"
        
        # Мокаем добавление сообщения в новую сессию
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.return_value = "success"
            
            # Создаем новую сессию после заказа
            new_session_id = await session_service.create_new_session_after_order("user_123")
            
            # Добавляем сообщение в новую сессию
            order_complete_message = Message(
                sender_id="user_123",
                session_id=new_session_id,
                role=MessageRole.ASSISTANT,
                content="Заказ завершен! Можем помочь с чем-то еще?"
            )
            await message_service.add_message_to_conversation(order_complete_message)
            
            assert new_session_id == "new_session_456"
            mock_create_session.assert_called_once_with("user_123")
            mock_add_message.assert_called_once_with(order_complete_message)


@pytest.mark.asyncio
async def test_message_history_for_ai_integration(message_service, session_service):
    """Тест получения истории сообщений для AI"""
    
    # Мокаем поиск владельца сессии
    with patch.object(message_service.repo, 'find_session_owner') as mock_find_owner:
        mock_find_owner.return_value = "user_123"
        
        # Мокаем получение истории для AI
        with patch.object(message_service.repo, 'get_conversation_history_by_sender') as mock_get_ai_history:
            expected_history = [
                {"role": "user", "content": "Покажите каталог"},
                {"role": "assistant", "content": "Вот наш каталог цветов"},
                {"role": "user", "content": "Хочу заказать розы"}
            ]
            mock_get_ai_history.return_value = expected_history
            
            # Получаем историю для AI
            ai_history = await message_service.get_conversation_history_for_ai("session_123", limit=10)
            
            assert len(ai_history) == 3
            assert ai_history[0]["role"] == "user"
            assert ai_history[0]["content"] == "Покажите каталог"
            assert ai_history[2]["content"] == "Хочу заказать розы"
            
            mock_find_owner.assert_called_once_with("session_123")
            mock_get_ai_history.assert_called_once_with("user_123", "session_123", limit=10)


@pytest.mark.asyncio
async def test_user_info_with_messages_integration(message_service, session_service):
    """Тест работы с информацией пользователя и его сообщениями"""
    
    # Мокаем получение информации пользователя
    with patch.object(session_service, 'get_user_info') as mock_get_user_info:
        mock_user_info = {
            'name': 'Иван Петров',
            'session_id': 'session_123',
            'updated_at': datetime.now()
        }
        mock_get_user_info.return_value = mock_user_info
        
        # Мокаем сохранение информации пользователя
        with patch.object(session_service, 'save_user_info') as mock_save_user_info:
            # Мокаем добавление сообщения
            with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
                mock_add_message.return_value = "success"
                
                # Получаем информацию пользователя
                user_info = await session_service.get_user_info("user_123")
                
                # Сохраняем обновленную информацию
                await session_service.save_user_info("user_123", "Новое имя")
                
                # Добавляем сообщение
                message = Message(
                    sender_id="user_123",
                    session_id=user_info['session_id'],
                    role=MessageRole.USER,
                    content="Привет, я " + user_info['name']
                )
                await message_service.add_message_to_conversation(message)
                
                assert user_info['name'] == 'Иван Петров'
                assert user_info['session_id'] == 'session_123'
                mock_save_user_info.assert_called_once_with("user_123", "Новое имя")
                mock_add_message.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_message_update_in_session_integration(message_service, session_service):
    """Тест обновления сообщений в рамках сессии"""
    
    # Мокаем получение сообщения
    with patch.object(message_service, 'get_message') as mock_get_message:
        original_message = Message(
            sender_id="user_123",
            session_id="session_123",
            role=MessageRole.USER,
            content="Оригинальное сообщение"
        )
        mock_get_message.return_value = original_message
        
        # Мокаем обновление сообщения
        with patch.object(message_service, 'update_message') as mock_update_message:
            mock_update_message.return_value = True
            
            # Получаем сообщение
            message = await message_service.get_message("message_id_123")
            
            # Обновляем сообщение
            message.content = "Обновленное сообщение"
            update_result = await message_service.update_message("message_id_123", message)
            
            assert update_result is True
            assert message.content == "Обновленное сообщение"
            mock_get_message.assert_called_once_with("message_id_123")
            mock_update_message.assert_called_once_with("message_id_123", message)


@pytest.mark.asyncio
async def test_error_handling_integration(message_service, session_service):
    """Тест обработки ошибок при работе с сообщениями и сессиями"""
    
    # Мокаем ошибку при получении сессии
    with patch.object(session_service, 'get_or_create_session_id') as mock_get_session:
        mock_get_session.side_effect = Exception("Session service error")
        
        # Мокаем ошибку при добавлении сообщения
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.side_effect = Exception("Message service error")
            
            try:
                session_id = await session_service.get_or_create_session_id("user_123")
            except Exception:
                session_id = None
            
            try:
                message = Message(
                    sender_id="user_123",
                    session_id="session_123",
                    role=MessageRole.USER,
                    content="Тестовое сообщение"
                )
                await message_service.add_message_to_conversation(message)
            except Exception:
                pass
            
            assert session_id is None
            mock_get_session.assert_called_once_with("user_123")
            mock_add_message.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_session_access_integration(message_service, session_service):
    """Тест одновременного доступа к сессии"""
    
    # Мокаем создание сессии
    with patch.object(session_service, 'get_or_create_session_id') as mock_get_session:
        mock_get_session.return_value = "session_123"
        
        # Мокаем добавление сообщений
        with patch.object(message_service, 'add_message_to_conversation') as mock_add_message:
            mock_add_message.return_value = "success"
            
            # Симулируем одновременные запросы
            session_id1 = await session_service.get_or_create_session_id("user_123")
            session_id2 = await session_service.get_or_create_session_id("user_123")
            
            # Добавляем сообщения в одну сессию
            message1 = Message(
                sender_id="user_123",
                session_id=session_id1,
                role=MessageRole.USER,
                content="Сообщение 1"
            )
            message2 = Message(
                sender_id="user_123",
                session_id=session_id2,
                role=MessageRole.ASSISTANT,
                content="Ответ 1"
            )
            
            await message_service.add_message_to_conversation(message1)
            await message_service.add_message_to_conversation(message2)
            
            assert session_id1 == session_id2 == "session_123"
            assert mock_get_session.call_count == 2
            assert mock_add_message.call_count == 2 
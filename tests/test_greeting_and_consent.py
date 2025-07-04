import pytest
from unittest.mock import AsyncMock, patch
from src.webhook_handlers import webhook_handler
from fastapi import Request
import json

@pytest.mark.asyncio
async def test_greeting_and_catalog_consent(monkeypatch):
    # Мокаем отправку сообщений
    sent_messages = []
    async def fake_send_message(to, msg):
        sent_messages.append(msg)
        return True
    monkeypatch.setattr('src.whatsapp_utils.send_whatsapp_message', fake_send_message)
    # Мокаем AI-менеджер
    async def fake_get_ai_response(sender_id, session_id, history):
        # Если пользователь только поздоровался — AI предлагает каталог
        if any('Здравствуйте' in m.get('content','') for m in history):
            return ("Добро пожаловать! Хотите посмотреть каталог?", {'type': 'send_catalog'})
        # Если пользователь согласился — AI отправляет команду каталога
        if any('Хочу' in m.get('content','') for m in history):
            return ("Показываю каталог", {'type': 'send_catalog'})
        return ("Неизвестная команда", None)
    monkeypatch.setattr('src.ai_manager.get_ai_response', fake_get_ai_response)
    # Мокаем командный обработчик
    async def fake_handle_commands(sender_id, session_id, command):
        sent_messages.append('Каталог отправлен')
        return {'status': 'success', 'action': 'catalog_sent'}
    monkeypatch.setattr('src.command_handler.handle_commands', fake_handle_commands)
    # Мокаем базу
    class FakeDB:
        def __init__(self):
            self.history = []
        def add_message(self, sender_id, session_id, role, content):
            self.history.append({'role': role, 'content': content})
        def get_conversation_history(self, sender_id, session_id):
            return self.history
        def get_conversation_history_for_ai(self, sender_id, session_id):
            return self.history
    fake_db = FakeDB()
    monkeypatch.setattr('src.database', fake_db)
    
    # Мокаем session_manager
    class FakeSessionManager:
        def get_or_create_session_id(self, sender_id):
            return f"{sender_id}_test_session"
        def is_session_created_after_order(self, session_id):
            return False
    fake_session_manager = FakeSessionManager()
    monkeypatch.setattr('src.session_manager', fake_session_manager)
    
    # Мокаем typing indicator
    async def fake_typing_indicator(to, typing):
        return True
    monkeypatch.setattr('src.whatsapp_utils.send_typing_indicator', fake_typing_indicator)
    
    # Симулируем приветствие
    req = Request({'type': 'http', 'method': 'POST'})
    req._body = json.dumps({
        'entry':[{'changes':[{'value':{'messages':[{'from':'79999999999','text':{'body':'Здравствуйте'}}], 'contacts':[{'profile':{'name':'Тест'}}]}}]}]
    }).encode()
    await webhook_handler(req)
    # Симулируем согласие
    req2 = Request({'type': 'http', 'method': 'POST'})
    req2._body = json.dumps({
        'entry':[{'changes':[{'value':{'messages':[{'from':'79999999999','text':{'body':'Хочу'}}], 'contacts':[{'profile':{'name':'Тест'}}]}}]}]
    }).encode()
    await webhook_handler(req2)
    # Проверки
    assert any(('Добро пожаловать' in m or 'Здравствуйте' in m or 'Привет' in m) for m in sent_messages)
    assert any('Каталог отправлен' in m for m in sent_messages) 
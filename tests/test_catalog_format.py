import pytest
from src.whatsapp_utils import handle_send_catalog
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_catalog_format(monkeypatch):
    # Мокаем отправку сообщений и изображений
    sent_messages = []
    sent_images = []
    async def fake_send_message(to, msg, sender_id=None, session_id=None):
        sent_messages.append(msg)
        return True
    async def fake_send_image(to, url, caption, sender_id=None, session_id=None):
        sent_images.append(caption)
        return True
    monkeypatch.setattr('src.whatsapp_utils.send_whatsapp_message', fake_send_message)
    monkeypatch.setattr('src.whatsapp_utils.send_whatsapp_image_with_caption', fake_send_image)
    
    # Мокаем каталог
    fake_catalog = [
        {'name': 'Розы', 'price': '1000₽', 'image_url': 'img1', 'availability': 'in stock'},
        {'name': 'Tulip🌷', 'price': '800₽', 'image_url': 'img2', 'availability': 'in stock'},
    ]
    monkeypatch.setattr('src.catalog_reader.get_catalog_products', lambda: fake_catalog)
    monkeypatch.setattr('src.catalog_reader.filter_available_products', lambda x: x)
    
    # Запуск
    sender_id = "test_user_catalog"
    await handle_send_catalog(sender_id)
    
    # Проверки
    assert any('Розы' in c and '1000' in c and 'ID' not in c and 'Описание' not in c for c in sent_images)
    assert any('Tulip' in c and '800' in c and 'ID' not in c and 'Описание' not in c for c in sent_images)
    for c in sent_images:
        assert c.endswith('🌸')
        assert 'ID' not in c and 'Описание' not in c
        assert '\n' in c  # название и цена на разных строках
        assert not any(e in c for e in ['💰','📝','🆔','🎉','🌺','🌹'])
    for m in sent_messages:
        assert m.endswith('🌸')
        assert not any(e in m for e in ['💰','📝','🆔','🎉','🌺','🌹']) 
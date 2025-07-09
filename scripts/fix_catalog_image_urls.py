#!/usr/bin/env python3
"""
Скрипт для массового обновления image_url в сообщениях каталога в Firestore
Использует collection_group как в CRM
"""

import asyncio
from src.services.catalog_service import CatalogService
from src.config.settings import WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
from google.cloud import firestore
import re

# Получаем актуальный каталог
catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)
catalog_products = catalog_service.get_available_products()

# Строим индекс: (name, price) -> image_url
catalog_index = {}
for product in catalog_products:
    name = product.get('name', '').strip()
    price = str(product.get('price', '')).strip()
    image_url = product.get('image_url')
    if name and price and image_url:
        catalog_index[(name, price)] = image_url

print(f"📋 Загружено {len(catalog_index)} товаров из каталога")

# Регулярка для извлечения названия и цены из caption
CATALOG_MSG_RE = re.compile(r'^(?P<name>.+)\n(?P<price>.+?)(?:\s*🌸)?$')

async def fix_catalog_messages():
    db = firestore.Client()
    
    # Получаем все сообщения через collection_group (как в CRM)
    messages = db.collection_group('messages').stream()
    
    updated = 0
    checked = 0
    no_match = 0
    
    for msg_doc in messages:
        msg_data = msg_doc.to_dict()
        
        # Только сообщения ассистента без image_url
        if msg_data.get('role') != 'assistant':
            continue
        if msg_data.get('image_url'):
            continue
            
        content = msg_data.get('content', '')
        m = CATALOG_MSG_RE.match(content.strip())
        if not m:
            continue
            
        name = m.group('name').strip()
        price = m.group('price').strip()
        key = (name, price)
        image_url = catalog_index.get(key)
        
        checked += 1
        
        if image_url:
            # Обновляем сообщение
            msg_doc.reference.update({'image_url': image_url})
            updated += 1
            print(f"✅ [{updated}] {msg_doc.reference.path}")
            print(f"   {name} - {price} -> {image_url}")
        else:
            no_match += 1
            if no_match <= 10:  # Показываем только первые 10 несовпадений
                print(f"❌ {msg_doc.reference.path}")
                print(f"   {name} - {price} (не найдено в каталоге)")
    
    print(f"\n📊 Результат:")
    print(f"   Проверено сообщений: {checked}")
    print(f"   Обновлено: {updated}")
    print(f"   Не найдено совпадений: {no_match}")

if __name__ == "__main__":
    asyncio.run(fix_catalog_messages()) 
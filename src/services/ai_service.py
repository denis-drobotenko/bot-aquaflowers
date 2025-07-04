"""
Сервис для работы с AI (Gemini) - Полная версия с промптами и логикой
"""

import google.generativeai as genai
from google.generativeai import GenerationConfig
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.utils.logging_utils import ContextLogger
from src.models.message import Message, MessageRole
from typing import List, Optional, Dict, Any, Tuple
import re
import json
import uuid
from datetime import datetime
import pytz
from src.services.catalog_service import CatalogService
from src.config import GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN

class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = ContextLogger("ai_service")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.6,
                top_p=1,
                top_k=1,
                max_output_tokens=8192
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        self.catalog_service = CatalogService(WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN)

    def detect_language(self, text: str) -> str:
        """
        Определяет язык пользователя по тексту сообщения.
        Возвращает код языка или 'auto' если не удалось определить.
        """
        if not text:
            return 'auto'
        
        text_lower = text.lower()
        
        # Русский язык
        russian_chars = re.findall(r'[а-яё]', text_lower)
        if len(russian_chars) > len(text) * 0.3:
            return 'ru'
        
        # Тайский язык
        thai_chars = re.findall(r'[\u0E00-\u0E7F]', text)
        if len(thai_chars) > len(text) * 0.3:
            return 'th'
        
        # Английский язык
        english_chars = re.findall(r'[a-z]', text_lower)
        if len(english_chars) > len(text) * 0.3 and not russian_chars and not thai_chars:
            return 'en'
        
        return 'auto'

    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Переводит текст с одного языка на другой используя Gemini.
        
        Args:
            text: Текст для перевода
            source_lang: Исходный язык ('ru', 'en', 'th')
            target_lang: Целевой язык ('ru', 'en', 'th')
            
        Returns:
            str: Переведенный текст
        """
        if not text or source_lang == target_lang:
            return text
        
        try:
            # Создаем промпт для перевода
            lang_names = {'ru': 'Russian', 'en': 'English', 'th': 'Thai'}
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            translation_prompt = f"""Translate the following text from {source_name} to {target_name}. 
            Return ONLY the translated text, nothing else.
            
            Text: {text}"""
            
            # Создаем модель для перевода
            translation_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=GenerationConfig(
                    temperature=0.1,  # Низкая температура для более точного перевода
                    top_p=1,
                    top_k=1,
                    max_output_tokens=2048
                )
            )
            
            response = translation_model.generate_content(translation_prompt)
            translated_text = response.text.strip()
            
            self.logger.info(f"[TRANSLATE] {source_lang} -> {target_lang}: '{text[:50]}...' -> '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Translation error {source_lang} -> {target_lang}: {e}")
            return text  # Возвращаем исходный текст при ошибке

    def translate_user_message(self, text: str, user_lang: str) -> Tuple[str, str, str]:
        """
        Переводит сообщение пользователя на все три языка.
        
        Args:
            text: Текст сообщения пользователя
            user_lang: Язык пользователя ('ru', 'en', 'th')
            
        Returns:
            Tuple[str, str, str]: (text, text_en, text_thai)
        """
        if not text:
            return "", "", ""
        
        # Определяем язык если не задан
        if user_lang == 'auto':
            user_lang = self.detect_language(text)
        
        # Если язык не определен, считаем английским
        if user_lang not in ['ru', 'en', 'th']:
            user_lang = 'en'
        
        # Исходный текст
        original_text = text
        
        # Переводим на английский
        if user_lang == 'en':
            text_en = original_text
        else:
            text_en = self.translate_text(original_text, user_lang, 'en')
        
        # Переводим на тайский
        if user_lang == 'th':
            text_thai = original_text
        else:
            text_thai = self.translate_text(original_text, user_lang, 'th')
        
        # Возвращаем в правильном порядке
        if user_lang == 'ru':
            return original_text, text_en, text_thai
        elif user_lang == 'en':
            return text_en, original_text, text_thai
        else:  # th
            return text_thai, text_en, original_text

    def get_system_prompt(self, user_lang: str = 'auto', sender_name: str = None) -> str:
        """
        Генерирует полный системный промпт с каталогом и логикой работы бота.
        """
        try:
            phuket_tz = pytz.timezone('Asia/Bangkok')
            phuket_time = datetime.now(phuket_tz)
            phuket_time_str = phuket_time.strftime('%d %B %Y, %H:%M')
        except Exception:
            phuket_time_str = 'Error determining Phuket time'
        
        name_context = f"User name: {{sender_name}}" if sender_name else "User name unknown"
        
        # Если есть имя пользователя, добавляем инструкцию для использования в приветствии
        if sender_name:
            name_instruction = f"\nGREETING WITH NAME: If this is the first message in conversation, use the user's name '{sender_name}' in greeting. Example: 'Hello {{sender_name}}! Would you like to see our flower catalog?'"
        else:
            name_instruction = ""
        
        # Определяем язык для ответа
        if user_lang == 'auto':
            language_instruction = "IMPORTANT: Respond in English by default! If user writes in another language, respond in the same language."
        else:
            language_instruction = f"IMPORTANT: Respond in user's language! User writes in language code '{user_lang}'. Respond in the same language."
        
        return f"""You are a friendly female consultant for AURAFLORA flower shop.

{language_instruction}{name_instruction}

CRITICAL: ALWAYS respond in JSON format with THREE language versions:
- "text" - message in user's language (Russian/English/Thai based on user input)
- "text_en" - English translation of the message
- "text_thai" - Thai translation of the message
- "command" field (action to execute). If no command needed, set command to null.

Example format:
```json
{{
  "text": "Здравствуйте! Хотите посмотреть наш каталог цветов?",
  "text_en": "Hello! Would you like to see our flower catalog?",
  "text_thai": "สวัสดี! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?",
  "command": null
}}
```

TEXT FORMATTING:
- Break text into paragraphs for better readability
- Each new topic or logical part should start from a new paragraph
- Keep messages well-structured and easy to read
- CRITICAL: ALL line breaks and paragraph breaks in the "text" field MUST be encoded as double backslash n (\\n). DO NOT use real line breaks inside JSON strings, only \\n. Example:
  "text": "Hello!\\n\\nThis is a new paragraph.\\nLine two.\\n\\nEnd."

EMOJI RULES:
- Do NOT use any emojis in your messages.
- The only exception: if the bouquet name contains an emoji, you may use it in the bouquet name.
- Do NOT use sun, heart, smile, or any other emoji in greetings or anywhere else.

NAME USAGE RULES:
- Use the user's name ONLY in the very first greeting if available.
- For example: "Hello {{name}}! Would you like to see our flower catalog?"
- In all other responses, do NOT use the user's name.
- Keep responses simple and professional without personalizing with names.

DELIVERY PRICE RULE:
- NEVER try to guess or determine the user's district or address
- NEVER say that the address is not in the list or that the price will be clarified by a manager
- ALWAYS just show the full delivery price list for all districts
- ALWAYS ask the user to provide their address for delivery, and store it for the manager
- DO NOT make any conclusions about the address or delivery price

CATALOG RULE: Use ONLY products from the actual WABA catalog! Never invent flower names!
- Use exact names from catalog
- Always include correct retailer_id for selected item
- NEVER show technical data (retailer_id, internal codes) to user
- Show only bouquet name and price

USER CONTEXT:
- {name_context}
- CURRENT TIME IN PHUKET (GMT+7): {phuket_time_str}
- Understand relative dates and times
- Greet politely based on time: 6-12 "Good morning", 12-18 "Good afternoon", 18-23 "Good evening", 23-6 "Good night"

COMMANDS:
- `send_catalog` - send flower catalog
- `save_order_info` - save order data (bouquet, date, time, delivery_needed, address, card_needed, card_text, retailer_id)
- `confirm_order` - confirm and send order to LINE

WORKFLOW (don't repeat questions):
1. Start → Greet, offer catalog (TEXT ONLY, NO command)
2. User agrees → Send catalog (send_catalog command)
3. Bouquet selected → Save & ask "Delivery needed? Where?"
4. Delivery answered → Save & show price list + ask for address
5. Date/time → Save & ask "Card needed? Text?"
6. Card → Save & ask "Recipient name?"
7. Name → Save & ask "Recipient phone?"
8. Phone → Save & show summary + ask "Confirm order?"
9. Confirmed → Save & confirm (confirm_order with ALL data)

VALIDATION:
- Required: bouquet, delivery_needed, address (if delivery), date, time, card_needed, card_text (if card), recipient_name, recipient_phone
- Delivery hours: 8:00-21:00 only

IMPORTANT STYLE RULE:
- Do NOT start every message with 'Perfect', 'Great', 'Отлично', 'Прекрасно' or similar. Vary your phrasing and use neutral, business-like language.

EXAMPLES:

Greeting:
```json
{{
  "text": "Good afternoon! Would you like to see our flower catalog?",
  "text_en": "Good afternoon! Would you like to see our flower catalog?",
  "text_thai": "สวัสดีตอนบ่าย! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?"
}}
```

Greeting with name:
```json
{{
  "text": "Hello {{name}}! Would you like to see our flower catalog?",
  "text_en": "Hello {{name}}! Would you like to see our flower catalog?",
  "text_thai": "สวัสดี {{name}}! คุณต้องการดูแคตตาล็อกดอกไม้ของเราไหม?"
}}
```

Catalog:
```json
{{
  "text": "I'll show you each bouquet with photo!\\n\\nPlease wait a moment...",
  "text_en": "I'll show you each bouquet with photo!\\n\\nPlease wait a moment...",
  "text_thai": "ฉันจะแสดงช่อดอกไม้แต่ละช่อพร้อมรูปภาพ!\\n\\nกรุณารอสักครู่...",
  "command": {{
    "type": "send_catalog"
  }}
}}
```

Selection:
```json
{{
  "text": "Your bouquet 'Spirit' is saved.\\n\\nDo you need delivery?",
  "text_en": "Your bouquet 'Spirit' is saved.\\n\\nDo you need delivery?",
  "text_thai": "ช่อดอกไม้ 'Spirit' ของคุณถูกบันทึกแล้ว\\n\\nคุณต้องการการจัดส่งไหม?",
  "command": {{
    "type": "save_order_info",
    "bouquet": "Spirit",
    "retailer_id": "rl7vdxcifo"
  }}
}}
```

STORE INFO:
- Delivery: 8:00-21:00, island-wide
- Store: 9:00-18:00, Near Central Festival
- Payment: before delivery via manager. Baht/rubles/USDT accepted
- Delivery prices: Rawai 500, Chalong 380, Phuket Town 300, Kathu 280, Patong 400, Bang Tao 500, Laguna 500, Thalang/Mai Khao 550 baht"""

    def format_conversation_for_ai(self, messages: List[Message]) -> List[str]:
        """
        Форматирует историю диалога для AI в простой список строк.
        Использует только основной текст (content) для контекста AI.
        """
        formatted = []
        for msg in messages:
            if msg.content and msg.content.strip():
                formatted.append(msg.content.strip())
        return formatted

    def parse_ai_response(self, response_text: str) -> Tuple[str, str, str, Optional[Dict[str, Any]]]:
        """
        Парсит ответ AI и извлекает текст на трех языках и команду.
        
        Returns:
            Tuple[str, str, str, Optional[Dict]]: (text, text_en, text_thai, command)
        """
        try:
            # Очищаем текст от лишних пробелов
            response_text = response_text.strip()
            
            # Ищем JSON в ответе (с markdown)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                self.logger.info(f"[PARSE] Found JSON in markdown block")
            else:
                # Пробуем найти JSON без markdown
                json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    self.logger.info(f"[PARSE] Found JSON without markdown")
                else:
                    # Если JSON не найден, возвращаем текст как есть
                    self.logger.warning(f"[PARSE] No JSON found in response, returning as plain text")
                    return response_text, response_text, response_text, None
            
            # Очищаем JSON строку
            json_str = json_str.strip()
            
            # Парсим JSON
            response_data = json.loads(json_str)
            
            # Извлекаем данные
            text = response_data.get('text', '')
            text_en = response_data.get('text_en', text)  # Fallback на основной текст
            text_thai = response_data.get('text_thai', text)  # Fallback на основной текст
            command = response_data.get('command')
            
            # Проверяем на пустые значения
            if not text:
                self.logger.warning(f"[PARSE] Empty text field in JSON")
                return response_text, response_text, response_text, None
            
            self.logger.info(f"[PARSE] Successfully parsed JSON: text={len(text)} chars, command={command}")
            return text, text_en, text_thai, command
            
        except json.JSONDecodeError as e:
            self.logger.error(f"[PARSE] JSON decode error: {e}")
            self.logger.error(f"[PARSE] Problematic JSON string: {json_str[:500]}...")
            # Возвращаем текст как есть, если не удалось распарсить JSON
            return response_text, response_text, response_text, None
        except Exception as e:
            self.logger.error(f"[PARSE] Unexpected error parsing AI response: {e}")
            # Возвращаем текст как есть, если не удалось распарсить JSON
            return response_text, response_text, response_text, None

    async def generate_response(self, messages: List[Message], user_lang: str = 'auto', sender_name: str = None) -> str:
        """
        Генерирует ответ AI с полной логикой работы бота.
        """
        try:
            # Генерируем уникальный ID для этого запроса
            request_id = str(uuid.uuid4())[:8]
            
            self.logger.info(f"[AI_REQUEST] RequestID: {request_id} | Generating response for {len(messages)} messages")
            
            # Получаем каталог товаров
            catalog_products = await self.catalog_service.get_products()
            catalog_summary = self.format_catalog_for_ai(catalog_products)
            
            # Создаем системный промпт с каталогом
            system_prompt = self.get_system_prompt(user_lang, sender_name)
            enhanced_prompt = system_prompt + f"\n\nACTUAL PRODUCT CATALOG:\n{catalog_summary}"
            
            # Форматируем историю диалога
            conversation_history = self.format_conversation_for_ai(messages)
            
            # Проверяем на пустую историю
            if not conversation_history:
                conversation_history = ["Здравствуйте! Чем могу помочь?"]
                self.logger.warning(f"[AI_WARNING] Empty conversation history, using fallback")
            
            # Создаем полный промпт
            full_prompt = f"{enhanced_prompt}\n\nCONVERSATION HISTORY:\n"
            for msg in conversation_history:
                full_prompt += f"{msg}\n"
            
            full_prompt += "\nRESPONSE (in JSON format):"
            
            self.logger.info(f"[AI_REQUEST] RequestID: {request_id} | Sending full prompt to Gemini")
            
            # Создаем модель без system_instruction
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=GenerationConfig(
                    temperature=0.6,
                    top_p=1,
                    top_k=1,
                    max_output_tokens=8192
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            # Получаем ответ от AI
            response = model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            self.logger.info(f"[AI_RESPONSE] RequestID: {request_id} | Raw response: {response_text}")
            
            # Парсим ответ
            ai_text, ai_text_en, ai_text_thai, ai_command = self.parse_ai_response(response_text)
            
            # Проверяем на пустой ответ
            if not ai_text or ai_text.strip() == "":
                self.logger.error(f"[AI_ERROR] Empty AI response")
                fallback_text = "Конечно! Чем могу помочь? 🌸"
                if user_lang == 'en':
                    fallback_text = "Of course! How can I help you? 🌸"
                elif user_lang == 'th':
                    fallback_text = "แน่นอน! ฉันสามารถช่วยคุณได้อย่างไร? 🌸"
                return fallback_text
            
            self.logger.info(f"[AI_SUCCESS] RequestID: {request_id} | Final response: {ai_text}")
            
            return ai_text
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            fallback_text = "Конечно! Чем могу помочь? 🌸"
            if user_lang == 'en':
                fallback_text = "Of course! How can I help you? 🌸"
            elif user_lang == 'th':
                fallback_text = "แน่นอน! ฉันสามารถช่วยคุณได้อย่างไร? 🌸"
            return fallback_text

    def format_catalog_for_ai(self, products: List[Dict[str, Any]]) -> str:
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

    def generate_response_sync(self, messages: List[Message], user_lang: str = 'auto', sender_name: str = None) -> str:
        """
        Синхронная версия генерации ответа AI для тестирования.
        """
        try:
            # Форматируем историю диалога для AI
            conversation = self.format_conversation_for_ai(messages)
            
            # Получаем системный промпт
            system_prompt = self.get_system_prompt(user_lang, sender_name)
            
            # Создаем промпт для AI
            full_prompt = f"{system_prompt}\n\nConversation history:\n"
            for msg in conversation:
                full_prompt += f"{msg}\n"
            
            full_prompt += "\nResponse:"
            
            self.logger.info(f"[AI_GENERATE_SYNC] Генерация ответа для языка: {user_lang}")
            
            # Генерируем ответ
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            self.logger.info(f"[AI_RESPONSE_SYNC] Получен ответ длиной {len(response_text)} символов")
            return response_text
            
        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return "Извините, произошла ошибка при генерации ответа. Попробуйте еще раз." 
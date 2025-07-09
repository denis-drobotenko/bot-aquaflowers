"""
Сервис для работы с AI (Gemini) - Упрощенная версия
"""

import google.generativeai as genai
from google.generativeai import GenerationConfig
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from src.utils.logging_decorator import log_function
from src.models.message import Message, MessageRole
from typing import List, Optional, Dict, Any, Tuple, Union
import re
import json
import uuid
from datetime import datetime
import pytz
from src.services.catalog_service import CatalogService
from src.config.settings import GEMINI_API_KEY, WHATSAPP_CATALOG_ID, WHATSAPP_TOKEN
import os
from src.utils.ai_utils import format_conversation_for_ai, parse_ai_response, get_fallback_text, format_catalog_for_ai

class AIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
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

    @log_function("ai_service")
    def detect_language(self, text: str) -> str:
        """Определяет язык пользователя по тексту сообщения с помощью AI и fallback логики"""
        result = self.detect_language_with_confidence(text)
        return result['language']

    @log_function("ai_service")
    def detect_language_with_confidence(self, text: str) -> dict:
        """Определяет язык пользователя с оценкой уверенности"""
        if not text:
            return {'language': 'auto', 'confidence': 0.0, 'should_ask': True}
        
        # Сначала пробуем AI определение с оценкой уверенности
        try:
            # Создаем промпт для определения языка с уверенностью
            language_detection_prompt = f"""Analyze this text and determine the language with confidence level.

Text: "{text}"

Respond in JSON format:
{{
    "language": "language_code",
    "confidence": 0.95,
    "should_ask_confirmation": true
}}

Language codes: ru, en, th, it, fr, es, de, pt, nl, pl, cs, sk, hu, ro, bg, hr, sr, sl, et, lv, lt, fi, sv, no, da, is, zh, ja, ko, vi, id, ms, tl, hi, bn, ur, ar, he, fa, tr, ka, hy, az, sw, am, yo, zu, xh, af

Set should_ask_confirmation to true if you're not very confident about the language detection.
Set should_ask_confirmation to false if you're very confident about the language.

Response:"""

            # Используем отдельную модель для определения языка
            detection_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=GenerationConfig(
                    temperature=0.1,
                    top_p=1,
                    top_k=1,
                    max_output_tokens=200
                ),
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            response = detection_model.generate_content(language_detection_prompt)
            response_text = response.text.strip()
            
            # Парсим JSON ответ
            try:
                import json
                result = json.loads(response_text)
                detected_lang = result.get('language', 'auto').lower()
                confidence = float(result.get('confidence', 0.0))
                should_ask = result.get('should_ask_confirmation', True)
                
                # Проверяем, что полученный код языка поддерживается
                supported_languages = ['ru', 'en', 'th', 'it', 'fr', 'es', 'de', 'pt', 'nl', 'pl', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr', 'sr', 'sl', 'et', 'lv', 'lt', 'fi', 'sv', 'no', 'da', 'is', 'zh', 'ja', 'ko', 'vi', 'id', 'ms', 'tl', 'hi', 'bn', 'ur', 'ar', 'he', 'fa', 'tr', 'ka', 'hy', 'az', 'sw', 'am', 'yo', 'zu', 'xh', 'af']
                
                if detected_lang in supported_languages:
                    return {
                        'language': detected_lang,
                        'confidence': confidence,
                        'should_ask': should_ask
                    }
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to parse AI response: {e}")
                print(f"Response: {response_text}")
                
        except Exception as e:
            print(f"AI language detection failed: {e}")
        
        # Fallback на старую логику определения языка
        fallback_lang = self._detect_language_fallback(text)
        return {
            'language': fallback_lang,
            'confidence': 0.6 if fallback_lang != 'auto' else 0.0,
            'should_ask': fallback_lang == 'auto'
        }
    
    def _detect_language_fallback(self, text: str) -> str:
        """Fallback логика определения языка по символам и ключевым словам"""
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
        
        # Итальянские приветствия и слова
        italian_greetings = ['ciao', 'buongiorno', 'buonasera', 'buonanotte', 'salve', 'arrivederci', 'grazie', 'prego', 'scusa', 'mi dispiace']
        if any(greeting in text_lower for greeting in italian_greetings):
            return 'it'
        
        # Французские приветствия и слова
        french_greetings = ['bonjour', 'bonsoir', 'salut', 'au revoir', 'merci', 's\'il vous plaît', 'excusez-moi', 'pardon']
        if any(greeting in text_lower for greeting in french_greetings):
            return 'fr'
        
        # Испанские приветствия и слова
        spanish_greetings = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'adiós', 'gracias', 'por favor', 'perdón', 'lo siento']
        if any(greeting in text_lower for greeting in spanish_greetings):
            return 'es'
        
        # Немецкие приветствия и слова
        german_greetings = ['hallo', 'guten tag', 'guten morgen', 'guten abend', 'auf wiedersehen', 'danke', 'bitte', 'entschuldigung']
        if any(greeting in text_lower for greeting in german_greetings):
            return 'de'
        
        # Португальские приветствия
        portuguese_greetings = ['olá', 'bom dia', 'boa tarde', 'boa noite', 'adeus', 'obrigado', 'por favor', 'desculpe']
        if any(greeting in text_lower for greeting in portuguese_greetings):
            return 'pt'
        
        # Голландские приветствия
        dutch_greetings = ['hallo', 'goedemorgen', 'goedemiddag', 'goedenavond', 'tot ziens', 'dank je', 'alsjeblieft']
        if any(greeting in text_lower for greeting in dutch_greetings):
            return 'nl'
        
        # Польские приветствия
        polish_greetings = ['cześć', 'dzień dobry', 'dobry wieczór', 'do widzenia', 'dziękuję', 'proszę', 'przepraszam']
        if any(greeting in text_lower for greeting in polish_greetings):
            return 'pl'
        
        # Чешские приветствия
        czech_greetings = ['ahoj', 'dobrý den', 'dobrý večer', 'na shledanou', 'děkuji', 'prosím', 'omlouvám se']
        if any(greeting in text_lower for greeting in czech_greetings):
            return 'cs'
        
        # Словацкие приветствия
        slovak_greetings = ['ahoj', 'dobrý deň', 'dobrý večer', 'dovidenia', 'ďakujem', 'prosím', 'ospravedlňujem sa']
        if any(greeting in text_lower for greeting in slovak_greetings):
            return 'sk'
        
        # Венгерские приветствия
        hungarian_greetings = ['szia', 'jó napot', 'jó estét', 'viszlát', 'köszönöm', 'kérlek', 'elnézést']
        if any(greeting in text_lower for greeting in hungarian_greetings):
            return 'hu'
        
        # Румынские приветствия
        romanian_greetings = ['salut', 'bună ziua', 'bună seara', 'la revedere', 'mulțumesc', 'te rog', 'scuze']
        if any(greeting in text_lower for greeting in romanian_greetings):
            return 'ro'
        
        # Болгарские приветствия
        bulgarian_greetings = ['здравей', 'добър ден', 'добър вечер', 'довиждане', 'благодаря', 'моля', 'извинявам се']
        if any(greeting in text_lower for greeting in bulgarian_greetings):
            return 'bg'
        
        # Хорватские приветствия
        croatian_greetings = ['zdravo', 'dobar dan', 'dobar večer', 'doviđenja', 'hvala', 'molim', 'ispričavam se']
        if any(greeting in text_lower for greeting in croatian_greetings):
            return 'hr'
        
        # Сербские приветствия
        serbian_greetings = ['здраво', 'добар дан', 'добар вече', 'довиђења', 'хвала', 'молим', 'извињавам се']
        if any(greeting in text_lower for greeting in serbian_greetings):
            return 'sr'
        
        # Словенские приветствия
        slovenian_greetings = ['zdravo', 'dober dan', 'dober večer', 'nasvidenje', 'hvala', 'prosim', 'opravičujem se']
        if any(greeting in text_lower for greeting in slovenian_greetings):
            return 'sl'
        
        # Эстонские приветствия
        estonian_greetings = ['tere', 'tere hommikust', 'tere päevast', 'tere õhtust', 'head aega', 'aitäh', 'palun']
        if any(greeting in text_lower for greeting in estonian_greetings):
            return 'et'
        
        # Латышские приветствия
        latvian_greetings = ['sveiki', 'labdien', 'labvakar', 'uz redzēšanos', 'paldies', 'lūdzu', 'atvainojiet']
        if any(greeting in text_lower for greeting in latvian_greetings):
            return 'lv'
        
        # Литовские приветствия
        lithuanian_greetings = ['labas', 'laba diena', 'labas vakaras', 'iki pasimatymo', 'ačiū', 'prašau', 'atsiprašau']
        if any(greeting in text_lower for greeting in lithuanian_greetings):
            return 'lt'
        
        # Финские приветствия
        finnish_greetings = ['hei', 'hyvää huomenta', 'hyvää päivää', 'hyvää iltaa', 'näkemiin', 'kiitos', 'ole hyvä']
        if any(greeting in text_lower for greeting in finnish_greetings):
            return 'fi'
        
        # Шведские приветствия
        swedish_greetings = ['hej', 'god morgon', 'god dag', 'god kväll', 'hej då', 'tack', 'varsågod']
        if any(greeting in text_lower for greeting in swedish_greetings):
            return 'sv'
        
        # Норвежские приветствия
        norwegian_greetings = ['hei', 'god morgen', 'god dag', 'god kveld', 'ha det', 'takk', 'vær så snill']
        if any(greeting in text_lower for greeting in norwegian_greetings):
            return 'no'
        
        # Датские приветствия
        danish_greetings = ['hej', 'god morgen', 'god dag', 'god aften', 'farvel', 'tak', 'vær venlig']
        if any(greeting in text_lower for greeting in danish_greetings):
            return 'da'
        
        # Исландские приветствия
        icelandic_greetings = ['halló', 'góðan dag', 'góða nótt', 'bless', 'takk', 'vinsamlegast', 'fyrirgefðu']
        if any(greeting in text_lower for greeting in icelandic_greetings):
            return 'is'
        
        # Китайские символы
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if len(chinese_chars) > len(text) * 0.3:
            return 'zh'
        
        # Японские символы
        japanese_chars = re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text)
        if len(japanese_chars) > len(text) * 0.3:
            return 'ja'
        
        # Корейские символы
        korean_chars = re.findall(r'[\uac00-\ud7af]', text)
        if len(korean_chars) > len(text) * 0.3:
            return 'ko'
        
        # Вьетнамские приветствия
        vietnamese_greetings = ['xin chào', 'chào buổi sáng', 'chào buổi chiều', 'tạm biệt', 'cảm ơn', 'xin vui lòng']
        if any(greeting in text_lower for greeting in vietnamese_greetings):
            return 'vi'
        
        # Индонезийские приветствия
        indonesian_greetings = ['halo', 'selamat pagi', 'selamat siang', 'selamat malam', 'terima kasih', 'tolong']
        if any(greeting in text_lower for greeting in indonesian_greetings):
            return 'id'
        
        # Малайские приветствия
        malay_greetings = ['hai', 'selamat pagi', 'selamat petang', 'selamat malam', 'terima kasih', 'sila']
        if any(greeting in text_lower for greeting in malay_greetings):
            return 'ms'
        
        # Тагальские приветствия
        tagalog_greetings = ['kamusta', 'magandang umaga', 'magandang hapon', 'magandang gabi', 'salamat', 'pakiusap']
        if any(greeting in text_lower for greeting in tagalog_greetings):
            return 'tl'
        
        # Хинди символы
        hindi_chars = re.findall(r'[\u0900-\u097f]', text)
        if len(hindi_chars) > len(text) * 0.3:
            return 'hi'
        
        # Бенгальские символы
        bengali_chars = re.findall(r'[\u0980-\u09ff]', text)
        if len(bengali_chars) > len(text) * 0.3:
            return 'bn'
        
        # Урду символы
        urdu_chars = re.findall(r'[\u0600-\u06ff]', text)
        if len(urdu_chars) > len(text) * 0.3:
            return 'ur'
        
        # Арабские символы
        arabic_chars = re.findall(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]', text)
        if len(arabic_chars) > len(text) * 0.3:
            return 'ar'
        
        # Иврит символы
        hebrew_chars = re.findall(r'[\u0590-\u05ff]', text)
        if len(hebrew_chars) > len(text) * 0.3:
            return 'he'
        
        # Персидские символы
        persian_chars = re.findall(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff\ufb50-\ufdff\ufe70-\ufeff]', text)
        if len(persian_chars) > len(text) * 0.3:
            return 'fa'
        
        # Турецкие приветствия
        turkish_greetings = ['merhaba', 'günaydın', 'iyi günler', 'iyi akşamlar', 'güle güle', 'teşekkürler', 'lütfen']
        if any(greeting in text_lower for greeting in turkish_greetings):
            return 'tr'
        
        # Грузинские символы
        georgian_chars = re.findall(r'[\u10a0-\u10ff]', text)
        if len(georgian_chars) > len(text) * 0.3:
            return 'ka'
        
        # Армянские символы
        armenian_chars = re.findall(r'[\u0530-\u058f]', text)
        if len(armenian_chars) > len(text) * 0.3:
            return 'hy'
        
        # Азербайджанские приветствия
        azerbaijani_greetings = ['salam', 'günaydın', 'yaxşı günlər', 'yaxşı axşamlar', 'sağ ol', 'təşəkkür edirəm']
        if any(greeting in text_lower for greeting in azerbaijani_greetings):
            return 'az'
        
        # Суахили приветствия
        swahili_greetings = ['hujambo', 'habari za asubuhi', 'habari za mchana', 'habari za jioni', 'asante', 'tafadhali']
        if any(greeting in text_lower for greeting in swahili_greetings):
            return 'sw'
        
        # Амхарские символы
        amharic_chars = re.findall(r'[\u1200-\u137f]', text)
        if len(amharic_chars) > len(text) * 0.3:
            return 'am'
        
        # Йоруба приветствия
        yoruba_greetings = ['bawo', 'eku aaro', 'eku osan', 'eku ale', 'o dabo', 'o se', 'jowo']
        if any(greeting in text_lower for greeting in yoruba_greetings):
            return 'yo'
        
        # Зулу приветствия
        zulu_greetings = ['sawubona', 'sawubona ekuseni', 'sawubona emini', 'sawubona kusihlwa', 'ngiyabonga', 'ngicela']
        if any(greeting in text_lower for greeting in zulu_greetings):
            return 'zu'
        
        # Коса приветствия
        xhosa_greetings = ['molo', 'molo ekuseni', 'molo emini', 'molo kusihlwa', 'enkosi', 'ndicela']
        if any(greeting in text_lower for greeting in xhosa_greetings):
            return 'xh'
        
        # Африкаанс приветствия
        afrikaans_greetings = ['hallo', 'goeie môre', 'goeie dag', 'goeie naand', 'totsiens', 'dankie', 'asseblief']
        if any(greeting in text_lower for greeting in afrikaans_greetings):
            return 'af'
        
        # Английский язык (только если нет других языков)
        english_chars = re.findall(r'[a-z]', text_lower)
        if len(english_chars) > len(text) * 0.3 and not russian_chars and not thai_chars:
            return 'en'
        
        return 'auto'

    @log_function("ai_service")
    def ask_language_confirmation(self, text: str, detected_lang: str) -> str:
        """Спрашивает пользователя о подтверждении языка"""
        if detected_lang == 'auto':
            return self._get_unknown_language_message()
        
        lang_names = {
            'ru': 'Russian', 'en': 'English', 'th': 'Thai', 'it': 'Italian', 'fr': 'French', 
            'es': 'Spanish', 'de': 'German', 'pt': 'Portuguese', 'nl': 'Dutch', 'pl': 'Polish',
            'cs': 'Czech', 'sk': 'Slovak', 'hu': 'Hungarian', 'ro': 'Romanian', 'bg': 'Bulgarian',
            'hr': 'Croatian', 'sr': 'Serbian', 'sl': 'Slovenian', 'et': 'Estonian', 'lv': 'Latvian',
            'lt': 'Lithuanian', 'fi': 'Finnish', 'sv': 'Swedish', 'no': 'Norwegian', 'da': 'Danish',
            'is': 'Icelandic', 'zh': 'Chinese', 'ja': 'Japanese', 'ko': 'Korean', 'vi': 'Vietnamese',
            'id': 'Indonesian', 'ms': 'Malay', 'tl': 'Tagalog', 'hi': 'Hindi', 'bn': 'Bengali',
            'ur': 'Urdu', 'ar': 'Arabic', 'he': 'Hebrew', 'fa': 'Persian', 'tr': 'Turkish',
            'ka': 'Georgian', 'hy': 'Armenian', 'az': 'Azerbaijani', 'sw': 'Swahili', 'am': 'Amharic',
            'yo': 'Yoruba', 'zu': 'Zulu', 'xh': 'Xhosa', 'af': 'Afrikaans'
        }
        
        lang_name = lang_names.get(detected_lang, detected_lang)
        
        # Создаем сообщение на разных языках
        messages = {
            'ru': f"Я определил ваш язык как {lang_name}. Правильно?",
            'en': f"I detected your language as {lang_name}. Is this correct?",
            'th': f"ฉันตรวจพบภาษาของคุณเป็น {lang_name} ถูกต้องหรือไม่?",
            'it': f"Ho rilevato la tua lingua come {lang_name}. È corretto?",
            'fr': f"J'ai détecté votre langue comme {lang_name}. Est-ce correct?",
            'es': f"He detectado tu idioma como {lang_name}. ¿Es correcto?",
            'de': f"Ich habe Ihre Sprache als {lang_name} erkannt. Ist das richtig?",
            'pt': f"Detectei seu idioma como {lang_name}. Está correto?",
            'nl': f"Ik heb uw taal gedetecteerd als {lang_name}. Klopt dit?",
            'pl': f"Wykryłem Twój język jako {lang_name}. Czy to prawda?",
            'cs': f"Detekoval jsem váš jazyk jako {lang_name}. Je to správně?",
            'sk': f"Detekoval som váš jazyk ako {lang_name}. Je to správne?",
            'hu': f"Nyelvét {lang_name}-ként észleltem. Helyes?",
            'ro': f"Am detectat limba dvs. ca {lang_name}. Este corect?",
            'bg': f"Открих езика ви като {lang_name}. Правилно ли е?",
            'hr': f"Otkrio sam vaš jezik kao {lang_name}. Je li točno?",
            'sr': f"Открио сам ваш језик као {lang_name}. Да ли је тачно?",
            'sl': f"Zaznal sem vaš jezik kot {lang_name}. Je pravilno?",
            'et': f"Tuvastasin teie keele kui {lang_name}. Kas see on õige?",
            'lv': f"Es atklāju jūsu valodu kā {lang_name}. Vai tas ir pareizi?",
            'lt': f"Aptikau jūsų kalbą kaip {lang_name}. Ar tai teisinga?",
            'fi': f"Havaitsin kielesi {lang_name}:ksi. Onko tämä oikein?",
            'sv': f"Jag upptäckte ditt språk som {lang_name}. Är det korrekt?",
            'no': f"Jeg oppdaget språket ditt som {lang_name}. Er det riktig?",
            'da': f"Jeg opdagede dit sprog som {lang_name}. Er det korrekt?",
            'is': f"Ég uppgötvaði tungumálið þitt sem {lang_name}. Er það rétt?",
            'zh': f"我检测到您的语言是{lang_name}。对吗？",
            'ja': f"あなたの言語を{lang_name}として検出しました。正しいですか？",
            'ko': f"귀하의 언어를 {lang_name}로 감지했습니다. 맞나요?",
            'vi': f"Tôi đã phát hiện ngôn ngữ của bạn là {lang_name}. Có đúng không?",
            'id': f"Saya mendeteksi bahasa Anda sebagai {lang_name}. Apakah benar?",
            'ms': f"Saya mengesan bahasa anda sebagai {lang_name}. Adakah betul?",
            'tl': f"Nadetect ko ang iyong wika bilang {lang_name}. Tama ba ito?",
            'hi': f"मैंने आपकी भाषा को {lang_name} के रूप में पहचाना। क्या यह सही है?",
            'bn': f"আমি আপনার ভাষাকে {lang_name} হিসাবে সনাক্ত করেছি। এটা কি ঠিক?",
            'ur': f"میں نے آپ کی زبان کو {lang_name} کے طور پر پہچانا۔ کیا یہ درست ہے؟",
            'ar': f"لقد اكتشفت لغتك كـ {lang_name}. هل هذا صحيح؟",
            'he': f"זיהיתי את השפה שלך כ-{lang_name}. האם זה נכון?",
            'fa': f"من زبان شما را به عنوان {lang_name} تشخیص دادم. آیا درست است؟",
            'tr': f"Dilinizi {lang_name} olarak tespit ettim. Doğru mu?",
            'ka': f"თქვენი ენა {lang_name} აღმოვაჩინე. სწორია?",
            'hy': f"Ես ձեր լեզուն հայտնաբերեցի որպես {lang_name}։ Ճիշտ է՞:",
            'az': f"Sizin dilinizi {lang_name} kimi müəyyən etdim. Düzgündür?",
            'sw': f"Nimegundua lugha yako kama {lang_name}. Je, ni sahihi?",
            'am': f"ቋንቋዎን እንደ {lang_name} አገኘሁ። ትክክል ነው?",
            'yo': f"Mo ṣe akiyesi èdè rẹ bi {lang_name}. Ṣe o tọọ?",
            'zu': f"Ngithole ulimi lwakho njenge-{lang_name}. Kuyiqiniso?",
            'xh': f"Ndiyifumene ulwimi lwakho njenge-{lang_name}. Kuyinyani?",
            'af': f"Ek het jou taal as {lang_name} opgespoor. Is dit reg?"
        }
        
        return messages.get(detected_lang, messages['en'])

    def _get_unknown_language_message(self) -> str:
        """Возвращает сообщение для неизвестного языка"""
        return "I couldn't determine your language. Please write in English, Russian, Thai, or another supported language."

    @log_function("ai_service")
    def translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Переводит текст с одного языка на другой используя Gemini"""
        if not text or source_lang == target_lang:
            return text
        
        try:
            lang_names = {
                'ru': 'Russian', 
                'en': 'English', 
                'th': 'Thai',
                'it': 'Italian',
                'fr': 'French',
                'es': 'Spanish',
                'de': 'German'
            }
            source_name = lang_names.get(source_lang, source_lang)
            target_name = lang_names.get(target_lang, target_lang)
            
            translation_prompt = f"""Translate the following text from {source_name} to {target_name}. 
            Return ONLY the translated text, nothing else.
            
            Text: {text}"""
            
            translation_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config=GenerationConfig(
                    temperature=0.1,
                    top_p=1,
                    top_k=1,
                    max_output_tokens=4096
                )
            )
            
            response = translation_model.generate_content(translation_prompt)
            translated_text = response.text.strip()
            
            # print(f"[TRANSLATE] {source_lang} -> {target_lang}: '{text[:50]}...' -> '{translated_text[:50]}...'")
            return translated_text
            
        except Exception as e:
            print(f"Translation error {source_lang} -> {target_lang}: {e}")
            return text

    @log_function("ai_service")
    def translate_user_message(self, text: str, user_lang: str) -> Tuple[str, str, str]:
        """Переводит сообщение пользователя на все три языка"""
        if not text:
            return "", "", ""
        
        # Определяем язык если не задан
        if user_lang == 'auto':
            user_lang = self.detect_language(text)
        
        # Если язык не определен, считаем английским
        if user_lang not in ['ru', 'en', 'th', 'it', 'fr', 'es', 'de']:
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
        
        # Возвращаем в правильном порядке: (content, content_en, content_thai)
        if user_lang == 'ru':
            return original_text, text_en, text_thai
        elif user_lang == 'en':
            return original_text, text_en, text_thai
        elif user_lang == 'th':
            return original_text, text_en, text_thai
        else:  # it, fr, es, de - используем оригинальный язык как основной
            return original_text, text_en, text_thai

    def get_system_prompt(self, user_lang: str = 'auto', sender_name: str = None, is_first_message: bool = False) -> str:
        """Генерирует полный системный промпт"""
        try:
            phuket_tz = pytz.timezone('Asia/Bangkok')
            phuket_time = datetime.now(phuket_tz)
            phuket_time_str = phuket_time.strftime('%d %B %Y, %H:%M')
        except Exception:
            phuket_time_str = 'Error determining Phuket time'
        
        name_context = f"User name: {sender_name}" if sender_name else "User name unknown"
        
        if sender_name and is_first_message:
            name_instruction = f"""
GREETING WITH NAME: This is the first message in conversation, use the user's name '{sender_name}' in greeting.
IMPORTANT: The name '{sender_name}' is from WhatsApp profile. If the user writes in Russian, use Russian name format.
If the user writes in English, use English name format. If the user writes in Thai, use Thai name format.
Example: 'Hello {sender_name}! Would you like to see our flower catalog?'"""
        else:
            name_instruction = ""
        
        if user_lang == 'auto':
            language_instruction = "IMPORTANT: Respond in English by default! If user writes in another language, respond in the same language."
        elif user_lang in ['it', 'fr', 'es', 'de']:
            # Для европейских языков отвечаем на английском, но понимаем их
            language_instruction = f"IMPORTANT: User writes in {user_lang.upper()} language, but respond in English! User understands English."
        else:
            language_instruction = f"IMPORTANT: Respond in user's language! User writes in language code '{user_lang}'. Respond in the same language."
        
        # Загружаем ТОЛЬКО основной промпт
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "ai_system_prompt.prompt")
        try:
            with open(prompt_path, encoding="utf-8") as f:
                prompt_template = f.read()
                print(f"[PROMPT_LOAD] Successfully loaded structured prompt from: {prompt_path}")
        except FileNotFoundError:
            print(f"[PROMPT_LOAD] ERROR: Structured prompt not found: {prompt_path}")
            raise FileNotFoundError(f"Required prompt file not found: {prompt_path}")
        
        return prompt_template.format(
            user_lang=user_lang,
            sender_name=sender_name or "",
            phuket_time_str=phuket_time_str,
            name_context=name_context,
            name_instruction=name_instruction,
            language_instruction=language_instruction
        )

    @log_function("ai_service")
    async def generate_response(
        self,
        messages: List[Union[Message, Dict]],
        user_lang: str = 'ru',
        sender_name: str = None,
        is_first_message: bool = False
    ) -> Tuple[str, str, str, Optional[dict]]:
        """Генерирует ответ AI на основе истории сообщений"""
        request_id = str(uuid.uuid4())[:8]
        
        try:
            # print(f"[AI_REQUEST] RequestID: {request_id} | Generating response for {len(messages)} messages")
            
            # Проверяем на повторяющиеся сообщения
            if self._is_repetitive_response(messages):
                # print(f"[AI_REQUEST] RequestID: {request_id} | Detected repetitive user message, generating contextual response")
                pass
            
            # Форматируем историю для логирования
            history_log = []
            for m in messages:
                if isinstance(m, dict):
                    role = m.get('role', 'unknown')
                    content = m.get('content', '')
                else:
                    role = m.role.value if hasattr(m.role, 'value') else str(m.role)
                    content = m.content
                history_log.append(f'[{role}] {content}')
            
            print(f"[AI_HISTORY] История для AI:")
            print("=" * 80)
            for i, msg in enumerate(history_log, 1):
                print(f"{i:2d}. {msg}")
            print("=" * 80)
            
            # Получаем каталог товаров
            catalog_products = self.catalog_service.get_products()
            catalog_summary = format_catalog_for_ai(catalog_products)
            
            # Создаем системный промпт с каталогом
            system_prompt = self.get_system_prompt(user_lang, sender_name, is_first_message)
            enhanced_prompt = system_prompt + f"\n\nACTUAL PRODUCT CATALOG:\n{catalog_summary}"
            
            # Форматируем историю диалога
            session_id = None
            sender_id = None
            if messages:
                first_msg = messages[0]
                if isinstance(first_msg, dict):
                    session_id = first_msg.get('session_id')
                    sender_id = first_msg.get('sender_id')
                else:
                    session_id = first_msg.session_id
                    sender_id = first_msg.sender_id
            
            conversation_history = await format_conversation_for_ai(messages, session_id, sender_id)
            
            # Проверяем на пустую историю
            if not conversation_history:
                conversation_history = [{"role": "assistant", "content": "Здравствуйте! Чем могу помочь?"}]
                print(f"[AI_WARNING] Empty conversation history, using fallback")
            
            # Создаем полный промпт
            full_prompt = f"{enhanced_prompt}\n\nCONVERSATION HISTORY:\n"
            history_json = json.dumps(conversation_history, ensure_ascii=False, indent=2)
            full_prompt += history_json
            full_prompt += "\n\nJSON RESPONSE:"
            
            # print(f"[AI_REQUEST] RequestID: {request_id} | Sending full prompt to Gemini")
            
            # Получаем ответ от AI с возможностью повторного запроса
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    response = self.model.generate_content(full_prompt)
                    response_text = response.text.strip()
                    
                    print(f"[AI_RESPONSE] RequestID: {request_id} | Attempt {attempt + 1} | Raw response length: {len(response_text)}")
                    print(f"[AI_RESPONSE] RequestID: {request_id} | Attempt {attempt + 1} | Raw response: {repr(response_text)}")
                    print(f"[AI_RESPONSE] RequestID: {request_id} | Attempt {attempt + 1} | Raw response (display): {response_text}")
                    
                    # Парсим ответ
                    ai_text, ai_text_en, ai_text_thai, ai_command = parse_ai_response(response_text)
                    
                    # Проверяем на пустой ответ (но с командой)
                    if not ai_text and not ai_command:
                        print(f"[AI_ERROR] Empty AI response on attempt {attempt + 1}")
                        if attempt < max_retries:
                            print(f"[AI_RETRY] Retrying... (attempt {attempt + 2}/{max_retries + 1})")
                            continue
                        else:
                            # Логируем ошибку в систему Errors вместо отправки fallback
                            await self._log_ai_error(
                                error="AI returned empty response after all retries",
                                context_data={
                                    "attempts": max_retries + 1,
                                    "user_lang": user_lang,
                                    "sender_name": sender_name
                                },
                                sender_id=sender_id if 'sender_id' in locals() else None,
                                session_id=session_id if 'session_id' in locals() else None
                            )
                            # Возвращаем пустые строки и None, чтобы система НЕ отправляла fallback
                            return "", "", "", None

                    # Если есть команда, но нет текста - это ошибка, нужно переделать
                    if ai_command and (not ai_text or ai_text.strip() == ""):
                        print(f"[AI_ERROR] Command without text: {ai_command}")
                        if attempt < max_retries:
                            print(f"[AI_RETRY] Retrying to get text with command... (attempt {attempt + 2}/{max_retries + 1})")
                            # Добавляем строгие инструкции о необходимости текста
                            retry_prompt = full_prompt + "\n\nCRITICAL: You MUST provide text field even when using commands. Never return empty text with commands. Always explain what you're doing before using a command."
                            full_prompt = retry_prompt
                            continue
                        else:
                            # Логируем ошибку в систему Errors вместо отправки fallback
                            await self._log_ai_error(
                                error="AI returned command without text after all retries",
                                context_data={
                                    "command": ai_command,
                                    "attempts": max_retries + 1,
                                    "user_lang": user_lang,
                                    "sender_name": sender_name
                                },
                                sender_id=sender_id if 'sender_id' in locals() else None,
                                session_id=session_id if 'session_id' in locals() else None
                            )
                            # Возвращаем пустые строки и None для команды, чтобы система НЕ отправляла fallback
                            return "", "", "", None
                    
                    # Если команда None, но есть текст - это может быть невалидный ответ
                    if ai_command is None and ai_text:
                        print(f"[AI_RETRY] Command is None but text exists, retrying... (attempt {attempt + 2}/{max_retries + 1})")
                        if attempt < max_retries:
                            # Добавляем более строгие инструкции в промпт
                            retry_prompt = full_prompt + "\n\nIMPORTANT: Your previous response was invalid. Please ensure you return a COMPLETE JSON with all required fields: text, text_en, text_thai, and command (as object with 'type' field)."
                            full_prompt = retry_prompt
                            continue
                    
                    print(f"[AI_RESPONSE] {ai_text}")
                    return ai_text, ai_text_en, ai_text_thai, ai_command
                    
                except Exception as e:
                    print(f"[AI_ERROR] Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries:
                        print(f"[AI_RETRY] Retrying... (attempt {attempt + 2}/{max_retries + 1})")
                        continue
                    else:
                        raise e
            
        except Exception as e:
            print(f"[AI_REQUEST] RequestID: {request_id} | Error generating response: {e}")
            # Логируем ошибку в систему Errors вместо отправки fallback
            await self._log_ai_error(
                error=f"AI service error: {e}",
                context_data={
                    "user_lang": user_lang,
                    "sender_name": sender_name
                },
                sender_id=sender_id if 'sender_id' in locals() else None,
                session_id=session_id if 'session_id' in locals() else None
            )
            # Возвращаем пустые строки и None, чтобы система НЕ отправляла fallback
            return "", "", "", None

    def _is_repetitive_response(self, messages: List[Message]) -> bool:
        """Проверяет, не является ли последнее сообщение пользователя повторением"""
        if not messages or len(messages) < 2:
            return False
        
        # Ищем последнее сообщение пользователя
        last_user_message = None
        for msg in reversed(messages[:-1]):
            if isinstance(msg, dict):
                role = msg.get('role')
                content = msg.get('content')
            else:
                role = msg.role
                content = msg.content
            
            if role == MessageRole.USER or role == 'user':
                last_user_message = content
                break
        
        if not last_user_message:
            return False
        
        # Проверяем, не является ли последнее сообщение пользователя коротким подтверждением
        short_confirmations = ['да', 'да.', 'да...', 'yes', 'yes.', 'yes...', 'ok', 'ok.', 'ok...', 'хорошо', 'хорошо.', 'хорошо...']
        return last_user_message.lower().strip() in short_confirmations 

    async def _log_ai_error(self, error: str, context_data: dict, sender_id: str = None, session_id: str = None):
        """Логирует ошибку AI в систему Errors"""
        try:
            from src.services.error_service import ErrorService
            error_service = ErrorService()
            
            await error_service.log_error(
                error=Exception(error),
                sender_id=sender_id,
                session_id=session_id,
                context_data=context_data,
                module="ai_service",
                function="generate_response"
            )
            print(f"[AI_ERROR_LOGGED] Error logged to Errors system: {error}")
        except Exception as e:
            print(f"[AI_ERROR_LOG_FAILED] Failed to log error: {e}")

    def _get_error_messages(self, user_lang: str) -> Dict[str, str]:
        """Возвращает сообщения об ошибках на разных языках"""
        if user_lang == 'en':
            return {
                'ru': 'Sorry, an error occurred. Please try again. 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            }
        elif user_lang == 'th':
            return {
                'ru': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            }
        else:  # ru или auto
            return {
                'ru': 'Извините, произошла ошибка. Попробуйте еще раз. 🌸',
                'en': 'Sorry, an error occurred. Please try again. 🌸',
                'th': 'ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง 🌸'
            } 
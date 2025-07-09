import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

from src.utils.whatsapp_client import WhatsAppClient
from src.services.message_service import MessageService
from src.models.message import Message, MessageRole
from src.utils.logging_decorator import log_function
from src.services.ai_service import AIService
from src.services.session_service import SessionService
from src.services.user_service import UserService
from src.services.command_service import CommandService
from src.services.error_service import ErrorService
from src.utils.waba_logger import waba_logger
from src.models.user import User, UserStatus
from src.config.settings import GEMINI_API_KEY

@dataclass
class AIResponse:
    """Ответ от AI с текстом и командой"""
    text: str
    text_en: str
    text_thai: str
    command: Optional[Dict[str, Any]]

class MessageProcessor:
    """Упрощенный процессор сообщений - единая точка обработки"""
    
    SUPPORTED_COMMANDS = {
        'send_catalog',
        'save_order_info',
        'add_order_item',
        'remove_order_item',
        'confirm_order',
    }
    
    def __init__(self):
        self.whatsapp_client = WhatsAppClient()
        self.message_service = MessageService()
        self.session_service = SessionService()
        self.user_service = UserService()
        self.ai_service = AIService(GEMINI_API_KEY)
        self.command_service = CommandService()
        self.error_service = ErrorService()

    @log_function("message_processor")
    async def process_user_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Основной метод обработки сообщения пользователя.
        Простая последовательность: статусы → сохранить → AI → команда → отправить
        """
        try:
            sender_id = message_data['sender_id']
            message_text = message_data['message_text']
            sender_name = message_data.get('sender_name')
            wamid = message_data.get('wa_message_id')
            
            # Логирование входящего сообщения
            print(f"\n[INCOMING] 👤 {sender_name}: {message_text}")
            if wamid:
                waba_logger.log_ai_processing(wamid, sender_id, message_text)
            
            # 0. Отправляем статусы (прочитано + печатает)
            if wamid:
                await self._send_status_updates(wamid, sender_id)
            
            # 1. Получаем сессию и пользователя
            session_id = await self.session_service.get_or_create_session_id(sender_id)
            await self._ensure_user_exists(sender_id, sender_name)

            # Сохраняем имя и телефон заказчика в заказ (если есть)
            customer_data = {}
            if sender_name:
                customer_data['customer_name'] = sender_name  # Исходное имя из WABA
            if 'sender_phone' in message_data:
                customer_data['customer_phone'] = message_data['sender_phone']  # Исходный телефон из WABA
            elif sender_id:  # Если нет sender_phone, используем sender_id как телефон
                customer_data['customer_phone'] = sender_id
            
            if customer_data:
                from src.services.order_service import OrderService
                order_service = OrderService()
                await order_service.update_order_data(session_id, sender_id, customer_data)
            
            # 2. Специальные команды
            if message_text.strip().lower() == '/newses':
                return await self._handle_newses_command(sender_id, session_id)
            
            # 3. Сохраняем сообщение пользователя
            user_message = self._create_user_message(message_data, session_id)
            success, _ = self.message_service.add_message_with_transaction_sync(user_message, limit=10)
            if not success:
                return False
            
            # 4. Получаем историю и обрабатываем через AI
            conversation_history = await self.message_service.get_conversation_history_for_ai_by_sender(
                sender_id, session_id, limit=100
            )
            
            # Логирование истории для AI
            print(f"[HISTORY] Получено {len(conversation_history)} сообщений")
            
            # 5. Генерируем ответ AI
            ai_response = await self._process_ai(message_data, session_id, conversation_history)
            
            # 6. Отправляем ответ пользователю (НЕ отправляем fallback при ошибках)
            await self._send_ai_response(ai_response, sender_id, session_id, wamid, 0)
            
            # Логирование результата
            print(f"[SUCCESS] ✅ Ответ обработан")
            
            return True
            
        except Exception as e:
            wamid = message_data.get("wa_message_id")
            waba_logger.log_error(wamid or "unknown", str(e), "process_user_message")
            logging.error(f"[MESSAGE_PROCESSOR] Error: {e}")
            # Логируем ошибку в систему Errors вместо отправки fallback
            await self.error_service.log_error(
                error=e,
                sender_id=message_data.get('sender_id'),
                session_id=session_id if 'session_id' in locals() else None,
                context_data={"message_data": message_data, "wamid": wamid},
                module="message_processor",
                function="process_user_message"
            )
            return True  # Возвращаем True, чтобы не отправлять fallback

    async def _ensure_user_exists(self, sender_id: str, sender_name: str):
        """Создает пользователя если не существует"""
        user = await self.user_service.get_user(sender_id)
        if not user:
            user = User(
                sender_id=sender_id,
                name=sender_name or "Unknown",
                language="auto",  # Язык будет определяться в сессии
                status=UserStatus.ACTIVE
            )
            await self.user_service.create_user(user)

    def _create_user_message(self, message_data: dict, session_id: str) -> Message:
        """Создает объект сообщения пользователя"""
        # Определяем язык и переводим
        user_lang = self.session_service.get_user_language_sync(message_data['sender_id'], session_id)
        if user_lang == 'auto' or not user_lang:
            user_lang = self.ai_service.detect_language(message_data['message_text'])
            self.session_service.save_user_language_sync(message_data['sender_id'], session_id, user_lang)
        
        text, text_en, text_thai = self.ai_service.translate_user_message(message_data['message_text'], user_lang)
        
        # Сохраняем имя пользователя
        if message_data.get('sender_name'):
            self.session_service.save_user_info_sync(message_data['sender_id'], message_data['sender_name'])
        
        return Message(
            sender_id=message_data['sender_id'],
            session_id=session_id,
            role=MessageRole.USER,
            content=text,
            content_en=text_en,
            content_thai=text_thai,
            wa_message_id=message_data.get('wa_message_id'),
            timestamp=datetime.now(),
            image_url=message_data.get('image_url'),
            audio_url=message_data.get('audio_url'),
            audio_duration=message_data.get('audio_duration'),
            transcription=message_data.get('transcription')
        )

    def _create_ai_message(self, ai_response: AIResponse, sender_id: str, session_id: str) -> Message:
        """Создает объект сообщения AI"""
        # Если есть команда, но нет текста, используем placeholder
        content = ai_response.text if ai_response.text and ai_response.text.strip() else "[COMMAND]"
        content_en = ai_response.text_en if ai_response.text_en and ai_response.text_en.strip() else "[COMMAND]"
        content_thai = ai_response.text_thai if ai_response.text_thai and ai_response.text_thai.strip() else "[COMMAND]"
        
        return Message(
            sender_id=sender_id,
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            content=content,
            content_en=content_en,
            content_thai=content_thai,
            wa_message_id=None,
            timestamp=datetime.now()
        )

    async def _process_ai(self, message_data: Dict[str, Any], session_id: str, conversation_history: List[Dict]) -> AIResponse:
        """Обрабатывает сообщение через AI"""
        try:
            # Конвертируем историю в объекты Message
            ai_messages = []
            for msg_dict in conversation_history:
                message = Message(
                    sender_id=message_data['sender_id'],
                    session_id=session_id,
                    role=MessageRole.USER if msg_dict.get('role') == 'user' else MessageRole.ASSISTANT,
                    content=msg_dict.get('content', ''),
                    content_en=msg_dict.get('content_en'),
                    content_thai=msg_dict.get('content_thai')
                )
                ai_messages.append(message)
            
            # Получаем язык пользователя
            user_lang = await self.session_service.get_user_language(message_data['sender_id'], session_id)
            
            # Проверяем, нужно ли определить язык
            if user_lang == 'auto' or not user_lang:
                detection_result = self.ai_service.detect_language_with_confidence(message_data['message_text'])
                detected_lang = detection_result['language']
                confidence = detection_result['confidence']
                should_ask = detection_result['should_ask']
                
                if detected_lang != 'auto':
                    # Сохраняем определенный язык
                    await self.session_service.save_user_language(message_data['sender_id'], session_id, detected_lang)
                    user_lang = detected_lang
                    
                    # Логируем результат определения языка
                    print(f"[LANGUAGE_DETECTION] Text: '{message_data['message_text']}' -> {detected_lang} (confidence: {confidence:.2f}, should_ask: {should_ask})")
                    
                    if should_ask:
                        # Возвращаем сообщение с подтверждением языка
                        confirmation_text = self.ai_service.ask_language_confirmation(message_data['message_text'], detected_lang)
                        return AIResponse(
                            text=confirmation_text,
                            text_en=confirmation_text,
                            text_thai=confirmation_text,
                            command=None
                        )
            
            # Определяем, является ли это первым сообщением в диалоге
            is_first_message = len(conversation_history) <= 1
            
            # Генерируем ответ AI
            ai_text, ai_text_en, ai_text_thai, ai_command = await self.ai_service.generate_response(
                ai_messages,
                user_lang=user_lang,
                sender_name=message_data.get('sender_name'),
                is_first_message=is_first_message
            )
            
            return AIResponse(ai_text, ai_text_en, ai_text_thai, ai_command)
            
        except Exception as e:
            logging.error(f"[MESSAGE_PROCESSOR] AI processing error: {e}")
            # Логируем ошибку в систему Errors вместо возврата fallback
            await self.error_service.log_error(
                error=e,
                sender_id=message_data['sender_id'],
                session_id=session_id,
                context_data={"message_data": message_data},
                module="message_processor",
                function="_process_ai"
            )
            # Возвращаем пустой ответ, чтобы система НЕ отправляла fallback
            return AIResponse("", "", "", None)

    async def _handle_ai_command(self, command: Dict[str, Any], session_id: str, sender_id: str, wamid: str = None) -> Dict[str, Any]:
        """Обрабатывает команду от AI и возвращает результат"""
        try:
            command_result = await self.command_service.handle_command(command, session_id, sender_id)
            if wamid:
                waba_logger.log_command_handled(wamid, command.get('type', ''), command_result)
            return command_result
        except Exception as e:
            # Логируем ошибку в систему Errors вместо отправки пользователю
            await self.error_service.log_error(
                error=e,
                sender_id=sender_id,
                session_id=session_id,
                context_data={"command": command, "wamid": wamid},
                module="message_processor",
                function="_handle_ai_command"
            )
            logging.error(f"[MESSAGE_PROCESSOR] Command handling error: {e}")
            return {"status": "error", "message": "Internal error occurred"}

    async def _send_ai_response(self, ai_response: AIResponse, sender_id: str, session_id: str, wamid: str = None, retry_count: int = 0) -> bool:
        """Отправляет ответ AI пользователю"""
        try:
            # Проверяем, есть ли валидный ответ от AI
            has_text = ai_response.text and ai_response.text.strip()
            has_command = ai_response.command is not None
            
            # Если нет ни текста, ни команды - это ошибка AI, НЕ отправляем fallback
            if not has_text and not has_command:
                print(f"[MESSAGE_PROCESSOR] AI returned empty response - logging error, NOT sending fallback")
                await self.error_service.log_error(
                    error=Exception("AI returned empty response (no text, no command)"),
                    sender_id=sender_id,
                    session_id=session_id,
                    context_data={"ai_response": str(ai_response), "wamid": wamid},
                    module="message_processor",
                    function="_send_ai_response"
                )
                return True  # Возвращаем True, чтобы не отправлять fallback
            
            # 1. Если есть текстовый ответ от AI, отправляем его
            if has_text:
                success = await self._send_text_message(
                    sender_id, 
                    ai_response.text, 
                    session_id, 
                    ai_response.text_en, 
                    ai_response.text_thai
                )
                if wamid:
                    waba_logger.log_message_sent(wamid, sender_id, ai_response.text)
                
                if not success:
                    return False
            
            # 2. Если есть команда, выполняем её
            if has_command:
                command_type = ai_response.command.get('type') if isinstance(ai_response.command, dict) else None
                if not command_type or command_type not in self.SUPPORTED_COMMANDS:
                    # Логируем ошибку в Errors
                    await self.error_service.log_error(
                        error=Exception(f"Unknown AI command: {command_type}"),
                        sender_id=sender_id,
                        session_id=session_id,
                        ai_response=str(ai_response.command),
                        context_data={"command": ai_response.command, "wamid": wamid},
                        module="message_processor",
                        function="_send_ai_response"
                    )
                    # Повторно отправляем запрос к AI при ошибке парсинга команды
                    if retry_count < 3:
                        logger.warning(f"Unknown command '{command_type}' from AI, retrying... (attempt {retry_count + 1})")
                        # Получаем историю сообщений для повторного запроса
                        conversation_history = await self.message_service.get_conversation_history_for_ai_by_sender(sender_id, session_id, limit=100)
                        # Повторно обрабатываем через AI
                        new_ai_response = await self._process_ai(
                            {"sender_id": sender_id, "message_text": conversation_history[-1].get('content', '') if conversation_history else ""},
                            session_id,
                            conversation_history
                        )
                        return await self._send_ai_response(new_ai_response, sender_id, session_id, wamid, retry_count + 1)
                    else:
                        logger.error(f"Max retries reached for unknown command: {command_type}")
                        return True  # Возвращаем True, чтобы не отправлять fallback
                
                command_result = await self._handle_ai_command(ai_response.command, session_id, sender_id, wamid)
                
                # Логируем результат команды
                if wamid and isinstance(ai_response.command, dict):
                    waba_logger.log_command_handled(wamid, ai_response.command.get('type', ''), command_result)
                
                # Если команда не выполнена, НЕ отправляем ошибку пользователю
                if command_result.get('status') != 'success':
                    print(f"[MESSAGE_PROCESSOR] Command failed: {command_result.get('message')} - logging error, NOT sending fallback")
                    await self.error_service.log_error(
                        error=Exception(f"Command execution failed: {command_result.get('message')}"),
                        sender_id=sender_id,
                        session_id=session_id,
                        context_data={"command": ai_response.command, "result": command_result, "wamid": wamid},
                        module="message_processor",
                        function="_send_ai_response"
                    )
                    return True  # Возвращаем True, чтобы не отправлять fallback
                
                # Обрабатываем специальные команды
                if command_result.get('action') == 'order_confirmed':
                    # Заказ подтвержден - оставляем текущую сессию
                    print(f"[MESSAGE_PROCESSOR] Заказ подтвержден, оставляем текущую сессию: {session_id}")
                    
                    # НЕ отправляем дополнительное сообщение - AI уже отправил финальный ответ
            
            return True
            
        except Exception as e:
            logging.error(f"[MESSAGE_PROCESSOR] Send response error: {e}")
            # Логируем ошибку, но НЕ отправляем fallback пользователю
            await self.error_service.log_error(
                error=e,
                sender_id=sender_id,
                session_id=session_id,
                context_data={"wamid": wamid},
                module="message_processor",
                function="_send_ai_response"
            )
            return True  # Возвращаем True, чтобы не отправлять fallback

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

    def _get_completion_messages(self, user_lang: str) -> Dict[str, str]:
        """Возвращает сообщения о завершении заказа на разных языках"""
        if user_lang == 'en':
            return {
                'ru': '✅ Your order has been sent! Wait for a call from the operator. 🌸',
                'en': '✅ Your order has been sent! Wait for a call from the operator. 🌸',
                'th': '✅ คำสั่งซื้อของคุณถูกส่งแล้ว! รอการโทรจากผู้ปฏิบัติงาน 🌸'
            }
        elif user_lang == 'th':
            return {
                'ru': '✅ คำสั่งซื้อของคุณถูกส่งแล้ว! รอการโทรจากผู้ปฏิบัติงาน 🌸',
                'en': '✅ Your order has been sent! Wait for a call from the operator. 🌸',
                'th': '✅ คำสั่งซื้อของคุณถูกส่งแล้ว! รอการโทรจากผู้ปฏิบัติงาน 🌸'
            }
        else:  # ru или auto
            return {
                'ru': '✅ Ваш заказ отправлен! Ожидайте звонка от оператора. 🌸',
                'en': '✅ Your order has been sent! Wait for a call from the operator. 🌸',
                'th': '✅ คำสั่งซื้อของคุณถูกส่งแล้ว! รอการโทรจากผู้ปฏิบัติงาน 🌸'
            }

    def _get_newses_messages(self, user_lang: str, session_id: str) -> Dict[str, str]:
        """Возвращает сообщения о создании новой сессии на разных языках"""
        if user_lang == 'en':
            return {
                'ru': f'✅ New session created! ID: {session_id}\n\nYou can now start a new dialogue. 🌸',
                'en': f'✅ New session created! ID: {session_id}\n\nYou can now start a new dialogue. 🌸',
                'th': f'✅ สร้างเซสชันใหม่แล้ว! ID: {session_id}\n\nตอนนี้คุณสามารถเริ่มการสนทนาใหม่ได้ 🌸'
            }
        elif user_lang == 'th':
            return {
                'ru': f'✅ สร้างเซสชันใหม่แล้ว! ID: {session_id}\n\nตอนนี้คุณสามารถเริ่มการสนทนาใหม่ได้ 🌸',
                'en': f'✅ New session created! ID: {session_id}\n\nYou can now start a new dialogue. 🌸',
                'th': f'✅ สร้างเซสชันใหม่แล้ว! ID: {session_id}\n\nตอนนี้คุณสามารถเริ่มการสนทนาใหม่ได้ 🌸'
            }
        else:  # ru или auto
            return {
                'ru': f'✅ Новая сессия создана! ID: {session_id}\n\nТеперь вы можете начать новый диалог. 🌸',
                'en': f'✅ New session created! ID: {session_id}\n\nYou can now start a new dialogue. 🌸',
                'th': f'✅ สร้างเซสชันใหม่แล้ว! ID: {session_id}\n\nตอนนี้คุณสามารถเริ่มการสนทนาใหม่ได้ 🌸'
            }

    async def _send_text_message(self, to_number: str, content: str, session_id: str, content_en: str = None, content_thai: str = None) -> bool:
        """Отправляет текстовое сообщение"""
        try:
            # Получаем язык пользователя
            user_lang = await self.session_service.get_user_language(to_number, session_id)
            
            # Логирование отправки
            print(f"[SEND] Отправляем пользователю {to_number}: {content[:100]}... (lang={user_lang})")
            
            # Отправляем через WhatsApp (эмодзи добавляется автоматически)
            message_id = await self.whatsapp_client.send_text_message(to_number, content, session_id)
            
            # Сохраняем в БД
            if message_id and session_id:
                message = Message(
                    sender_id=to_number,
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=content,
                    content_en=content_en,
                    content_thai=content_thai,
                    wa_message_id=message_id,
                    timestamp=datetime.now()
                )
                await self.message_service.add_message_to_conversation(message)
            
            if message_id:
                print(f"[SEND] Сообщение отправлено успешно, ID: {message_id}")
            else:
                print(f"[SEND] Ошибка отправки сообщения")
            
            return message_id is not None
            
        except Exception as e:
            logging.error(f"[MESSAGE_PROCESSOR] Send text error: {e}")
            return False

    async def _handle_newses_command(self, sender_id: str, session_id: str) -> bool:
        """Обрабатывает команду создания новой сессии"""
        try:
            new_session_id = await self.session_service.create_new_session_after_order(sender_id)
            user_lang = await self.session_service.get_user_language(sender_id, session_id)
            confirmation_messages = self._get_newses_messages(user_lang, new_session_id)
            return await self._send_text_message(sender_id, confirmation_messages['ru'], session_id, confirmation_messages['en'], confirmation_messages['th'])
        except Exception as e:
            logging.error(f"[MESSAGE_PROCESSOR] Newses command error: {e}")
            return False

    async def _send_status_updates(self, wamid: str, sender_id: str):
        """Отправляет статусы (прочитано + печатает)"""
        try:
            # 1. Отмечаем сообщение как прочитанное
            read_success = await self.whatsapp_client.mark_message_as_read(wamid)
            if read_success:
                # print(f"[STATUS] Сообщение {wamid} отмечено как прочитанное")
                if wamid:
                    waba_logger.log_status_sent(wamid, sender_id, "read")
            
            # 2. Отправляем индикатор печатания
            typing_success = await self.whatsapp_client.send_typing_indicator(wamid)
            if typing_success:
                # print(f"[STATUS] Индикатор печатания отправлен для {wamid}")
                if wamid:
                    waba_logger.log_status_sent(wamid, sender_id, "typing")
            
            return True
            
        except Exception as e:
            logging.error(f"[MESSAGE_PROCESSOR] Send status updates error: {e}")
            return False 
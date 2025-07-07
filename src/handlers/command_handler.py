"""
Обработчик команд от AI
"""

from typing import Optional
from src.services.session_service import SessionService
from src.services.catalog_sender import handle_send_catalog

class CommandHandler:
    """Обработчик команд от AI (каталог, заказы и т.д.)"""
    
    def __init__(self):
        self.session_service = SessionService()
    
    async def process_command(self, sender_id: str, ai_command: dict) -> bool:
        """
        Обрабатывает команду от AI.
        
        Args:
            sender_id: ID пользователя WhatsApp
            ai_command: Команда от AI
            
        Returns:
            bool: True если команда обработана успешно
        """
        if not ai_command:
            return False
        
        command_type = ai_command.get('type')
        print(f"[COMMAND] Обрабатываем команду: {command_type}")
        
        if command_type == 'send_catalog':
            return await self._handle_send_catalog(sender_id)
        
        # TODO: Добавить обработку других команд
        # elif command_type == 'save_order_info':
        #     return await self._handle_save_order_info(sender_id, ai_command)
        # elif command_type == 'confirm_order':
        #     return await self._handle_confirm_order(sender_id, ai_command)
        
        print(f"[COMMAND] Неизвестная команда: {command_type}")
        return False
    
    async def _handle_send_catalog(self, sender_id: str) -> bool:
        """Обрабатывает команду отправки каталога"""
        print(f"[CATALOG] Отправляем каталог пользователю {sender_id}")
        
        try:
            # Проверяем, не отправляется ли уже каталог
            if hasattr(self, '_catalog_sending') and self._catalog_sending.get(sender_id, False):
                print(f"[CATALOG] Каталог уже отправляется пользователю {sender_id}, пропускаем")
                return True
            
            # Отмечаем, что каталог отправляется
            if not hasattr(self, '_catalog_sending'):
                self._catalog_sending = {}
            self._catalog_sending[sender_id] = True
            
            try:
                # Получаем session_id для отправки каталога
                session_id = await self.session_service.get_or_create_session_id(sender_id)
                
                # Отправляем каталог
                success = await handle_send_catalog(sender_id, sender_id, session_id)
                
                if success:
                    print(f"[CATALOG] Каталог отправлен успешно")
                else:
                    print(f"[CATALOG] Ошибка отправки каталога")
                
                return success
                
            finally:
                # Снимаем флаг отправки
                self._catalog_sending[sender_id] = False
            
        except Exception as e:
            print(f"[CATALOG_ERROR] Ошибка отправки каталога: {e}")
            # Снимаем флаг отправки в случае ошибки
            if hasattr(self, '_catalog_sending'):
                self._catalog_sending[sender_id] = False
            return False 
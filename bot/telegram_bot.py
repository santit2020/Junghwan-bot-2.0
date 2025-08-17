import logging
import asyncio
from typing import Optional
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from .handlers import setup_handlers
from .conversation_manager import ConversationManager
from .broadcast_manager import BroadcastManager
from .user_manager import UserManager
from .gemini_client import GeminiClient
from .personality import PersonalityManager
from config.settings import Settings

class TelegramBot:
    """Main Telegram bot class that orchestrates all components."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize bot with enhanced properties
        default_properties = DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True
        )
        
        self.bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=default_properties
        )
        
        self.dp = Dispatcher()
        
        # Initialize core components
        self.gemini_client = GeminiClient(settings.GEMINI_API_KEY)
        self.personality = PersonalityManager(settings)
        self.user_manager = UserManager()
        self.conversation_manager = ConversationManager(
            gemini_client=self.gemini_client,
            personality=self.personality,
            settings=settings
        )
        self.broadcast_manager = BroadcastManager(
            bot=self.bot,
            user_manager=self.user_manager,
            owner_id=settings.BOT_OWNER_ID
        )
        
        # Setup handlers
        setup_handlers(
            dp=self.dp,
            conversation_manager=self.conversation_manager,
            broadcast_manager=self.broadcast_manager,
            user_manager=self.user_manager,
            settings=settings
        )
        
        self.logger.info("TelegramBot initialized successfully")
    
    async def start_polling(self):
        """Start the bot with polling."""
        try:
            # Get bot info and log
            bot_info = await self.bot.get_me()
            self.logger.info(f"Bot started: @{bot_info.username} ({bot_info.full_name})")
            
            # Start polling
            await self.dp.start_polling(
                self.bot,
                allowed_updates=['message', 'callback_query', 'chat_member']
            )
            
        except TelegramAPIError as e:
            self.logger.error(f"Telegram API error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during polling: {e}")
            raise
    
    async def stop(self):
        """Gracefully stop the bot."""
        try:
            await self.dp.stop_polling()
            await self.bot.session.close()
            self.logger.info("Bot stopped gracefully")
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
    
    async def send_message_safe(self, chat_id: int, text: str, **kwargs) -> Optional[bool]:
        """Send message with error handling."""
        try:
            await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
            return True
        except TelegramAPIError as e:
            self.logger.warning(f"Failed to send message to {chat_id}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending message to {chat_id}: {e}")
            return False

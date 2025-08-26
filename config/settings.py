import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Central configuration management for the bot."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Required Environment Variables
        self.TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        
        # Bot Identity
        self.BOT_NAME = os.getenv("BOT_NAME", "Junghwan")
        self.BOT_USERNAME = os.getenv("BOT_USERNAME", "")
        self.BOT_OWNER_NAME = os.getenv("BOT_OWNER_NAME", "@santit2020")
        self.BOT_OWNER_ID = int(os.getenv("BOT_OWNER_ID", "123456789"))
        self.GR_NAME = os.getenv("GR_NAME", "Tech Group")
        self.BOT_PERSONALITY = os.getenv("BOT_PERSONALITY", "friendly and natural conversationalist")
        
        # Conversation Settings
        self.MAX_CONTEXT_MESSAGES = int(os.getenv("MAX_CONTEXT_MESSAGES", "10"))
        self.CONTEXT_TIMEOUT_HOURS = int(os.getenv("CONTEXT_TIMEOUT_HOURS", "2"))
        # Rate limiting disabled for better user experience
        self.RATE_LIMIT_MESSAGES = int(os.getenv("RATE_LIMIT_MESSAGES", "999999"))
        
        # AI Model Settings
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-001")
        self.AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.9"))
        self.AI_TOP_P = float(os.getenv("AI_TOP_P", "0.95"))
        self.AI_TOP_K = int(os.getenv("AI_TOP_K", "40"))
        self.AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "500"))
        
        # Group Chat Settings  
        self.GROUP_MAX_MESSAGE_LENGTH = int(os.getenv("GROUP_MAX_MESSAGE_LENGTH", "400"))
        
        # Logging Settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Deployment Settings
        self.PORT = int(os.getenv("PORT", "8000"))
        self.HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
        
        # Data Storage
        self.DATA_FILE = os.getenv("DATA_FILE", "user_data.json")
        self.BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
       
        # Data Storage
         DATA_FILE: str = Field(default="user_data.json")
        BACKUP_INTERVAL_HOURS: int = Field(default=24)
    
        # Database settings
        MONGODB_URL: str = Field(default="mongodb://localhost:5432/junghwan_bot")

       # Rate limiting settings
       RATE_LIMIT_RPM: int = Field(default=45)
       RATE_LIMIT_RPH: int = Field(default=1000)
       MAX_RETRIES: int = Field(default=3)

        
        # Security Settings
        self.ALLOWED_UPDATES = ["message", "callback_query", "chat_member"]
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
        
        self.logger.info("Settings initialized successfully")
    
    def validate(self):
        """Validate required environment variables."""
        errors = []
        
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if self.BOT_OWNER_ID == 0 or self.BOT_OWNER_ID == 123456789:
            errors.append("BOT_OWNER_ID must be set to a valid Telegram user ID")
        
        # Validate numeric ranges
        if not (0.0 <= self.AI_TEMPERATURE <= 2.0):
            errors.append("AI_TEMPERATURE must be between 0.0 and 2.0")
        
        if not (0.0 <= self.AI_TOP_P <= 1.0):
            errors.append("AI_TOP_P must be between 0.0 and 1.0")
        
        if not (1 <= self.AI_TOP_K <= 100):
            errors.append("AI_TOP_K must be between 1 and 100")
        
        
        
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            self.logger.error(error_message)
            raise ValueError(error_message)
        
        self.logger.info("Configuration validation passed")
    
    def get_bot_info(self) -> dict:
        """Get bot information for display."""
        return {
            "name": self.BOT_NAME,
            "username": self.BOT_USERNAME,
            "owner": self.BOT_OWNER_NAME,
            "group": self.GR_NAME,
            "personality": self.BOT_PERSONALITY,
            "model": self.GEMINI_MODEL,
            "version": "2.0.0"
        }
    
    def get_ai_config(self) -> dict:
        """Get AI model configuration."""
        return {
            "model": self.GEMINI_MODEL,
            "temperature": self.AI_TEMPERATURE,
            "top_p": self.AI_TOP_P,
            "top_k": self.AI_TOP_K,
            "max_tokens": self.AI_MAX_TOKENS
        }
    
    def get_conversation_config(self) -> dict:
        """Get conversation management configuration."""
        return {
            "max_context_messages": self.MAX_CONTEXT_MESSAGES,
            "context_timeout_hours": self.CONTEXT_TIMEOUT_HOURS,
            "rate_limit_messages": self.RATE_LIMIT_MESSAGES,
            "group_max_message_length": self.GROUP_MAX_MESSAGE_LENGTH
        }
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is the bot owner."""
        is_owner = user_id == self.BOT_OWNER_ID
        if is_owner:
            self.logger.info(f"Owner access granted for user {user_id}")
        return is_owner
    
    def get_owner_info(self) -> dict:
        """Get comprehensive owner information."""
        return {
            "owner_id": self.BOT_OWNER_ID,
            "owner_name": self.BOT_OWNER_NAME,
            "bot_name": self.BOT_NAME,
            "group_name": self.GR_NAME,
            "is_configured": self.BOT_OWNER_ID != 0 and self.BOT_OWNER_ID != 123456789
        }
    
    def __str__(self):
        """String representation of settings (without sensitive data)."""
        return f"Settings(bot_name={self.BOT_NAME}, owner={self.BOT_OWNER_NAME}, model={self.GEMINI_MODEL})"

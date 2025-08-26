import logging
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Required tokens
    TELEGRAM_BOT_TOKEN: str
    GEMINI_API_KEY: str

    # Bot Identity
    BOT_NAME: str = Field(default="Junghwan")
    BOT_USERNAME: str = Field(default="")
    BOT_OWNER_NAME: str = Field(default="@santit2020")
    BOT_OWNER_ID: int = Field(default=123456789)
    GR_NAME: str = Field(default="Tech Group")
    BOT_PERSONALITY: str = Field(default="friendly and natural conversationalist")

    # Conversation Settings
    MAX_CONTEXT_MESSAGES: int = Field(default=10)
    CONTEXT_TIMEOUT_HOURS: int = Field(default=2)
    RATE_LIMIT_MESSAGES: int = Field(default=999999)  # Disabled rate limiting
    
    # AI Model Settings
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash-001")
    AI_TEMPERATURE: float = Field(default=0.9)
    AI_TOP_P: float = Field(default=0.95)
    AI_TOP_K: int = Field(default=40)
    AI_MAX_TOKENS: int = Field(default=500)

    # Group Chat Settings
    GROUP_MAX_MESSAGE_LENGTH: int = Field(default=400)

    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO")

    # Deployment Settings
    PORT: int = Field(default=8000)
    HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # Data Storage
    DATA_FILE: str = Field(default="user_data.json")
    BACKUP_INTERVAL_HOURS: int = Field(default=24)
    
    # Database settings
    MONGODB_URL: str = Field(default="mongodb://localhost:5432/junghwan_bot")

    # Rate limiting settings
    RATE_LIMIT_RPM: int = Field(default=45)
    RATE_LIMIT_RPH: int = Field(default=1000)
    MAX_RETRIES: int = Field(default=3)

    # Bot behavior settings
    DEFAULT_LANGUAGE: str = Field(default="english")
    RESPONSE_TIMEOUT: float = Field(default=30.0)

    # Database cleanup settings
    MESSAGE_RETENTION_DAYS: int = Field(default=90)
    
    # Security Settings
    ALLOWED_UPDATES: list[str] = Field(default_factory=lambda: ["message", "callback_query", "chat_member"])
    MAX_FILE_SIZE_MB: int = Field(default=20)

    model_config = {
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'case_sensitive': False,
        'populate_by_name': True,
        'extra': 'ignore',
    }

    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_up = v.upper()
        if v_up not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return v_up

    @field_validator('command_prefix', pre=True, always=True)
    @classmethod
    def validate_command_prefix(cls, v):
        if v is None or len(v) > 3:
            raise ValueError('Command prefix must be 1-3 characters long')
        return v
    
    @field_validator('RATE_LIMIT_RPM')
    @classmethod
    def validate_rpm(cls, v):
        if v <= 0 or v > 60:
            raise ValueError('Requests per minute must be between 1 and 60')
        return v

    @field_validator('RATE_LIMIT_RPH')
    @classmethod
    def validate_rph(cls, v):
        if v <= 0 or v > 10000:
            raise ValueError('Requests per hour must be between 1 and 10000')
        return v

    def validate(self):
        errors = []
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not self.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY is required")
        
        if self.BOT_OWNER_ID == 0 or self.BOT_OWNER_ID == 123456789:
            errors.append("BOT_OWNER_ID must be set to a valid Telegram user ID")
        
        if not (0.0 <= self.AI_TEMPERATURE <= 2.0):
            errors.append("AI_TEMPERATURE must be between 0.0 and 2.0")
        
        if not (0.0 <= self.AI_TOP_P <= 1.0):
            errors.append("AI_TOP_P must be between 0.0 and 1.0")
        
        if not (1 <= self.AI_TOP_K <= 100):
            errors.append("AI_TOP_K must be between 1 and 100")

        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_message)

    def get_bot_info(self) -> dict:
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
        return {
            "model": self.GEMINI_MODEL,
            "temperature": self.AI_TEMPERATURE,
            "top_p": self.AI_TOP_P,
            "top_k": self.AI_TOP_K,
            "max_tokens": self.AI_MAX_TOKENS
        }

    def get_conversation_config(self) -> dict:
        return {
            "max_context_messages": self.MAX_CONTEXT_MESSAGES,
            "context_timeout_hours": self.CONTEXT_TIMEOUT_HOURS,
            "rate_limit_messages": self.RATE_LIMIT_MESSAGES,
            "group_max_message_length": self.GROUP_MAX_MESSAGE_LENGTH
        }

    def is_owner(self, user_id: int) -> bool:
        is_owner = user_id == self.BOT_OWNER_ID
        return is_owner

    def get_owner_info(self) -> dict:
        return {
            "owner_id": self.BOT_OWNER_ID,
            "owner_name": self.BOT_OWNER_NAME,
            "bot_name": self.BOT_NAME,
            "group_name": self.GR_NAME,
            "is_configured": self.BOT_OWNER_ID != 0 and self.BOT_OWNER_ID != 123456789
        }

    def __str__(self):
        return f"Settings(bot_name={self.BOT_NAME}, owner={self.BOT_OWNER_NAME}, model={self.GEMINI_MODEL})"


# Example usage
if __name__ == "__main__":
    settings = Settings()
    try:
        settings.validate()
    except Exception as e:
        print(f"Settings validation error: {e}")
    else:
        print(f"Loaded Settings: {settings}")

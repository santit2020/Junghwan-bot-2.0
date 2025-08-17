import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

from .gemini_client import GeminiClient
from .personality import PersonalityManager
from .utils import detect_language_and_tone
from config.settings import Settings

class ConversationContext:
    """Stores conversation context for a user."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages: List[Dict] = []
        self.last_activity = datetime.now()
        self.language = "en"
        self.tone = "casual"
        self.conversation_state = {}

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only recent messages to prevent context overflow
        if len(self.messages) > 20:  # Increased from 10 for better context
            self.messages = self.messages[-20:]

        self.last_activity = datetime.now()

    def get_recent_context(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation context."""
        return self.messages[-limit:] if self.messages else []

    def is_expired(self, timeout_hours: int = 2) -> bool:
        """Check if conversation context has expired."""
        return datetime.now() - self.last_activity > timedelta(hours=timeout_hours)

class ConversationManager:
    """Manages conversations and AI responses."""

    def __init__(self, gemini_client: GeminiClient, personality: PersonalityManager, settings: Settings):
        self.gemini_client = gemini_client
        self.personality = personality
        self.settings = settings
        self.logger = logging.getLogger(__name__)

        # User contexts
        self.contexts: Dict[int, ConversationContext] = {}

        # Rate limiting (disabled)
        # self.rate_limits: Dict[int, List[datetime]] = {}

        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_contexts())

        self.logger.info("ConversationManager initialized")

    def get_user_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get chat history for a specific user (owner only feature)."""
        if user_id in self.contexts:
            context = self.contexts[user_id]
            # Return all messages with timestamps, limited by the specified amount
            messages = context.messages[-limit:] if limit else context.messages
            return [{
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "language": context.language,
                "tone": context.tone
            } for msg in messages]
        return []

    def get_all_active_users(self) -> List[int]:
        """Get list of all users with conversation contexts."""
        return list(self.contexts.keys())

    async def get_response(
        self, 
        message: str, 
        user_id: int, 
        chat_type: str = "private",
        user_name: str = None
    ) -> Optional[str]:
        """Get AI response for a message."""
        try:
            # Rate limiting disabled for better user experience
            # if not self._check_rate_limit(user_id):
            #     self.logger.warning(f"Rate limit exceeded for user {user_id}")
            #     return "Whoa, slow down there! Give me a sec to catch up. 😅"

            # Get or create conversation context
            context = self._get_context(user_id)

            # Detect language and tone
            language, tone = detect_language_and_tone(message)
            context.language = language
            context.tone = tone

            # Add user message to context
            context.add_message("user", message)

            # Create system prompt with personality
            system_prompt = self.personality.create_system_prompt(chat_type, user_name)

            # Prepare conversation history
            conversation_history = self._prepare_conversation_history(context)

            # Get AI response
            ai_response = await self.gemini_client.generate_response(
                message=message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                language=language,
                tone=tone
            )

            if ai_response:
                # Enhance response with personality
                enhanced_response = self.personality.enhance_response(ai_response, user_name)

                # Add AI response to context
                context.add_message("assistant", enhanced_response)

                self.logger.info(f"Generated response for user {user_id} in {language} ({tone} tone)")
                return enhanced_response
            else:
                # Fallback response
                return self._get_fallback_response(tone, user_name)

        except Exception as e:
            self.logger.error(f"Error generating response for user {user_id}: {e}")
            return self._get_error_response(user_name)

    def _get_context(self, user_id: int) -> ConversationContext:
        """Get or create conversation context for user."""
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id)

        context = self.contexts[user_id]

        # Reset context if expired
        if context.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS):
            self.logger.info(f"Resetting expired context for user {user_id}")
            self.contexts[user_id] = ConversationContext(user_id)
            context = self.contexts[user_id]

        return context

    def _check_rate_limit(self, user_id: int) -> bool:
        """Rate limiting disabled - always allow messages."""
        return True
        
        # Original rate limiting code (commented out):
        # now = datetime.now()
        # minute_ago = now - timedelta(minutes=1)
        # if user_id not in self.rate_limits:
        #     self.rate_limits[user_id] = []
        # self.rate_limits[user_id] = [
        #     timestamp for timestamp in self.rate_limits[user_id] 
        #     if timestamp > minute_ago
        # ]
        # if len(self.rate_limits[user_id]) >= self.settings.RATE_LIMIT_MESSAGES:
        #     return False
        # self.rate_limits[user_id].append(now)
        # return True

    def _prepare_conversation_history(self, context: ConversationContext) -> List[Dict]:
        """Prepare conversation history for AI."""
        history = []
        recent_messages = context.get_recent_context(8)  # Get last 8 messages

        for msg in recent_messages:
            # Convert to format expected by Gemini
            role = "user" if msg["role"] == "user" else "model"
            history.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        return history

    def _get_fallback_response(self, tone: str, user_name: str = None) -> str:
        """Get a fallback response when AI fails."""
        if tone == "formal":
            responses = [
                "I apologize, but I'm having difficulty processing that right now.",
                "Could you please rephrase your question?",
                "I'm experiencing some technical difficulties at the moment."
            ]
        else:
            responses = [
                "Sorry, my brain's having a moment! Can you try that again?",
                "Hmm, I'm not sure I caught that. What were you saying?",
                "Oops, something went wrong on my end. Mind rephrasing?",
                "My thoughts are a bit scattered right now. Could you repeat that?",
                "I'm having trouble processing that. Can you say it differently?"
            ]

        import random
        response = random.choice(responses)

        if user_name and tone != "formal":
            response = f"{user_name}, {response.lower()}"

        return response

    def _get_error_response(self, user_name: str = None) -> str:
        """Get an error response when something goes wrong."""
        responses = [
            "Oof, something went wrong! Give me a sec to get back on track.",
            "My brain just glitched for a moment. What were we talking about?",
            "Technical difficulties on my end! Can you try again?",
            "Sorry, I'm having a moment here. Mind repeating that?"
        ]

        import random
        response = random.choice(responses)

        if user_name:
            response = f"Hey {user_name}, {response.lower()}"

        return response

    async def _cleanup_expired_contexts(self):
        """Periodically clean up expired conversation contexts."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                expired_users = []
                for user_id, context in self.contexts.items():
                    if context.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS):
                        expired_users.append(user_id)

                for user_id in expired_users:
                    del self.contexts[user_id]
                    if user_id in self.rate_limits:
                        del self.rate_limits[user_id]

                if expired_users:
                    self.logger.info(f"Cleaned up {len(expired_users)} expired contexts")

            except Exception as e:
                self.logger.error(f"Error in context cleanup: {e}")

    def get_conversation_stats(self) -> Dict:
        """Get conversation statistics."""
        total_contexts = len(self.contexts)
        active_contexts = sum(1 for ctx in self.contexts.values() 
                            if not ctx.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS))

        total_messages = sum(len(ctx.messages) for ctx in self.contexts.values())

        return {
            "total_contexts": total_contexts,
            "active_contexts": active_contexts,
            "total_messages": total_messages,
            "avg_messages_per_context": total_messages / max(total_contexts, 1)
        }
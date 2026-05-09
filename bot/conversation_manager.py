import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .gemini_client import GeminiClient
from .personality import PersonalityManager
from .personality_responder import PersonalityResponder
from config.settings import Settings


def detect_language_and_tone(text: str):
    text_lower = text.lower().strip()
    hindi_markers = [
        "tum", "main", "mera", "tera", "kya", "kaise", "kaisa", "kaisi",
        "kon", "kaun", "kahan", "kab", "kyun", "kyon", "nahi", "nahin",
        "hai", "ho", "hain", "hoon", "tha", "thi", "bhi", "aur",
        "se", "ko", "ki", "ka", "ke", "mein", "pe", "par", "yaar",
        "bhai", "dost", "accha", "acha", "theek", "bahut", "thoda",
        "bilkul", "zaroor", "mat", "bas", "ab", "abhi", "phir", "fir",
        "aap", "hum", "batao", "bolo", "suno", "pyar", "dil", "mast",
    ]
    sad_markers = ["sad", "cry", "crying", "depressed", "lonely", "hurt", "heartbreak",
                   "alone", "upset", "broken", "dukhi", "udaas", "rona", "akela"]
    excited_markers = ["omg", "wow", "amazing", "awesome", "yay", "waah", "mast",
                       "incredible", "fantastic", "zabardast", "kamaal"]
    formal_markers = ["please", "could you", "would you", "kindly", "regarding", "sir"]
    angry_markers = ["stupid", "idiot", "hate", "shut up", "horrible", "worst",
                     "useless", "ugh", "annoying", "bakwas", "chup"]

    words = text_lower.split()
    hindi_count = sum(1 for w in words if w in hindi_markers)
    language = "hi" if hindi_count >= 1 else "en"

    if any(m in text_lower for m in sad_markers):
        tone = "sad"
    elif any(m in text_lower for m in angry_markers):
        tone = "angry"
    elif any(m in text_lower for m in excited_markers):
        tone = "excited"
    elif any(m in text_lower for m in formal_markers):
        tone = "formal"
    else:
        tone = "casual"

    return language, tone


class ConversationContext:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages: List[Dict] = []
        self.last_activity = datetime.now()
        self.language = "en"
        self.tone = "casual"
        self.conversation_state = {}

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        if len(self.messages) > 20:
            self.messages = self.messages[-20:]
        self.last_activity = datetime.now()

    def get_recent_context(self, limit: int = 10) -> List[Dict]:
        return self.messages[-limit:] if self.messages else []

    def is_expired(self, timeout_hours: int = 2) -> bool:
        return datetime.now() - self.last_activity > timedelta(hours=timeout_hours)


class ConversationManager:
    def __init__(self, gemini_client: GeminiClient, personality: PersonalityManager, settings: Settings):
        self.gemini_client = gemini_client
        self.personality = personality
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.contexts: Dict[int, ConversationContext] = {}
        self.personality_responder = PersonalityResponder(
            bot_name=settings.BOT_NAME,
            owner_name=settings.BOT_OWNER_NAME
        )
        asyncio.create_task(self._cleanup_expired_contexts())
        self.logger.info("ConversationManager initialized")

    async def get_response(self, message: str, user_id: int,
                           chat_type: str = "private", user_name: str = None) -> Optional[str]:
        try:
            context = self._get_context(user_id)
            language, tone = detect_language_and_tone(message)
            context.language = language
            context.tone = tone
            context.add_message("user", message)

            system_prompt = self.personality.create_system_prompt(chat_type, user_name)
            conversation_history = self._prepare_conversation_history(context)

            ai_response = await self.gemini_client.generate_response(
                message=message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                language=language,
                tone=tone
            )

            if ai_response:
                enhanced = self.personality.enhance_response(ai_response, user_name)
                context.add_message("assistant", enhanced)
                self.logger.info(f"Gemini response for user {user_id} [{language}/{tone}]")
                return enhanced

            self.logger.info(f"Using personality responder for user {user_id} [{language}/{tone}]")
            local_response = self.personality_responder.get_response(
                message=message, user_name=user_name, language=language, tone=tone
            )
            context.add_message("assistant", local_response)
            return local_response

        except Exception as e:
            self.logger.error(f"Error generating response for user {user_id}: {e}")
            return self.personality_responder.get_response(
                message=message, user_name=user_name, language="en", tone="casual"
            )

    def _get_context(self, user_id: int) -> ConversationContext:
        if user_id not in self.contexts:
            self.contexts[user_id] = ConversationContext(user_id)
        context = self.contexts[user_id]
        if context.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS):
            self.logger.info(f"Resetting expired context for user {user_id}")
            self.contexts[user_id] = ConversationContext(user_id)
            context = self.contexts[user_id]
        return context

    def _prepare_conversation_history(self, context: ConversationContext) -> List[Dict]:
        history = []
        for msg in context.get_recent_context(8):
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg["content"]}]})
        return history

    async def _cleanup_expired_contexts(self):
        while True:
            try:
                await asyncio.sleep(3600)
                expired = [uid for uid, ctx in self.contexts.items()
                           if ctx.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS)]
                for uid in expired:
                    del self.contexts[uid]
                if expired:
                    self.logger.info(f"Cleaned up {len(expired)} expired contexts")
            except Exception as e:
                self.logger.error(f"Error in context cleanup: {e}")

    def get_user_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        if user_id in self.contexts:
            context = self.contexts[user_id]
            messages = context.messages[-limit:] if limit else context.messages
            return [{"role": m["role"], "content": m["content"],
                     "timestamp": m["timestamp"], "language": context.language,
                     "tone": context.tone} for m in messages]
        return []

    def get_all_active_users(self) -> List[int]:
        return list(self.contexts.keys())

    def get_conversation_stats(self) -> Dict:
        total = len(self.contexts)
        active = sum(1 for c in self.contexts.values()
                     if not c.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS))
        msgs = sum(len(c.messages) for c in self.contexts.values())
        return {"total_contexts": total, "active_contexts": active,
                "total_messages": msgs, "avg_messages_per_context": msgs / max(total, 1)}

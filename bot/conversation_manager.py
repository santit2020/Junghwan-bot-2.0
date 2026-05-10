import logging
import asyncio
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .gemini_client import GeminiClient
from .personality import PersonalityManager
from .personality_responder import PersonalityResponder
from config.settings import Settings


def detect_language_and_tone(text: str) -> Tuple[str, str]:
    if not text or not text.strip():
        return "en", "casual"

    text_stripped = text.strip()

    # Step 1: Unicode script detection (catches Hindi script, Arabic, Bengali, Tamil, etc.)
    script_counts: Dict[str, int] = {}
    for ch in text_stripped:
        if ch.isspace() or not ch.isalpha():
            continue
        try:
            name = unicodedata.name(ch, "")
        except ValueError:
            continue

        if "DEVANAGARI" in name:
            script_counts["hi"] = script_counts.get("hi", 0) + 1
        elif "ARABIC" in name:
            script_counts["ar_or_ur"] = script_counts.get("ar_or_ur", 0) + 1
        elif "BENGALI" in name:
            script_counts["bn"] = script_counts.get("bn", 0) + 1
        elif "TAMIL" in name:
            script_counts["ta"] = script_counts.get("ta", 0) + 1
        elif "TELUGU" in name:
            script_counts["te"] = script_counts.get("te", 0) + 1
        elif "GUJARATI" in name:
            script_counts["gu"] = script_counts.get("gu", 0) + 1
        elif "GURMUKHI" in name:
            script_counts["pa"] = script_counts.get("pa", 0) + 1
        elif "MALAYALAM" in name:
            script_counts["ml"] = script_counts.get("ml", 0) + 1
        elif "KANNADA" in name:
            script_counts["kn"] = script_counts.get("kn", 0) + 1
        elif "SINHALA" in name:
            script_counts["si"] = script_counts.get("si", 0) + 1
        elif "CYRILLIC" in name:
            script_counts["ru"] = script_counts.get("ru", 0) + 1
        elif "CJK" in name or "HIRAGANA" in name or "KATAKANA" in name:
            script_counts["ja"] = script_counts.get("ja", 0) + 1
        elif "HANGUL" in name:
            script_counts["ko"] = script_counts.get("ko", 0) + 1
        elif "LATIN" in name:
            script_counts["latin"] = script_counts.get("latin", 0) + 1

    if script_counts:
        dominant = max(script_counts, key=lambda k: script_counts[k])
        if dominant != "latin" and script_counts.get(dominant, 0) > 0:
            lang = dominant
            if lang == "ar_or_ur":
                urdu_words = {"hai", "hain", "kya", "nahi", "aur", "bhi", "tum", "hum", "ap", "yeh"}
                lang = "ur" if any(w in text_stripped.lower() for w in urdu_words) else "ar"
            return lang, _detect_tone(text_stripped)

    # Step 2: Latin-script keyword heuristics (catches Hinglish, Spanish, French, etc.)
    text_lower = text_stripped.lower()
    words = set(text_lower.split())

    hindi_markers = {
        "tum", "main", "mera", "tera", "kya", "kaise", "kaisa", "kaisi",
        "kon", "kaun", "kahan", "kab", "kyun", "kyon", "nahi", "nahin",
        "hai", "ho", "hain", "hoon", "tha", "thi", "bhi", "aur", "se",
        "ko", "ki", "ka", "ke", "mein", "pe", "par", "yaar", "bhai",
        "dost", "accha", "acha", "theek", "bahut", "thoda", "bilkul",
        "zaroor", "mat", "bas", "ab", "abhi", "phir", "fir", "aap",
        "hum", "batao", "bolo", "suno", "pyar", "dil", "mast", "yeh",
        "woh", "matlab", "samjha", "samjhao", "chal", "kal", "aaj",
    }
    if words & hindi_markers:
        return "hi", _detect_tone(text_stripped)

    spanish_markers = {"hola", "como", "estoy", "bien", "gracias", "quiero", "amor", "que", "por"}
    if words & spanish_markers:
        return "es", _detect_tone(text_stripped)

    french_markers = {"bonjour", "merci", "comment", "aller", "bien", "oui", "non", "je", "tu"}
    if words & french_markers:
        return "fr", _detect_tone(text_stripped)

    indonesian_markers = {"aku", "kamu", "tidak", "saya", "iya", "makasih", "gimana", "siapa"}
    if words & indonesian_markers:
        return "id", _detect_tone(text_stripped)

    turkish_markers = {"merhaba", "nasil", "evet", "hayir", "tesekkur", "nereye", "neden"}
    if words & turkish_markers:
        return "tr", _detect_tone(text_stripped)

    return "en", _detect_tone(text_stripped)


def _detect_tone(text: str) -> str:
    text_lower = text.lower()
    words = set(text_lower.split())

    sad_markers = {
        "sad", "cry", "crying", "depressed", "lonely", "hurt", "heartbreak",
        "alone", "upset", "broken", "dukhi", "udaas", "rona", "akela", "akeli",
        "dard", "tanha", "bura", "miss", "missing",
    }
    excited_markers = {
        "omg", "wow", "amazing", "awesome", "yay", "waah", "mast",
        "incredible", "fantastic", "zabardast", "kamaal",
    }
    formal_markers = {
        "please", "could you", "would you", "kindly", "regarding", "sir", "madam",
        "request", "inform", "require",
    }
    angry_markers = {
        "stupid", "idiot", "hate", "shut up", "horrible", "worst",
        "useless", "ugh", "annoying", "bakwas", "chup", "gadha", "bewakoof",
    }

    if words & sad_markers or any(m in text_lower for m in sad_markers):
        return "sad"
    if words & angry_markers or any(m in text_lower for m in angry_markers):
        return "angry"
    if words & excited_markers or any(m in text_lower for m in excited_markers):
        return "excited"
    if any(m in text_lower for m in formal_markers):
        return "formal"
    return "casual"


class ConversationContext:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.messages: List[Dict] = []
        self.last_activity = datetime.now()
        self.language = "en"
        self.tone = "casual"

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self.messages) > 30:
            self.messages = self.messages[-30:]
        self.last_activity = datetime.now()

    def get_recent_context(self, limit: int = 15) -> List[Dict]:
        return self.messages[-limit:] if self.messages else []

    def is_expired(self, timeout_hours: int = 4) -> bool:
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
            owner_name=settings.BOT_OWNER_NAME,
        )
        asyncio.create_task(self._cleanup_expired_contexts())
        self.logger.info("ConversationManager initialized")

    async def get_response(
        self,
        message: str,
        user_id: int,
        chat_type: str = "private",
        user_name: str = None,
    ) -> Optional[str]:
        try:
            context = self._get_context(user_id)
            language, tone = detect_language_and_tone(message)

            # Don't flip language back to English for very short messages
            if context.language and context.language != "en" and language == "en":
                if len(message.split()) <= 3:
                    language = context.language

            context.language = language
            context.tone = tone
            context.add_message("user", message)

            system_prompt = self.personality.create_system_prompt(
                chat_type=chat_type,
                user_name=user_name,
                language=language,
                tone=tone,
            )
            conversation_history = self._prepare_conversation_history(context)

            ai_response = await self.gemini_client.generate_response(
                message=message,
                system_prompt=system_prompt,
                conversation_history=conversation_history,
                language=language,
                tone=tone,
            )

            if ai_response:
                enhanced = self.personality.enhance_response(ai_response, user_name, language)
                context.add_message("assistant", enhanced)
                self.logger.info(f"Gemini response for user {user_id} [{language}/{tone}]")
                return enhanced

            self.logger.info(f"Using personality responder for user {user_id} [{language}/{tone}]")
            local_response = self.personality_responder.get_response(
                message=message, user_name=user_name, language=language, tone=tone,
            )
            context.add_message("assistant", local_response)
            return local_response

        except Exception as e:
            self.logger.error(f"Error generating response for user {user_id}: {e}")
            return self.personality_responder.get_response(
                message=message, user_name=user_name, language="en", tone="casual",
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
        for msg in context.get_recent_context(15):
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg["content"]}]})
        return history

    async def _cleanup_expired_contexts(self):
        while True:
            try:
                await asyncio.sleep(3600)
                expired = [
                    uid for uid, ctx in self.contexts.items()
                    if ctx.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS)
                ]
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
            return [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "timestamp": m["timestamp"],
                    "language": context.language,
                    "tone": context.tone,
                }
                for m in messages
            ]
        return []

    def get_all_active_users(self) -> List[int]:
        return list(self.contexts.keys())

    def get_conversation_stats(self) -> Dict:
        total = len(self.contexts)
        active = sum(
            1 for c in self.contexts.values()
            if not c.is_expired(self.settings.CONTEXT_TIMEOUT_HOURS)
        )
        msgs = sum(len(c.messages) for c in self.contexts.values())
        return {
            "total_contexts": total,
            "active_contexts": active,
            "total_messages": msgs,
            "avg_messages_per_context": msgs / max(total, 1),
        }

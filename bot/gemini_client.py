import logging
import asyncio
from typing import Dict, List, Optional
from google import genai
from google.genai import types


class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

        # Allow 3 concurrent requests — reduces queue wait time in groups
        self._semaphore = asyncio.Semaphore(3)
        self._min_request_gap: float = 1.5
        self._last_request_time: float = 0.0

        # Circuit breaker — more lenient thresholds
        self.failure_count = 0
        self.max_failures = 15
        self.circuit_open = False
        self.circuit_reset_time: Optional[float] = None
        self._circuit_open_duration: float = 60.0

        self.logger.info(f"GeminiClient initialized with model: {self.model}")

    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        conversation_history: List[Dict] = None,
        language: str = "en",
        tone: str = "casual",
    ) -> Optional[str]:
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker open — using local fallback")
            return None

        contents = []
        if conversation_history:
            contents.extend(conversation_history)
        contents.append({"role": "user", "parts": [{"text": message}]})

        token_budget = self._estimate_token_budget(message, tone)

        async with self._semaphore:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_gap:
                await asyncio.sleep(self._min_request_gap - elapsed)

            try:
                self._last_request_time = asyncio.get_event_loop().time()

                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.92,
                        top_p=0.95,
                        top_k=64,
                        max_output_tokens=token_budget,
                        candidate_count=1,
                    ),
                )

                if response and response.text:
                    self.failure_count = 0
                    self.circuit_open = False
                    return self._clean_response(response.text.strip(), language)
                else:
                    self.logger.warning("Empty Gemini response")
                    return None

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    self.logger.warning("Gemini rate limit — using local personality response")
                    self._handle_failure()
                    return None
                elif "404" in error_str or "NOT_FOUND" in error_str:
                    self.logger.error(
                        f"Gemini model '{self.model}' not found. "
                        "Check GEMINI_MODEL in your .env. Using local response."
                    )
                    return None
                else:
                    self.logger.error(f"Gemini error: {e}")
                    self._handle_failure()
                    return None

    def _estimate_token_budget(self, message: str, tone: str) -> int:
        msg_len = len(message)
        deep_keywords = [
            "why", "how", "explain", "what is", "what are", "tell me about",
            "advice", "help me", "problem", "think", "feel", "sad", "depressed",
            "code", "error", "fix", "issue", "understand", "relationship",
            "philosophy", "meaning", "life", "kya", "kaise", "kyun", "batao",
            "samjhao", "problem hai", "help karo",
        ]
        is_deep = (
            msg_len > 80 or
            any(kw in message.lower() for kw in deep_keywords) or
            tone in ("sad", "formal")
        )
        return 800 if is_deep else 400

    def _clean_response(self, text: str, language: str = "en") -> str:
        try:
            text = text.replace("**", "").replace("*", "")

            ai_phrases = [
                "I'm an AI", "As an AI", "I'm here to help", "As a language model",
                "I'm a chatbot", "I'm a bot", "I'm an assistant", "I'm designed to",
                "My purpose is", "I was created to", "I'm programmed to",
                "I don't have feelings", "I can't experience", "I lack the capacity",
                "How can I assist", "Is there anything else", "I hope this helps",
            ]
            for phrase in ai_phrases:
                if phrase.lower() in text.lower():
                    sentences = text.split(". ")
                    text = ". ".join(s for s in sentences if phrase.lower() not in s.lower())

            if len(text) > 1000:
                sentences = text.split(". ")
                truncated, count = [], 0
                for s in sentences:
                    if count + len(s) > 900:
                        break
                    truncated.append(s)
                    count += len(s)
                text = ". ".join(truncated) if truncated else text[:900] + "..."
                if truncated and not text.endswith("."):
                    text += "."

            return text.strip()
        except Exception as e:
            self.logger.error(f"Error cleaning response: {e}")
            return text

    def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.circuit_open = True
            self.circuit_reset_time = asyncio.get_event_loop().time() + self._circuit_open_duration
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Auto-reset in {self._circuit_open_duration}s."
            )

    def _is_circuit_open(self) -> bool:
        if not self.circuit_open:
            return False
        now = asyncio.get_event_loop().time()
        if self.circuit_reset_time and now > self.circuit_reset_time:
            self.circuit_open = False
            self.failure_count = 0
            self.circuit_reset_time = None
            self.logger.info("Circuit breaker reset — resuming Gemini calls")
            return False
        return True

    async def test_connection(self) -> bool:
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents="Hi",
                config=types.GenerateContentConfig(max_output_tokens=20, temperature=0.1),
            )
            return bool(response and response.text)
        except Exception as e:
            self.logger.error(f"Gemini test failed: {e}")
            return False

    def get_client_stats(self) -> Dict:
        return {
            "model": self.model,
            "failure_count": self.failure_count,
            "circuit_open": self.circuit_open,
            "max_failures": self.max_failures,
        }

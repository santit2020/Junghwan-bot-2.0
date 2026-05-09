import logging
import asyncio
import time
from typing import Dict, List, Optional
from google import genai
from google.genai import types

class GeminiClient:
    """Client for interacting with Google Gemini AI."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

        # Rate limiting: max 1 request at a time, min 4s gap = ~15 RPM safely
        self._semaphore = asyncio.Semaphore(1)
        self._last_request_time: float = 0.0
        self._min_request_gap: float = 4.0  # seconds between requests

        # Circuit breaker — only open after 10 consecutive failures, reset after 60s
        self.failure_count = 0
        self.max_failures = 10
        self.circuit_open = False
        self.circuit_reset_time: Optional[float] = None

        self.logger.info(f"GeminiClient initialized with model: {self.model}")

    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        conversation_history: List[Dict] = None,
        language: str = "en",
        tone: str = "casual"
    ) -> Optional[str]:
        """Generate a response using Gemini AI.

        Requests are serialised through a semaphore so we never fire more than
        one call at a time, and we enforce a minimum gap between calls to stay
        well under the free-tier rate limit (15 RPM).
        """
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is open — skipping Gemini request")
            return None

        contents = []
        if conversation_history:
            contents.extend(conversation_history)
        contents.append({"role": "user", "parts": [{"text": message}]})

        language_instruction = (
            f"\n\nCRITICAL LANGUAGE REQUIREMENT: Respond in the same language the user used. "
            f"Detected language code: '{language}'. This is mandatory."
        )
        enhanced_system_prompt = system_prompt + language_instruction

        # Acquire the semaphore so only one request runs at a time
        async with self._semaphore:
            # Enforce minimum gap between requests
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_request_gap:
                wait = self._min_request_gap - elapsed
                self.logger.debug(f"Rate-limit gap: sleeping {wait:.1f}s before Gemini call")
                await asyncio.sleep(wait)

            # Retry up to 3 times; on 429 wait longer before retrying
            for attempt in range(3):
                try:
                    self._last_request_time = asyncio.get_event_loop().time()

                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=enhanced_system_prompt,
                            temperature=0.9,
                            top_p=0.95,
                            top_k=40,
                            max_output_tokens=1000,
                            candidate_count=1
                        )
                    )

                    if response and response.text:
                        self.failure_count = 0
                        self.circuit_open = False
                        self.logger.info("Gemini response received successfully")
                        return self._post_process_response(response.text.strip(), language, tone)
                    else:
                        self.logger.warning("Empty response from Gemini")
                        self._handle_failure()
                        return None

                except Exception as e:
                    error_str = str(e)

                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        # Exponential back-off: 15s, 30s, 60s
                        wait_time = 15 * (2 ** attempt)
                        self.logger.warning(
                            f"Gemini rate limit hit (attempt {attempt + 1}/3). "
                            f"Waiting {wait_time}s before retry..."
                        )
                        await asyncio.sleep(wait_time)
                        if attempt == 2:
                            self.logger.error("All retries exhausted after rate limit")
                            self._handle_failure()
                            return None
                        self._last_request_time = asyncio.get_event_loop().time()
                    else:
                        self.logger.error(f"Gemini error: {e}")
                        self._handle_failure()
                        return None

        return None

    def _post_process_response(self, text: str, language: str, tone: str) -> str:
        try:
            text = text.replace("**", "").replace("*", "")
            unwanted_phrases = [
                "I'm an AI", "As an AI", "I'm here to help", "As a language model",
                "I'm a chatbot", "I'm a bot", "I'm an assistant", "I'm designed to",
                "My purpose is", "I was created to", "I'm programmed to",
                "I don't have feelings", "I can't experience", "I lack the capacity"
            ]
            for phrase in unwanted_phrases:
                if phrase.lower() in text.lower():
                    sentences = text.split('. ')
                    text = '. '.join([s for s in sentences if phrase.lower() not in s.lower()])

            if len(text) > 1000:
                sentences = text.split('. ')
                truncated = []
                char_count = 0
                for sentence in sentences:
                    if char_count + len(sentence) > 800:
                        break
                    truncated.append(sentence)
                    char_count += len(sentence)
                text = '. '.join(truncated) if truncated else text[:800] + "..."
                if truncated and not text.endswith('.'):
                    text += '.'

            return text.strip()
        except Exception as e:
            self.logger.error(f"Error post-processing response: {e}")
            return text

    def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.circuit_open = True
            self.circuit_reset_time = asyncio.get_event_loop().time() + 60
            self.logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                "Will auto-reset in 60s."
            )

    def _is_circuit_open(self) -> bool:
        if not self.circuit_open:
            return False
        if self.circuit_reset_time and asyncio.get_event_loop().time() > self.circuit_reset_time:
            self.circuit_open = False
            self.failure_count = 0
            self.circuit_reset_time = None
            self.logger.info("Circuit breaker reset — Gemini calls re-enabled")
            return False
        return True

    async def test_connection(self) -> bool:
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents="Hello, this is a test message.",
                config=types.GenerateContentConfig(max_output_tokens=50, temperature=0.1)
            )
            success = bool(response and response.text)
            self.logger.info(f"Gemini API test: {'SUCCESS' if success else 'FAILED'}")
            return success
        except Exception as e:
            self.logger.error(f"Gemini API test failed: {e}")
            return False

    def get_client_stats(self) -> Dict:
        return {
            "model": self.model,
            "failure_count": self.failure_count,
            "circuit_open": self.circuit_open,
            "circuit_reset_time": self.circuit_reset_time,
            "max_failures": self.max_failures,
            "min_request_gap_seconds": self._min_request_gap
        }

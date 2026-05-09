import logging
import asyncio
from typing import Dict, List, Optional
from google import genai
from google.genai import types


class GeminiClient:
    """Client for interacting with Google Gemini AI."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

        self._semaphore = asyncio.Semaphore(1)
        self._last_request_time: float = 0.0
        self._min_request_gap: float = 3.0

        self.failure_count = 0
        self.max_failures = 8
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
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker open — using local fallback")
            return None

        contents = []
        if conversation_history:
            contents.extend(conversation_history)
        contents.append({"role": "user", "parts": [{"text": message}]})

        language_instruction = (
            f"\n\nCRITICAL: Respond in the SAME language the user wrote in. "
            f"Detected language: '{language}'. This is mandatory. Keep it SHORT (1-2 sentences)."
        )
        enhanced_system_prompt = system_prompt + language_instruction

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
                        system_instruction=enhanced_system_prompt,
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=300,
                        candidate_count=1
                    )
                )

                if response and response.text:
                    self.failure_count = 0
                    self.circuit_open = False
                    self.logger.info("Gemini responded OK")
                    return self._clean_response(response.text.strip())
                else:
                    self.logger.warning("Empty Gemini response")
                    self._handle_failure()
                    return None

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    self.logger.warning("Gemini rate limit — falling back to local response")
                    self._handle_failure()
                    return None
                else:
                    self.logger.error(f"Gemini error: {e}")
                    self._handle_failure()
                    return None

    def _clean_response(self, text: str) -> str:
        try:
            text = text.replace("**", "").replace("*", "")
            ai_phrases = [
                "I'm an AI", "As an AI", "I'm here to help", "As a language model",
                "I'm a chatbot", "I'm a bot", "I'm an assistant", "I'm designed to",
                "My purpose is", "I was created to", "I'm programmed to",
                "I don't have feelings", "I can't experience", "I lack the capacity"
            ]
            for phrase in ai_phrases:
                if phrase.lower() in text.lower():
                    sentences = text.split('. ')
                    text = '. '.join(s for s in sentences if phrase.lower() not in s.lower())
            if len(text) > 800:
                sentences = text.split('. ')
                truncated, count = [], 0
                for s in sentences:
                    if count + len(s) > 600:
                        break
                    truncated.append(s)
                    count += len(s)
                text = '. '.join(truncated) if truncated else text[:600] + "..."
                if truncated and not text.endswith('.'):
                    text += '.'
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error cleaning response: {e}")
            return text

    def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.circuit_open = True
            self.circuit_reset_time = asyncio.get_event_loop().time() + 90
            self.logger.warning("Circuit breaker opened. Auto-reset in 90s.")

    def _is_circuit_open(self) -> bool:
        if not self.circuit_open:
            return False
        if self.circuit_reset_time and asyncio.get_event_loop().time() > self.circuit_reset_time:
            self.circuit_open = False
            self.failure_count = 0
            self.circuit_reset_time = None
            self.logger.info("Circuit breaker reset")
            return False
        return True

    async def test_connection(self) -> bool:
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents="Hi",
                config=types.GenerateContentConfig(max_output_tokens=20, temperature=0.1)
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

import logging
import asyncio
from typing import Dict, List, Optional
import os
from google import genai
from google.genai import types
import time

class GeminiClient:
    """Client for interacting with Google Gemini AI with multiple API key rotation."""

    def __init__(self, api_keys: Optional[List[str]] = None):
        if not api_keys:
            # Load keys from environment variable if not provided
            keys_str = os.getenv("GEMINI_API_KEYS", "")
            api_keys = [key.strip() for key in keys_str.split(",") if key.strip()]

        if not api_keys:
            raise ValueError("No Gemini API keys provided")

        self.api_keys = api_keys
        self.current_index = 0
        self.logger = logging.getLogger(__name__)
        self.client = self._create_client(self.api_keys[self.current_index])

        self.failure_count = 0
        self.max_failures = 5
        self.circuit_open = False
        self.circuit_reset_time = None

        self.logger.info(f"GeminiClient initialized with {len(self.api_keys)} API keys")

    def _create_client(self, api_key: str):
        return genai.Client(api_key=api_key)

    def _rotate_key(self):
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self.client = self._create_client(self.api_keys[self.current_index])
        self.logger.warning(f"Rotated Gemini API key: {self.api_keys[old_index][:6]}... → {self.api_keys[self.current_index][:6]}...")

    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict]] = None,
        language: str = "en",
        tone: str = "casual"
    ) -> Optional[str]:
        if self._is_circuit_open():
            self.logger.warning("Circuit breaker is open; skipping Gemini request")
            return None

        contents = conversation_history[:] if conversation_history else []
        contents.append({"role": "user", "parts": [{"text": message}]})

        language_instruction = (
            f"\n\nCRITICAL LANGUAGE REQUIREMENT: User language code '{language}'. "
            "Respond only in this language."
        )
        enhanced_system_prompt = system_prompt + language_instruction

        for _ in range(len(self.api_keys)):
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model="gemini-2.0-flash-001",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=enhanced_system_prompt,
                        temperature=0.9,
                        top_p=0.95,
                        top_k=40,
                        max_output_tokens=3000,
                        candidate_count=1
                    )
                )
                if response and response.text:
                    self.failure_count = 0
                    self.circuit_open = False
                    processed = self._post_process_response(response.text.strip(), language, tone)
                    self.logger.debug(f"Generated response: {processed[:100]}...")
                    return processed
                self.logger.warning("Empty response from Gemini")
                self._handle_failure()
                return None
            except Exception as e:
                error_str = str(e).lower()
                if hasattr(e, "status_code") and e.status_code == 429 or "quota" in error_str or "rate limit" in error_str:
                    self.logger.warning(f"Rate limit hit: {e} - rotating API key")
                    self._rotate_key()
                    continue
                self.logger.error(f"Error generating response: {e}")
                self._handle_failure()
                return None

        self.logger.error("All API keys exhausted or failed.")
        return None

    def _post_process_response(self, text: str, language: str, tone: str) -> str:
        # Your original post-process code here (omitted for brevity)
        # Include markdown stripping, unwanted phrase removal, casual endings, truncation, etc.
        return text

    def _handle_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.circuit_open = True
            self.circuit_reset_time = time.time() + 300
            self.logger.warning("Circuit breaker opened due to repeated failures")

    def _is_circuit_open(self) -> bool:
        if not self.circuit_open:
            return False
        if self.circuit_reset_time and time.time() > self.circuit_reset_time:
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
                model="gemini-2.5-flash",
                contents="Hello, this is a test message.",
                config=types.GenerateContentConfig(
                    max_output_tokens=50,
                    temperature=0.1
                )
            )
            self.logger.info(f"Gemini API test: {'SUCCESS' if (response and response.text) else 'FAILED'}")
            return bool(response and response.text)
        except Exception as e:
            self.logger.error(f"Gemini API test failed: {e}")
            return False

    def get_client_stats(self) -> Dict:
        return {
            "failure_count": self.failure_count,
            "circuit_open": self.circuit_open,
            "circuit_reset_time": self.circuit_reset_time,
            "max_failures": self.max_failures,
            "current_key": self.api_keys[self.current_index][:6] + "..."
        }

import logging
import asyncio
from typing import Dict, List, Optional
from google import genai
from google.genai import types
import time

class GeminiClient:
    """Client for interacting with Google Gemini AI, with API key rotation."""

    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.logger = logging.getLogger(__name__)
        self.client = self._create_client(self.api_keys[self.current_index])
        self.failure_count = 0
        self.max_failures = 5
        self.circuit_open = False
        self.circuit_reset_time = None

        self.logger.info(f"GeminiClient initialized with {len(self.api_keys)} API Keys")

    def _create_client(self, api_key: str):
        return genai.Client(api_key=api_key)

    def _rotate_key(self):
        """Rotate to the next API key."""
        old_index = self.current_index
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self.client = self._create_client(self.api_keys[self.current_index])
        self.logger.warning(f"Rotating Gemini API key: {self.api_keys[old_index][:6]}... → {self.api_keys[self.current_index][:6]}...")

    async def generate_response(
        self,
        message: str,
        system_prompt: str,
        conversation_history: List[Dict] = None,
        language: str = "en",
        tone: str = "casual"
    ) -> Optional[str]:
        """Generate a response using Gemini AI, with key rotation on rate limits."""
        try:
            if self._is_circuit_open():
                self.logger.warning("Circuit breaker is open, skipping Gemini request")
                return None

            contents = []
            if conversation_history:
                contents.extend(conversation_history)
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })

            language_instruction = (
                f"\n\nCRITICAL LANGUAGE REQUIREMENT: The user is writing in language code '{language}'. "
                "You MUST respond in the exact same language the user used. If they wrote in English, respond in English. "
                "If they wrote in Hindi/Hinglish, respond in Hindi/Hinglish. If they wrote in any other language, match that language exactly. "
                "This is mandatory - never respond in a different language than the user used."
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
                        generated_text = response.text.strip()
                        processed_response = self._post_process_response(generated_text, language, tone)
                        self.logger.debug(f"Generated response: {processed_response[:100]}...")
                        return processed_response
                    else:
                        self.logger.warning("Empty response from Gemini")
                        self._handle_failure()
                        return None
                except Exception as e:
                    if hasattr(e, "status_code") and e.status_code == 429 or "quota" in str(e).lower() or "rate limit" in str(e).lower():
                        self.logger.warning(f"Gemini API rate limit hit: {e} - rotating key")
                        self._rotate_key()
                        continue
                    self.logger.error(f"Error generating response with Gemini: {e}")
                    self._handle_failure()
                    return None
            self.logger.error("All API keys exhausted or failed.")
            return None
        except Exception as e:
            self.logger.error(f"Error in generate_response logic: {e}")
            self._handle_failure()
            return None

    def _post_process_response(self, text: str, language: str, tone: str) -> str:
        """Post-process the AI response for better quality."""
        try:
            text = text.replace("**", "").replace("*", "")
            unwanted_phrases = [
                "I'm an AI", "As an AI", "I'm here to help", "How can I assist",
                "I don't have personal opinions", "I can't feel emotions",
                "I don't have personal experiences", "As a language model",
                "I'm a chatbot", "I'm a bot", "I'm an assistant", "I'm designed to",
                "My purpose is", "I was created to", "I'm programmed to",
                "Is there anything else you'd like to know", "How can I help you",
                "Let me know if you need anything", "I'm happy to help",
                "I'd be happy to", "I can help you with", "I can assist you",
                "As a digital assistant", "I don't have feelings", "I can't experience",
                "I don't have the ability to", "I'm not able to feel", "I lack the capacity"
            ]
            for phrase in unwanted_phrases:
                if phrase.lower() in text.lower():
                    sentences = text.split('. ')
                    text = '. '.join([s for s in sentences if phrase.lower() not in s.lower()])
            if text.endswith('.'):
                if tone == "casual" and len(text) > 50:
                    import random
                    casual_endings = [" lol", " haha", " 😊", " right?", " you know?"]
                    if random.random() < 0.2:
                        text = text[:-1] + random.choice(casual_endings)
            if len(text) > 1000:
                sentences = text.split('. ')
                truncated = []
                char_count = 0
                for sentence in sentences:
                    if char_count + len(sentence) > 800:
                        break
                    truncated.append(sentence)
                    char_count += len(sentence)
                if truncated:
                    text = '. '.join(truncated)
                    if not text.endswith('.'):
                        text += '.'
                else:
                    text = text[:800] + "..."
            return text.strip()
        except Exception as e:
            self.logger.error(f"Error post-processing response: {e}")
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
            success = bool(response and response.text)
            self.logger.info(f"Gemini API test: {'SUCCESS' if success else 'FAILED'}")
            return success
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

# Initialize GeminiClient with your API keys
api_keys = [
    "AIzaSyAn5VFwFl_5VtMZECQY5etScp1NC_i3Nlk",
    "AIzaSyDdbHFnl6rNJgTYcApkl9ULfsQQVlACv4s",
    "AIzaSyBR495JulD06A19X6SSOTgKcc3mUEv3gH4",
    "AIzaSyDqDJ_-2U0UW6-uR0i1_mHjHlISTKOu32Q",
    "AIzaSyDhOljZt95wuGxwqReRvaNrjKdCLWM7RLc"
]

gemini_client = GeminiClient(api_keys)

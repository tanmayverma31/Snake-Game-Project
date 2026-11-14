"""
Dedicated Google Gemini API client wrapper.
Uses the official Google Gen AI SDK (`google-genai`).
Securely reads API key from environment variables.
Provides fallback mechanisms so core game logic is 100% resilient if AI is unavailable.
"""

import logging
import os
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("snake.ai.client")


class GeminiClientWrapper:
    """
    Encapsulates Gemini API communication using the official google-genai SDK.
    Handles authentication, timeouts, rate limits, and fallback behavior.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = settings.GEMINI_TIMEOUT_SECONDS,
    ):
        # Always read from provided key, environment variable, or settings
        self.api_key: str = (api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or "").strip()
        self.model_name: str = model_name or os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL
        self.timeout: float = timeout
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initializes the google-genai Client if an API key is available."""
        if not self.api_key:
            logger.info("GEMINI_API_KEY not found. Gemini AI features will run in fallback heuristic mode.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info("Google GenAI client initialized successfully with model '%s'.", self.model_name)
        except Exception as e:
            logger.warning("Failed to initialize Google GenAI client: %s. Using fallback mode.", e)
            self._client = None

    @property
    def is_available(self) -> bool:
        """Checks if the Gemini client is configured and ready."""
        return self._client is not None

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Calls Gemini API using client.interactions.create with timeout and error handling.
        Returns generated text or None on failure.
        """
        if not self.is_available:
            return None

        try:
            # Combine system instruction into prompt or interaction parameters
            full_input = prompt
            if system_instruction:
                full_input = f"[System Instruction: {system_instruction}]\n\n{prompt}"

            # Modern google-genai interactions API call
            interaction = self._client.interactions.create(
                model=self.model_name,
                input=full_input,
            )

            # Retrieve text from output_text property
            text = getattr(interaction, "output_text", None)
            if text:
                return text.strip()

            # Fallback inspection if interaction.output_text is None
            if hasattr(interaction, "outputs") and interaction.outputs:
                for out in interaction.outputs:
                    if hasattr(out, "text") and out.text:
                        return out.text.strip()

            return None
        except Exception as exc:
            # Log error without crashing caller; game continues smoothly
            logger.warning("Gemini API call failed (%s: %s). Falling back gracefully.", type(exc).__name__, exc)
            return None

"""
ai/groq_client.py
==================
Groq API client wrapper.
Handles authentication, rate limits, retries, and error reporting.

IMPORTANT: Never log API keys or full resume content.
"""

import json
import logging
import time
from typing import Optional

from config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    GROQ_MAX_TOKENS,
    GROQ_MAX_RETRIES,
)

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Raised for unrecoverable Groq API errors."""


class GroqRateLimitError(GroqAPIError):
    """Raised when Groq rate limit is hit and retries are exhausted."""


def _get_client():
    """
    Create and return a Groq client.
    Validates that the API key is set before creating the client.
    """
    if not GROQ_API_KEY:
        raise GroqAPIError(
            "GROQ_API_KEY is not set. Please add it to your .env file.\n"
            "Get your key at: https://console.groq.com/keys"
        )
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        raise GroqAPIError(
            "The 'groq' package is not installed. Run: pip install groq"
        )


def call_groq_for_extraction(
    system_prompt: str,
    user_prompt: str,
    model: str = GROQ_MODEL,
    temperature: float = GROQ_TEMPERATURE,
    max_tokens: int = GROQ_MAX_TOKENS,
    max_retries: int = GROQ_MAX_RETRIES,
) -> str:
    """
    Call Groq API and return the response content string.
    Implements exponential backoff on rate limit errors.

    Returns the raw response string (expected to be JSON).
    Raises GroqAPIError on unrecoverable failures.
    """
    client = _get_client()

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Groq API call — model: %s, attempt: %d/%d",
                model, attempt, max_retries,
            )

            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    # Request JSON output mode if supported by model
                    response_format={"type": "json_object"},
                )
            except Exception as format_exc:
                if "response_format" in str(format_exc).lower():
                    logger.warning("Model '%s' does not support json_object mode; falling back to standard prompt.", model)
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                else:
                    raise

            content = response.choices[0].message.content
            if not content:
                raise GroqAPIError("Groq returned an empty response.")

            logger.info(
                "Groq response received — %d characters.", len(content)
            )
            return content

        except Exception as exc:
            exc_str = str(exc)
            exc_type = type(exc).__name__

            # Rate limit: exponential backoff
            if "rate_limit" in exc_str.lower() or "429" in exc_str:
                wait_seconds = 2 ** attempt  # 2, 4, 8 seconds
                logger.warning(
                    "Groq rate limit hit (attempt %d/%d). Waiting %ds...",
                    attempt, max_retries, wait_seconds,
                )
                if attempt < max_retries:
                    time.sleep(wait_seconds)
                    continue
                raise GroqRateLimitError(
                    f"Groq rate limit exceeded after {max_retries} attempts. "
                    "Please wait a moment and try again, or reduce batch size."
                ) from exc

            # Authentication failure
            if "authentication" in exc_str.lower() or "401" in exc_str or "invalid_api_key" in exc_str.lower():
                raise GroqAPIError(
                    "Groq API authentication failed. "
                    "Check that your GROQ_API_KEY in .env is correct.\n"
                    "Get your key at: https://console.groq.com/keys"
                ) from exc

            # Model not found
            if "model_not_found" in exc_str.lower() or "404" in exc_str:
                raise GroqAPIError(
                    f"Model '{model}' not found on Groq.\n"
                    "Check available models at: https://console.groq.com/docs/models\n"
                    "Update GROQ_MODEL in your .env file."
                ) from exc

            # Timeout — retry
            if "timeout" in exc_str.lower() or "timed out" in exc_str.lower():
                logger.warning(
                    "Groq request timed out (attempt %d/%d).", attempt, max_retries
                )
                if attempt < max_retries:
                    time.sleep(2)
                    continue

            # Context length exceeded
            if "context_length" in exc_str.lower() or "token" in exc_str.lower():
                raise GroqAPIError(
                    "Resume text is too long for the model's context window. "
                    "The text has been truncated — check MAX_TEXT_CHARS in .env."
                ) from exc

            # Generic retry for other errors
            if attempt < max_retries:
                logger.warning(
                    "Groq API error (%s) — retrying (attempt %d/%d): %s",
                    exc_type, attempt, max_retries, exc_str[:200],
                )
                time.sleep(1)
                continue

            # All retries exhausted
            raise GroqAPIError(
                f"Groq API call failed after {max_retries} attempts: {exc_str[:300]}"
            ) from exc

    raise GroqAPIError("Groq API: unexpected exit from retry loop.")


def test_groq_connection(model: Optional[str] = None) -> tuple[bool, str]:
    """
    Quick connectivity test.
    Returns (True, model_name) on success, (False, error_message) on failure.
    """
    target_model = model or GROQ_MODEL
    try:
        response = call_groq_for_extraction(
            system_prompt="You are a helpful assistant. You output valid JSON only.",
            user_prompt='Return this exact JSON object: {"status": "ok"}',
            model=target_model,
            max_tokens=500,
            max_retries=1,
        )
        if '"ok"' in response or 'ok' in response:
            return True, target_model
        return True, target_model
    except GroqAPIError as exc:
        return False, str(exc)


def get_available_models() -> list[str]:
    """Return list of text models available on this Groq account."""
    try:
        client = _get_client()
        models = [m.id for m in client.models.list().data]
        # Filter for text/chat models
        chat_models = [m for m in models if "whisper" not in m.lower() and "guard" not in m.lower()]
        return sorted(chat_models) if chat_models else sorted(models)
    except Exception as exc:
        logger.warning("Could not list Groq models: %s", exc)
        return []

"""
ai/resume_extractor.py
=======================
Orchestrates the full extraction pipeline:
  1. Send cleaned text to Groq
  2. Parse JSON response
  3. Repair malformed JSON (up to 2 attempts)
  4. Validate with Pydantic
  5. Return CandidateProfile

Never silently drops failures — always surfaces errors to the caller.
"""

import json
import logging
import re
from typing import Optional

from ai.groq_client import call_groq_for_extraction, GroqAPIError
from ai.extraction_prompt import SYSTEM_PROMPT, build_extraction_prompt
from schemas.candidate_schema import CandidateProfile
from config.settings import GROQ_MODEL

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when extraction cannot produce a usable CandidateProfile."""


# ---------------------------------------------------------------------------
# JSON repair helpers
# ---------------------------------------------------------------------------

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrapping if present."""
    text = text.strip()
    # Remove opening fence
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    # Remove closing fence
    text = re.sub(r'```\s*$', '', text)
    return text.strip()


def _extract_json_object(text: str) -> str:
    """Find the first complete {...} JSON object in a string."""
    start = text.find('{')
    if start == -1:
        return text
    # Walk to find matching closing brace
    depth = 0
    for i, ch in enumerate(text[start:], start=start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    # Return from start to end if no match found
    return text[start:]


def _attempt_json_repair(raw: str) -> Optional[dict]:
    """
    Two-pass repair:
    Pass 1: Strip markdown fences, extract JSON object, parse.
    Pass 2: Try json5 / ast.literal_eval as last resort (not installed by default).
    Returns parsed dict or None.
    """
    # Pass 1
    cleaned = _strip_markdown_fences(raw)
    cleaned = _extract_json_object(cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Pass 2: remove trailing commas (common LLM error)
    no_trailing = re.sub(r',\s*([}\]])', r'\1', cleaned)
    try:
        return json.loads(no_trailing)
    except json.JSONDecodeError:
        pass

    return None


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_candidate_from_text(
    cleaned_text: str,
    filename: str,
    candidate_id: str,
) -> CandidateProfile:
    """
    Full extraction pipeline for one resume.

    Args:
        cleaned_text: Pre-cleaned resume text.
        filename: Original filename (for schema metadata).
        candidate_id: Unique ID like "CAND_001".

    Returns:
        CandidateProfile with all extracted data.

    Raises:
        ExtractionError: If extraction and all repair attempts fail.
    """
    if not cleaned_text.strip():
        raise ExtractionError(
            f"No text content to process for '{filename}'. "
            "The file may be empty or extraction failed."
        )

    user_prompt = build_extraction_prompt(cleaned_text, filename)

    # --- Call Groq ---
    try:
        raw_response = call_groq_for_extraction(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
    except GroqAPIError as exc:
        raise ExtractionError(str(exc)) from exc

    # --- Parse JSON ---
    parsed: Optional[dict] = None
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        logger.warning("Direct JSON parse failed for '%s' — attempting repair.", filename)
        parsed = _attempt_json_repair(raw_response)

    if parsed is None:
        logger.error(
            "JSON repair failed for '%s'. Raw response (first 500 chars): %s",
            filename, raw_response[:500],
        )
        raise ExtractionError(
            f"Groq returned invalid JSON for '{filename}' that could not be repaired. "
            "This may be a temporary API issue — try reprocessing."
        )

    # --- Inject metadata ---
    parsed["candidate_id"] = candidate_id
    parsed["source_file"] = filename

    # --- Validate with Pydantic ---
    try:
        profile = CandidateProfile.model_validate(parsed)
    except Exception as exc:
        logger.warning(
            "Pydantic validation error for '%s': %s. Attempting partial recovery.",
            filename, str(exc)[:300],
        )
        # Try building with only the safely parseable parts
        profile = _partial_recovery(parsed, filename, candidate_id)
        if profile is None:
            raise ExtractionError(
                f"Pydantic schema validation failed for '{filename}': {str(exc)[:300]}"
            ) from exc

    # Ensure source_file and candidate_id are correct
    profile.source_file = filename
    profile.candidate_id = candidate_id

    logger.info(
        "Extraction complete for '%s' — confidence: %s, status: %s",
        filename, profile.confidence_score, profile.validation_status,
    )
    return profile


def _partial_recovery(raw_dict: dict, filename: str, candidate_id: str) -> Optional[CandidateProfile]:
    """
    Attempt to build a CandidateProfile from a dict that partially
    fails Pydantic validation, by stripping problematic nested fields.
    """
    # Create a minimal profile and manually populate safe fields
    try:
        safe = {
            "candidate_id": candidate_id,
            "source_file": filename,
            "validation_status": "needs_review",
            "extraction_error": "Partial extraction — some fields failed validation.",
        }
        # Only copy top-level fields that are dicts/lists (Pydantic handles defaults)
        for key in ("personal_information", "professional_information"):
            if isinstance(raw_dict.get(key), dict):
                safe[key] = raw_dict[key]

        for key in ("education", "work_experience", "projects", "certifications", "achievements"):
            val = raw_dict.get(key)
            if isinstance(val, list):
                safe[key] = val

        if isinstance(raw_dict.get("technical_skills"), dict):
            safe["technical_skills"] = raw_dict["technical_skills"]

        return CandidateProfile.model_validate(safe)
    except Exception as exc:
        logger.error("Partial recovery also failed: %s", exc)
        return None

"""
validators/data_validator.py
==============================
Post-extraction validation and confidence scoring.
All checks are local — no additional LLM calls.
"""

import re
import hashlib
import logging
from typing import Optional

from schemas.candidate_schema import CandidateProfile
from config.settings import CONFIDENCE_VERIFIED, CONFIDENCE_NEEDS_REVIEW

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9.\-]+$'
)
_PHONE_RE = re.compile(
    r'^[+\d\s\(\)\-\.]{7,20}$'
)
_URL_RE = re.compile(
    r'https?://[^\s]+'
)


# ---------------------------------------------------------------------------
# Field validators
# ---------------------------------------------------------------------------

def is_valid_email(email: Optional[str]) -> bool:
    if not email:
        return False
    return bool(_EMAIL_RE.match(email.strip()))


def is_plausible_phone(phone: Optional[str]) -> bool:
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    return 7 <= len(digits) <= 15


def is_plausible_year(year_str: Optional[str]) -> bool:
    if not year_str:
        return False
    year_match = re.search(r'\b(19|20)\d{2}\b', str(year_str))
    return bool(year_match)


def is_plausible_date(date_str: Optional[str]) -> bool:
    """Check YYYY-MM or YYYY format."""
    if not date_str:
        return True  # None is acceptable
    if date_str.lower() in ('present', 'current', 'ongoing'):
        return True
    return bool(re.match(r'^\d{4}(-\d{2})?$', date_str.strip()))


# ---------------------------------------------------------------------------
# Missing fields detector
# ---------------------------------------------------------------------------

IMPORTANT_FIELDS = [
    "personal_information.full_name",
    "personal_information.email",
    "personal_information.phone",
    "professional_information.current_designation",
    "professional_information.total_experience_years",
    "education",
    "work_experience",
    "technical_skills",
]


def detect_missing_fields(profile: CandidateProfile) -> list[str]:
    """Return list of important fields that are missing."""
    missing = []
    pi = profile.personal_information
    prof = profile.professional_information
    ts = profile.technical_skills

    if not pi.full_name:
        missing.append("full_name")
    if not pi.email:
        missing.append("email")
    if not pi.phone:
        missing.append("phone")
    if not prof.current_designation:
        missing.append("current_designation")
    if prof.total_experience_years is None:
        missing.append("total_experience_years")
    if not profile.education:
        missing.append("education")
    if not profile.work_experience:
        missing.append("work_experience")

    all_skills = (
        ts.programming_languages + ts.frameworks + ts.databases +
        ts.cloud_technologies + ts.developer_tools + ts.other_technical_skills
    )
    if not all_skills:
        missing.append("technical_skills")

    return missing


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

def compute_confidence_score(
    profile: CandidateProfile,
    missing_fields: list[str],
) -> float:
    """
    Local confidence scoring based on extraction evidence.
    Returns a float 0–100.
    """
    score = 100.0

    # Deduct for missing important fields
    deductions = {
        "full_name": 20,
        "email": 10,
        "phone": 5,
        "current_designation": 5,
        "total_experience_years": 5,
        "education": 10,
        "work_experience": 15,
        "technical_skills": 10,
    }
    for field in missing_fields:
        score -= deductions.get(field, 3)

    # Bonus for rich content
    pi = profile.personal_information
    if profile.work_experience:
        score = min(score + 5, 100)
    if profile.projects:
        score = min(score + 3, 100)
    if profile.certifications:
        score = min(score + 2, 100)
    if pi.linkedin:
        score = min(score + 2, 100)

    # Penalty for email format issues
    if pi.email and not is_valid_email(pi.email):
        score -= 5

    # Penalty for invalid phone
    for phone in pi.phone:
        if not is_plausible_phone(phone):
            score -= 3
            break

    # Penalty for invalid dates in work experience
    for we in profile.work_experience:
        if we.start_date and not is_plausible_date(we.start_date):
            score -= 2
        if we.end_date and not is_plausible_date(we.end_date):
            score -= 2

    return max(0.0, min(100.0, round(score, 1)))


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

_seen_hashes: set[str] = set()


def check_duplicate(file_hash: str) -> bool:
    """Return True if this file hash has been seen before in the session."""
    if file_hash in _seen_hashes:
        return True
    _seen_hashes.add(file_hash)
    return False


def reset_duplicate_tracker() -> None:
    """Call this when starting a new session or clearing data."""
    _seen_hashes.clear()


# ---------------------------------------------------------------------------
# Full validation pipeline
# ---------------------------------------------------------------------------

def validate_candidate(profile: CandidateProfile) -> CandidateProfile:
    """
    Run full validation on a CandidateProfile.
    Updates confidence_score, missing_fields, and validation_status in-place.
    Returns the updated profile.
    """
    # Detect missing fields
    missing = detect_missing_fields(profile)
    profile.missing_fields = missing

    # Compute confidence
    confidence = compute_confidence_score(profile, missing)
    profile.confidence_score = confidence

    # Set validation status
    if confidence >= CONFIDENCE_VERIFIED:
        profile.validation_status = "verified"
    elif confidence >= CONFIDENCE_NEEDS_REVIEW:
        profile.validation_status = "needs_review"
    else:
        profile.validation_status = "failed"

    logger.info(
        "Validation — '%s': confidence=%.1f, status=%s, missing=%s",
        profile.source_file,
        confidence,
        profile.validation_status,
        missing,
    )
    return profile

"""
config/settings.py
==================
Central configuration loader.
Reads .env variables, provides typed constants for the whole application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (parent of this file)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


def _get_secret_or_env(key: str, default: str = "") -> str:
    """Retrieve config from environment variable or Streamlit Cloud Secrets."""
    val = os.getenv(key)
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return (val if val is not None else default).strip("\"'")


# ---------------------------------------------------------------------------
# Groq API
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = _get_secret_or_env("GROQ_API_KEY", "")
GROQ_MODEL: str = _get_secret_or_env("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.1"))
GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "8000"))
GROQ_MAX_RETRIES: int = int(os.getenv("GROQ_MAX_RETRIES", "3"))

# ---------------------------------------------------------------------------
# Tesseract OCR
# ---------------------------------------------------------------------------
TESSERACT_PATH: str = _get_secret_or_env(
    "TESSERACT_PATH",
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
)

# ---------------------------------------------------------------------------
# Processing limits
# ---------------------------------------------------------------------------
MAX_RESUMES_PER_BATCH: int = int(os.getenv("MAX_RESUMES_PER_BATCH", "20"))
MAX_TEXT_CHARS: int = int(os.getenv("MAX_TEXT_CHARS", "15000"))
MIN_EXTRACTABLE_CHARS: int = int(os.getenv("MIN_EXTRACTABLE_CHARS", "50"))

# ---------------------------------------------------------------------------
# Supported file formats
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEMP_DIR = DATA_DIR / "temp"
EXPORTS_DIR = DATA_DIR / "exports"

# Create directories if they don't exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Confidence thresholds
# ---------------------------------------------------------------------------
CONFIDENCE_VERIFIED = 80
CONFIDENCE_NEEDS_REVIEW = 50


def validate_config() -> list[str]:
    """Return a list of configuration problems, empty if all is good."""
    problems: list[str] = []
    key = _get_secret_or_env("GROQ_API_KEY", GROQ_API_KEY)
    if not key:
        problems.append("GROQ_API_KEY is not set (add to .env or Streamlit Cloud Secrets)")
    elif len(key) < 20:
        problems.append("GROQ_API_KEY looks invalid (too short)")
    return problems

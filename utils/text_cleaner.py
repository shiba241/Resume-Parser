"""
utils/text_cleaner.py
======================
Cleans extracted resume text before sending it to the LLM.
Goals:
  - Collapse repeated whitespace / blank lines
  - Remove repeated headers and footers
  - Remove null bytes and control characters
  - Truncate to MAX_TEXT_CHARS to control token usage
"""

import re
import logging
from config.settings import MAX_TEXT_CHARS

logger = logging.getLogger(__name__)

# Patterns for common resume noise
_REPEATED_LINE_THRESHOLD = 3  # if a line appears more than this many times → remove
_NULL_BYTES = re.compile(r'\x00+')
_CONTROL_CHARS = re.compile(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]')
_MULTIPLE_BLANKS = re.compile(r'\n{3,}')
_TRAILING_SPACES = re.compile(r'[ \t]+\n')
_HORIZONTAL_RULE = re.compile(r'^[-=_]{5,}$', re.MULTILINE)


def clean_text(raw_text: str) -> str:
    """
    Full cleaning pipeline for resume text.
    Returns cleaned text, truncated to MAX_TEXT_CHARS.
    """
    if not raw_text:
        return ""

    text = raw_text

    # 1. Remove null bytes and control characters
    text = _NULL_BYTES.sub(' ', text)
    text = _CONTROL_CHARS.sub(' ', text)

    # 2. Normalize Windows line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # 3. Remove trailing spaces on each line
    text = _TRAILING_SPACES.sub('\n', text)

    # 4. Remove decorative horizontal rules
    text = _HORIZONTAL_RULE.sub('', text)

    # 5. Collapse 3+ consecutive blank lines into 2
    text = _MULTIPLE_BLANKS.sub('\n\n', text)

    # 6. Remove repeated lines (common in scanned PDFs — repeated headers/footers)
    text = _remove_repeated_lines(text)

    # 7. Strip leading/trailing whitespace
    text = text.strip()

    # 8. Truncate to token-safe length
    original_len = len(text)
    if original_len > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS]
        logger.info(
            "Resume text truncated from %d to %d characters for token control.",
            original_len, MAX_TEXT_CHARS,
        )

    return text


def _remove_repeated_lines(text: str) -> str:
    """
    Remove lines that appear more than _REPEATED_LINE_THRESHOLD times.
    This handles page headers/footers like "Resume | John Doe | Page X of Y".
    """
    lines = text.split('\n')
    line_counts: dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        if stripped:
            line_counts[stripped] = line_counts.get(stripped, 0) + 1

    # Build blacklist of overly-repeated lines
    blacklist = {
        line for line, count in line_counts.items()
        if count > _REPEATED_LINE_THRESHOLD and len(line) < 120
    }

    if blacklist:
        logger.debug("Removing %d repeated header/footer line(s).", len(blacklist))

    cleaned = []
    for line in lines:
        if line.strip() not in blacklist:
            cleaned.append(line)

    return '\n'.join(cleaned)


def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces into one, strip each line."""
    lines = [' '.join(line.split()) for line in text.split('\n')]
    return '\n'.join(lines)

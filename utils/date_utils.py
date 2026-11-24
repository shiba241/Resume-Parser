"""
utils/date_utils.py
====================
Normalize date strings extracted from resumes to YYYY-MM where possible.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Month name → number mapping
_MONTH_MAP = {
    'jan': '01', 'january': '01',
    'feb': '02', 'february': '02',
    'mar': '03', 'march': '03',
    'apr': '04', 'april': '04',
    'may': '05',
    'jun': '06', 'june': '06',
    'jul': '07', 'july': '07',
    'aug': '08', 'august': '08',
    'sep': '09', 'sept': '09', 'september': '09',
    'oct': '10', 'october': '10',
    'nov': '11', 'november': '11',
    'dec': '12', 'december': '12',
}

# Patterns
_YYYY_MM_DD = re.compile(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})')
_MON_YYYY = re.compile(r'([A-Za-z]+)[,.\s]+(\d{4})')
_YYYY_ONLY = re.compile(r'\b(\d{4})\b')


def normalize_date(raw: Optional[str]) -> Optional[str]:
    """
    Try to convert raw date string to YYYY-MM.
    Returns None if input is None or empty.
    Returns the original string if normalization fails.
    """
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None

    # "Present" / "Current" → preserve as-is
    if raw.lower() in ('present', 'current', 'ongoing', 'till date', 'till now'):
        return 'Present'

    # 2024-03-15 or 2024/03/15
    m = _YYYY_MM_DD.search(raw)
    if m:
        year, month = m.group(1), m.group(2).zfill(2)
        return f"{year}-{month}"

    # "March 2024" / "Mar, 2024" / "Mar. 2024"
    m = _MON_YYYY.search(raw)
    if m:
        mon_str = m.group(1).lower()
        year = m.group(2)
        month_num = _MONTH_MAP.get(mon_str)
        if month_num:
            return f"{year}-{month_num}"

    # "2024" only
    m = _YYYY_ONLY.search(raw)
    if m:
        return m.group(1)

    # Could not normalize — return original
    logger.debug("Could not normalize date: '%s'", raw)
    return raw

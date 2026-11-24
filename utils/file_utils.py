"""
utils/file_utils.py
====================
File hashing, temp-file management, and safe cleanup.
"""

import hashlib
import shutil
import logging
from pathlib import Path

from config.settings import TEMP_DIR

logger = logging.getLogger(__name__)


def compute_file_hash(file_bytes: bytes) -> str:
    """Return SHA-256 hex digest of file bytes — used for duplicate detection."""
    return hashlib.sha256(file_bytes).hexdigest()


def save_temp_file(file_bytes: bytes, filename: str) -> Path:
    """
    Write uploaded bytes to TEMP_DIR and return the temp path.
    Uses the file hash as a prefix to avoid collisions.
    """
    file_hash = compute_file_hash(file_bytes)[:12]
    safe_name = Path(filename).name  # strip any directory component
    temp_path = TEMP_DIR / f"{file_hash}_{safe_name}"
    temp_path.write_bytes(file_bytes)
    logger.debug("Saved temp file: %s", temp_path)
    return temp_path


def delete_temp_file(temp_path: Path) -> None:
    """Delete a single temp file, silently ignoring errors."""
    try:
        if temp_path.exists():
            temp_path.unlink()
            logger.debug("Deleted temp file: %s", temp_path)
    except Exception as exc:
        logger.warning("Could not delete temp file %s: %s", temp_path, exc)


def clear_temp_directory() -> int:
    """Delete all files in TEMP_DIR. Returns the number of files deleted."""
    count = 0
    for f in TEMP_DIR.iterdir():
        try:
            if f.is_file():
                f.unlink()
                count += 1
        except Exception as exc:
            logger.warning("Could not delete %s: %s", f, exc)
    return count


def clear_exports_directory(exports_dir: Path) -> int:
    """Delete all files in an exports directory."""
    count = 0
    for f in exports_dir.iterdir():
        try:
            if f.is_file():
                f.unlink()
                count += 1
        except Exception as exc:
            logger.warning("Could not delete %s: %s", f, exc)
    return count

"""
processors/file_detector.py
============================
Detects the type of an uploaded file using its extension (and optionally
its magic bytes), and routes it to the correct processor.
"""

import logging
from pathlib import Path
from config.settings import SUPPORTED_EXTENSIONS, IMAGE_EXTENSIONS

logger = logging.getLogger(__name__)

# Magic byte signatures for format verification
_MAGIC_SIGNATURES = {
    b'%PDF': 'pdf',
    b'PK\x03\x04': 'docx_or_doc',  # ZIP-based: could be DOCX or modern DOC
    b'\xff\xd8\xff': 'jpeg',
    b'\x89PNG': 'png',
    b'\xd0\xcf\x11\xe0': 'doc',    # Compound Document (old DOC format)
}


def detect_file_type(filename: str, file_bytes: bytes) -> str:
    """
    Detect file type. Returns one of:
      'pdf', 'docx', 'doc', 'image', 'unsupported'

    Priority: magic bytes first, extension as fallback.
    """
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        logger.warning("Unsupported extension: %s", ext)
        return 'unsupported'

    # --- Magic byte check ---
    header = file_bytes[:8] if len(file_bytes) >= 8 else file_bytes

    for signature, file_type in _MAGIC_SIGNATURES.items():
        if header.startswith(signature):
            if file_type == 'docx_or_doc':
                # Both DOCX and new-style DOC use ZIP; rely on extension
                if ext == '.docx':
                    return 'docx'
                return 'doc'
            if file_type in ('jpeg', 'png'):
                return 'image'
            return file_type

    # --- Extension fallback ---
    if ext == '.pdf':
        return 'pdf'
    if ext == '.docx':
        return 'docx'
    if ext == '.doc':
        return 'doc'
    if ext in IMAGE_EXTENSIONS:
        return 'image'

    return 'unsupported'


def is_supported(filename: str) -> bool:
    """Quick check: is the extension in the supported set?"""
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS

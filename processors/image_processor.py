"""
processors/image_processor.py
==============================
Processes image-format resumes (JPG, JPEG, PNG).
Uses Pillow for preprocessing, then Tesseract OCR.
"""

import logging
from pathlib import Path

from processors.ocr_processor import ocr_image, OCRError

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    pass


def extract_text_from_image(file_bytes: bytes, filename: str = "") -> str:
    """
    Extract text from a JPG/JPEG/PNG resume image.
    Returns the extracted text string.
    Raises ImageProcessingError on failure.
    """
    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ImageProcessingError(
            f"Cannot open image file '{filename}': {exc}"
        ) from exc

    logger.info("Running OCR on image: %s (size: %s)", filename, image.size)

    try:
        text = ocr_image(image)
    except OCRError as exc:
        raise ImageProcessingError(str(exc)) from exc

    if not text.strip():
        raise ImageProcessingError(
            f"OCR produced no readable text from '{filename}'. "
            "The image may be blank, corrupt, or unreadable."
        )

    logger.info("OCR extracted %d characters from '%s'.", len(text), filename)
    return text

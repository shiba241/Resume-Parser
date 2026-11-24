"""
processors/ocr_processor.py
=============================
Tesseract OCR wrapper.
Applies image preprocessing (grayscale, resize, threshold) before OCR
to improve accuracy on low-quality scans.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from config.settings import TESSERACT_PATH

logger = logging.getLogger(__name__)


def _resolve_tesseract_binary() -> Optional[str]:
    """Find tesseract binary at configured path or in system PATH."""
    if TESSERACT_PATH and Path(TESSERACT_PATH).exists():
        return TESSERACT_PATH
    system_path = shutil.which("tesseract")
    if system_path:
        return system_path
    return None


# Configure Tesseract path if available
try:
    import pytesseract
    resolved_cmd = _resolve_tesseract_binary()
    if resolved_cmd:
        pytesseract.pytesseract.tesseract_cmd = resolved_cmd
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed — OCR unavailable.")

try:
    from PIL import Image, ImageFilter, ImageEnhance
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("Pillow not installed — image processing unavailable.")


class OCRError(Exception):
    """Raised when OCR fails or is unavailable."""


def _check_dependencies() -> None:
    if not _TESSERACT_AVAILABLE:
        raise OCRError(
            "pytesseract is not installed. Run: pip install pytesseract\n"
            "Also install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
        )
    if not _PIL_AVAILABLE:
        raise OCRError("Pillow is not installed. Run: pip install Pillow")
    # Verify Tesseract binary exists
    resolved = _resolve_tesseract_binary()
    if not resolved:
        raise OCRError(
            f"Tesseract binary not found at '{TESSERACT_PATH}' or in system PATH.\n"
            "Install Tesseract and update TESSERACT_PATH in .env.\n"
            "Windows installer: https://github.com/UB-Mannheim/tesseract/wiki"
        )
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = resolved


def preprocess_image(image: "Image.Image") -> "Image.Image":
    """
    Apply preprocessing pipeline to improve OCR accuracy:
    1. Convert to grayscale
    2. Scale up small images (better OCR on small text)
    3. Sharpen
    4. Increase contrast
    """
    # Grayscale
    img = image.convert('L')

    # Upscale if image is too small (< 1500px wide)
    width, height = img.size
    if width < 1500:
        scale = 1500 / width
        new_w = int(width * scale)
        new_h = int(height * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    return img


def ocr_image(image: "Image.Image") -> str:
    """
    Run Tesseract OCR on a PIL Image object.
    Returns extracted text string.
    """
    _check_dependencies()
    try:
        preprocessed = preprocess_image(image)
        # PSM 3 = Fully automatic page segmentation (default)
        # OEM 3 = Default, based on what is available
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(preprocessed, config=custom_config)
        return text.strip()
    except Exception as exc:
        logger.error("OCR failed: %s", exc)
        raise OCRError(f"OCR processing failed: {exc}") from exc


def ocr_image_path(image_path: Path) -> str:
    """
    Run OCR on an image file by path.
    """
    _check_dependencies()
    try:
        image = Image.open(image_path)
        return ocr_image(image)
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError(f"Could not open image for OCR: {exc}") from exc


def is_ocr_available() -> tuple[bool, str]:
    """
    Check if OCR is fully available.
    Returns (True, '') or (False, reason_string).
    """
    if not _TESSERACT_AVAILABLE:
        return False, "pytesseract not installed"
    if not _PIL_AVAILABLE:
        return False, "Pillow not installed"
    resolved = _resolve_tesseract_binary()
    if not resolved:
        return False, f"Tesseract binary not found at '{TESSERACT_PATH}' or in PATH"
    return True, ""

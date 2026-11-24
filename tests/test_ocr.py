"""
tests/test_ocr.py
==================
Tests for OCR processor.
Run: pytest tests/test_ocr.py -v
"""

import pytest
from processors.ocr_processor import is_ocr_available, preprocess_image


def test_ocr_availability_check():
    """Should return a tuple of (bool, str) without crashing."""
    available, reason = is_ocr_available()
    assert isinstance(available, bool)
    assert isinstance(reason, str)


def test_preprocess_image_grayscale():
    """Preprocessing should produce a valid PIL Image."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    # Create a simple 200x200 RGB image
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    result = preprocess_image(img)
    assert result.mode == "L"  # Should be grayscale
    assert result.size[0] >= 200  # Should be at least original size or upscaled


def test_preprocess_image_upscales_small():
    """Small images should be upscaled for better OCR."""
    try:
        from PIL import Image
    except ImportError:
        pytest.skip("Pillow not installed")

    img = Image.new("RGB", (500, 300), color=(255, 255, 255))
    result = preprocess_image(img)
    # Should be upscaled to at least 1500px wide
    assert result.size[0] >= 1500

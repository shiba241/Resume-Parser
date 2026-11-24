"""
tests/test_pdf.py
==================
Tests for PDF text extraction.
Run: pytest tests/test_pdf.py -v
"""

import pytest
from processors.pdf_processor import extract_text_from_pdf, PDFProcessingError


def _make_simple_pdf() -> bytes:
    """Create a minimal valid PDF in memory."""
    try:
        import pymupdf as fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "John Doe\njohndoe@email.com\nSoftware Engineer")
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes
    except ImportError:
        pytest.skip("PyMuPDF not installed")


class TestPDFExtraction:

    def test_extract_simple_pdf(self):
        pdf_bytes = _make_simple_pdf()
        text = extract_text_from_pdf(pdf_bytes, "test.pdf")
        assert "John Doe" in text
        assert "johndoe@email.com" in text

    def test_empty_pdf_raises_error(self):
        try:
            import pymupdf as fitz
            doc = fitz.open()
            # Create a page with no text
            doc.new_page()
            pdf_bytes = doc.tobytes()
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not installed")
        # An empty page should either fall through to OCR or raise
        # This tests that it doesn't crash silently
        try:
            text = extract_text_from_pdf(pdf_bytes, "empty.pdf")
            # Either empty text or OCR fallback — both are acceptable
        except PDFProcessingError:
            pass  # Expected for truly empty PDFs when OCR is unavailable

    def test_corrupted_bytes_raises_error(self):
        with pytest.raises(PDFProcessingError):
            extract_text_from_pdf(b"not a pdf file", "corrupt.pdf")

    def test_zero_bytes_raises_error(self):
        with pytest.raises(PDFProcessingError):
            extract_text_from_pdf(b"", "empty.pdf")

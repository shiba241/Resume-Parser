"""
processors/pdf_processor.py
=============================
PDF text extraction using PyMuPDF (fitz).

Strategy:
  1. Try to extract text page-by-page using PyMuPDF.
  2. If total extracted text is below MIN_EXTRACTABLE_CHARS (scanned PDF),
     convert each page to an image and run Tesseract OCR.
"""

import logging
import io
from pathlib import Path

from config.settings import MIN_EXTRACTABLE_CHARS

logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    pass


def extract_text_from_pdf(file_bytes: bytes, filename: str = "") -> str:
    """
    Extract text from a PDF file.
    Automatically falls back to OCR if the PDF is scanned / image-only.
    """
    try:
        import pymupdf as fitz  # PyMuPDF (new import alias)
    except ImportError:
        raise PDFProcessingError(
            "PyMuPDF is not installed. Run: pip install PyMuPDF"
        )

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFProcessingError(
            f"Cannot open PDF '{filename}': {exc}"
        ) from exc

    if doc.page_count == 0:
        raise PDFProcessingError(f"PDF '{filename}' has no pages.")

    # --- Attempt direct text extraction ---
    all_text_parts: list[str] = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")  # type: ignore[arg-type]
        if text.strip():
            all_text_parts.append(f"[Page {page_num + 1}]\n{text}")

    combined_text = "\n\n".join(all_text_parts)

    # --- Decide if OCR fallback is needed ---
    if len(combined_text.strip()) >= MIN_EXTRACTABLE_CHARS:
        logger.info(
            "PDF '%s' — text extracted directly (%d chars, %d pages).",
            filename, len(combined_text), doc.page_count,
        )
        doc.close()
        return combined_text

    # --- OCR fallback for scanned / image-only PDFs ---
    logger.info(
        "PDF '%s' appears scanned (only %d chars extracted). Switching to OCR.",
        filename, len(combined_text.strip()),
    )
    return _ocr_pdf(doc, filename)


def _ocr_pdf(doc: "fitz.Document", filename: str) -> str:  # type: ignore[name-defined]
    """Convert each PDF page to an image and apply OCR."""
    from processors.ocr_processor import ocr_image, OCRError, is_ocr_available

    available, reason = is_ocr_available()
    if not available:
        raise PDFProcessingError(
            f"PDF '{filename}' requires OCR, but OCR is unavailable: {reason}"
        )

    try:
        from PIL import Image
    except ImportError:
        raise PDFProcessingError("Pillow is required for PDF OCR. Run: pip install Pillow")

    import pymupdf as fitz
    ocr_parts: list[str] = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        # Render at 2x resolution for better OCR accuracy
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))
        try:
            text = ocr_image(image)
            if text.strip():
                ocr_parts.append(f"[Page {page_num + 1}]\n{text}")
        except OCRError as exc:
            logger.warning("OCR failed for page %d of '%s': %s", page_num + 1, filename, exc)

    doc.close()

    if not ocr_parts:
        raise PDFProcessingError(
            f"OCR produced no readable text from PDF '{filename}'. "
            "The file may be blank, password-protected, or the scan quality is too low."
        )

    result = "\n\n".join(ocr_parts)
    logger.info("OCR extracted %d characters from PDF '%s'.", len(result), filename)
    return result

"""
processors/docx_processor.py
==============================
Extracts text from DOCX files using python-docx.
Handles paragraphs (including headings and bullet lists) and tables.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DocxProcessingError(Exception):
    pass


def extract_text_from_docx(file_bytes: bytes, filename: str = "") -> str:
    """
    Extract all text from a DOCX file.
    Returns the full text as a single string.
    """
    try:
        from docx import Document
        import io
    except ImportError:
        raise DocxProcessingError(
            "python-docx is not installed. Run: pip install python-docx"
        )

    try:
        doc = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise DocxProcessingError(
            f"Cannot open DOCX file '{filename}': {exc}"
        ) from exc

    text_parts: list[str] = []

    # --- Paragraphs (includes headings, body text, bullet points) ---
    for para in doc.paragraphs:
        para_text = para.text.strip()
        if para_text:
            text_parts.append(para_text)

    # --- Tables ---
    for table_idx, table in enumerate(doc.tables):
        table_rows: list[str] = []
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                table_rows.append(" | ".join(row_cells))
        if table_rows:
            text_parts.append(f"\n[Table {table_idx + 1}]")
            text_parts.extend(table_rows)

    # --- Text boxes / headers / footers (best-effort via XML) ---
    try:
        body_xml_text = _extract_textboxes(doc)
        if body_xml_text:
            text_parts.append("\n[Additional Text Boxes / Headers]")
            text_parts.append(body_xml_text)
    except Exception as exc:
        logger.debug("Could not extract text boxes from '%s': %s", filename, exc)

    combined = "\n".join(text_parts)

    if not combined.strip():
        raise DocxProcessingError(
            f"DOCX file '{filename}' appears to be empty or unreadable."
        )

    logger.info(
        "DOCX '%s' — extracted %d characters.", filename, len(combined)
    )
    return combined


def _extract_textboxes(doc) -> str:
    """
    Attempt to pull text from drawing/textbox elements in the DOCX XML.
    Only extracts text inside textbox containers (w:txbxContent or w:drawing)
    without duplicating normal paragraph and table texts.
    """
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    }
    body = doc.element.body

    textbox_texts: list[str] = []
    # Search for textboxes specifically
    txbx_nodes = body.findall('.//w:txbxContent//w:t', ns) + body.findall('.//wps:txbx//w:t', ns)
    for node in txbx_nodes:
        if node.text and node.text.strip():
            textbox_texts.append(node.text.strip())

    return " ".join(textbox_texts)

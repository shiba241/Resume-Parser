"""
processors/doc_processor.py
=============================
Handles old-format .DOC files via LibreOffice headless conversion.
LibreOffice converts .doc → .docx (or .txt), then we use the DOCX processor.

If LibreOffice is not available, raises a clear, user-friendly error.
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocConversionError(Exception):
    pass


def _find_libreoffice() -> Optional[str]:
    """Find the LibreOffice executable on this system."""
    # Common Windows paths
    candidates = [
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ]
    for path in candidates:
        if path and Path(path).exists():
            return path
    return None


def extract_text_from_doc(file_bytes: bytes, filename: str = "") -> str:
    """
    Convert .DOC to DOCX using LibreOffice, then extract text.
    Raises DocConversionError with actionable instructions if unavailable.
    """
    from typing import Optional  # local import to avoid circular
    lo_path = _find_libreoffice()

    if not lo_path:
        raise DocConversionError(
            "LibreOffice is required to process .DOC files but was not found.\n\n"
            "To install LibreOffice on Windows:\n"
            "  1. Download from: https://www.libreoffice.org/download/download/\n"
            "  2. Install and restart.\n"
            "  3. Ensure 'soffice.exe' is in your PATH or at:\n"
            "     C:\\Program Files\\LibreOffice\\program\\soffice.exe\n\n"
            "Alternative: Convert your .DOC file to .DOCX in Microsoft Word\n"
            "and upload the .DOCX version instead."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        input_file = tmp_path / (Path(filename).stem or "resume") + ".doc"
        input_file.write_bytes(file_bytes)

        logger.info("Converting '%s' to DOCX via LibreOffice...", filename)

        try:
            result = subprocess.run(
                [
                    lo_path,
                    "--headless",
                    "--convert-to", "docx",
                    "--outdir", str(tmp_path),
                    str(input_file),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            raise DocConversionError(
                f"LibreOffice conversion timed out for '{filename}'. "
                "The file may be corrupt or too large."
            )
        except Exception as exc:
            raise DocConversionError(
                f"LibreOffice conversion failed for '{filename}': {exc}"
            ) from exc

        if result.returncode != 0:
            raise DocConversionError(
                f"LibreOffice returned error code {result.returncode} for '{filename}'.\n"
                f"stderr: {result.stderr[:500]}"
            )

        # Locate the converted DOCX
        converted_files = list(tmp_path.glob("*.docx"))
        if not converted_files:
            raise DocConversionError(
                f"LibreOffice did not produce a DOCX file for '{filename}'."
            )

        docx_bytes = converted_files[0].read_bytes()

    # Now use the DOCX processor
    from processors.docx_processor import extract_text_from_docx
    return extract_text_from_docx(docx_bytes, filename=filename)

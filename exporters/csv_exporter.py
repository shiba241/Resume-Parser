"""
exporters/csv_exporter.py
==========================
Export candidate profiles to CSV format.
One row per candidate, nested fields flattened.
"""

import io
from pathlib import Path
from typing import Union

import pandas as pd
from schemas.candidate_schema import CandidateProfile


def _build_dataframe(candidates: list[CandidateProfile]) -> pd.DataFrame:
    rows = [c.to_flat_dict() for c in candidates]
    return pd.DataFrame(rows)


def export_to_csv(
    candidates: list[CandidateProfile],
    output_path: Union[str, Path],
) -> Path:
    output_path = Path(output_path)
    df = _build_dataframe(candidates)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")  # utf-8-sig for Excel compatibility
    return output_path


def export_to_csv_bytes(candidates: list[CandidateProfile]) -> bytes:
    """Return CSV export as bytes (for Streamlit download button)."""
    df = _build_dataframe(candidates)
    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue().encode("utf-8-sig")

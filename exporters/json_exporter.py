"""
exporters/json_exporter.py
===========================
Export candidate profiles to JSON format.
"""

import json
from pathlib import Path
from typing import Union
from schemas.candidate_schema import CandidateProfile


def export_to_json(
    candidates: list[CandidateProfile],
    output_path: Union[str, Path],
) -> Path:
    """
    Export all candidates to a single JSON file.
    Preserves full nested structure.
    """
    output_path = Path(output_path)
    data = {
        "total_candidates": len(candidates),
        "candidates": [c.model_dump() for c in candidates],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return output_path


def export_to_json_bytes(candidates: list[CandidateProfile]) -> bytes:
    """Return JSON export as bytes (for Streamlit download button)."""
    data = {
        "total_candidates": len(candidates),
        "candidates": [c.model_dump() for c in candidates],
    }
    return json.dumps(data, indent=2, ensure_ascii=False, default=str).encode("utf-8")

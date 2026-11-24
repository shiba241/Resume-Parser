"""
exporters/excel_exporter.py
============================
Export candidate profiles to Excel (.xlsx).
Main sheet: one row per candidate (flattened).
Additional sheets: education, work_experience, projects, certifications.
"""

import io
from pathlib import Path
from typing import Union

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from schemas.candidate_schema import CandidateProfile


# ---------------------------------------------------------------------------
# Sheet builders
# ---------------------------------------------------------------------------

def _main_sheet_rows(candidates: list[CandidateProfile]) -> list[dict]:
    return [c.to_flat_dict() for c in candidates]


def _education_rows(candidates: list[CandidateProfile]) -> list[dict]:
    rows = []
    for c in candidates:
        for edu in c.education:
            rows.append({
                "candidate_id": c.candidate_id,
                "candidate_name": c.personal_information.full_name,
                "degree": edu.degree,
                "course": edu.course,
                "specialization": edu.specialization,
                "institution_name": edu.institution_name,
                "university_name": edu.university_name,
                "start_year": edu.start_year,
                "graduation_year": edu.graduation_year,
                "cgpa": edu.cgpa,
                "percentage": edu.percentage,
                "academic_achievements": " | ".join(edu.academic_achievements),
            })
    return rows


def _experience_rows(candidates: list[CandidateProfile]) -> list[dict]:
    rows = []
    for c in candidates:
        for we in c.work_experience:
            rows.append({
                "candidate_id": c.candidate_id,
                "candidate_name": c.personal_information.full_name,
                "company_name": we.company_name,
                "job_designation": we.job_designation,
                "employment_type": we.employment_type,
                "job_location": we.job_location,
                "start_date": we.start_date,
                "end_date": we.end_date,
                "currently_working": we.currently_working,
                "duration": we.duration,
                "roles_and_responsibilities": " | ".join(we.roles_and_responsibilities),
                "technologies_used": " | ".join(we.technologies_used),
                "key_accomplishments": " | ".join(we.key_accomplishments),
            })
    return rows


def _projects_rows(candidates: list[CandidateProfile]) -> list[dict]:
    rows = []
    for c in candidates:
        for proj in c.projects:
            rows.append({
                "candidate_id": c.candidate_id,
                "candidate_name": c.personal_information.full_name,
                "project_name": proj.project_name,
                "project_description": proj.project_description,
                "project_objective": proj.project_objective,
                "technologies_used": " | ".join(proj.technologies_used),
                "tools_used": " | ".join(proj.tools_used),
                "candidate_role": proj.candidate_role,
                "key_features": " | ".join(proj.key_features),
                "project_outcomes": proj.project_outcomes,
                "project_url": proj.project_url,
            })
    return rows


def _certifications_rows(candidates: list[CandidateProfile]) -> list[dict]:
    rows = []
    for c in candidates:
        for cert in c.certifications:
            rows.append({
                "candidate_id": c.candidate_id,
                "candidate_name": c.personal_information.full_name,
                "certification_name": cert.certification_name,
                "issuing_organization": cert.issuing_organization,
                "issue_date": cert.issue_date,
                "expiry_date": cert.expiry_date,
                "credential_id": cert.credential_id,
                "credential_url": cert.credential_url,
            })
    return rows


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------

def _style_header_row(ws, header_fill_hex: str = "1F4E79"):
    """Bold white text on dark-blue background for header row."""
    header_fill = PatternFill(fill_type="solid", fgColor=header_fill_hex)
    header_font = Font(bold=True, color="FFFFFF", size=11)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", wrap_text=False)


def _auto_width(ws):
    """Auto-fit column widths (capped at 60 chars)."""
    for col_cells in ws.columns:
        max_len = max(
            (len(str(cell.value)) if cell.value else 0 for cell in col_cells),
            default=0
        )
        col_letter = get_column_letter(col_cells[0].column)
        ws.column_dimensions[col_letter].width = min(max_len + 4, 60)


# ---------------------------------------------------------------------------
# Public export functions
# ---------------------------------------------------------------------------

def _write_sheet(writer, sheet_name: str, rows: list[dict], header_color: str):
    if not rows:
        return
    df = pd.DataFrame(rows)
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    ws = writer.sheets[sheet_name]
    _style_header_row(ws, header_color)
    _auto_width(ws)


def export_to_excel_bytes(candidates: list[CandidateProfile]) -> bytes:
    """Return Excel file as bytes for Streamlit download button."""
    buf = io.BytesIO()
    _write_excel(candidates, buf)
    return buf.getvalue()


def export_to_excel(
    candidates: list[CandidateProfile],
    output_path: Union[str, Path],
) -> Path:
    output_path = Path(output_path)
    with open(output_path, "wb") as f:
        f.write(export_to_excel_bytes(candidates))
    return output_path


def _write_excel(candidates: list[CandidateProfile], target):
    """Write all sheets to `target` (file path or BytesIO)."""
    with pd.ExcelWriter(target, engine="openpyxl") as writer:
        # Main candidates sheet
        main_rows = _main_sheet_rows(candidates)
        df_main = pd.DataFrame(main_rows)
        df_main.to_excel(writer, sheet_name="Candidates", index=False)
        ws_main = writer.sheets["Candidates"]
        _style_header_row(ws_main, "1F4E79")
        _auto_width(ws_main)

        # Freeze top row
        ws_main.freeze_panes = "A2"

        # Additional detail sheets
        _write_sheet(writer, "Education", _education_rows(candidates), "375623")
        _write_sheet(writer, "Work Experience", _experience_rows(candidates), "7B3F00")
        _write_sheet(writer, "Projects", _projects_rows(candidates), "4B0082")
        _write_sheet(writer, "Certifications", _certifications_rows(candidates), "1A5276")

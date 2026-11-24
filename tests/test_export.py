"""
tests/test_export.py
=====================
Tests for all export formats.
Run: pytest tests/test_export.py -v
"""

import json
import pytest
from schemas.candidate_schema import CandidateProfile, PersonalInformation, ProfessionalInformation


def _make_sample_candidate(candidate_id="CAND_001", name="John Doe") -> CandidateProfile:
    profile = CandidateProfile()
    profile.candidate_id = candidate_id
    profile.source_file = "test_resume.pdf"
    profile.personal_information.full_name = name
    profile.personal_information.email = "john@example.com"
    profile.personal_information.phone = ["+1-555-0100"]
    profile.professional_information.current_designation = "Software Engineer"
    profile.professional_information.total_experience_years = 3.5
    profile.technical_skills.programming_languages = ["Python", "JavaScript"]
    profile.validation_status = "verified"
    profile.confidence_score = 85.0
    return profile


class TestJSONExport:
    def test_json_export_valid(self):
        from exporters.json_exporter import export_to_json_bytes
        candidates = [_make_sample_candidate()]
        result = export_to_json_bytes(candidates)
        data = json.loads(result.decode("utf-8"))
        assert data["total_candidates"] == 1
        assert data["candidates"][0]["personal_information"]["full_name"] == "John Doe"

    def test_json_export_multiple(self):
        from exporters.json_exporter import export_to_json_bytes
        candidates = [
            _make_sample_candidate("CAND_001", "Alice"),
            _make_sample_candidate("CAND_002", "Bob"),
        ]
        result = export_to_json_bytes(candidates)
        data = json.loads(result.decode("utf-8"))
        assert data["total_candidates"] == 2


class TestCSVExport:
    def test_csv_export_valid(self):
        from exporters.csv_exporter import export_to_csv_bytes
        import io
        import pandas as pd
        candidates = [_make_sample_candidate()]
        csv_bytes = export_to_csv_bytes(candidates)
        df = pd.read_csv(io.BytesIO(csv_bytes), encoding="utf-8-sig")
        assert len(df) == 1
        assert df["full_name"].iloc[0] == "John Doe"

    def test_csv_export_multiple_rows(self):
        from exporters.csv_exporter import export_to_csv_bytes
        import io
        import pandas as pd
        candidates = [
            _make_sample_candidate("CAND_001", "Alice"),
            _make_sample_candidate("CAND_002", "Bob"),
        ]
        csv_bytes = export_to_csv_bytes(candidates)
        df = pd.read_csv(io.BytesIO(csv_bytes), encoding="utf-8-sig")
        assert len(df) == 2


class TestExcelExport:
    def test_excel_export_valid(self):
        from exporters.excel_exporter import export_to_excel_bytes
        import io
        import pandas as pd
        candidates = [_make_sample_candidate()]
        excel_bytes = export_to_excel_bytes(candidates)
        # Read the main sheet
        df = pd.read_excel(io.BytesIO(excel_bytes), sheet_name="Candidates")
        assert len(df) == 1
        assert df["full_name"].iloc[0] == "John Doe"


class TestTXTExport:
    def test_txt_export_contains_name(self):
        from exporters.txt_exporter import export_to_txt_bytes
        candidates = [_make_sample_candidate()]
        result = export_to_txt_bytes(candidates)
        text = result.decode("utf-8")
        assert "John Doe" in text
        assert "john@example.com" in text
        assert "CAND_001" in text

    def test_txt_export_separates_candidates(self):
        from exporters.txt_exporter import export_to_txt_bytes
        candidates = [
            _make_sample_candidate("CAND_001", "Alice"),
            _make_sample_candidate("CAND_002", "Bob"),
        ]
        text = export_to_txt_bytes(candidates).decode("utf-8")
        assert "Alice" in text
        assert "Bob" in text
        assert text.count("=" * 70) >= 2

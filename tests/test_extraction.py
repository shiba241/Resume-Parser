"""
tests/test_extraction.py
=========================
Tests for AI extraction + JSON repair.
Run: pytest tests/test_extraction.py -v
"""

import json
import pytest
from ai.resume_extractor import _attempt_json_repair, _strip_markdown_fences, _extract_json_object
from schemas.candidate_schema import CandidateProfile


class TestJsonRepair:

    def test_strip_markdown_fences(self):
        raw = '```json\n{"name": "John"}\n```'
        result = _strip_markdown_fences(raw)
        assert result == '{"name": "John"}'

    def test_strip_plain_fences(self):
        raw = '```\n{"name": "Jane"}\n```'
        result = _strip_markdown_fences(raw)
        assert result == '{"name": "Jane"}'

    def test_no_fences_unchanged(self):
        raw = '{"name": "Alice"}'
        result = _strip_markdown_fences(raw)
        assert result == '{"name": "Alice"}'

    def test_extract_json_object_embedded(self):
        text = 'Here is the data: {"key": "value"} done'
        result = _extract_json_object(text)
        assert result == '{"key": "value"}'

    def test_repair_valid_json(self):
        raw = '{"candidate_id": "CAND_001"}'
        result = _attempt_json_repair(raw)
        assert result is not None
        assert result["candidate_id"] == "CAND_001"

    def test_repair_trailing_comma(self):
        raw = '{"name": "John", "email": "j@j.com",}'
        result = _attempt_json_repair(raw)
        assert result is not None
        assert result["name"] == "John"

    def test_repair_fenced_json(self):
        raw = '```json\n{"candidate_id": "CAND_002"}\n```'
        result = _attempt_json_repair(raw)
        assert result is not None
        assert result["candidate_id"] == "CAND_002"

    def test_completely_invalid_returns_none(self):
        raw = "This is not JSON at all!"
        result = _attempt_json_repair(raw)
        assert result is None


class TestCandidateSchema:

    def test_empty_profile_defaults(self):
        profile = CandidateProfile()
        assert profile.personal_information.full_name is None
        assert profile.personal_information.phone == []
        assert profile.education == []
        assert profile.work_experience == []
        assert profile.validation_status == "pending"

    def test_profile_from_dict(self):
        data = {
            "candidate_id": "CAND_001",
            "source_file": "test.pdf",
            "personal_information": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "phone": ["1234567890"],
            },
        }
        profile = CandidateProfile.model_validate(data)
        assert profile.personal_information.full_name == "John Doe"
        assert profile.personal_information.email == "john@example.com"

    def test_flat_dict_generation(self):
        profile = CandidateProfile()
        profile.personal_information.full_name = "Jane Smith"
        profile.personal_information.email = "jane@example.com"
        flat = profile.to_flat_dict()
        assert flat["full_name"] == "Jane Smith"
        assert flat["email"] == "jane@example.com"
        assert "candidate_id" in flat

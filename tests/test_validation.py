"""
tests/test_validation.py
=========================
Tests for the data validator.
Run: pytest tests/test_validation.py -v
"""

import pytest
from validators.data_validator import (
    is_valid_email, is_plausible_phone, is_plausible_date,
    detect_missing_fields, compute_confidence_score,
    check_duplicate, reset_duplicate_tracker
)
from schemas.candidate_schema import CandidateProfile


class TestEmailValidation:
    def test_valid_emails(self):
        for email in ["user@example.com", "user.name+tag@domain.co.in", "a@b.org"]:
            assert is_valid_email(email), f"Should be valid: {email}"

    def test_invalid_emails(self):
        for email in ["notanemail", "@domain.com", "user@", "user @domain.com", None, ""]:
            assert not is_valid_email(email), f"Should be invalid: {email}"


class TestPhoneValidation:
    def test_valid_phones(self):
        for phone in ["+1-800-555-0100", "9876543210", "+91 98765 43210", "(555) 123-4567"]:
            assert is_plausible_phone(phone), f"Should be valid: {phone}"

    def test_invalid_phones(self):
        for phone in ["123", "not-a-phone", None, ""]:
            assert not is_plausible_phone(phone), f"Should be invalid: {phone}"


class TestDateValidation:
    def test_valid_dates(self):
        for date in ["2023-06", "2024", "Present", "current", None]:
            assert is_plausible_date(date)

    def test_invalid_dates(self):
        # Dates that don't match YYYY or YYYY-MM and aren't "present"
        for date in ["March 2024", "13-2024", "not-a-date"]:
            assert not is_plausible_date(date)


class TestMissingFields:
    def test_complete_profile_no_missing(self):
        profile = CandidateProfile()
        profile.personal_information.full_name = "John"
        profile.personal_information.email = "j@j.com"
        profile.personal_information.phone = ["1234567890"]
        profile.professional_information.current_designation = "Engineer"
        profile.professional_information.total_experience_years = 3.0
        profile.education = [{"degree": "B.Tech"}]  # type: ignore
        from schemas.candidate_schema import Education, TechnicalSkills
        profile.technical_skills.programming_languages = ["Python"]

        # Rebuild with real objects
        from schemas.candidate_schema import Education
        profile.education = [Education(degree="B.Tech")]
        profile.work_experience = []  # still missing

        missing = detect_missing_fields(profile)
        assert "email" not in missing
        assert "full_name" not in missing

    def test_empty_profile_all_missing(self):
        profile = CandidateProfile()
        missing = detect_missing_fields(profile)
        assert "full_name" in missing
        assert "email" in missing


class TestConfidenceScore:
    def test_high_confidence_complete_profile(self):
        profile = CandidateProfile()
        profile.personal_information.full_name = "Jane"
        profile.personal_information.email = "jane@example.com"
        profile.personal_information.phone = ["9876543210"]
        profile.professional_information.current_designation = "Dev"
        profile.professional_information.total_experience_years = 2.0
        from schemas.candidate_schema import Education, WorkExperience
        profile.education = [Education(degree="B.Sc")]
        profile.work_experience = [WorkExperience(company_name="Acme")]
        profile.technical_skills.programming_languages = ["Python"]

        score = compute_confidence_score(profile, detect_missing_fields(profile))
        assert score >= 70

    def test_low_confidence_empty_profile(self):
        profile = CandidateProfile()
        score = compute_confidence_score(profile, detect_missing_fields(profile))
        assert score < 50


class TestDuplicateDetection:
    def setup_method(self):
        reset_duplicate_tracker()

    def test_first_occurrence_not_duplicate(self):
        assert not check_duplicate("abc123")

    def test_second_occurrence_is_duplicate(self):
        check_duplicate("abc123")
        assert check_duplicate("abc123")

    def test_different_hashes_not_duplicate(self):
        check_duplicate("hash1")
        assert not check_duplicate("hash2")

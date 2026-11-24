"""
schemas/candidate_schema.py
============================
Pydantic v2 models defining the full candidate extraction schema.
Every field uses None / [] as the default for missing data.
"""

from __future__ import annotations
import re
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ---------------------------------------------------------------------------
# Base model with permissive type coercion for LLM extraction
# ---------------------------------------------------------------------------

class BaseSchema(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, extra="ignore")


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PersonalInformation(BaseSchema):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    personal_website: Optional[str] = None


class ProfessionalInformation(BaseSchema):
    headline: Optional[str] = None
    current_designation: Optional[str] = None
    current_company: Optional[str] = None
    total_experience_years: Optional[float] = None
    experience_calculation_uncertain: bool = False
    professional_summary: Optional[str] = None
    career_objective: Optional[str] = None
    employment_status: Optional[str] = None  # e.g. "Employed", "Open to work"

    @field_validator("total_experience_years", mode="before")
    @classmethod
    def parse_experience(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if m:
                return float(m.group(1))
        return None


class Education(BaseSchema):
    degree: Optional[str] = None
    course: Optional[str] = None
    specialization: Optional[str] = None
    institution_name: Optional[str] = None
    university_name: Optional[str] = None
    start_year: Optional[str] = None
    graduation_year: Optional[str] = None
    cgpa: Optional[str] = None
    percentage: Optional[str] = None
    academic_achievements: list[str] = Field(default_factory=list)


class WorkExperience(BaseSchema):
    company_name: Optional[str] = None
    job_designation: Optional[str] = None
    employment_type: Optional[str] = None   # Full-time, Part-time, Contract, etc.
    job_location: Optional[str] = None
    start_date: Optional[str] = None        # Normalized YYYY-MM where possible
    end_date: Optional[str] = None          # "Present" if currently working
    currently_working: bool = False
    duration: Optional[str] = None
    roles_and_responsibilities: list[str] = Field(default_factory=list)
    technologies_used: list[str] = Field(default_factory=list)
    key_accomplishments: list[str] = Field(default_factory=list)


class TechnicalSkills(BaseSchema):
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    libraries: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_technologies: list[str] = Field(default_factory=list)
    developer_tools: list[str] = Field(default_factory=list)
    ai_ml_technologies: list[str] = Field(default_factory=list)
    operating_systems: list[str] = Field(default_factory=list)
    other_technical_skills: list[str] = Field(default_factory=list)


class SoftSkills(BaseSchema):
    communication: Optional[str] = None
    leadership: Optional[str] = None
    teamwork: Optional[str] = None
    problem_solving: Optional[str] = None
    management: Optional[str] = None
    other_soft_skills: list[str] = Field(default_factory=list)


class Project(BaseSchema):
    project_name: Optional[str] = None
    project_description: Optional[str] = None
    project_objective: Optional[str] = None
    technologies_used: list[str] = Field(default_factory=list)
    tools_used: list[str] = Field(default_factory=list)
    candidate_role: Optional[str] = None
    responsibilities: list[str] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list)
    project_outcomes: Optional[str] = None
    project_url: Optional[str] = None


class Certification(BaseSchema):
    certification_name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class Achievement(BaseSchema):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None  # Award, Publication, Competition, etc.
    date: Optional[str] = None
    issuing_organization: Optional[str] = None


class LanguageProficiency(BaseSchema):
    language: Optional[str] = None
    proficiency: Optional[str] = None  # Native, Fluent, Intermediate, Basic


class Internship(BaseSchema):
    company_name: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    technologies_used: list[str] = Field(default_factory=list)


class AdditionalInformation(BaseSchema):
    languages: list[LanguageProficiency] = Field(default_factory=list)
    internships: list[Internship] = Field(default_factory=list)
    publications: list[str] = Field(default_factory=list)
    research_work: list[str] = Field(default_factory=list)
    volunteer_experience: list[str] = Field(default_factory=list)
    professional_memberships: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Root candidate model
# ---------------------------------------------------------------------------

class CandidateProfile(BaseSchema):
    candidate_id: str = "CAND_001"
    source_file: str = ""
    personal_information: PersonalInformation = Field(default_factory=PersonalInformation)
    professional_information: ProfessionalInformation = Field(default_factory=ProfessionalInformation)
    education: list[Education] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    technical_skills: TechnicalSkills = Field(default_factory=TechnicalSkills)
    soft_skills: SoftSkills = Field(default_factory=SoftSkills)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    additional_information: AdditionalInformation = Field(default_factory=AdditionalInformation)

    # Meta fields
    missing_fields: list[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    validation_status: str = "pending"  # pending | verified | needs_review | failed
    extraction_error: Optional[str] = None
    file_hash: Optional[str] = None

    def to_flat_dict(self) -> dict[str, Any]:
        """Return a flat dictionary suitable for DataFrame / CSV / Excel rows."""
        pi = self.personal_information
        prof = self.professional_information
        ts = self.technical_skills
        ss = self.soft_skills

        def join(lst: list) -> str:
            return " | ".join(str(x) for x in lst if x) if lst else ""

        def edu_summary() -> str:
            parts = []
            for e in self.education:
                parts.append(f"{e.degree or ''} from {e.institution_name or ''} ({e.graduation_year or ''})")
            return " | ".join(p for p in parts if p.strip(" from ()"))

        def exp_summary() -> str:
            parts = []
            for w in self.work_experience:
                parts.append(f"{w.job_designation or ''} at {w.company_name or ''} ({w.start_date or ''}–{w.end_date or ''})")
            return " | ".join(p for p in parts if p.strip(" at ()–"))

        return {
            "candidate_id": self.candidate_id,
            "source_file": self.source_file,
            "full_name": pi.full_name,
            "email": pi.email,
            "phone": join(pi.phone),
            "location": pi.location,
            "city": pi.city,
            "state": pi.state,
            "country": pi.country,
            "linkedin": pi.linkedin,
            "github": pi.github,
            "portfolio": pi.portfolio,
            "headline": prof.headline,
            "current_designation": prof.current_designation,
            "current_company": prof.current_company,
            "total_experience_years": prof.total_experience_years,
            "employment_status": prof.employment_status,
            "professional_summary": prof.professional_summary,
            "career_objective": prof.career_objective,
            "education_summary": edu_summary(),
            "work_experience_summary": exp_summary(),
            "programming_languages": join(ts.programming_languages),
            "frameworks": join(ts.frameworks),
            "databases": join(ts.databases),
            "cloud_technologies": join(ts.cloud_technologies),
            "developer_tools": join(ts.developer_tools),
            "ai_ml_technologies": join(ts.ai_ml_technologies),
            "other_technical_skills": join(ts.other_technical_skills),
            "soft_skills": join(
                ([ss.communication] if ss.communication else []) +
                ([ss.leadership] if ss.leadership else []) +
                ([ss.teamwork] if ss.teamwork else []) +
                ([ss.problem_solving] if ss.problem_solving else []) +
                ([ss.management] if ss.management else []) +
                ss.other_soft_skills
            ),
            "num_projects": len(self.projects),
            "num_certifications": len(self.certifications),
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "missing_fields": join(self.missing_fields),
        }

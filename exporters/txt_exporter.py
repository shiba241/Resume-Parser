"""
exporters/txt_exporter.py
==========================
Export candidate profiles to a human-readable TXT report.
Each candidate is clearly separated.
"""

from pathlib import Path
from typing import Union
from schemas.candidate_schema import CandidateProfile


def _format_candidate(c: CandidateProfile) -> str:
    lines = []
    sep = "=" * 70

    pi = c.personal_information
    prof = c.professional_information
    ts = c.technical_skills
    ss = c.soft_skills

    def section(title: str):
        lines.append(f"\n{'─' * 50}")
        lines.append(f"  {title.upper()}")
        lines.append(f"{'─' * 50}")

    def field(label: str, value):
        if value:
            lines.append(f"  {label:<30} {value}")

    def listfield(label: str, items: list):
        if items:
            lines.append(f"  {label:<30} {', '.join(str(i) for i in items if i)}")

    lines.append(sep)
    lines.append(f"  CANDIDATE: {c.candidate_id}  |  File: {c.source_file}")
    lines.append(f"  Confidence: {c.confidence_score or 'N/A'}  |  Status: {c.validation_status.upper()}")
    lines.append(sep)

    section("Personal Information")
    field("Full Name:", pi.full_name)
    field("Email:", pi.email)
    listfield("Phone:", pi.phone)
    field("Location:", pi.location)
    field("LinkedIn:", pi.linkedin)
    field("GitHub:", pi.github)
    field("Portfolio:", pi.portfolio)

    section("Professional Information")
    field("Headline:", prof.headline)
    field("Current Designation:", prof.current_designation)
    field("Current Company:", prof.current_company)
    field("Total Experience:", f"{prof.total_experience_years} years" if prof.total_experience_years else None)
    field("Employment Status:", prof.employment_status)
    if prof.professional_summary:
        lines.append(f"\n  Summary:\n  {prof.professional_summary}")
    if prof.career_objective:
        lines.append(f"\n  Career Objective:\n  {prof.career_objective}")

    if c.education:
        section("Education")
        for i, edu in enumerate(c.education, 1):
            lines.append(f"\n  [{i}] {edu.degree or ''} {edu.specialization or ''}")
            field("    Institution:", edu.institution_name)
            field("    University:", edu.university_name)
            field("    Period:", f"{edu.start_year or '?'} – {edu.graduation_year or '?'}")
            field("    CGPA:", edu.cgpa)
            field("    Percentage:", edu.percentage)

    if c.work_experience:
        section("Work Experience")
        for i, we in enumerate(c.work_experience, 1):
            lines.append(f"\n  [{i}] {we.job_designation or ''} at {we.company_name or ''}")
            field("    Type:", we.employment_type)
            field("    Location:", we.job_location)
            field("    Period:", f"{we.start_date or '?'} – {we.end_date or ('Present' if we.currently_working else '?')}")
            field("    Duration:", we.duration)
            if we.roles_and_responsibilities:
                lines.append("    Responsibilities:")
                for r in we.roles_and_responsibilities:
                    lines.append(f"      • {r}")
            if we.technologies_used:
                lines.append(f"    Technologies: {', '.join(we.technologies_used)}")
            if we.key_accomplishments:
                lines.append("    Accomplishments:")
                for a in we.key_accomplishments:
                    lines.append(f"      • {a}")

    section("Technical Skills")
    listfield("Programming:", ts.programming_languages)
    listfield("Frameworks:", ts.frameworks)
    listfield("Libraries:", ts.libraries)
    listfield("Databases:", ts.databases)
    listfield("Cloud:", ts.cloud_technologies)
    listfield("Tools:", ts.developer_tools)
    listfield("AI/ML:", ts.ai_ml_technologies)
    listfield("OS:", ts.operating_systems)
    listfield("Other:", ts.other_technical_skills)

    section("Soft Skills")
    field("Communication:", ss.communication)
    field("Leadership:", ss.leadership)
    field("Teamwork:", ss.teamwork)
    field("Problem Solving:", ss.problem_solving)
    field("Management:", ss.management)
    listfield("Other:", ss.other_soft_skills)

    if c.projects:
        section("Projects")
        for i, proj in enumerate(c.projects, 1):
            lines.append(f"\n  [{i}] {proj.project_name or 'Unnamed Project'}")
            if proj.project_description:
                lines.append(f"    {proj.project_description}")
            listfield("    Technologies:", proj.technologies_used)
            field("    URL:", proj.project_url)

    if c.certifications:
        section("Certifications")
        for cert in c.certifications:
            lines.append(f"  • {cert.certification_name or ''} — {cert.issuing_organization or ''} ({cert.issue_date or ''})")

    if c.achievements:
        section("Achievements")
        for ach in c.achievements:
            lines.append(f"  • {ach.title or ''}: {ach.description or ''}")

    ai = c.additional_information
    if ai.languages:
        section("Languages")
        for lang in ai.languages:
            lines.append(f"  • {lang.language} ({lang.proficiency or ''})")

    if ai.hobbies:
        section("Hobbies & Interests")
        lines.append(f"  {', '.join(ai.hobbies)}")

    if c.missing_fields:
        lines.append(f"\n  ⚠ Missing: {', '.join(c.missing_fields)}")

    lines.append(f"\n{'=' * 70}\n")
    return "\n".join(lines)


def export_to_txt_bytes(candidates: list[CandidateProfile]) -> bytes:
    parts = [
        f"AI RESUME PARSER — CANDIDATE REPORT\n"
        f"Total Candidates: {len(candidates)}\n"
        f"{'=' * 70}\n"
    ]
    for c in candidates:
        parts.append(_format_candidate(c))
    return "\n".join(parts).encode("utf-8")


def export_to_txt(
    candidates: list[CandidateProfile],
    output_path: Union[str, Path],
) -> Path:
    output_path = Path(output_path)
    output_path.write_bytes(export_to_txt_bytes(candidates))
    return output_path

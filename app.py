"""
app.py
======
AI-Powered Resume Parser & Bulk Information Extraction Engine
Unified Single-Page Professional Dashboard
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

import streamlit as st
import pandas as pd
import json

# ---------------------------------------------------------------------------
# Page configuration — Must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Intelligence Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Core Project Imports
# ---------------------------------------------------------------------------
from config.settings import (
    GROQ_MODEL, MAX_RESUMES_PER_BATCH, validate_config, SUPPORTED_EXTENSIONS
)
from processors.file_detector import detect_file_type, is_supported
from processors.pdf_processor import extract_text_from_pdf, PDFProcessingError
from processors.docx_processor import extract_text_from_docx, DocxProcessingError
from processors.doc_processor import extract_text_from_doc, DocConversionError
from processors.image_processor import extract_text_from_image, ImageProcessingError
from processors.ocr_processor import is_ocr_available
from utils.text_cleaner import clean_text
from utils.file_utils import compute_file_hash, clear_temp_directory
from ai.resume_extractor import extract_candidate_from_text, ExtractionError
from ai.groq_client import test_groq_connection, get_available_models, GroqAPIError
from validators.data_validator import validate_candidate, reset_duplicate_tracker
from schemas.candidate_schema import CandidateProfile
from exporters.excel_exporter import export_to_excel_bytes
from exporters.json_exporter import export_to_json_bytes
from exporters.csv_exporter import export_to_csv_bytes
from exporters.txt_exporter import export_to_txt_bytes


# ---------------------------------------------------------------------------
# Professional Modern CSS Styling
# ---------------------------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
    /* Global layout enhancements */
    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 96%;
    }
    
    /* Header card */
    .dashboard-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 24px 28px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
    }
    .dashboard-header h1 {
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .dashboard-header p {
        color: #94a3b8;
        font-size: 0.95rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    .header-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        color: #cbd5e1;
    }

    /* Section cards */
    .dashboard-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* KPI Metric Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 2px;
    }

    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: capitalize;
    }
    .status-verified {
        background: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }
    .status-needs_review {
        background: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
    }
    .status-failed {
        background: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }
    .status-pending {
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    /* Skill pill badges */
    .skill-pill {
        display: inline-block;
        background: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #dbeafe;
        padding: 3px 10px;
        border-radius: 16px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 2px 4px 2px 0;
    }
    .skill-pill-tool {
        background: #f8fafc;
        color: #334155;
        border: 1px solid #e2e8f0;
    }
    .skill-pill-soft {
        background: #fdf4ff;
        color: #86198f;
        border: 1px solid #f5d0fe;
    }

    /* Section dividers with title */
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 10px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Candidate Dossier Header */
    .candidate-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def _init_session():
    defaults = {
        "candidates": [],           # list[CandidateProfile]
        "processing_log": [],       # list[dict]
        "processed_hashes": set(),  # duplicate tracking set
        "selected_candidate_id": None,
        "active_model": GROQ_MODEL,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()


# ---------------------------------------------------------------------------
# Sidebar: System Status & Diagnostic Control
# ---------------------------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Engine Control")
        st.caption("Central settings and AI diagnostics")
        st.divider()

        # Config validation status
        issues = validate_config()
        if issues:
            st.error("⚠️ Config Alert")
            for i in issues:
                st.caption(f"• {i}")
        else:
            st.success("✅ Environment Configured")

        # Model details & test
        st.markdown(f"**AI Model:** `{st.session_state.active_model}`")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            if st.button("🔌 Ping API", use_container_width=True):
                with st.spinner("Connecting..."):
                    ok, msg = test_groq_connection(model=st.session_state.active_model)
                if ok:
                    st.toast(f"Connected to Groq ({msg})", icon="✅")
                else:
                    st.toast(f"Connection failed: {msg}", icon="❌")

        with col_t2:
            if st.button("📋 Models", use_container_width=True):
                with st.spinner("Fetching..."):
                    models_list = get_available_models()
                if models_list:
                    st.info(f"{len(models_list)} model(s) available")
                    st.code("\n".join(models_list), language="text")
                else:
                    st.warning("Could not fetch models.")

        st.divider()
        st.markdown("### 🔍 OCR Engine")
        ocr_ok, ocr_reason = is_ocr_available()
        if ocr_ok:
            st.success("✅ Tesseract OCR Ready")
        else:
            st.warning(f"⚠️ OCR Offline: {ocr_reason}")
            with st.expander("Install OCR"):
                st.caption(
                    "Download Windows installer from: "
                    "https://github.com/UB-Mannheim/tesseract/wiki "
                    "and add to PATH."
                )

        st.divider()
        st.markdown("### 📊 Session Data")
        total_c = len(st.session_state.candidates)
        st.write(f"Total Profiles in Memory: **{total_c}**")

        if total_c > 0:
            if st.button("🗑️ Clear All Session Data", use_container_width=True, type="secondary"):
                st.session_state.candidates = []
                st.session_state.processing_log = []
                st.session_state.processed_hashes = set()
                st.session_state.selected_candidate_id = None
                reset_duplicate_tracker()
                clear_temp_directory()
                st.toast("Session cleared successfully.", icon="🧹")
                st.rerun()

        st.caption("🔒 All resume text is processed in-memory for this session only.")


# ---------------------------------------------------------------------------
# Section: Header & Top KPI Strip
# ---------------------------------------------------------------------------
def render_header_and_kpis():
    active_m = st.session_state.active_model
    candidates: list[CandidateProfile] = st.session_state.candidates
    log = st.session_state.processing_log

    total_uploads = len(log)
    total_processed = len(candidates)
    verified_count = sum(1 for c in candidates if c.validation_status == "verified")
    needs_review_count = sum(1 for c in candidates if c.validation_status == "needs_review")
    
    avg_conf = 0.0
    if candidates:
        scores = [c.confidence_score for c in candidates if c.confidence_score is not None]
        avg_conf = (sum(scores) / len(scores)) if scores else 0.0

    # Executive Header
    st.markdown(f"""
    <div class="dashboard-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <h1>💼 AI Resume Intelligence & Extraction Engine</h1>
                <p>Bulk parsing, context-aware information extraction, automated validation & enterprise exports</p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="header-tag">⚡ Model: <b>{active_m}</b></span>
                <span class="header-tag">📄 Max Batch: <b>{MAX_RESUMES_PER_BATCH} Files</b></span>
                <span class="header-tag">🛡️ Privacy: <b>In-Memory Session</b></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Metric Cards (KPI Strip)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Uploaded Files</div>
            <div class="kpi-value">{total_uploads}</div>
            <div class="kpi-sub">Total batch inputs</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Extracted Candidates</div>
            <div class="kpi-value">{total_processed}</div>
            <div class="kpi-sub">Structured profiles</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Confidence</div>
            <div class="kpi-value">{avg_conf:.1f}%</div>
            <div class="kpi-sub">Extraction reliability</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Verified Quality</div>
            <div class="kpi-value" style="color: #16a34a;">{verified_count}</div>
            <div class="kpi-sub">Score ≥ 80%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Requires Review</div>
            <div class="kpi-value" style="color: #d97706;">{needs_review_count}</div>
            <div class="kpi-sub">Missing key fields</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")


# ---------------------------------------------------------------------------
# Section 1: Upload & Processing Command Center
# ---------------------------------------------------------------------------
def render_upload_center():
    with st.expander("📤 **Upload & Batch Extraction Center**", expanded=(len(st.session_state.candidates) == 0)):
        st.markdown(
            "Drop resumes in **PDF, DOCX, DOC, JPG, JPEG, or PNG** format. "
            f"Supports up to **{MAX_RESUMES_PER_BATCH} resumes** simultaneously."
        )

        col_drop, col_act = st.columns([3, 1])
        with col_drop:
            uploaded_files = st.file_uploader(
                "Upload Resume Files",
                type=["pdf", "docx", "doc", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="resume_uploader",
            )
        
        with col_act:
            if uploaded_files:
                st.write(f"📁 **{len(uploaded_files)} file(s) loaded**")
                file_sizes_kb = sum(f.size for f in uploaded_files) / 1024
                st.caption(f"Total batch size: {file_sizes_kb:.1f} KB")
                process_btn = st.button("🚀 Process Batch Now", type="primary", use_container_width=True)
            else:
                st.info("Upload files to enable extraction.")
                process_btn = False

        if process_btn and uploaded_files:
            _execute_bulk_extraction(uploaded_files)


def _execute_bulk_extraction(uploaded_files):
    """Processes uploaded resumes sequentially with live feedback."""
    if len(uploaded_files) > MAX_RESUMES_PER_BATCH:
        st.warning(f"Batch limited to first {MAX_RESUMES_PER_BATCH} files.")
        uploaded_files = uploaded_files[:MAX_RESUMES_PER_BATCH]

    total = len(uploaded_files)
    progress_bar = st.progress(0, text="Initializing extraction pipeline...")
    status_box = st.empty()
    live_log = st.container()

    new_candidates: list[CandidateProfile] = []
    new_log: list[dict] = []
    existing_count = len(st.session_state.candidates)

    for idx, uploaded_file in enumerate(uploaded_files):
        filename = uploaded_file.name
        progress_bar.progress(idx / total, text=f"Processing ({idx + 1}/{total}): {filename}")
        status_box.info(f"🔄 **{filename}** — Reading document bytes...")

        file_bytes = uploaded_file.read()
        file_hash = compute_file_hash(file_bytes)

        log_item = {
            "filename": filename,
            "size_kb": round(len(file_bytes) / 1024, 1),
            "status": "pending",
            "candidate_name": "—",
            "confidence": "—",
            "message": "",
        }

        # 1. Duplicate check
        if file_hash in st.session_state.processed_hashes:
            log_item["status"] = "skipped"
            log_item["message"] = "Duplicate file already in session"
            new_log.append(log_item)
            live_log.warning(f"⚠️ **{filename}** — Duplicate skipped.")
            continue

        # 2. File type detection
        if not is_supported(filename):
            log_item["status"] = "error"
            log_item["message"] = "Unsupported format"
            new_log.append(log_item)
            live_log.error(f"❌ **{filename}** — Unsupported file format.")
            continue

        file_type = detect_file_type(filename, file_bytes)
        status_box.info(f"🔄 **{filename}** — Format: {file_type.upper()}. Extracting raw text...")

        # 3. Document text extraction
        raw_text = ""
        ext_err = None
        try:
            if file_type == "pdf":
                raw_text = extract_text_from_pdf(file_bytes, filename)
            elif file_type == "docx":
                raw_text = extract_text_from_docx(file_bytes, filename)
            elif file_type == "doc":
                raw_text = extract_text_from_doc(file_bytes, filename)
            elif file_type == "image":
                raw_text = extract_text_from_image(file_bytes, filename)
        except Exception as exc:
            ext_err = str(exc)

        if ext_err or not raw_text.strip():
            msg = ext_err or "No readable text extracted"
            log_item["status"] = "error"
            log_item["message"] = msg[:120]
            new_log.append(log_item)
            live_log.error(f"❌ **{filename}** — {msg[:100]}")
            continue

        # 4. Text cleaning
        status_box.info(f"🔄 **{filename}** — Cleaning text and suppressing noise ({len(raw_text)} chars)...")
        cleaned_text = clean_text(raw_text)

        # 5. AI Extraction with Groq
        cand_id = f"CAND_{existing_count + len(new_candidates) + 1:03d}"
        status_box.info(f"🤖 **{filename}** — AI Extraction via {st.session_state.active_model}...")

        try:
            profile = extract_candidate_from_text(cleaned_text, filename, cand_id)
        except ExtractionError as exc:
            log_item["status"] = "error"
            log_item["message"] = f"Extraction failed: {str(exc)[:120]}"
            new_log.append(log_item)
            live_log.error(f"❌ **{filename}** — AI parsing failed: {str(exc)[:100]}")
            continue

        # 6. Validation & Confidence Scoring
        profile.file_hash = file_hash
        validate_candidate(profile)

        # 7. Commit
        st.session_state.processed_hashes.add(file_hash)
        new_candidates.append(profile)

        c_name = profile.personal_information.full_name or "Unknown Candidate"
        c_conf = f"{profile.confidence_score:.1f}%" if profile.confidence_score else "N/A"
        log_item["status"] = "success"
        log_item["candidate_name"] = c_name
        log_item["confidence"] = c_conf
        log_item["message"] = profile.validation_status.replace("_", " ").title()
        new_log.append(log_item)

        live_log.success(f"✅ **{filename}** ➔ **{c_name}** ({c_conf} confidence, {profile.validation_status})")

    # Finalize batch
    progress_bar.progress(1.0, text="Batch processing completed.")
    status_box.empty()

    st.session_state.candidates.extend(new_candidates)
    st.session_state.processing_log.extend(new_log)

    # Auto-select the first candidate if none selected
    if new_candidates and not st.session_state.selected_candidate_id:
        st.session_state.selected_candidate_id = new_candidates[0].candidate_id

    st.toast(f"Batch complete: {len(new_candidates)} candidate(s) extracted successfully!", icon="🎉")
    st.rerun()


# ---------------------------------------------------------------------------
# Section 2: Candidate Results Hub & Search Bar
# ---------------------------------------------------------------------------
def render_results_table(candidates: list[CandidateProfile]) -> list[CandidateProfile]:
    st.markdown('<div class="section-title">👥 Candidate Intelligence Directory</div>', unsafe_allow_html=True)

    # Search & Filter Controls
    col_search, col_status, col_exp, col_skill = st.columns([2.5, 1.2, 1, 1.8])

    with col_search:
        search_query = st.text_input(
            "Search Candidates",
            placeholder="Search by name, email, company, or job title...",
            label_visibility="collapsed",
        ).strip().lower()

    with col_status:
        status_opts = ["All Statuses", "verified", "needs_review", "failed"]
        status_filter = st.selectbox(
            "Filter Status",
            status_opts,
            label_visibility="collapsed",
            format_func=lambda x: "All Statuses" if x == "All Statuses" else x.replace("_", " ").title(),
        )

    with col_exp:
        min_experience = st.number_input(
            "Min Years Exp",
            min_value=0.0,
            max_value=40.0,
            value=0.0,
            step=0.5,
            label_visibility="collapsed",
            help="Filter candidates having at least this many years of experience",
        )

    with col_skill:
        # Collect top unique skills across candidates
        all_skills_set = set()
        for c in candidates:
            all_skills_set.update(c.technical_skills.programming_languages)
            all_skills_set.update(c.technical_skills.frameworks)
            all_skills_set.update(c.technical_skills.cloud_technologies)
            all_skills_set.update(c.technical_skills.databases)
        
        skill_opts = ["All Technologies"] + sorted(list(all_skills_set))
        skill_filter = st.selectbox("Filter Tech", skill_opts, label_visibility="collapsed")

    # Apply Filtering Logic
    filtered = []
    for c in candidates:
        pi = c.personal_information
        prof = c.professional_information
        ts = c.technical_skills

        # Text match
        if search_query:
            haystack = f"{pi.full_name or ''} {pi.email or ''} {prof.current_company or ''} {prof.current_designation or ''} {prof.headline or ''}".lower()
            if search_query not in haystack:
                continue

        # Status match
        if status_filter != "All Statuses" and c.validation_status != status_filter:
            continue

        # Experience match
        cand_exp = prof.total_experience_years or 0.0
        if min_experience > 0 and cand_exp < min_experience:
            continue

        # Skill match
        if skill_filter != "All Technologies":
            all_c_skills = [s.lower() for s in (ts.programming_languages + ts.frameworks + ts.cloud_technologies + ts.databases)]
            if skill_filter.lower() not in all_c_skills:
                continue

        filtered.append(c)

    # Show count banner
    st.caption(f"Showing **{len(filtered)}** of **{len(candidates)}** candidate profiles")

    if not filtered:
        st.warning("No candidate records match the active search/filter criteria.")
        return []

    # Prepare tabular data
    table_rows = []
    for c in filtered:
        pi = c.personal_information
        prof = c.professional_information
        ts = c.technical_skills
        
        skills_summary = ", ".join(ts.programming_languages[:3] + ts.frameworks[:2])
        if not skills_summary:
            skills_summary = "—"

        status_display = {
            "verified": "🟢 Verified",
            "needs_review": "🟡 Needs Review",
            "failed": "🔴 Failed",
            "pending": "⚪ Pending",
        }.get(c.validation_status, c.validation_status)

        table_rows.append({
            "ID": c.candidate_id,
            "Full Name": pi.full_name or "Unknown",
            "Current Role": prof.current_designation or "—",
            "Company": prof.current_company or "—",
            "Experience": f"{prof.total_experience_years:.1f} yrs" if prof.total_experience_years else "—",
            "Email": pi.email or "—",
            "Phone": pi.phone[0] if pi.phone else "—",
            "Key Skills": skills_summary,
            "Confidence": f"{c.confidence_score:.1f}%" if c.confidence_score else "N/A",
            "Status": status_display,
        })

    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
    return filtered


# ---------------------------------------------------------------------------
# Section 3: Detailed Candidate Dossier & Quick Editor
# ---------------------------------------------------------------------------
def render_candidate_dossier(filtered_candidates: list[CandidateProfile]):
    st.markdown('<div class="section-title">🔍 Detailed Candidate Dossier & Field Editor</div>', unsafe_allow_html=True)

    # Candidate selection dropdown
    options_map = {
        c.candidate_id: f"{c.candidate_id} — {c.personal_information.full_name or c.source_file} ({c.professional_information.current_designation or 'No Title'})"
        for c in filtered_candidates
    }

    current_sel = st.session_state.selected_candidate_id
    if current_sel not in options_map:
        current_sel = filtered_candidates[0].candidate_id
        st.session_state.selected_candidate_id = current_sel

    col_pick, col_badge = st.columns([3, 1])
    with col_pick:
        selected_id = st.selectbox(
            "Select Candidate Dossier",
            options=list(options_map.keys()),
            format_func=lambda x: options_map[x],
            index=list(options_map.keys()).index(current_sel),
            label_visibility="collapsed",
        )
        st.session_state.selected_candidate_id = selected_id

    # Retrieve selected profile
    candidate = next((c for c in filtered_candidates if c.candidate_id == selected_id), None)
    if not candidate:
        return

    pi = candidate.personal_information
    prof = candidate.professional_information
    ts = candidate.technical_skills
    ss = candidate.soft_skills

    with col_badge:
        status_cls = f"status-{candidate.validation_status}"
        conf_str = f"{candidate.confidence_score:.1f}%" if candidate.confidence_score else "N/A"
        st.markdown(f"""
        <div style="text-align: right; padding-top: 6px;">
            <span class="status-badge {status_cls}">{candidate.validation_status.replace('_', ' ').upper()}</span>
            <div style="font-size: 0.82rem; color: #64748b; margin-top: 4px;">Confidence: <b>{conf_str}</b></div>
        </div>
        """, unsafe_allow_html=True)

    # Dossier Tabs
    tab_overview, tab_exp, tab_edu, tab_skills, tab_projects, tab_edit = st.tabs([
        "👤 Profile & Contact",
        "💼 Experience History",
        "🎓 Education",
        "🛠️ Skill Matrix",
        "🔬 Projects & Certs",
        "✏️ Edit Information",
    ])

    # Tab 1: Profile & Contact
    with tab_overview:
        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("#### Contact Details")
            st.write(f"**Full Name:** {pi.full_name or '—'}")
            st.write(f"**Email:** {pi.email or '—'}")
            st.write(f"**Phone:** {', '.join(pi.phone) if pi.phone else '—'}")
            st.write(f"**Location:** {pi.location or '—'} ({pi.city or ''}, {pi.country or ''})".rstrip(" (, )"))
            st.write(f"**Source Resume File:** `{candidate.source_file}`")

        with c_right:
            st.markdown("#### Professional Identity")
            st.write(f"**Headline:** {prof.headline or '—'}")
            st.write(f"**Current Designation:** {prof.current_designation or '—'}")
            st.write(f"**Company:** {prof.current_company or '—'}")
            st.write(f"**Total Experience:** {f'{prof.total_experience_years} years' if prof.total_experience_years else '—'}")
            
            # Online Profiles
            links = []
            if pi.linkedin:
                links.append(f"[LinkedIn]({pi.linkedin})")
            if pi.github:
                links.append(f"[GitHub]({pi.github})")
            if pi.portfolio:
                links.append(f"[Portfolio]({pi.portfolio})")
            if pi.personal_website:
                links.append(f"[Website]({pi.personal_website})")
            st.write(f"**Web Links:** {' | '.join(links) if links else '—'}")

        if prof.professional_summary:
            st.markdown("#### Professional Summary")
            st.info(prof.professional_summary)
        elif prof.career_objective:
            st.markdown("#### Career Objective")
            st.info(prof.career_objective)

    # Tab 2: Work Experience
    with tab_exp:
        if not candidate.work_experience:
            st.caption("No explicit employment records detected in resume.")
        else:
            for idx, we in enumerate(candidate.work_experience, 1):
                st.markdown(f"##### {idx}. {we.job_designation or 'Role'} — **{we.company_name or 'Company'}**")
                period_str = f"{we.start_date or '?'} to {we.end_date or ('Present' if we.currently_working else '?')}"
                st.caption(f"🗓️ {period_str} | 📍 {we.job_location or 'Location not specified'} | Type: {we.employment_type or 'Full-time'}")

                if we.roles_and_responsibilities:
                    st.write("**Key Responsibilities:**")
                    for resp in we.roles_and_responsibilities:
                        st.markdown(f"• {resp}")

                if we.technologies_used:
                    tech_html = "".join([f'<span class="skill-pill">{t}</span>' for t in we.technologies_used])
                    st.markdown(f"**Tech Used:** {tech_html}", unsafe_allow_html=True)

                if we.key_accomplishments:
                    st.write("**Accomplishments:**")
                    for acc in we.key_accomplishments:
                        st.markdown(f"⭐ {acc}")
                
                if idx < len(candidate.work_experience):
                    st.divider()

    # Tab 3: Education
    with tab_edu:
        if not candidate.education:
            st.caption("No education records detected.")
        else:
            for idx, edu in enumerate(candidate.education, 1):
                st.markdown(f"##### {idx}. {edu.degree or 'Degree'} {f'in {edu.specialization}' if edu.specialization else ''}")
                st.write(f"**Institution:** {edu.institution_name or edu.university_name or '—'}")
                st.caption(f"Graduation: **{edu.graduation_year or '—'}** | CGPA/Score: **{edu.cgpa or edu.percentage or '—'}**")
                if edu.academic_achievements:
                    for ach in edu.academic_achievements:
                        st.markdown(f"• {ach}")
                if idx < len(candidate.education):
                    st.divider()

    # Tab 4: Skill Matrix
    with tab_skills:
        def render_pill_group(title, items, pill_class="skill-pill"):
            if items:
                st.markdown(f"**{title} ({len(items)})**")
                html = "".join([f'<span class="{pill_class}">{it}</span>' for it in items if it])
                st.markdown(html, unsafe_allow_html=True)
                st.write("")

        render_pill_group("Programming Languages", ts.programming_languages)
        render_pill_group("Frameworks & Libraries", ts.frameworks + ts.libraries)
        render_pill_group("Databases", ts.databases)
        render_pill_group("Cloud Technologies", ts.cloud_technologies)
        render_pill_group("Developer Tools & Platforms", ts.developer_tools, "skill-pill skill-pill-tool")
        render_pill_group("AI & Machine Learning", ts.ai_ml_technologies)
        render_pill_group("Operating Systems", ts.operating_systems, "skill-pill skill-pill-tool")
        render_pill_group("Other Technical Competencies", ts.other_technical_skills)

        # Soft Skills
        soft_list = ([ss.communication] if ss.communication else []) + \
                    ([ss.leadership] if ss.leadership else []) + \
                    ([ss.teamwork] if ss.teamwork else []) + \
                    ([ss.problem_solving] if ss.problem_solving else []) + \
                    ([ss.management] if ss.management else []) + \
                    ss.other_soft_skills
        render_pill_group("Soft & Behavioral Skills", [s for s in soft_list if s], "skill-pill skill-pill-soft")

    # Tab 5: Projects & Certifications
    with tab_projects:
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            st.markdown("#### Projects")
            if not candidate.projects:
                st.caption("No standalone project records.")
            else:
                for p in candidate.projects:
                    st.markdown(f"**{p.project_name or 'Project'}**")
                    if p.project_description:
                        st.write(p.project_description)
                    if p.technologies_used:
                        t_pills = "".join([f'<span class="skill-pill">{t}</span>' for t in p.technologies_used])
                        st.markdown(t_pills, unsafe_allow_html=True)
                    if p.project_url:
                        st.markdown(f"🔗 [Project Link]({p.project_url})")
                    st.write("")

        with c_p2:
            st.markdown("#### Certifications & Awards")
            if not candidate.certifications and not candidate.achievements:
                st.caption("No certifications or awards listed.")
            else:
                for cert in candidate.certifications:
                    st.markdown(f"🎖️ **{cert.certification_name}**")
                    st.caption(f"{cert.issuing_organization or 'Issuer'} | Issued: {cert.issue_date or '—'}")
                for ach in candidate.achievements:
                    st.markdown(f"🏆 **{ach.title or 'Achievement'}**")
                    st.caption(ach.description or "")

    # Tab 6: In-Place Editing Form
    with tab_edit:
        st.caption("Correct any extracted information directly. Updates sync immediately to exports.")
        with st.form(key=f"edit_form_{candidate.candidate_id}"):
            col_e1, col_e2 = st.columns(2)
            f_name = col_e1.text_input("Full Name", value=pi.full_name or "")
            f_email = col_e2.text_input("Email", value=pi.email or "")
            f_phone = col_e1.text_input("Phone (comma separated)", value=", ".join(pi.phone))
            f_role = col_e2.text_input("Current Designation", value=prof.current_designation or "")
            f_comp = col_e1.text_input("Current Company", value=prof.current_company or "")
            f_exp = col_e2.number_input(
                "Total Work Experience (Years)",
                min_value=0.0,
                max_value=50.0,
                value=float(prof.total_experience_years or 0.0),
                step=0.5,
            )
            f_summary = st.text_area("Professional Summary", value=prof.professional_summary or "", height=85)

            submitted = st.form_submit_button("💾 Save Profile Changes", type="primary")
            if submitted:
                pi.full_name = f_name or None
                pi.email = f_email or None
                pi.phone = [p.strip() for p in f_phone.split(",") if p.strip()]
                prof.current_designation = f_role or None
                prof.current_company = f_comp or None
                prof.total_experience_years = f_exp if f_exp > 0 else None
                prof.professional_summary = f_summary or None
                
                # Re-validate candidate
                validate_candidate(candidate)
                st.toast("Profile changes saved successfully!", icon="✅")
                st.rerun()


# ---------------------------------------------------------------------------
# Section 4: Unified Export Hub (Always Available on Same Page)
# ---------------------------------------------------------------------------
def render_export_hub(candidates: list[CandidateProfile]):
    st.markdown('<div class="section-title">📥 Unified Multi-Format Export Hub</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown(
            "Export full structured candidate intelligence directly into enterprise spreadsheets, "
            "nested JSON databases, CSV datasets, or executive TXT reports."
        )

        col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)

        # Excel
        with col_ex1:
            try:
                excel_data = export_to_excel_bytes(candidates)
                st.download_button(
                    label="📊 Download Excel (.xlsx)",
                    data=excel_data,
                    file_name="resume_candidates_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Multi-sheet workbook: Candidates, Work Experience, Education, Projects & Certs",
                )
            except Exception as e:
                st.error(f"Excel export error: {e}")

        # JSON
        with col_ex2:
            try:
                json_data = export_to_json_bytes(candidates)
                st.download_button(
                    label="📋 Download JSON (.json)",
                    data=json_data,
                    file_name="resume_candidates_export.json",
                    mime="application/json",
                    use_container_width=True,
                    help="Complete hierarchical nested schema for database ingestion or API pipelines",
                )
            except Exception as e:
                st.error(f"JSON export error: {e}")

        # CSV
        with col_ex3:
            try:
                csv_data = export_to_csv_bytes(candidates)
                st.download_button(
                    label="📄 Download CSV (.csv)",
                    data=csv_data,
                    file_name="resume_candidates_export.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Normalized flat dataset with one row per candidate",
                )
            except Exception as e:
                st.error(f"CSV export error: {e}")

        # TXT
        with col_ex4:
            try:
                txt_data = export_to_txt_bytes(candidates)
                st.download_button(
                    label="📝 Download Report (.txt)",
                    data=txt_data,
                    file_name="resume_candidates_report.txt",
                    mime="text/plain",
                    use_container_width=True,
                    help="Formatted, human-readable executive candidate evaluation report",
                )
            except Exception as e:
                st.error(f"TXT export error: {e}")


# ---------------------------------------------------------------------------
# Main Single-Page Application Runner
# ---------------------------------------------------------------------------
def main():
    inject_custom_css()
    render_sidebar()
    render_header_and_kpis()

    # Section 1: Upload & Extraction
    render_upload_center()

    candidates = st.session_state.candidates
    if candidates:
        st.divider()
        # Section 2: Filterable Candidate Results Table
        filtered_candidates = render_results_table(candidates)

        if filtered_candidates:
            st.divider()
            # Section 3: Deep Candidate Dossier with Tabbed Breakdown & Editor
            render_candidate_dossier(filtered_candidates)

        st.divider()
        # Section 4: Export Hub
        render_export_hub(candidates)
    else:
        st.info("💡 **Getting Started:** Drop 1 to 20 resumes in the upload box above and click **Process Batch Now**. All structured intelligence, candidate cards, and one-click downloads will render here on this single dashboard page.")


if __name__ == "__main__":
    main()

# 📄 AI-Powered Resume Parser & Bulk Information Extraction System

A complete, production-ready application that accepts multiple resumes in any format, intelligently extracts structured candidate information using Groq AI, and exports results in Excel, JSON, CSV, and TXT formats.

---

## ✨ Features

- **Multi-format support** — PDF (text-based & scanned), DOCX, DOC, JPG, JPEG, PNG
- **AI-powered extraction** — Uses Groq LLM for context-aware parsing regardless of resume layout
- **OCR fallback** — Automatically detects scanned PDFs and image resumes, applies Tesseract OCR
- **Bulk processing** — Process 1–20 resumes per batch with per-file error handling
- **Structured output** — Pydantic-validated JSON schema for every candidate
- **Confidence scoring** — Reliability estimate per extraction (0–100)
- **Manual editing** — Correct any extracted field directly in the dashboard
- **4 export formats** — Excel (multi-sheet), JSON, CSV, TXT
- **Duplicate detection** — Hash-based detection prevents reprocessing the same file
- **Privacy-first** — Only extracted text (not binary files) is sent to Groq API

---

## 🏗️ Architecture

```
User → Streamlit Dashboard → File Upload → File Type Detector
     → [PDF Processor | DOCX Processor | DOC→DOCX | Image + OCR]
     → Text Cleaner → Groq API → JSON Parser → Pydantic Validator
     → Confidence Scorer → Candidate Store → Results Dashboard
     → [Excel | JSON | CSV | TXT] Export
```

---

## 📂 Project Structure

```
resume_parser/
├── app.py                      # Streamlit entry point
├── requirements.txt
├── .env                        # Environment configuration
├── .gitignore
├── README.md
│
├── config/
│   └── settings.py             # All configuration constants
│
├── processors/
│   ├── file_detector.py        # MIME/extension detection
│   ├── pdf_processor.py        # PyMuPDF + OCR fallback
│   ├── docx_processor.py       # python-docx
│   ├── doc_processor.py        # LibreOffice conversion
│   ├── image_processor.py      # Pillow preprocessing
│   └── ocr_processor.py        # Tesseract OCR wrapper
│
├── ai/
│   ├── groq_client.py          # Groq SDK with retry logic
│   ├── extraction_prompt.py    # System + user prompts
│   └── resume_extractor.py     # Extraction + JSON repair + Pydantic
│
├── schemas/
│   └── candidate_schema.py     # Full Pydantic v2 schema
│
├── validators/
│   └── data_validator.py       # Email, phone, date, duplicate checks
│
├── exporters/
│   ├── excel_exporter.py       # Multi-sheet XLSX
│   ├── json_exporter.py        # Nested JSON
│   ├── csv_exporter.py         # Flat CSV
│   └── txt_exporter.py         # Human-readable report
│
├── utils/
│   ├── text_cleaner.py         # Noise/whitespace removal
│   ├── date_utils.py           # Date normalization
│   └── file_utils.py           # Hashing, temp file management
│
├── tests/                      # pytest test suite
└── data/                       # Temp files and exports (gitignored)
```

---

## 🚀 Prerequisites

| Requirement | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| Groq API key | AI extraction |
| Tesseract OCR | Scanned PDFs and image resumes |
| LibreOffice (optional) | .DOC file support |

---

## ⚙️ Installation

### Step 1 — Clone the project

```bash
# Navigate to your desired directory
cd "c:\Users\shiba\OneDrive\Desktop"
# The project folder already exists as "Resume Data Extractor"
cd "Resume Data Extractor"
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install Tesseract OCR (Windows)

1. Download the installer from: **https://github.com/UB-Mannheim/tesseract/wiki**
2. Run the installer. When prompted, check **"Add Tesseract to PATH"**.
3. Default install path: `C:\Program Files\Tesseract-OCR\tesseract.exe`
4. Verify: open a new terminal and run `tesseract --version`

### Step 5 — Install LibreOffice (optional, for .DOC files)

1. Download from: **https://www.libreoffice.org/download/download/**
2. Install with default settings.
3. Verify: `soffice --version`

---

## 🔑 Groq API Setup

1. Create an account at **https://console.groq.com**
2. Go to **API Keys** and create a new key.
3. Check available models at **https://console.groq.com/docs/models**.
   - Look for models supporting **chat completions** and **JSON mode**.
   - Recommended: `llama-3.3-70b-versatile`
4. Create or edit `.env` in the project root:
   ```env
   GROQ_API_KEY=your_actual_key_here
   GROQ_MODEL=openai/gpt-oss-120b
   ```

> **Important:** Never commit `.env` to Git. It is already in `.gitignore`.

---

## 🌐 Running the Application

```bash
# Activate virtual environment (if not already active)
venv\Scripts\activate

# Run the Streamlit app
streamlit run app.py
```

The app will open at **http://localhost:8501** in your browser.

---

## 📋 Using the Application (Unified Single-Page Dashboard)

The entire application runs on **a single cohesive dashboard page** — no jumping between separate tabs or pages.

1. **Upload & Extract**: Drop up to 20 resumes (PDF, DOCX, DOC, JPG, PNG) into the **Upload Center** and click **🚀 Process Batch Now**.
2. **Real-Time KPIs**: Track total uploads, structured profiles, average confidence score, and verification status right on the top KPI cards.
3. **Candidate Directory**: Instantly search, filter by validation status, minimum years of experience, or specific tech stack.
4. **Dossier & Quick Editor**: Select any candidate to explore their contact info, employment timeline, education, skill matrix pills, and projects, or edit and correct fields on the fly.
5. **One-Click Export Hub**: Download results immediately in **Excel (.xlsx)**, **JSON (.json)**, **CSV (.csv)**, or **TXT (.txt)** from the export bar on the same page.

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_validation.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 🔧 Troubleshooting

### "GROQ_API_KEY is not set"
- Ensure `.env` exists in the project root (not `.env.example`).
- Ensure the key is on its own line: `GROQ_API_KEY=gsk_...`
- Restart the app after editing `.env`.

### "Tesseract binary not found"
- Install Tesseract from the link above.
- Set `TESSERACT_PATH` in `.env` to the exact path of `tesseract.exe`.
- Example: `TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe`

### "Model not found on Groq"
- Visit **https://console.groq.com/docs/models** to see current models.
- Update `GROQ_MODEL` in `.env` to a valid model ID.

### "Rate limit exceeded"
- The free tier has rate limits. Wait 60 seconds and retry.
- Reduce batch size to 5 or fewer resumes.
- Upgrade to a paid Groq tier for higher limits.

### ".DOC file not supported"
- Install LibreOffice (see Prerequisites above).
- Alternatively, open the .DOC in Microsoft Word and save as .DOCX.

### "OCR produced no readable text"
- The image quality may be too low. Try scanning at 300 DPI or higher.
- Ensure the image is not rotated.
- PDFs that are password-protected cannot be processed.

### Pydantic validation errors in logs
- The app automatically attempts JSON repair and partial recovery.
- If the candidate still appears with `needs_review` status, manually edit the fields.

---

## 🔒 Privacy & Security

- API keys are read from `.env` only — never displayed in the UI.
- Only **extracted text** is sent to the Groq API, not original binary files.
- All temporary files are stored in `data/temp/` and deleted on session clear.
- Use **🗑️ Clear All Data** in the sidebar to remove all session data.
- Resume content is **not persisted** beyond the browser session.

---

## 📊 Extracted Information Categories

| Category | Fields |
|---|---|
| Personal | Name, email, phone, location, LinkedIn, GitHub, portfolio |
| Professional | Headline, designation, company, experience, summary, objective |
| Education | Degree, institution, year, CGPA (supports multiple) |
| Work Experience | Company, role, dates, responsibilities, technologies (supports multiple) |
| Technical Skills | Languages, frameworks, databases, cloud, tools, AI/ML |
| Soft Skills | Communication, leadership, teamwork, problem-solving |
| Projects | Name, description, technologies, outcomes, URL (supports multiple) |
| Certifications | Name, issuer, date, credential ID |
| Achievements | Awards, publications, competitions |
| Additional | Languages, internships, publications, volunteer work, hobbies |

---

## 📝 Sample JSON Output

```json
{
  "candidate_id": "CAND_001",
  "source_file": "john_doe_resume.pdf",
  "personal_information": {
    "full_name": "John Doe",
    "email": "john.doe@email.com",
    "phone": ["+1-555-0100"],
    "linkedin": "https://linkedin.com/in/johndoe",
    "city": "San Francisco",
    "country": "USA"
  },
  "professional_information": {
    "current_designation": "Senior Software Engineer",
    "current_company": "Tech Corp",
    "total_experience_years": 5.5
  },
  "education": [{
    "degree": "B.Tech",
    "specialization": "Computer Science",
    "institution_name": "MIT",
    "graduation_year": "2019"
  }],
  "work_experience": [{
    "company_name": "Tech Corp",
    "job_designation": "Senior Software Engineer",
    "start_date": "2021-03",
    "end_date": "Present",
    "currently_working": true,
    "technologies_used": ["Python", "AWS", "PostgreSQL"]
  }],
  "technical_skills": {
    "programming_languages": ["Python", "JavaScript", "Go"],
    "frameworks": ["FastAPI", "React"],
    "databases": ["PostgreSQL", "Redis"],
    "cloud_technologies": ["AWS", "Docker"]
  },
  "confidence_score": 92.0,
  "validation_status": "verified"
}
```

---

## 🛡️ Technology Stack

| Component | Technology | Why |
|---|---|---|
| Dashboard | Streamlit | Rapid Python-native UI, no JS required |
| AI Provider | Groq API | Fast inference, free tier, JSON mode |
| PDF Extraction | PyMuPDF | Fast, accurate text + image rendering |
| DOCX | python-docx | Native DOCX parsing including tables |
| OCR | Tesseract + pytesseract | Free, proven, Windows-compatible |
| Image Processing | Pillow | Lightweight preprocessing before OCR |
| Schema Validation | Pydantic v2 | Type-safe, fast, great error messages |
| Excel Export | openpyxl | Direct XLSX writing, style support |
| Data Manipulation | Pandas | CSV handling and DataFrame operations |
| Environment | python-dotenv | .env file support, keeps keys secure |

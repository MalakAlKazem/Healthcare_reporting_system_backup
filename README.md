# Smart Healthcare Reporting System

A comprehensive hospital reporting platform with four integrated modules: **Mortality Analysis**, **Medication Error Reporting**, **VAP Infection Control**, and **CLABSI Infection Control**. Each module processes Excel data uploaded by hospital staff, tracks quarterly history, generates interactive Arabic/English dashboards, and produces fully formatted Word reports with embedded charts and AI-written Arabic analysis.

---

## Table of Contents

- [Overview](#overview)
- [Modules](#modules)
  - [Mortality Analysis](#1-mortality-analysis)
  - [Medication Error Reporting](#2-medication-error-reporting)
  - [VAP Infection Control](#3-vap-ventilator-associated-pneumonia)
  - [CLABSI Infection Control](#4-clabsi-central-line-associated-bloodstream-infection)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Flow](#data-flow)
- [Data Processing & Validation](#data-processing--validation)
  - [Mortality Validation](#mortality-data-validation)
  - [VAP Validation](#vap-data-validation)
  - [Medication Error Validation](#medication-error-validation)
- [Report Generation](#report-generation)
  - [Mortality Report](#mortality-word-report)
  - [VAP Report](#vap-word-report)
  - [Medication Error Report](#medication-error-word-report)
- [AI Analysis](#ai-analysis)
  - [GPU Setup (Recommended)](#gpu-setup-recommended)
  - [CPU Setup](#cpu-setup-fallback)
  - [Editing the Model Path](#editing-the-model-path)
- [History & Storage](#history--storage)
- [API Endpoints](#api-endpoints)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Usage Guide](#usage-guide)

---

## Overview

This system replaces manual Excel-based hospital reporting with an automated pipeline. Hospital staff upload a quarterly Excel file, and the system:

1. Parses and validates the data automatically
2. Calculates all KPIs, rates, and statistical breakdowns
3. Stores the quarter in a history file for trend tracking
4. Displays a live interactive dashboard
5. Generates a complete Arabic RTL Word report with charts and AI-written analysis — in under 60 seconds

No database required. All data is stored in versioned JSON files.

---

## Modules

### 1. Mortality Analysis

Tracks quarterly inpatient deaths across all hospital departments.

**What it calculates:**
- Total deaths vs KPI deaths (deaths qualifying for the official mortality rate)
- Mortality rate = KPI deaths / total admitted patients × 100
- Death breakdown by: department, building (BCI/RAH), gender, age group, admission source, WHO disease category, doctor specialty
- Length of stay distribution
- Month-by-month trend within the quarter

**Dashboard features:**
- Mortality rate KPI card vs target
- Building distribution (BCI vs RAH)
- Age group bar chart
- Department pie chart
- WHO diagnosis categories
- Historical quarterly trend (last 10 quarters)

---

### 2. Medication Error Reporting

Monitors medication mistakes reported across hospital departments.

**What it calculates:**
- Error count by type (wrong dose, wrong drug, wrong patient, wrong route, wrong time, omission)
- Error count by severity level
- Department-level breakdown and ranking
- Quarter-over-quarter trend
- AI-generated Arabic narrative analysis per section

**Dashboard features:**
- Error type distribution chart
- Severity heatmap
- Department comparison bar chart
- Historical trend line

---

### 3. VAP (Ventilator-Associated Pneumonia)

Tracks VAP cases per 1000 ventilator days across ICU floors.

**Floors tracked:** ICU, CCU, CSU, Ped, ICN, ITU

**What it calculates per floor:**
- VAP rate (‰) = cases / ventilator days × 1000
- Status vs target rate (floor-specific targets)
- Germ distribution (type, count, percentage)
- Per-case details: age, gender, diagnosis, dates, duration of ventilation, risk factors, germ

**Target rates:**

| Floor | Target (‰) |
|-------|-----------|
| ICU   | 25.0      |
| CCU   | 15.0      |
| CSU   | 9.5       |
| Ped   | 5.5       |
| ICN   | 10.0      |
| ITU   | 25.0      |

**Dashboard features:**
- Gauge per floor (rate vs target, color-coded)
- Germ distribution heatmap across all floors
- Quarterly trend chart (Actual Rate vs Target line)
- Summary table with all floor metrics

---

### 4. CLABSI (Central Line-Associated Bloodstream Infection)

Tracks central-line infections per 1000 catheter days across departments.

**What it calculates:**
- CLABSI rate (‰) = cases / catheter days × 1000 per department
- Germ distribution
- Quarter-over-quarter trend

**Dashboard features:**
- Rate gauges per department
- Trend chart
- Germ heatmap
- Case detail table

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | React + Vite | 19.x / 7.x |
| Routing | React Router | v6 |
| Charts (UI) | Recharts | 2.10 |
| Styling | Tailwind CSS + CSS Modules | 4.x |
| Internationalization | i18next + react-i18next | 23.x |
| HTTP Client | Axios | 1.6 |
| Backend API | FastAPI + Uvicorn | 0.128 / 0.40 |
| Data Processing | Pandas + NumPy | 3.0 / 2.4 |
| Excel Parsing | openpyxl | 3.1 |
| Report Generation | python-docx | 1.2 |
| Charts (Reports) | Matplotlib + Pillow | 3.10 / 12 |
| Arabic Text | arabic-reshaper + python-bidi | 3.0 / 0.4 |
| AI Analysis | llama-cpp-python + Qwen 2.5-7B GGUF | local |
| Logging | Loguru | 0.7 |
| Storage | JSON flat files | — |

---

## Project Structure

```
healthcare_motality_system/
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx                        # Main router + navbar
│       ├── main.jsx                       # React entry point
│       ├── i18n/
│       │   └── config.js                  # Arabic / English translation strings
│       ├── styles/                        # CSS Modules (one file per page)
│       └── pages/
│           ├── Home.jsx                   # Module selector (3 cards)
│           ├── Dashboard.jsx              # Mortality dashboard
│           ├── Upload.jsx                 # Mortality Excel upload
│           ├── Reports.jsx                # Mortality Word report
│           ├── Analysis.jsx               # Mortality deep analysis
│           ├── HistoricalComparisons.jsx  # Quarterly trend comparison
│           ├── MedicationUpload.jsx       # Medication error upload
│           ├── MedicationDashboard.jsx    # Medication error dashboard
│           ├── MedicationReports.jsx      # Medication error Word report
│           ├── VapUpload.jsx              # VAP Excel upload
│           ├── VapDashboard.jsx           # VAP gauges, heatmap, trends
│           ├── VapReports.jsx             # VAP Word report generator
│           ├── ClabsiUpload.jsx           # CLABSI Excel upload
│           └── ClabsiDashboard.jsx        # CLABSI dashboard
│
├── python-service/
│   ├── main.py                            # FastAPI app: CORS, routers, startup
│   ├── requirements.txt
│   └── app/
│       ├── api/
│       │   ├── routes.py                  # Mortality endpoints (/api/*)
│       │   ├── medication_routes.py       # Medication endpoints (/api/medication/*)
│       │   ├── vap_routes.py              # VAP endpoints (/api/vap/*)
│       │   └── clabsi_routes.py           # CLABSI endpoints (/api/clabsi/*)
│       ├── core/                          # Mortality module
│       │   ├── data_processor.py          # Excel parsing, cleaning, validation
│       │   ├── excel_handler.py           # Multi-sheet Excel reader
│       │   ├── statistics.py              # KPI calculations, department breakdown
│       │   └── history_manager.py         # Read/write mortality_history.json
│       ├── services/                      # Mortality report generators
│       │   ├── docx_generator.py          # 6-page Arabic Word report
│       │   ├── chart_generator.py         # 10 Matplotlib charts
│       │   └── ai_service.py              # Qwen AI paragraphs (mortality)
│       ├── medication_error/              # Medication error module
│       │   ├── data_processor.py
│       │   ├── statistics.py
│       │   ├── history_manager.py
│       │   ├── chart_generator.py
│       │   ├── docx_generator.py
│       │   └── medication_error_ai_service.py
│       ├── infection_control/
│       │   └── VAP/                       # VAP module
│       │       ├── vap_processor.py       # openpyxl Excel parser
│       │       ├── vap_statistics.py      # Rate, germ, case table calculations
│       │       ├── vap_history.py         # Read/write VAP_history.json
│       │       ├── vap_chart_generator.py # 6 Matplotlib charts
│       │       ├── vap_docx_generator.py  # 7-page Arabic Word report
│       │       └── vap_ai_service.py      # Qwen AI paragraphs (VAP, 11 methods)
│       └── clabsi/                        # CLABSI module
│           ├── clabsi_processor.py
│           └── clabsi_history.py
│
├── storage/                               # Runtime-generated files (not committed)
│   ├── data/
│   │   ├── mortality_history.json
│   │   ├── VAP_history_test.json
│   │   ├── clabsi_history.json
│   │   └── medication_error_history.json
│   ├── reports/                           # Generated .docx files
│   ├── charts/                            # Generated .png chart files
│   ├── uploads/                           # Temporary Excel uploads
│   └── temp/
│
├── sample_data/                           # Example Excel files for testing
│   ├── mortality-data2.xlsx
│   ├── Medication Error3.xlsx
│   └── infection_control.xlsx
│
├── docker-compose.yml
└── .gitignore
```

---

## Data Flow

The same pipeline applies to all modules:

```
Hospital Staff
    │
    │  Upload Excel file via browser
    ▼
React Upload Page
    │  POST multipart/form-data
    │  (file + quarter + year + module-specific params)
    ▼
FastAPI Route Handler
    ├── 1. Validate file type (.xlsx / .xls only)
    ├── 2. Save file temporarily to storage/uploads/
    ├── 3. Parse Excel → Pandas DataFrame / openpyxl rows
    ├── 4. Clean & validate data (see validation section)
    ├── 5. Calculate statistics (rates, breakdowns, tables)
    ├── 6. Save quarter to history JSON file
    ├── 7. Delete temp file
    └── 8. Return statistics JSON to React
    │
    ▼
React Dashboard (live charts and KPIs)

    ── Later ──

React Reports Page
    │  User selects quarter → clicks Generate Report
    │  POST /generate-report { statistics, quarter, year }
    ▼
FastAPI Report Route
    ├── 1. Load history (excluding current quarter)
    ├── 2. Generate charts (Matplotlib → BytesIO PNG)
    ├── 3. Call AI service (Qwen LLM → Arabic paragraphs)
    ├── 4. Build Word document (python-docx)
    ├── 5. Save .docx to storage/reports/
    └── 6. Unload AI model from memory
    │
    ▼
React shows download link
    │  GET /download-report?fileName=...
    ▼
Browser downloads the .docx file
```

---

## Data Processing & Validation

### Mortality Data Validation

The mortality processor applies **conservative cleaning** — it never deletes records. Every death row is preserved even if some fields are incomplete.

**Step 1 — Source Auto-Detection**

The system automatically detects whether the file is a proper Excel file (Arabic column names) or a CSV exported with encoding issues (garbled characters):

- If more than 10 garbled characters (`?`, `\ufffd`) and fewer than 3 Arabic column names → **CSV mode** (maps columns by position)
- Otherwise → **Excel mode** (maps columns by name)

**Step 2 — Column Standardization**

Arabic and English hospital column names are normalized to standard internal names:

| Hospital Column | Internal Name |
|----------------|--------------|
| `العمر` / `Age` | `age` |
| `الجنس` / `gender` | `gender` |
| `القسم التمريضي` | `nursing_department` |
| `تاريخ الدخول` | `admission_date` |
| `تاريخ الوفاة` | `death_date` |
| `تصنيف who category 1` | `who_category_1` |
| `include kpi` | `include_kpi` |
| `المبنى` | `building` |
| `الإختصاص` | `specialty` |

Also handles: column names with trailing spaces (a real occurrence in hospital Excel files), duplicate column names (keeps the first occurrence).

**Step 3 — Age Cleaning**

Age values arrive in multiple formats and are normalized to numeric years:

| Input | Output |
|-------|--------|
| `45` | `45.0` years |
| `"1 month"` | `0.083` years |
| `"10 days"` | `0.027` years |
| `-1`, `999`, empty | `"Unknown"` (record kept) |

**Step 4 — Gender Standardization**

| Input | Normalized |
|-------|-----------|
| `"ذكر"` / `"male"` / `"M"` | `"ذكر"` |
| `"انثى"` / `"female"` / `"F"` | `"انثى"` |

**Step 5 — KPI Flag**

Each death record has an `include_kpi` flag determining whether it counts toward the official mortality rate:

| Input | Result |
|-------|--------|
| `"YES"` / `"yes"` / `"Y"` / `"نعم"` / `1` / `True` | KPI = YES |
| Everything else | KPI = NO |

KPI deaths are used for the official rate. Non-KPI deaths (e.g., DOA, stillborn) are tracked separately but excluded from the rate calculation.

**Step 6 — Length of Stay**

If the LOS column is missing or empty, it is automatically calculated:
```
LOS = death_date − admission_date  (in days)
```

**Step 7 — Missing Value Handling**

- Text fields → filled with `"Unknown"` or `"غير محدد"`
- Numeric fields → kept as `None` (not `0`, to avoid skewing averages)
- No record is ever deleted

**Step 8 — Age Categories**

After cleaning, every record is assigned to one of 8 age groups used for dashboard charts and historical tracking:

```
< 5 years | 5–15 | 16–30 | 31–50 | 51–60 | 61–70 | 71–80 | 81+
```

---

### VAP Data Validation

VAP data is processed with `openpyxl` directly (row by row) rather than Pandas, because each case row requires structured multi-field parsing.

**Step 1 — Column Normalization**

All column header variations are normalized:
```python
"  Heart disease " → strip → lowercase → "heart disease" → "heart_disease"
```
This handles a real issue in hospital Excel files where column names have leading/trailing spaces.

**Step 2 — Age Parsing**

VAP patient ages are stored as formatted strings and converted to numeric years:

| Input | Output |
|-------|--------|
| `"45Y"` | `45.0` years |
| `"3M"` | `0.25` years (3 ÷ 12) |
| `"10D"` | `0.027` years (10 ÷ 365) |
| `"N/A"` / `"—"` / empty | `None` |

The same parser is used in the AI service (`_parse_age_display`) to compute average age per floor for the narrative analysis.

**Step 3 — Date Parsing**

Date fields (admission, intubation, infection) try 4 formats automatically:

```
DD/MM/YYYY  →  25/01/2025
DD/MM/YY    →  25/01/25
YYYY-MM-DD  →  2025-01-25
MM/DD/YYYY  →  01/25/2025
```

**Step 4 — Risk Factor Parsing**

13 Yes/No columns (Diabetic, Hypertension, COPD, Cancer, etc.) are each normalized:

| Input | Result |
|-------|--------|
| `"Yes"` / `"yes"` / `True` / `1` / `"نعم"` | `True` |
| `"No"` / `"no"` / `False` / `0` | `False` |

Per-case risk factors are collected into a comma-separated string:
```
"Diabetic / السكري, COPD / مرض الانسداد الرئوي, Cancer / السرطان"
```

**Step 5 — VAP Rate Calculation**

Rate is calculated per floor using the ventilator days entered by the user on upload:

```
VAP Rate (‰) = (number of cases on floor / ventilator days on floor) × 1000
```

Each floor rate is compared against its target. Status is flagged as above/below target.

**Step 6 — Germ Distribution**

For each floor, germs are counted across all cases and converted to percentages. This feeds the heatmap on the dashboard and the germ comparison charts in the report.

---

### Medication Error Validation

- Error type is normalized to a fixed set of categories (wrong dose, wrong drug, wrong patient, etc.)
- Severity levels are mapped to standard tiers (minor, moderate, severe)
- Department names are trimmed and lowercased for consistent grouping
- Empty or unrecognized values default to `"غير محدد"` (unspecified) without dropping the record

---

## Report Generation

### Mortality Word Report

A 6-page fully formatted Arabic RTL Word document.

| Page | Contents |
|------|---------|
| 1 | Metadata table, results table (KPI vs total deaths), mortality trend chart, analysis paragraph |
| 2 | Building distribution chart (BCI/RAH), admission source chart, age distribution chart |
| 3 | Department pie chart + data table, age-vs-quarter historical trend chart |
| 4 | Department comparison chart (current vs previous quarter), WHO age category chart |
| 5 | WHO diagnosis categories chart, doctor specialty table |
| 6 | Final result statement, previous actions table, current actions table, approval/signature table |

All 10 charts are generated in memory as `BytesIO` PNG buffers (never written to disk) and embedded directly into the Word file.

---

### VAP Word Report

A 7-page Arabic RTL Word document covering all three main ICU floors.

| Page | Contents |
|------|---------|
| 1 | Metadata, results table (6-quarter summary), floor comparison table, AI analysis |
| 2 | ICU trend chart + AI analysis, ICU germ comparison chart + AI analysis |
| 3 | ICU case detail table + AI analysis, CCU trend chart + AI analysis |
| 4 | CCU germ comparison chart + AI analysis, CCU case detail table + AI analysis |
| 5 | ICN trend chart + AI analysis, ICN germ comparison chart + AI analysis |
| 6 | ICN case detail table + AI analysis |
| Last | Final result statement, action tracking tables, approval table |

**Case detail tables** include per-patient rows with: case number, age, gender, diagnosis, admission date, intubation date, infection date, germ, risk factors, ventilation duration.

---

### Medication Error Word Report

A multi-section Arabic RTL Word document with:

- Summary KPI table
- Error type breakdown chart and table
- Severity distribution chart
- Department comparison charts (current vs previous quarter)
- AI-written Arabic analysis for each section

---

## AI Analysis

All three modules use the same local AI model: **Qwen 2.5-7B Instruct** in GGUF format, loaded via `llama-cpp-python`. The model runs entirely on your own machine — no internet or cloud API required.

For each report section, the AI:
1. Receives a focused Arabic prompt with exact numbers from the data
2. Generates a 2–3 sentence Arabic analysis paragraph
3. The output is validated (minimum length, Arabic characters present, no CJK contamination, no bullet points)
4. If validation fails → a pre-written static fallback is used instead

**The report is always complete even if the AI fails or the model is not installed.**

After the report is saved, the model is automatically unloaded from memory (`vap_ai_service.unload()`) so it does not conflict with other modules.

---

### GPU Setup (Recommended)

Using a GPU dramatically speeds up report generation (from ~60s to ~10s).

**Requirements:**
- NVIDIA GPU with CUDA support
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) — install version matching your GPU driver
- Verify installation: `nvcc --version` and `nvidia-smi`

**Install llama-cpp-python with CUDA support (pre-built wheels):**

Choose the command matching your installed CUDA version. Check your version with `nvcc --version` or `nvidia-smi`.

```bash
# CUDA 12.2
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122

# CUDA 12.1
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu121

# CUDA 12.0
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu120

# CUDA 11.8
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118
```

> This installs a pre-built binary — no compiler or CMake required. If your CUDA version is not listed above, use the [CMake build method](https://github.com/abetlen/llama-cpp-python#installation-with-hardware-acceleration) instead.

**Download the model:**

Download `qwen2.5-7b-instruct-q3_k_m.gguf` (or any Qwen 2.5 GGUF variant) and place it in:
```
C:\models\qwen2.5-7b-instruct-q3_k_m.gguf
```

Or download it directly from Hugging Face using Python:

```bash
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='Qwen/Qwen2.5-7B-Instruct-GGUF', filename='qwen2.5-7b-instruct-q3_k_m.gguf', local_dir='C:/models')"
```

The model is searched in these locations (in order):
```
C:/models/*.gguf
models/*.gguf
/models/*.gguf
/app/models/*.gguf
python-service/models/*.gguf
```

In the AI service files, `n_gpu_layers=-1` means **all layers on GPU**. This is the default.

---

### CPU Setup (Fallback)

If you do not have a compatible GPU or CUDA toolkit:

```bash
pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

Then open both AI service files and change `n_gpu_layers`:

**File 1:** `python-service/app/services/ai_service.py`

**File 2:** `python-service/app/infection_control/VAP/vap_ai_service.py`

Find the `Llama(...)` constructor in `_load_llm()` and change:

```python
# FROM (GPU):
n_gpu_layers=-1,

# TO (CPU only):
n_gpu_layers=0,
```

> **Note:** CPU inference is significantly slower (~3–5 minutes per report vs ~10–60 seconds on GPU). The report quality is identical.

---

### Editing the Model Path

If your model file is stored in a different location, edit the model search patterns in the `_load_llm()` method of each AI service file:

**`python-service/app/services/ai_service.py`** — mortality + medication error AI
**`python-service/app/infection_control/VAP/vap_ai_service.py`** — VAP AI

Find this block and add your path:

```python
candidates = []
for pattern in [
    "C:/models/*.gguf",          # ← change this to your path
    "models/*.gguf",
    ...
]:
    candidates.extend(glob.glob(pattern))
```

Or set the environment variable before starting the backend:

```bash
# Windows
set QWEN_MODEL_PATH=D:/my-models/qwen2.5-7b-instruct-q3_k_m.gguf

# Linux / macOS
export QWEN_MODEL_PATH=/home/user/models/qwen2.5-7b-instruct-q3_k_m.gguf
```

---

## History & Storage

Each module stores quarterly data in a JSON file. Uploading a quarter that already exists **overwrites** it. New quarters are appended in chronological order.

| Module | History File |
|--------|-------------|
| Mortality | `storage/data/mortality_history.json` |
| VAP | `storage/data/VAP_history_test.json` |
| CLABSI | `storage/data/clabsi_history.json` |
| Medication Error | `storage/data/medication_error_history.json` |

Each history entry stores everything needed for trend charts and report generation without re-uploading the Excel file.

**VAP history entry example:**
```json
{
  "quarter": "الفصل الرابع",
  "year": "2025",
  "floors": {
    "ICU": { "cases": 2, "vent_days": 1200, "rate": 1.67, "target": 25.0 },
    "CCU": { "cases": 4, "vent_days": 980,  "rate": 4.08, "target": 15.0 }
  },
  "germs_overall": { "Klebsiella": 3, "Acinetobacter": 2 },
  "icu_cases_table": [
    { "age": "45Y", "gender": "Male", "germs": "Klebsiella", "risk_factors": "Diabetic, COPD" }
  ],
  "ccu_cases_table": [...],
  "icn_cases_table": [...]
}
```

Generated reports are saved to `storage/reports/` and charts to `storage/charts/`. Both directories are excluded from git (only `.gitkeep` is committed to preserve the folder).

---

## API Endpoints

All endpoints are documented interactively at **http://localhost:8000/docs** (Swagger UI).

### Mortality

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/process-data` | Upload and process mortality Excel file |
| `GET` | `/api/history` | Get all saved quarterly records |
| `POST` | `/api/generate-report` | Generate mortality Word report |
| `GET` | `/api/download-report?fileName=...` | Download generated .docx file |
| `GET` | `/api/test` | Health check |

### Medication Error

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/medication/process-data` | Upload and process medication error Excel |
| `GET` | `/api/medication/history` | Get all saved quarterly records |
| `POST` | `/api/medication/generate-report` | Generate medication error Word report |
| `GET` | `/api/medication/download-report?fileName=...` | Download generated .docx file |

### VAP Infection Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/vap/process-data` | Upload VAP Excel + floor ventilator days |
| `GET` | `/api/vap/history` | Get all saved quarters (oldest → newest) |
| `GET` | `/api/vap/history/latest` | Get the most recent quarter |
| `GET` | `/api/vap/chart-data` | Get data for the 6 dashboard charts |
| `GET` | `/api/vap/table-comparison?n=5` | Get multi-floor comparison table (last n quarters) |
| `POST` | `/api/vap/generate-report` | Generate VAP Word report |
| `GET` | `/api/vap/download-report?fileName=...` | Download generated .docx file |
| `DELETE` | `/api/vap/history/{quarter}/{year}` | Delete a specific quarter |

### CLABSI Infection Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/clabsi/process-data` | Upload CLABSI Excel + catheter days |
| `GET` | `/api/clabsi/history` | Get all saved quarterly records |
| `GET` | `/api/clabsi/history/latest` | Get the most recent quarter |
| `DELETE` | `/api/clabsi/history/{year}/{quarter}` | Delete a specific quarter |

---

## Installation

### Prerequisites

- **Python** 3.10 or higher
- **Node.js** 18 or higher (tested with v24.x)
- **CUDA Toolkit** (optional, for GPU AI inference — see [GPU Setup](#gpu-setup-recommended))

### 1. Clone the Repository

```bash
git clone <repository-url>
cd healthcare_motality_system
```

### 2. Python Backend

```bash
cd python-service

# Create virtual environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**For AI support, also install llama-cpp-python:**

```bash
# GPU — use the wheel matching your CUDA version (check with: nvcc --version)
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122

# CPU only (no CUDA required, but slower)
pip install llama-cpp-python --prefer-binary --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Model File (for AI analysis)

Download the model directly from Hugging Face:

```bash
pip install huggingface_hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download(repo_id='Qwen/Qwen2.5-7B-Instruct-GGUF', filename='qwen2.5-7b-instruct-q3_k_m.gguf', local_dir='C:/models')"
```

Or manually download `qwen2.5-7b-instruct-q3_k_m.gguf` and place it at:
```
C:\models\qwen2.5-7b-instruct-q3_k_m.gguf
```

Any quantization variant works (`q3_k_m`, `q4_k_m`, `q5_k_m`, etc.). Higher quantization = better quality but more VRAM required.

---

## Running the System

> **Windows:** Set `PYTHONUTF8=1` before starting the backend to ensure correct Arabic text rendering in Word reports.

**Terminal 1 — Python Backend:**

```bash
cd python-service

# Windows
set PYTHONUTF8=1 && venv\Scripts\python.exe main.py

# macOS / Linux
PYTHONUTF8=1 python main.py
```

**Terminal 2 — React Frontend:**

```bash
cd frontend
npm run dev
```

**Access:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Python API | http://localhost:8000 |
| API Docs (Swagger UI) | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Usage Guide

### Mortality Analysis

1. Navigate to **Mortality → Upload**
2. Select quarter and year
3. Enter the total number of admitted patients this quarter
4. Upload the mortality Excel file (`.xlsx` or `.xls`)
5. Click **Process** — the dashboard appears automatically
6. Navigate to **Dashboard** to view charts and KPIs
7. Navigate to **Historical Comparisons** to view quarter-over-quarter trends
8. Navigate to **Reports** → click **Generate Word Report** → download the `.docx` file

### Medication Error

1. Navigate to **Medication Error → Upload**
2. Select quarter and year, upload Excel file
3. View the **Dashboard** for error breakdowns and trends
4. Navigate to **Reports** → click **Generate Report** → download

### VAP Infection Control

1. Navigate to **VAP → Upload**
2. Select quarter and year
3. Enter the ventilator days for each floor (ICU, CCU, CSU, Ped, ICN, ITU)
4. Upload the infection control Excel file
5. Click **Process** — data saved to history
6. View the **Dashboard** for floor gauges, heatmap, and trend chart
7. Navigate to **Reports** → select the quarter → click **Generate Report** → download

### CLABSI Infection Control

1. Navigate to **CLABSI → Upload**
2. Select quarter and year, enter catheter days per department, upload Excel
3. View the **Dashboard** for rate gauges and germ distribution

---

## Version

**2.1.0** — Four-module platform: Mortality Analysis · Medication Error Reporting · VAP Infection Control · CLABSI Infection Control
AI analysis enabled for Mortality and VAP modules with automatic GPU/CPU fallback and memory management.

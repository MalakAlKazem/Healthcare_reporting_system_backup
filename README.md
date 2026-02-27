# Smart Healthcare Reporting System

A comprehensive hospital reporting platform with three integrated modules: **Mortality Analysis**, **Medication Error Reporting**, and **Infection Control (VAP & CLABSI)**. Each module processes Excel data, tracks quarterly history, generates interactive dashboards, and produces formatted Word reports in Arabic and English.

---

## Modules

### 1. Mortality Analysis System
Tracks quarterly patient mortality across hospital departments. Calculates death rates, WHO disease category breakdowns, age/gender distributions, and length-of-stay statistics. Generates a formatted Arabic RTL Word report with embedded charts.

### 2. Medication Error Reporting System
Monitors and analyzes medication errors across departments. Tracks error types, severity levels, reporting trends, and department-level comparisons. Produces quality and drug safety Word reports with AI-assisted narrative analysis.

### 3. Infection Control System
Monitors hospital-acquired infection indicators with two active sub-modules:

- **VAP (Ventilator-Associated Pneumonia)** — Tracks VAP cases per 1000 ventilator days across ICU, CCU, CSU, ICN, Ped, and ITU. Generates 6 charts (trend + germ comparison per floor), floor-level rate gauges, germ heatmaps, and downloadable Word reports.
- **CLABSI (Central Line-Associated Bloodstream Infection)** — Tracks CLABSI cases per 1000 catheter days. Displays quarterly rate trends, germ distribution heatmaps, and detailed case tables per department.
- **CAUTI** — Coming soon.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, React Router v6, Recharts, CSS Modules, i18next |
| Backend API | Python 3.10+, FastAPI, Uvicorn |
| Data Processing | Pandas, NumPy |
| Report Generation | python-docx, Matplotlib, arabic-reshaper, python-bidi |
| AI Analysis | Qwen / local LLM integration (medication error module) |
| Storage | JSON files (history), local filesystem (charts, reports) |

---

## Project Structure

```
healthcare_motality_system/
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── Home.jsx                  # System selector (3 cards)
│       │   ├── Dashboard.jsx             # Mortality dashboard
│       │   ├── Upload.jsx                # Mortality upload
│       │   ├── Reports.jsx               # Mortality reports
│       │   ├── MedicationUpload.jsx      # Medication error upload
│       │   ├── MedicationDashboard.jsx   # Medication error dashboard
│       │   ├── MedicationReports.jsx     # Medication error reports
│       │   ├── VapUpload.jsx             # VAP data upload
│       │   ├── VapDashboard.jsx          # VAP dashboard (gauges, trends, heatmaps)
│       │   ├── VapReports.jsx            # VAP Word report generator
│       │   ├── ClabsiUpload.jsx          # CLABSI data upload
│       │   └── ClabsiDashboard.jsx       # CLABSI dashboard
│       ├── styles/                       # CSS Modules per page
│       └── i18n/                         # Arabic / English translations
│
├── python-service/
│   ├── main.py                           # FastAPI entry point
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes.py                 # Mortality endpoints
│   │   │   ├── medication_routes.py      # Medication error endpoints
│   │   │   ├── vap_routes.py             # VAP endpoints
│   │   │   └── clabsi_routes.py          # CLABSI endpoints
│   │   ├── core/                         # Mortality processor, statistics, history
│   │   ├── services/                     # Shared DOCX & chart generators
│   │   ├── medication_error/             # Medication error processor, history, AI service
│   │   ├── infection_control/
│   │   │   └── VAP/                      # VAP processor, statistics, history, charts, DOCX
│   │   └── clabsi/                       # CLABSI processor, history, targets
│   ├── storage/
│   │   ├── data/                         # mortality_history.json, VAP_history.json, clabsi_history.json
│   │   ├── charts/                       # Generated chart PNGs
│   │   ├── reports/                      # Generated .docx reports
│   │   └── temp/                         # Upload temp files
│   └── requirements.txt
│
├── sample_data/                          # Example Excel files
└── .gitignore
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (tested with v24.x)

### 1. Python Backend

```bash
cd python-service

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

---

## Running the System

> **Windows Note:** Set `PYTHONUTF8=1` for correct Arabic text rendering in reports.

**Terminal 1 — Python API:**

```bash
cd python-service

# Windows
set PYTHONUTF8=1 && .venv\Scripts\python.exe main.py

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
| API Docs (Swagger) | http://localhost:8000/docs |

---

## Usage

### Mortality Analysis
1. Go to **Mortality → Upload**, select quarter/year, enter total patients, upload Excel
2. View **Dashboard** for auto-generated charts and KPIs
3. Go to **Reports** to generate and download a formatted Arabic Word report

### Medication Error
1. Go to **Medication → Upload**, select quarter/year, upload Excel
2. View **Dashboard** for error type breakdowns and trends
3. Go to **Reports** to generate a medication error Word report

### Infection Control — VAP
1. Go to **VAP → Upload**, select quarter/year, enter ventilator days per floor, upload Excel
2. View **Dashboard** for floor-level rate gauges, quarterly trends, and germ heatmaps
3. Go to **Reports** to generate and download a VAP Word report

### Infection Control — CLABSI
1. Go to **CLABSI → Upload**, select quarter/year, enter catheter days per department, upload Excel
2. View **Dashboard** for department rate gauges, trend charts, and germ distribution heatmaps

---

## API Endpoints

### Mortality
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/process-data` | Upload & process mortality Excel |
| POST | `/api/generate-report` | Generate mortality DOCX report |
| GET | `/api/download-report?fileName=...` | Download generated report |
| GET | `/api/history` | Get all quarterly history |

### Medication Error
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/medication/process-data` | Upload & process medication error Excel |
| POST | `/api/medication/generate-report` | Generate medication error DOCX report |
| GET | `/api/medication/download-report?fileName=...` | Download generated report |
| GET | `/api/medication/history` | Get all quarterly history |

### VAP (Infection Control)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/vap/process-data` | Upload & process VAP Excel |
| POST | `/api/vap/generate-report` | Generate VAP DOCX report |
| GET | `/api/vap/download-report?fileName=...` | Download generated report |
| GET | `/api/vap/history` | Get all quarterly history |

### CLABSI (Infection Control)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/clabsi/process-data` | Upload & process CLABSI Excel |
| GET | `/api/clabsi/history` | Get all quarterly history |
| GET | `/api/clabsi/history/latest` | Get most recent quarter |
| DELETE | `/api/clabsi/history/{year}/{quarter}` | Delete a quarter entry |

---

## Historical Data

Each module stores quarterly history in its own JSON file:

| Module | History File |
|--------|-------------|
| Mortality | `python-service/storage/data/mortality_history.json` |
| VAP | `python-service/storage/data/VAP_history.json` |
| CLABSI | `python-service/storage/data/clabsi_history.json` |

- Uploading a quarter **updates** it if it already exists
- New quarters are **appended** in chronological order
- Dashboards display **all stored quarters** as trend data

---

## Version

**2.0.0** — Three-module platform: Mortality Analysis + Medication Error Reporting + Infection Control (VAP & CLABSI)

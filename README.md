# Healthcare Mortality Analysis System

A professional mortality data analysis system for hospital quarterly reporting. Processes Excel patient data, calculates KPI statistics, generates charts, and produces formatted Arabic/English Word reports.

## Features

- **Data Upload** — Import Excel mortality files; auto-detects and cleans data
- **Statistical Analysis** — Departments, age groups, WHO disease categories, gender, length of stay
- **Historical Tracking** — Stores quarterly data and compares trends across up to 11+ quarters
- **Word Report Generation** — Produces a formatted `.docx` report with embedded charts (Arabic RTL layout)
- **Bilingual UI** — Full Arabic and English interface support
- **Offline Operation** — No external APIs or cloud services required

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, Tailwind CSS, Recharts, i18next |
| API / Data | Python 3.x, FastAPI, Pandas, NumPy |
| Reports | python-docx, Matplotlib, arabic-reshaper |
| Storage | JSON (history), local filesystem (reports, charts) |

## Project Structure

```
healthcare_motality_system/
├── frontend/                  # React app (Vite)
│   └── src/
│       ├── pages/             # Upload, Dashboard, Analysis, Reports
│       ├── styles/            # CSS Modules per page
│       └── i18n/              # Arabic / English translations
├── python-service/            # FastAPI backend
│   ├── main.py                # App entry point
│   ├── app/
│   │   ├── api/routes.py      # API endpoints
│   │   ├── core/              # Data processor, statistics, history manager
│   │   └── services/          # DOCX generator, chart generator
│   ├── storage/data/          # mortality_history.json
│   └── requirements.txt
├── storage/
│   ├── reports/               # Generated .docx files
│   ├── charts/                # Generated chart images
│   └── temp/                  # Upload temp files
├── sample_data/               # Example Excel files
└── docker-compose.yml
```

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 24+ (developed with v24.11.0, npm 11.6.1)

### 1. Python Service

```bash
cd python-service

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend

```bash
cd frontend
npm install
```

## Running the System

> **Windows Note:** The `PYTHONUTF8=1` flag is required for correct Arabic text rendering.

**Terminal 1 — Python API:**

```bash
cd python-service
set PYTHONUTF8=1 && .venv\Scripts\python.exe main.py
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

**Access:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Python API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Usage

1. **Upload** — Go to the Upload page, select the quarter and year, enter total patients, and upload the Excel file
2. **Dashboard** — View auto-generated charts and KPIs for the uploaded quarter
3. **Analysis** — Explore detailed breakdowns by department, age group, disease category, and historical trends
4. **Reports** — Click **Generate Word Report** to produce a formatted `.docx` and download it

## Excel File Format

The system expects an Excel file with at minimum:

| Column | Description |
|--------|-------------|
| Age | Patient age |
| Gender (الجنس) | ذكر / انثى |
| Nursing Department | Department name |
| Length of Stay (LOS) | Days |
| KPI | YES = counted in mortality rate |
| WHO Category 1 | Disease classification |
| Building | BCI or RAH |

The mortality rate is calculated as: `KPI deaths / total_patients × 100`

## Historical Data

Quarterly records are stored in `python-service/storage/data/mortality_history.json`.

- Uploading a quarter **updates** it if it already exists
- New quarters are **appended** in chronological order
- When generating a report for a past quarter, only quarters that came **before** it are used for trend comparison

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/process-data` | Upload and process an Excel file |
| POST | `/api/generate-report` | Generate a DOCX report |
| GET | `/api/download-report?fileName=...` | Download a generated report |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger API docs |

## Version

**1.0.0** — Phase 1 (AI analysis placeholder text; AI integration planned for Phase 2)

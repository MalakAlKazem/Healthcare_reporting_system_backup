# Code Guide — Healthcare Quality Indicators System

This document explains how the code is organized, how data flows through every layer, how each component works, what design decisions were made, and what is currently missing or incomplete.

---

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Backend Deep Dive](#2-backend-deep-dive)
   - [Entry Point — main.py](#entry-point--mainpy)
   - [How a Request Flows Through the Backend](#how-a-request-flows-through-the-backend)
   - [Mortality Module](#mortality-module)
   - [Medication Error Module](#medication-error-module)
   - [Shared Infection Control Engine](#shared-infection-control-engine)
   - [VAP Module (IC)](#vap-module-ic)
   - [CLABSI Module (IC)](#clabsi-module-ic)
   - [CAUTI Module (IC)](#cauti-module-ic)
3. [Frontend Deep Dive](#3-frontend-deep-dive)
   - [Routing](#routing)
   - [State Management](#state-management)
   - [Upload Pages](#upload-pages)
   - [Dashboard Pages](#dashboard-pages)
   - [Report Pages](#report-pages)
4. [Storage Layer](#4-storage-layer)
5. [AI Service Layer](#5-ai-service-layer)
6. [Arabic RTL Word Reports — How BiDi Works](#6-arabic-rtl-word-reports--how-bidi-works)
7. [What Is Missing / Known Gaps](#7-what-is-missing--known-gaps)
8. [Local Server Deployment (Step by Step)](#8-local-server-deployment-step-by-step)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser (any machine on the hospital LAN)                      │
│                                                                 │
│  React SPA (Single Page Application)                            │
│  • React Router — navigation between modules                   │
│  • Recharts — interactive charts on dashboards                  │
│  • i18next — Arabic / English text switching                    │
│  • Axios — all HTTP calls to the backend                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP JSON  (port 8000)
┌──────────────────────────▼──────────────────────────────────────┐
│  FastAPI (Python)                                               │
│                                                                 │
│  5 routers mounted in main.py:                                 │
│    /api/*            → mortality_routes.py                     │
│    /api/medication/* → medication_routes.py                    │
│    /api/vap/*        → vap_routes.py                           │
│    /api/clabsi/*     → clabsi_routes.py                        │
│    /api/cauti/*      → cauti_routes.py                         │
│                                                                 │
│  Business logic (per module):                                   │
│    Excel parsing → statistics → history → docx → AI            │
│                                                                 │
│  Storage (flat files on disk, no database):                     │
│    storage/data/*.json     — quarterly history                  │
│    storage/reports/*.docx  — generated Word reports            │
│    storage/charts/*.png    — generated chart images            │
└─────────────────────────────────────────────────────────────────┘
```

The frontend and backend are **completely decoupled** — they communicate only via HTTP JSON. The frontend never touches the file system directly.

---

## 2. Backend Deep Dive

### Entry Point — main.py

`python-service/main.py` is the only file you run. It:

1. Creates the FastAPI `app` instance
2. Adds CORS middleware (allows the frontend on port 3000/5173 to call the API)
3. Mounts all 5 routers
4. On startup, checks if `llama_cpp` is importable and logs AI availability
5. Creates storage directories if they do not exist
6. Starts uvicorn on `0.0.0.0:8000` (accessible from any network interface)

```python
# CORS allows these origins — add your server IP here for network deployment:
allow_origins=["http://localhost:5173", "http://localhost:3000", "*"]
```

> The `"*"` means all origins are allowed. For a secure hospital deployment, replace `"*"` with the specific IP/hostname of your server.

---

### How a Request Flows Through the Backend

Taking VAP upload as a concrete example:

```
POST /api/vap/process-data
  multipart body: file=<xlsx>, year=2025, quarter=4,
                  denominators={"ICU":1200,"CCU":980}
          │
          ▼  vap_routes.py: process_data()
          │
          ├─ 1. Write file bytes to storage/temp/vap_<uuid>.xlsx
          │
          ├─ 2. process_vap_sheet(path, year, quarter, denominators)
          │         └── vap/processor.py
          │             • openpyxl: open workbook, find header row
          │             • For each data row:
          │               - normalize column headers (strip, lowercase, underscore)
          │               - parse age string → float years + age_display string
          │               - parse dates (4 formats tried)
          │               - parse 13 risk factor boolean columns
          │               - collect into case dict
          │             • Returns: {"cases": [...], "meta": {"total_cases": N}}
          │
          ├─ 3. _compute_vap_stats(processed, denominators, quarter, year)
          │         └── vap_routes.py (local helper)
          │             • InfectionControlStatistics("vap").calculate_all_statistics(...)
          │               - counts cases per floor using _match_floor()
          │               - computes rate = cases / vent_days × 1000 per floor
          │               - counts germs per floor
          │               - computes risk factors, age groups, genders, monthly trend
          │             • Augments with floor-specific targets (FLOOR_TARGETS)
          │             • Returns full stats dict
          │
          ├─ 4. VAPHistory.save_quarter(quarter, year, stats, cases)
          │         └── vap/history.py
          │             • save_current({"year":..., "quarter":..., "cases":[...]})
          │               → overwrites VAP_current.json (raw case rows)
          │             • Appends/updates quarter summary in VAP_history.json
          │
          ├─ 5. Delete temp file
          │
          └─ 6. Return stats JSON → React renders dashboard
```

---

### Mortality Module

**Files:** `app/mortality/`

```
excel_handler.py    → reads the Excel file, handles multi-sheet, detects CSV vs Excel
data_processor.py   → cleans and validates each row
statistics.py       → computes all KPIs from the cleaned DataFrame
history_manager.py  → reads/writes mortality_history.json
chart_generator.py  → generates 10 Matplotlib charts as BytesIO objects
docx_generator.py   → assembles the 6-page Word report
ai_service.py       → loads Qwen model, generates Arabic analysis paragraphs
```

**Key design decision: Two-step Excel reading**

`excel_handler.py` detects whether the file is a real Excel or a broken CSV-exported-as-xlsx:
- If the column headers contain many `?` or `\ufffd` characters → CSV mode (map columns by position)
- Otherwise → Excel mode (map columns by Arabic/English name)

This handles a real-world issue where some hospital systems export reports as CSV but save them with a `.xlsx` extension.

**Key design decision: No records deleted**

`data_processor.py` never drops rows. If a field is missing or invalid, it fills it with a safe default (`"Unknown"`, `None`, `"غير محدد"`). This ensures the total death count is always accurate even with incomplete data.

**Mortality rate formula:**
```
Rate (%) = (KPI deaths / total admitted patients) × 100
```

KPI deaths = only rows where `include_kpi` is YES. Deaths marked NO (e.g., DOA, stillborn, <24h stay) are counted in total deaths but excluded from the rate.

---

### Medication Error Module

**Files:** `app/medication/`

```
data_processor.py   → reads Excel, normalizes error types and severity
statistics.py       → counts by type, severity, department, shift, cycle, staff
history_manager.py  → reads/writes medication_error_history.json
chart_generator.py  → 7 Matplotlib charts
docx_generator.py   → Arabic Word report
ai_service.py       → AI analysis paragraphs
```

Error types normalized to fixed categories:
```
Wrong Dose | Wrong Drug | Wrong Patient | Wrong Route | Wrong Time | Omission | Other
```

Severity mapped to:
```
Minor | Moderate | Severe | Near Miss
```

---

### Shared Infection Control Engine

This is the most important architectural piece. CLABSI, CAUTI, and VAP all share:

```
app/infection_control/
├── ic_statistics.py      ← InfectionControlStatistics class
├── ic_docx_generator.py  ← InfectionControlDocxGenerator class
├── ic_chart_generator.py ← InfectionControlChartGenerator class
└── ic_ai_service.py      ← Shared AI service
```

**Why shared?**

All three infection types have the same mathematical structure:
- Cases per floor
- Rate = cases / device-days × 1000
- Germ distribution per floor
- Risk factors (same 15 boolean columns)
- Case detail tables with the same columns

Instead of duplicating this code three times, it is implemented once and configured by a type string.

**ic_statistics.py — InfectionControlStatistics**

```python
CONFIGS = {
    "clabsi": {"days_key": "catheter_days"},
    "cauti":  {"days_key": "urinary_catheter_days"},
    "vap":    {"days_key": "ventilator_days"},
}

stats = InfectionControlStatistics("vap")
result = stats.calculate_all_statistics(cases, floor_vent_days, quarter=4, year=2025)
```

The `days_key` tells the calculator which JSON key to use when storing device-day counts. Everything else is identical.

`_match_floor(floor_value, standard)` — matches floor names from the Excel against standard floor names using an alias dictionary. Handles variations like "ICU" vs "Intensive Care Unit" vs "MICU".

**ic_docx_generator.py — InfectionControlDocxGenerator**

The shared report builder receives a config dict at construction:

```python
config = {
    "indicator": "CLABSI",
    "indicator_ar": "كلابسي",
    "days_key": "catheter_days",
    "days_label_ar": "أيام القسطرة",
    "insertion_col": "date_of_insertion",
    "insertion_col_ar": "تاريخ الإدخال",
    "metadata_topic_ar": "...",
    "file_prefix": "CLABSI",
}
```

The same class builds CLABSI, CAUTI, and (via a thin wrapper) VAP reports — only the config dict differs.

**_add_bidi_para() — Arabic/Latin mixed text rendering**

This is the core method for rendering mixed Arabic/Latin text correctly in Word:

```python
def _add_bidi_para(self, container, text, font_name, size, ...):
    # Splits text at Arabic/LTR boundaries using regex
    # Arabic segments → run with <w:rtl/> in rPr
    # LTR segments (A-Z, 0-9) → run without <w:rtl/>
    # Paragraph itself gets <w:bidi/> in pPr
```

Without `<w:rtl/>` on the run, Word's bidi algorithm may render Arabic text left-to-right even if the paragraph direction is RTL — particularly when the text contains leading neutral characters (`-`, space) or trailing LTR words like "Target".

**_set_table_bidi() vs _set_table_rtl()**

Both add `<w:bidiVisual/>` to the table properties. This makes Word render the table columns right-to-left (rightmost column is "first"). Without this, table cells appear in the wrong order in RTL documents.

---

### VAP Module (IC)

**Files:** `app/infection_control/vap/`

VAP is slightly different from CLABSI/CAUTI because it has:
- Its own AI service (`vap/ai_service.py`) with 11 different analysis methods (one per report section per floor)
- Its own chart generator (`vap/chart_generator.py`) with 6 charts specific to VAP layout
- Its own docx generator (`vap/docx_generator.py`) with a different page structure
- Floor-specific targets and STANDARD_FLOORS defined in `vap/history.py`

**VAP processor — age_display field**

The VAP processor outputs both a numeric age (for calculations) and a display string (for tables):

```python
case = {
    "age": 0.25,          # numeric: 3 months in years
    "age_display": "3M",  # display: shown in case table
    ...
}
```

The display format: `"53Y"` (years) / `"3M"` (months) / `"10D"` (days).

**VAP routes — _compute_vap_stats()**

Since VAP was refactored to use the shared `InfectionControlStatistics`, the route file contains a thin `_compute_vap_stats()` function that:
1. Calls `_ic.calculate_all_statistics(cases, floor_vent_days, ...)` (shared engine)
2. Augments the result with VAP-specific data: floor targets, `pct_of_total`, germs_overall

---

### CLABSI Module (IC)

**Files:** `app/infection_control/clabsi/`

```
processor.py        → openpyxl Excel parser → normalized case dicts
history.py          → clabsi_history.json + clabsi_current.json (raw cases)
clabsi_targets.py   → CLABSI_TARGETS dict {floor: target_rate}
docx_generator.py   → thin wrapper: creates InfectionControlDocxGenerator with CLABSI config
```

`clabsi_current.json` stores the raw case rows from the latest quarter. The report generator reads this to build per-floor case detail tables dynamically — only floors that have actual cases get a section.

---

### CAUTI Module (IC)

**Files:** `app/infection_control/cauti/`

Identical structure to CLABSI, with:
- `urinary_catheter_days` as the device-day key (instead of `catheter_days`)
- `cauti_targets.py` with CAUTI-specific floor target rates
- `cauti_current.json` for raw cases

The frontend uses the **same Upload and Reports pages** as CLABSI (parameterized with `type="cauti"`).

---

## 3. Frontend Deep Dive

### Routing

All routes are defined in `src/App.jsx`. The app uses React Router v6.

```
/                           → Home.jsx (module selector)

/mortality/upload           → mortality/Upload.jsx
/mortality/dashboard        → mortality/Dashboard.jsx
/mortality/reports          → mortality/Reports.jsx

/vap/upload                 → infection_control/Upload.jsx (defaultTab="vap")
/vap/dashboard              → infection_control/vap/Dashboard.jsx
/vap/reports                → infection_control/Reports.jsx (type="vap")

/clabsi/upload              → infection_control/Upload.jsx (defaultTab="clabsi")
/clabsi/dashboard           → infection_control/clabsi/Dashboard.jsx
/clabsi/reports             → infection_control/Reports.jsx (type="clabsi")

/cauti/upload               → infection_control/Upload.jsx (defaultTab="cauti")
/cauti/dashboard            → infection_control/cauti/Dashboard.jsx
/cauti/reports              → infection_control/Reports.jsx (type="cauti")

/medication/upload          → medication/Upload.jsx
/medication/dashboard       → medication/Dashboard.jsx
/medication/reports         → medication/Reports.jsx
```

**Important:** The infection control Upload and Reports pages are **shared** between VAP, CLABSI, and CAUTI. They receive a `type` prop (or `defaultTab`) that tells them which API endpoints to call and which labels to show.

---

### State Management

The app uses **simple React state** — no Redux, no Zustand, no Context API beyond what React Router provides.

**Mortality data:** Stored in `App.jsx` state (`mortalityData`, `historyData`) and passed down as props to Dashboard and Reports pages.

**Medication data:** Also lifted to `App.jsx` state (`medicationData`). On startup, `App.jsx` fetches `GET /api/medication/current` and stores the result. After an upload, the Upload page calls `onDataLoaded(setMedicationData)` with the freshly processed data. Dashboard receives it as `data` prop; Reports receives it as `currentData` prop.

**IC modules (VAP, CLABSI, CAUTI):** Each dashboard page fetches its own data on mount from the backend. State is local to the component.

This is intentional simplicity — the system has a small number of pages and does not need a global state manager.

---

### Upload Pages

Each upload page:
1. Renders a form with quarter/year selectors and file input
2. For IC modules: also shows floor denominator inputs (ventilator days / catheter days per floor)
3. On submit: creates `FormData`, sends `POST` with `multipart/form-data` to the backend
4. On success: calls `onDataLoaded` callback (Mortality and Medication) with the returned statistics, updating the lifted state in `App.jsx` so Dashboard and Reports reflect the new quarter immediately without a page reload

For IC modules, the shared `infection_control/Upload.jsx` has tabs for VAP, CLABSI, and CAUTI. The active tab determines which API endpoint to call and which denominator labels to show.

---

### Dashboard Pages

Dashboard pages:
1. On mount: fetch data from backend (`/api/<module>/history` or `/history/latest`)
2. Store data in local state
3. Render Recharts components (BarChart, LineChart, PieChart, RadialBar for gauges)

**Mortality and Medication dashboards** receive the current quarter's full data as a `data` prop from `App.jsx` (pre-fetched on startup from `*_current.json`). Breakdown charts use `data.statistics` directly; trend charts merge history from the API with the current entry.

**IC dashboards** (VAP, CLABSI, CAUTI) fetch their own current data from `GET /api/<type>/current` on mount.

The dashboards display **pre-computed statistics** returned by the backend — they do not do any calculations themselves.

**i18n:** Text labels switch between Arabic and English based on the `language` prop passed from `App.jsx`. Chart labels and axis values are formatted accordingly.

---

### Report Pages

Report pages:
1. Show a list of available quarters (from history)
2. Auto-selects the **last uploaded** quarter (not the highest chronological quarter) using a `useEffect` that watches `currentData`/`data` prop
3. User selects a quarter → clicks "Generate Report"
4. Sends `POST /api/<module>/generate-report` to backend
5. Waits for response (can take 30–90 seconds if AI is running)
6. Shows download link → `GET /api/<module>/download-report?fileName=...`

**Medication Reports:** When the selected quarter matches `currentData` (the last uploaded), uses the full `currentData.statistics` (all breakdown fields) instead of the lean history entry (which only has 5 fields). This ensures the report preview shows complete data.

**IC Reports:** Fetches `/current` alongside `/history` to determine which history entry to default to. Uses the matched entry for the stats display; the actual DOCX generation always uses `*_current.json` on the backend.

The Word file is downloaded directly from the backend's `storage/reports/` directory.

---

## 4. Storage Layer

No database. All data is stored in JSON flat files.

### File Locations

```
python-service/
└── storage/
    ├── data/
    │   ├── mortality_history.json         — list of quarterly mortality records
    │   ├── VAP_history.json               — list of quarterly VAP summaries
    │   ├── VAP_current.json               — raw cases from last VAP upload
    │   ├── clabsi_history.json            — list of quarterly CLABSI summaries
    │   ├── clabsi_current.json            — raw cases from last CLABSI upload
    │   ├── cauti_history.json             — list of quarterly CAUTI summaries
    │   ├── cauti_current.json             — raw cases from last CAUTI upload
    │   ├── medication_error_history.json  — lean 5-field quarterly records (trend charts + DOCX comparison table)
    │   └── medication_current.json        — full snapshot of last uploaded medication quarter (stats + records)
    ├── reports/                           — generated .docx files
    ├── charts/                            — generated .png chart images (cached)
    ├── uploads/                           — temp storage for uploaded Excel files
    └── temp/                              — temp storage (CAUTI uses this path)
```

### History JSON Structure

Each history file is a JSON array. New quarters are appended; existing quarters are overwritten when re-uploaded.

**mortality_history.json entry:**
```json
{
  "quarter": "الفصل الثالث",
  "year": "2025",
  "total_deaths": 47,
  "kpi_deaths": 38,
  "total_patients": 1200,
  "mortality_rate": 3.17,
  "departments": { "ICU": 12, "CCU": 8, "General": 18 },
  "buildings": { "BCI": 30, "RAH": 17 },
  "age_groups": { "<5": 2, "5-15": 1, "16-30": 4, ... },
  "gender": { "ذكر": 25, "انثى": 22 },
  ...
}
```

**VAP_history.json entry:**
```json
{
  "quarter": "الفصل الرابع",
  "year": "2025",
  "floors": {
    "ICU": { "cases": 2, "ventilator_days": 1200, "rate": 1.67, "target": 25.0 },
    "CCU": { "cases": 0, "ventilator_days": 980,  "rate": 0.0,  "target": 15.0 }
  },
  "germs_overall": { "Klebsiella": 2, "Acinetobacter": 0 },
  "germs_by_floor": {
    "ICU": { "counts": { "Klebsiella": 2 }, "percentages": { "Klebsiella": 100.0 } }
  }
}
```

**VAP_current.json (raw cases):**
```json
{
  "year": "2025",
  "quarter": "الفصل الرابع",
  "cases": [
    {
      "floor": "ICU",
      "case_number": 1,
      "age": 53.0,
      "age_display": "53Y",
      "gender": "Male",
      "diagnosis": "ARDS",
      "germs": "Klebsiella pneumoniae",
      "admission_date": "2025-10-01",
      "intubation_date": "2025-10-02",
      "infection_date": "2025-10-08",
      "vent_duration": 6,
      "diabetic": true,
      "hypertension": false,
      "copd": true,
      ...
    }
  ]
}
```

**medication_error_history.json entry (lean — 5 fields only):**
```json
{
  "quarter": "الفصل الثالث",
  "year": "2025",
  "error_rate": 0.045,
  "total_errors": 45,
  "total_doses": 1000
}
```

**medication_current.json entry (full snapshot):**
```json
{
  "quarter": "الفصل الثالث",
  "year": "2025",
  "statistics": {
    "summary": { "total_errors": 45, "total_doses": 1000, "error_rate": 0.045 },
    "error_cycle": { "Q1": 10, "Q2": 15, "Q3": 20 },
    "detected_by": { "Nurse": 30, "Pharmacist": 15 },
    "ncc_merp": { "A": 5, "B": 20, "C": 15, "D": 5 },
    ...
  },
  "records": [ { "Date": "2025-07-01", "Error Type": "Wrong Dose", ... } ]
}
```
`medication_current.json` always holds **exactly one entry** — the most recently uploaded quarter. It is overwritten on every upload.

---

### Why `*_current.json` Is Separate from `*_history.json`

The history file stores **lean summaries** — only the fields needed for trend charts and DOCX comparison tables. For medication: `quarter, year, error_rate, total_errors, total_doses`. This keeps the file small and fast over time.

The current file stores the **full snapshot** — all breakdown statistics plus raw records. This is what the dashboard breakdown charts and report generation need. Storing all of this in history would make the history file very large and slow over time.

The report generator always uses the **latest** `*_current.json` for detailed analysis. If someone uploads a new quarter, the current file is overwritten. This means full case-level reports can only be generated for the most recently uploaded quarter.

---

## 5. AI Service Layer

### Model

- **Model:** Qwen 2.5-7B Instruct GGUF (quantized to q3_k_m)
- **Loader:** llama-cpp-python (Python bindings for llama.cpp C++ runtime)
- **Model path:** `C:/models/qwen2.5-7b-instruct-q3_k_m.gguf` (override via `QWEN_MODEL_PATH` env variable)

### How the Model Is Loaded

```python
from llama_cpp import Llama

self._llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=1024,           # context window — how many tokens it can "see" at once
    n_threads_batch=4,    # CPU threads for batch processing
    n_batch=512,          # tokens processed per batch
    n_gpu_layers=-1,      # -1 = put ALL layers on GPU (set to 0 for CPU-only)
    verbose=False,        # suppress llama.cpp debug logs
)
```

The model is loaded **lazily** — only when the first report generation is requested. It stays loaded until the report is complete, then unloaded (`del self._llm`) to free GPU/RAM for the next module.

### How Text Is Generated — Chat Format

The code uses `create_chat_completion()` (the chat/instruct format), not raw text completion:

```python
result = self._llm.create_chat_completion(
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},   # rules + persona
        {"role": "user",   "content": user_prompt},     # data + specific request
    ],
    max_tokens=150,       # max Arabic words in response (~150 tokens ≈ 80-100 Arabic words)
    temperature=0.1,      # very low = more deterministic, less creative
    repeat_penalty=1.1,   # penalizes repeating the same phrases
    stop=["###", "---", "\n\n\n"],  # stop if model tries to generate these
)
text = result['choices'][0]['message']['content'].strip()
```

**Why chat format?** Instruction-tuned models like Qwen2.5-Instruct are fine-tuned to respond to a system prompt + user message. Using raw completion (`self._llm("prompt text")`) would produce worse results because the model expects the chat structure.

### The System Prompt (Mortality)

```
أنت محلل بيانات طبي خبير في تقارير الوفيات للمستشفيات.
اكتب تحليلاً احترافياً باللغة العربية الفصحى.
القواعد الأساسية:
1. استخدم اللغة العربية الفصحى السليمة مع علامات الترقيم المناسبة
2. اكتب فقرة واحدة متماسكة ومتصلة (3-5 جمل)
3. لا تستخدم النقاط أو التعداد الرقمي داخل الفقرة
4. ابدأ مباشرة بالتحليل بدون مقدمات
5. استخدم الأرقام كما هي في البيانات فقط، لا تخترع أرقاماً
6. ممنوع استخدام عبارة 'المبلغ عنه' أو 'وفقاً للبيانات' أو 'بناءً على'
7. استخدم الأقواس الصحيحة هكذا: (مثال) وليس )مثال(
8. لا تذكر نسب مئوية للنمو أو الارتفاع — فقط الأرقام المطلقة
9. لا تخترع أسماء أمراض أو أقسام غير موجودة في البيانات
```

This is sent with every generation call as the `system` role. It shapes the model's "personality" and enforces output rules.

### The User Prompt (per section, with actual data)

Each analysis method builds a specific `user_prompt` with the real numbers, then asks for a specific paragraph. Example from `analyze_mortality_trend()`:

```python
user_prompt = (
    f"بيانات نسبة الوفيات:\n"
    f"- الفصل الحالي: {quarter} {year}، النسبة {current_rate:.2f}%، "
    f"عدد الوفيات {current_deaths} حالة\n"
    f"- الفصل السابق: {prev_quarter}، النسبة {prev_rate:.2f}%، "
    f"عدد الوفيات {prev_deaths} حالة\n"
    f"- الاتجاه: {trend} بمقدار {diff:.2f}%\n"
    f"- الـ Target: {target_rate:.1f}%\n"
    f"- وضع النسبة الحالية: {vs_target} الـ Target\n\n"
    f"اكتب فقرة واحدة تذكر:\n"
    f"1. بلغت نسبة الوفيات {current_rate:.2f}% وعدد الوفيات {current_deaths} حالة\n"
    f"2. مقارنة بالفصل السابق ({prev_rate:.2f}% و {prev_deaths} حالة): {trend} بمقدار {diff:.2f}%\n"
    f"3. النسبة الحالية {vs_target} الـ Target البالغ {target_rate:.1f}%\n"
    f"ممنوع: 'المبلغ عنه' أو نسب نمو مئوية أو أرقام مخترعة."
)
```

The data is already computed by Python before calling the model — the model just needs to write sentences around the numbers. This is intentional: the model is bad at arithmetic, so we never ask it to calculate anything.

### Validation (Reject Bad Output)

After generation, the text is checked:

**Mortality validation:**
```python
def _is_valid_arabic_output(self, text):
    if not text or len(text.strip()) < 20:
        return False            # too short
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' ...)
    if cjk > 0:
        return False            # Chinese/Japanese characters = hallucination
    return True
```

**Medication validation (stricter):**
```python
def _safe(self, prompt, max_tokens):
    raw = self._generate(prompt, max_tokens)
    raw = self._clean(raw)      # strip CJK chars, fix Arabic punctuation
    if (raw
        and len(raw) > 30
        and not re.search(r'[\u4e00-\u9fff]', raw)     # no CJK
        and not re.search(r'(?m)^\s*\d+[.)]\s', raw)): # no numbered lists
        return raw
    return ""    # empty = caller uses fallback template
```

If validation fails → **fallback text** is used. The fallback is a Python f-string template that produces a grammatically correct Arabic sentence using the same data variables — no AI involved.

### The Hybrid Approach (Medication Module)

The medication AI service uses a **hybrid** strategy — some sections are generated by AI, some are built entirely by Python with no model call:

| Method | Strategy |
|--------|----------|
| `analyze_summary()` | **Pure Python** — builds 6 pre-structured lines from data dicts. No model call. |
| `analyze_ncc_merp()` | **Pure Python** — fills a template with b_count, c_count, b_pct. |
| `analyze_detection()` | **Pure Python** — sorts detected_by dict and builds sentence. |
| `analyze_shift()` | **Pure Python** — sorts shift_counts and builds sentence. |
| `analyze_trend_post()` | **AI first, Python fallback** — tries model; if empty, uses template. |
| `analyze_comparison()` | **AI first, Python fallback** |
| `analyze_error_cycle()` | **AI first, Python fallback** |
| `analyze_staff()` | **AI first, Python fallback** |
| `analyze_causes()` | **AI first, Python fallback** |

**Why this design?** The sections that are "Pure Python" follow very strict formatting rules matching the reference document. After testing, pure Python templates produced more reliable results than the model for these structured sections. The model is used where paragraph-style prose is needed.

### Bypassed Methods (Mortality — WHO Categories)

Two mortality AI methods exist in code but are **never called**:
```python
def analyze_who_comparison(self, ...):
    return ""   # bypassed — docx_generator builds this statically

def analyze_who_diagnosis(self, ...):
    return ""   # bypassed — docx_generator uses a lookup table
```

These were disabled because the model was hallucinating disease names. The DOCX generator now builds WHO category text from a hardcoded Arabic lookup table (`who_category → Arabic description`) — 100% reliable, never invents names.

### Module-Specific AI Services

| Module | File | Methods | Strategy |
|--------|------|---------|----------|
| Mortality | `app/mortality/ai_service.py` | 5 active methods | AI first + Python fallback |
| Medication | `app/medication/ai_service.py` | 9 methods | Hybrid (some Pure Python) |
| VAP | `app/infection_control/vap/ai_service.py` | 11 methods | AI first + Python fallback |
| CLABSI/CAUTI | `app/infection_control/ic_ai_service.py` | Shared methods | AI first + Python fallback |

---

## 6. Arabic RTL Word Reports — How BiDi Works

Arabic Word documents require explicit BiDi (bidirectional text) markup at multiple levels. This is the most complex part of the report generator.

### Three Levels of RTL

**Level 1 — Document** (set once, handled by paragraph/table level):
There is no document-level RTL flag in python-docx. It is controlled per paragraph and per table.

**Level 2 — Paragraph (`<w:pPr>`):**
```xml
<w:pPr>
  <w:bidi/>          <!-- tells Word this paragraph is RTL -->
  <w:jc w:val="right"/>  <!-- optional: explicit right alignment -->
</w:pPr>
```

Set in code with:
```python
def _set_rtl(self, para):
    para.paragraph_format.right_to_left = True
    pPr = para._element.get_or_add_pPr()
    if pPr.find(qn('w:bidi')) is None:
        bidi = OxmlElement('w:bidi')
        bidi.set(qn('w:val'), '1')
        pPr.append(bidi)
```

**Level 3 — Run (`<w:rPr>`):**
```xml
<w:rPr>
  <w:rtl/>    <!-- tells Word this specific run is RTL text -->
</w:rPr>
```

Without `<w:rtl/>` on the run, Word uses its Unicode BiDi algorithm to guess direction. For **pure Arabic** text this usually works. But for **mixed text** (Arabic + "Target" or "- مقارنة..."), the guess can be wrong — the paragraph appears on the left even though `<w:bidi/>` is set.

**Level 4 — Table (`<w:tblPr>`):**
```xml
<w:tblPr>
  <w:bidiVisual/>   <!-- table columns appear right-to-left -->
</w:tblPr>
```

Without this, a 3-column table has columns [A, B, C] from left. With `<w:bidiVisual/>`, columns appear [C, B, A] from left (i.e., A is rightmost, which is "first" in Arabic reading order).

### The `_add_bidi_para` Pattern

For mixed Arabic/Latin text, splits the string at LTR boundaries:

```python
text = "- مقارنة نسبة الوفيات مع الـ Target"

# Split into:
# ("- مقارنة نسبة الوفيات مع الـ ", Arabic) → run + <w:rtl/>
# ("Target",                          LTR)   → run, no <w:rtl/>
```

Arabic runs get `<w:rtl/>` in their `<w:rPr>`. LTR runs do not. This ensures "Target" renders left-to-right (correct) while the Arabic text renders right-to-left.

### Why Explicit Alignment Is Sometimes Omitted

When `<w:bidi/>` is set on the paragraph **and** `<w:rtl/>` is set on the Arabic runs, Word correctly infers right alignment. Adding `para.alignment = WD_ALIGN_PARAGRAPH.RIGHT` on top can sometimes interfere with the BiDi algorithm in complex table cells. The `_add_rtl_para` helper intentionally does **not** set explicit alignment.

---

## 7. What Is Missing / Known Gaps

### Missing Features

**1. CLABSI Report Generation (frontend)**
The CLABSI reports page currently exists in the frontend (`infection_control/Reports.jsx` with `type="clabsi"`), but the backend `clabsi_routes.py` may be missing a `/generate-report` endpoint or the endpoint may not be fully wired to the shared `InfectionControlDocxGenerator`. Verify that `POST /api/clabsi/generate-report` works end-to-end.

**2. CAUTI Report Generation (frontend)**
Same situation as CLABSI. The CAUTI docx generator wrapper exists (`cauti/docx_generator.py`) but the full report generation pipeline should be tested end-to-end.

**3. Mortality `*_current.json`**
Mortality does not have a `current.json` file. This means the mortality report is generated entirely from history data — there is no per-patient case detail table in the mortality report. If per-patient tables are ever needed, a `mortality_current.json` should be added following the IC pattern.

**4. ~~Medication Error `*_current.json`~~ ✅ Resolved**
`medication_current.json` now exists. It stores the full snapshot (all statistics + raw records) of the last uploaded quarter. History file is trimmed to 5 lean fields. Dashboard reads from `data` prop (App.jsx), Reports uses `currentData` prop for full statistics when the selected quarter is the current one.

**5. CLABSI/CAUTI Dashboard Charts**
The CLABSI and CAUTI dashboards (`clabsi/Dashboard.jsx`, `cauti/Dashboard.jsx`) may have limited chart coverage compared to VAP. The VAP dashboard has a full trend chart, germ heatmap, and floor gauges. Verify that CLABSI and CAUTI dashboards have equivalent coverage.

**6. Quarter Delete in Mortality and Medication**
The VAP, CLABSI, and CAUTI routes have a `DELETE /{quarter}/{year}` endpoint. Mortality and medication error history currently do not have delete endpoints — to remove an incorrect quarter, you must manually edit the JSON file.

**7. CLABSI/CAUTI `floor_catheter_days` parameter naming**
In `cauti_routes.py`, the call to `_stats.calculate_all_statistics()` uses `floor_catheter_days=denominators_dict` — but the parameter was renamed to `floor_device_days` in `ic_statistics.py`. This may cause a `TypeError`. Check `cauti_routes.py` and `clabsi_routes.py` for this mismatch.

**8. Frontend API URL Hardcoded**
The frontend has `http://localhost:8000` hardcoded in several places. For network deployment, this must be changed to the server IP. A `.env.production` file with `VITE_API_URL` is not yet wired up — the fetch calls do not use `import.meta.env.VITE_API_URL`.

**9. No Authentication**
There is no login or authentication system. Anyone who can reach the server IP can upload data, view history, and generate reports. For hospital deployment, consider adding basic authentication (HTTP Basic Auth in nginx, or a simple API key middleware in FastAPI).

**10. Report Storage Growth**
Generated `.docx` files accumulate in `storage/reports/`. There is no automatic cleanup. Over time this directory can become large. Consider adding a cleanup route or a cron-style task.

**11. No Input Validation on Denominators**
Floor ventilator/catheter day values entered by the user are accepted as-is. If a user enters `0` for a floor, the rate calculation divides by zero — this is handled with a conditional `if total_days > 0 else 0.0`, but the user gets no warning. Frontend validation for denominator inputs would improve usability.

**12. VAP Neonatal Floor**
`STANDARD_FLOORS` in `vap/history.py` includes `"Neonatal"` with a target of `0.0`. If the hospital does not have a Neonatal floor, it shows up as an empty section in the report. Consider making floor list configurable.

### Known Limitations

- **Single concurrent report generation:** The AI model is loaded into memory synchronously inside the HTTP request handler. If two users trigger report generation simultaneously, the second request will likely fail or be very slow. This is acceptable for hospital use (small team) but would require a task queue (Celery, etc.) for multi-user concurrent access.
- **No backup:** History JSON files are not automatically backed up. If the server disk fails, all history is lost.
- **Excel format dependency:** The processors are written for specific Excel column names used by this hospital's reporting system. A different hospital with different column naming would need processor customization.

---

## 8. Local Server Deployment (Step by Step)

This section explains how to deploy the system on a Windows or Linux server so the entire hospital network can access it at a single IP address.

### What "Local Server" Means

You run the backend and serve the frontend from one machine on the hospital LAN. All other computers on the same network open a browser and go to `http://SERVER-IP` — no software installation needed on client machines.

```
Hospital LAN
     │
     ├── Nurse workstation A  ─┐
     ├── Nurse workstation B  ─┤── browser → http://192.168.1.100
     ├── Doctor workstation   ─┘
     │
     └── SERVER (192.168.1.100)
           ├── Python backend  :8000  (FastAPI)
           └── nginx           :80   (React static files + API proxy)
```

---

### Windows Server Deployment

#### Step 1 — Clone / Copy the Project

Copy the project folder to the server. Recommended location:
```
C:\healthcare_system\
```

#### Step 2 — Install Python and Dependencies

1. Install Python 3.11 from https://python.org (check "Add to PATH")
2. Open Command Prompt as Administrator:

```cmd
cd C:\healthcare_system\python-service

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For GPU AI support (if server has NVIDIA GPU):
```cmd
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
```

Place the Qwen model file at `C:\models\qwen2.5-7b-instruct-q3_k_m.gguf`.

#### Step 3 — Build the Frontend

Install Node.js 18+ from https://nodejs.org.

Before building, update the API URL. Create `C:\healthcare_system\frontend\.env.production`:
```
VITE_API_URL=http://192.168.1.100:8000
```

Then update any `fetch('http://localhost:8000/...')` calls in the frontend source to use:
```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
fetch(`${API_URL}/api/...`)
```

Then build:
```cmd
cd C:\healthcare_system\frontend
npm install
npm run build
```

This creates `C:\healthcare_system\frontend\dist\`.

#### Step 4 — Install and Configure nginx

1. Download nginx for Windows from https://nginx.org/en/download.html
2. Extract to `C:\nginx\`
3. Edit `C:\nginx\conf\nginx.conf`:

```nginx
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    sendfile      on;

    server {
        listen 80;
        server_name localhost;

        # Serve React build
        root C:/healthcare_system/frontend/dist;
        index index.html;

        # React Router support — unknown paths → index.html
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Proxy API calls to FastAPI
        location /api/ {
            proxy_pass http://127.0.0.1:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 300s;    # AI report generation can take up to 5 min
            proxy_connect_timeout 10s;
        }

        # Proxy health check
        location /health {
            proxy_pass http://127.0.0.1:8000/health;
        }

        # Proxy API docs
        location /docs {
            proxy_pass http://127.0.0.1:8000/docs;
        }
    }
}
```

4. Start nginx:
```cmd
cd C:\nginx
nginx.exe
```

To stop: `nginx.exe -s stop`

#### Step 5 — Run the Python Backend as a Windows Service

Install NSSM from https://nssm.cc/download — extract `nssm.exe` to `C:\Windows\System32\`.

Then in an elevated command prompt:
```cmd
nssm install HealthcareAPI
```

In the NSSM GUI:
- **Path:** `C:\healthcare_system\python-service\venv\Scripts\python.exe`
- **Startup directory:** `C:\healthcare_system\python-service`
- **Arguments:** `main.py`
- **Environment:** `PYTHONUTF8=1`

Or via command line:
```cmd
nssm install HealthcareAPI "C:\healthcare_system\python-service\venv\Scripts\python.exe" "main.py"
nssm set HealthcareAPI AppDirectory "C:\healthcare_system\python-service"
nssm set HealthcareAPI AppEnvironmentExtra "PYTHONUTF8=1"
nssm set HealthcareAPI AppStdout "C:\healthcare_system\python-service\logs\service.log"
nssm set HealthcareAPI AppStderr "C:\healthcare_system\python-service\logs\service.log"
nssm start HealthcareAPI
```

The service now starts automatically on Windows boot.

#### Step 6 — Also Start nginx on Boot

Create a Task Scheduler task to run `C:\nginx\nginx.exe` at system startup, or install nginx as a service using NSSM:
```cmd
nssm install nginx "C:\nginx\nginx.exe"
nssm start nginx
```

#### Step 7 — Open Firewall Ports

```cmd
netsh advfirewall firewall add rule name="Healthcare HTTP" dir=in action=allow protocol=TCP localport=80
```

> Port 8000 does NOT need to be opened if nginx proxies all API calls. Only open 8000 if you want direct API access from other machines.

#### Step 8 — Verify

From the server:
```
http://localhost          → React frontend
http://localhost:8000/health  → {"status": "healthy"}
```

From another machine on the LAN:
```
http://192.168.1.100      → React frontend (full system)
```

---

### Linux Server Deployment

#### Step 1 — Install Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip nodejs npm nginx -y
```

#### Step 2 — Setup Python Backend

```bash
cd /opt/healthcare_system/python-service
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3 — Build Frontend

```bash
cd /opt/healthcare_system/frontend

# Create production env
echo "VITE_API_URL=http://$(hostname -I | awk '{print $1}'):8000" > .env.production

npm install
npm run build
```

#### Step 4 — Configure nginx

```bash
sudo nano /etc/nginx/sites-available/healthcare
```

```nginx
server {
    listen 80;
    server_name _;

    root /opt/healthcare_system/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
        proxy_connect_timeout 10s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/healthcare /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 5 — Create systemd Service

```bash
sudo nano /etc/systemd/system/healthcare-api.service
```

```ini
[Unit]
Description=Healthcare Quality Indicators API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/healthcare_system/python-service
Environment=PYTHONUTF8=1
Environment=QWEN_MODEL_PATH=/opt/models/qwen2.5-7b-instruct-q3_k_m.gguf
ExecStart=/opt/healthcare_system/python-service/venv/bin/python main.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/healthcare_system/python-service/logs/service.log
StandardError=append:/opt/healthcare_system/python-service/logs/service.log

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable healthcare-api
sudo systemctl start healthcare-api
sudo systemctl status healthcare-api
```

#### Step 6 — Open Firewall

```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

---

### Updating the System

When you have code changes to deploy:

**Backend update:**
```cmd
# Windows
cd C:\healthcare_system\python-service
git pull
venv\Scripts\activate
pip install -r requirements.txt   # only if requirements changed
nssm restart HealthcareAPI
```

```bash
# Linux
cd /opt/healthcare_system/python-service
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart healthcare-api
```

**Frontend update:**
```bash
cd frontend
git pull
npm install         # only if package.json changed
npm run build       # rebuilds dist/
# nginx picks up changes automatically — no restart needed
```

---

### Quick Troubleshooting

| Problem | Check |
|---------|-------|
| Frontend shows blank page | Run `npm run build` again; check browser console for errors |
| API not reachable | Run `curl http://localhost:8000/health` on the server |
| Arabic text garbled in reports | Ensure `PYTHONUTF8=1` is set in the service environment |
| AI report takes forever | Model not found → check model path; or using CPU → see CPU setup |
| Report download fails | Check `storage/reports/` directory exists and is writable |
| "404 Not Found" on page refresh | nginx `try_files` not configured — React Router needs this |
| Cannot access from another PC | Check firewall port 80 is open; check nginx is running |

---

### Storage and Backup

Data files that must be backed up regularly:
```
storage/data/mortality_history.json
storage/data/VAP_history.json
storage/data/VAP_current.json
storage/data/clabsi_history.json
storage/data/clabsi_current.json
storage/data/cauti_history.json
storage/data/cauti_current.json
storage/data/medication_error_history.json
```

Simple backup script (Windows, run weekly with Task Scheduler):
```cmd
xcopy "C:\healthcare_system\python-service\storage\data" "D:\backups\healthcare\%DATE%" /E /I /Y
```

Linux (add to crontab — runs every Sunday at 2 AM):
```bash
0 2 * * 0 cp -r /opt/healthcare_system/python-service/storage/data /backups/healthcare/$(date +\%Y-\%m-\%d)
```

---

## 9. Module Deep Dive — Calculations, Functions, Charts, Reports

---

### 9.1 Mortality Module — Full Detail

#### Python Files & Key Functions

**`app/mortality/excel_handler.py` — ExcelHandler**

| Function | What it does |
|----------|-------------|
| `parse_excel(path)` | Opens workbook with openpyxl. Reads Sheet 1 for patient rows, Sheet 2 for WHO category summary. Returns `(df, who_summary, raw_wb)`. |
| `_detect_encoding_issue(df)` | Checks if >20% of column headers contain `?` or `\ufffd` — if yes, the file is a malformed CSV saved as xlsx. Switches to `_parse_csv_mode()`. |
| `_map_columns(df)` | Maps Arabic/English column names to internal snake_case keys. Column name aliases are defined in a dict at the top of the file. |
| `_parse_who_sheet(wb)` | Reads Sheet 2, extracts WHO category name → count pairs. Returns a list of `{"category": str, "count": int}`. |

**`app/mortality/data_processor.py` — DataProcessor**

| Function | What it does |
|----------|-------------|
| `clean_data(df)` | Main entry point. Calls all sub-cleaners and returns a cleaned DataFrame. Never drops rows. |
| `_normalize_gender(val)` | Maps Arabic/English gender strings → `"ذكر"` / `"أنثى"` / `"غير محدد"`. |
| `_normalize_kpi(val)` | Maps yes/no variants → `"YES"` / `"NO"`. Critical: only YES rows count in the mortality rate. |
| `_parse_age(val)` | Parses age strings like `"5 سنة"`, `"3 أشهر"`, `"45"` → float years. |
| `_normalize_department(val)` | Strips and title-cases department names. |
| `get_validation_report()` | Returns dict of {field: missing_count} for frontend to display data quality info. |

**`app/mortality/statistics.py` — StatisticsCalculator**

| Function | What it does |
|----------|-------------|
| `calculate_all_statistics(df, total_patients, admission_data)` | Master function. Calls all sub-calculators and returns a single dict. |
| `_calculate_mortality_metrics(df, total_patients)` | Rate = `(kpi_deaths / total_patients) × 100`. Also computes total deaths vs KPI deaths. |
| `_calculate_departments(df)` | Groups KPI=YES rows by `nursing_department`, returns sorted list of `{name, count, percentage}`. |
| `_calculate_demographics(df)` | Gender split, 8 age groups (KPI=YES rows), age categories from `تصنيف العمر` column. |
| `_calculate_clinical(df)` | Time-to-death (admission→death), admission source, discharge destination breakdowns. |
| `_calculate_buildings(df)` | BCI vs RAH split from `building` column. Falls back to department name matching if `building` column empty. |
| `_calculate_specialties(df)` | Groups by medical specialty if specialty column present. |
| `_calculate_who_categories_kpi(df)` | Returns dict of WHO category → count using only KPI=YES rows. |

**Key Calculations:**
```
Mortality Rate = (KPI Deaths / Total Admitted Patients) × 100

KPI Deaths = rows where include_kpi == "YES"
Total Deaths = all rows (regardless of KPI flag)

Age groups:
  <5y  | 5-15y | 16-30y | 31-50y | 51-60y | 61-70y | 71-80y | >80y

Department percentage = (dept_deaths / kpi_deaths) × 100
Building percentage   = (building_deaths / kpi_total) × 100
```

**`app/mortality/chart_generator.py` — MatplotlibDocxChartGenerator**

Charts generated as BytesIO PNG objects and embedded directly into Word:

| Chart # | Name | Type | Data Used |
|---------|------|------|-----------|
| 1 | Mortality Rate Trend | Line chart | Historical quarterly rates + 2% target line |
| 2 | Deaths by Department | Horizontal bar | dept name → death count |
| 3 | Deaths by Building | Pie / Donut | BCI vs RAH counts |
| 4 | Gender Distribution | Pie | ذكر vs أنثى counts |
| 5 | Age Group Distribution | Bar | 8 age bands |
| 6 | WHO Category Distribution | Horizontal bar | who_category → count |
| 7 | Monthly Trend | Line | deaths per month of quarter |
| 8 | Admission Source | Bar | admission source → count |
| 9 | Discharge Destination | Bar | destination → count |
| 10 | KPI vs Total Deaths | Grouped bar | KPI deaths vs Total deaths comparison |

**`app/mortality/docx_generator.py` — MatplotlibDocxGenerator**

DOCX Report Structure (6 pages):

| Page | Content |
|------|---------|
| Page 1 | Cover page: hospital logo, title, quarter, year, date of generation |
| Page 2 | Executive summary table: total patients, total deaths, KPI deaths, mortality rate, BCI/RAH split |
| Page 3 | Mortality rate trend chart (Chart 1) + AI analysis paragraph |
| Page 4 | Department breakdown table + bar chart (Chart 2) + gender pie (Chart 4) |
| Page 5 | Age distribution (Chart 5) + WHO categories (Chart 6) + AI paragraph |
| Page 6 | Clinical details: admission source, discharge destination, time-to-death + AI paragraph |

---

### 9.2 Medication Error Module — Full Detail

#### Python Files & Key Functions

**`app/medication/data_processor.py` — MedicationDataProcessor**

| Function | What it does |
|----------|-------------|
| `process_file(path)` | Main entry: reads Excel, maps columns, normalizes values, returns cleaned DataFrame. |
| `_normalize_error_type(val)` | Maps Arabic/English error type strings → 7 standard English categories. |
| `_normalize_severity(val)` | Maps severity descriptions → Minor / Moderate / Severe / Near Miss. |
| `_normalize_cycle(val)` | Maps medication cycle stage → Prescribing / Transcription / Dispensing / Administration / Monitoring / Preparation. |
| `_normalize_shift(val)` | Maps shift descriptions → Morning / Evening / Night. |

**Standard column mapping (Excel → internal key):**
```
الخطأ / Error Type          → error_type
الخطورة / Severity          → severity
القسم / Department          → department
المناوبة / Shift            → shift
دورة الدواء / Error Cycle   → error_cycle
سبب الخطأ / Error Cause     → error_cause
عدد الأخطاء / Error Count   → error_count
```

**`app/medication/statistics.py` — MedicationStatisticsCalculator**

| Function | What it does |
|----------|-------------|
| `calculate_all_statistics(df, total_doses, quarter, year)` | Master function. Returns full stats dict. |
| `_count_by_type(df)` | Sum of `error_count` grouped by `error_type`. |
| `_count_by_severity(df)` | Sum of `error_count` grouped by `severity`. |
| `_count_by_department(df)` | Sum of `error_count` grouped by `department`. |
| `_count_by_shift(df)` | Sum of `error_count` grouped by `shift` (Morning / Evening / Night). |
| `_count_by_cycle(df)` | Sum grouped by `error_cycle` (prescribing stage). |
| `_count_by_cause(df)` | Sum grouped by `error_cause`. |
| `_calculate_rate(total_errors, total_doses)` | Rate = `(total_errors / total_doses) × 10000` (errors per 10,000 doses). |
| `_calculate_heatmap(df, row_col, col_col)` | Pandas `pivot_table` cross-tabulation. Returns nested dict `{row: {col: count}}`. Used for cycle×cause matrix. |

**Key Calculations:**
```
Error Rate = (Total Errors / Total Doses Dispensed) × 10,000

Severity Rate = (Severe errors / Total Errors) × 100

Heatmap cell value = exact count from pivot_table (no approximation)
```

**`app/medication/chart_generator.py`**

| Chart # | Name | Type | Data |
|---------|------|------|------|
| 1 | Errors by Type | Horizontal bar | error_type → count |
| 2 | Errors by Severity | Pie / Donut | severity → count |
| 3 | Errors by Department | Horizontal bar | department → count |
| 4 | Errors by Shift | Pie / Donut | shift → count |
| 5 | Error Rate Trend | Line | Historical rate over quarters |
| 6 | Errors by Cycle | Bar | cycle stage → count |
| 7 | Cycle × Cause Heatmap | Heatmap | Matplotlib `imshow` on pivot matrix |

**`app/medication/docx_generator.py` — MedicationDocxGenerator**

DOCX Report Structure:

| Page | Content |
|------|---------|
| Page 1 | Cover: hospital logo, title "تقرير أخطاء الدواء", quarter, year |
| Page 2 | Summary table: total doses, total errors, error rate, severity breakdown |
| Page 3 | Error type bar chart + AI analysis |
| Page 4 | Department breakdown table + severity pie |
| Page 5 | Shift distribution + cycle stage breakdown + AI paragraph |
| Page 6 | Heatmap (cycle × cause) + trend chart |
| Page 7 | Results comparison table: current quarter vs target (5 errors per 10k doses) |

The results table ("جدول النتائج") has a "النتيجة الحالية" column filled with the current quarter label (e.g., "الفصل الثالث 2025").

---

### 9.3 VAP Module — Full Detail

#### Python Files & Key Functions

**`app/infection_control/vap/processor.py` — VAPProcessor**

| Function | What it does |
|----------|-------------|
| `process_vap_sheet(path, year, quarter, denominators)` | Entry point. Opens Excel with openpyxl, finds header row, iterates data rows. Returns `{"cases": [...], "meta": {...}}`. |
| `_find_header_row(ws)` | Scans first 10 rows to find the row containing known header keywords. |
| `_map_headers(header_row)` | Builds `{col_idx: field_name}` dict from Arabic/English header cells. |
| `_parse_age(val)` | Returns `(float_years, display_str)`. Handles `"53"` → `(53.0, "53Y")`, `"3 months"` → `(0.25, "3M")`, `"10 days"` → `(0.027, "10D")`. |
| `_parse_date(val)` | Tries 4 date formats: Excel serial number, `DD/MM/YYYY`, `YYYY-MM-DD`, free text. Returns ISO string or `None`. |
| `_parse_boolean(val)` | Maps yes/no/+/- → `True`/`False` for 13 risk factor columns. |
| `_parse_germs(val)` | Splits multi-germ strings (`, ` or ` + `) → list of normalized germ names. |

**VAP Case Dictionary Structure:**
```json
{
  "floor": "ICU",
  "case_number": 1,
  "age": 53.0,
  "age_display": "53Y",
  "gender": "Male",
  "diagnosis": "ARDS",
  "germs": "Klebsiella pneumoniae",
  "admission_date": "2025-10-01",
  "intubation_date": "2025-10-02",
  "infection_date": "2025-10-08",
  "vent_duration": 6,
  "diabetic": true,
  "hypertension": false,
  "copd": true,
  "renal_failure": false,
  "immunosuppressed": false,
  "hob_elevation": true,
  "oral_care": false,
  "subglottic_suctioning": false,
  "cuff_pressure": true,
  "circuit_change": false,
  "closed_suction": false,
  "pvp_bundle": false,
  "sedation_vacation": false
}
```

**`app/infection_control/ic_statistics.py` — InfectionControlStatistics**

| Function | What it does |
|----------|-------------|
| `calculate_all_statistics(cases, floor_device_days, quarter, year)` | Master function for VAP/CLABSI/CAUTI. Returns full stats dict. |
| `_calculate_floor_stats(cases, floor_device_days)` | For each floor: counts cases, reads device-days from denominators dict, computes rate. |
| `_match_floor(raw_floor, standard_floors)` | Fuzzy matches floor names from Excel against standard list using alias dict. |
| `_calculate_germ_distribution(cases)` | Counts each germ overall and per floor. Returns `{"overall": {...}, "by_floor": {...}}`. |
| `_calculate_risk_factors(cases)` | For each of 13 boolean risk factor fields: count True values, compute percentage. |
| `_calculate_age_groups(cases)` | Bins numeric ages into 5 groups: <1y, 1-14y, 15-45y, 46-60y, >60y. |
| `_calculate_monthly_trend(cases, quarter)` | Counts cases per month within the quarter (3 months). Returns list of 3 `{month, count}`. |

**VAP Rate Formula:**
```
VAP Rate = (Number of VAP cases on floor / Ventilator Days on floor) × 1000

Unit: infections per 1,000 ventilator-days

Standard target thresholds (from FLOOR_TARGETS in vap/history.py):
  ICU:      ≤ 25.0 per 1,000 vent-days
  CCU:      ≤ 15.0
  Neonatal: ≤  0.0 (not applicable)
```

**`app/infection_control/vap/chart_generator.py`**

| Chart | Type | Data |
|-------|------|------|
| Floor Rate Bar | Horizontal bar | VAP rate per floor vs target |
| Germ Distribution (Overall) | Pie | Germ name → total case count |
| Germ Distribution (per floor) | One pie per floor | Germ → count for that floor |
| Risk Factor Bar | Horizontal bar | Risk factor → % of cases with factor |
| Monthly Trend | Line | Month → case count for quarter |
| Age Group Bar | Bar | Age group → case count |

**`app/infection_control/vap/docx_generator.py`**

VAP DOCX Report Structure:

| Section | Content |
|---------|---------|
| Cover | Logo, "تقرير الالتهاب الرئوي المرتبط بالتهوية الميكانيكية", quarter, year |
| Summary | Total cases, total vent-days, overall rate, floors with zero VAP |
| Per-floor sections | For each floor with cases: rate gauge chart, case detail table (age, gender, diagnosis, germs, risk factors), germ pie chart, AI analysis paragraph |
| Overall germs | Germ distribution across all floors |
| Risk factors | Bar chart of 13 risk factors |
| Trend | Historical quarterly rate trend per floor |

**`app/infection_control/vap/ai_service.py`**

11 separate AI methods, each generating one paragraph:

| Method | Generates analysis for |
|--------|----------------------|
| `analyze_floor_rate(floor, rate, target)` | Whether floor rate is above/below target |
| `analyze_germs_overall(germs)` | Most prevalent organisms across all floors |
| `analyze_germs_floor(floor, germs)` | Organisms specific to one floor |
| `analyze_risk_factors(factors)` | Risk factor prevalence and recommendations |
| `analyze_age_distribution(ages)` | Age pattern of infected patients |
| `analyze_gender(gender_data)` | Gender distribution |
| `analyze_monthly_trend(monthly)` | Within-quarter case timing trend |
| `analyze_diagnoses(diagnoses)` | Underlying diagnoses of cases |
| `analyze_bundle_compliance(cases)` | VAP prevention bundle adherence |
| `analyze_vent_duration(cases)` | Duration of ventilation before infection |
| `generate_recommendations(stats)` | Overall recommendations section |

---

### 9.4 CLABSI Module — Full Detail

**Files:** `app/infection_control/clabsi/`

**Rate Formula:**
```
CLABSI Rate = (Number of CLABSI cases / Catheter Days) × 1000

Standard target: ≤ 0.0 to ≤ 2.0 per 1,000 catheter-days (floor-specific)
```

**`processor.py` — CLABSIProcessor**

Same structure as VAP processor. Key difference: tracks `catheter_days` (central line) per case rather than vent duration.

**`clabsi_targets.py` — CLABSI_TARGETS**

```python
CLABSI_TARGETS = {
    "ICU":        1.0,   # target infections per 1000 catheter-days
    "CCU":        1.0,
    "Pediatric":  0.5,
    "Oncology":   2.0,
    # ... other floors
}
```

**`docx_generator.py`**

Thin wrapper that creates `InfectionControlDocxGenerator` with this config:
```python
config = {
    "indicator":          "CLABSI",
    "indicator_ar":       "عدوى مجرى الدم المرتبطة بالقثطار المركزي",
    "days_key":           "catheter_days",
    "days_label_ar":      "أيام القسطرة المركزية",
    "insertion_col":      "date_of_insertion",
    "insertion_col_ar":   "تاريخ إدخال القسطرة",
    "file_prefix":        "CLABSI",
}
```

The shared `InfectionControlDocxGenerator` (`ic_docx_generator.py`) builds the report identically to VAP using this config to fill in labels. The structure is the same (cover → summary → per-floor sections → germs → risk factors → trend).

---

### 9.5 CAUTI Module — Full Detail

**Files:** `app/infection_control/cauti/`

Identical structure to CLABSI with:

**Rate Formula:**
```
CAUTI Rate = (Number of CAUTI cases / Urinary Catheter Days) × 1000

Standard target: ≤ 1.0 to ≤ 3.0 per 1,000 urinary catheter-days (floor-specific)
```

Config passed to shared docx generator:
```python
config = {
    "indicator":          "CAUTI",
    "indicator_ar":       "عدوى المسالك البولية المرتبطة بالقسطرة",
    "days_key":           "urinary_catheter_days",
    "days_label_ar":      "أيام القسطرة البولية",
    "insertion_col":      "date_of_catheter_insertion",
    "insertion_col_ar":   "تاريخ إدخال القسطرة البولية",
    "file_prefix":        "CAUTI",
}
```

---

## 10. Frontend Component Reference

### 10.1 Shared Components (`src/components/`)

| Component | File | What it does |
|-----------|------|-------------|
| `Navbar` | `Navbar.jsx` | Top navigation bar. Receives `language` and `toggleLanguage` props from App.jsx. Renders module links. |
| `AdvancedDonut` | Probably in `components/` | Recharts PieChart configured as donut. Accepts `data`, `centerValue`, `centerLabel` props. Center text shows total. |
| `Heatmap` | In `components/` | Renders cycle×cause grid. Accepts `rows`, `cols`, `data`, `grandTotal` props. Bottom-right cell uses `grandTotal` to avoid Math.round drift. |
| `Gauge` | In `components/` | RadialBarChart with target line. Accepts `value`, `target`, `label`. |
| `TrendChart` | In `components/` | LineChart showing historical quarterly rates. Accepts `data` array and `target` number. |

### 10.2 Mortality Pages

**`src/pages/mortality/Upload.jsx`**
- Form fields: Quarter select (Arabic names), Year number input, Total Patients number input, File input (.xlsx/.xls/.csv)
- `onWheel={(e) => e.target.blur()}` on all number inputs to prevent scroll-wheel accidents
- `max={new Date().getFullYear()}` on year input (dynamic, updates each year)
- On submit: `FormData` POST to `http://localhost:8000/api/process-data`
- On success: calls `onDataLoaded(responseData)` prop (updates App.jsx state) then navigates to `/mortality/dashboard`

**`src/pages/mortality/Dashboard.jsx`**
- Receives `data`, `historyData`, `totalPatients`, `quarter`, `year`, `language` props from App.jsx
- Empty state check: if `!data`, shows "Upload Data" button → navigates to `/mortality/upload`
- `MORTALITY_TARGET = 2` (2% benchmark line on charts)
- KPI cards: Mortality Rate, KPI Deaths, Total Deaths, Total Patients
- Charts rendered: Gauge (mortality rate vs 2% target), TrendChart (history), department bar, building pie, gender pie, age bar, WHO categories bar

**`src/pages/mortality/Reports.jsx`**
- Loads history from `GET /api/history` on mount
- Shows quarter selector list
- "Generate Report" → `POST /api/generate-report` with `{quarter, year}`
- Loading state shown during generation (can take 30–90s if AI runs)
- Download link → `GET /api/download-report?fileName=...`

### 10.3 Medication Error Pages

**`src/pages/medication/Upload.jsx`**
- Fields: Quarter select, Year input, Total Doses Dispensed input, File input
- `onWheel={(e) => e.target.blur()}` on all number inputs
- POST to `http://localhost:8000/api/medication/process-data`
- On success: navigates to `/medication/dashboard`

**`src/pages/medication/Dashboard.jsx`**
- Fetches latest data from `GET /api/medication/current` on mount
- Charts:
  - Error rate gauge vs 5/10k target
  - Rate trend line chart (historical quarters)
  - Error type horizontal bar
  - Severity donut
  - Shift donut with total in center: `<AdvancedDonut data={shiftData} centerValue={total} centerLabel={t('medDeptTotal')} />`
  - Department horizontal bar
  - Cycle stage bar
  - Heatmap: Cycle × Cause grid — uses `grandTotal={current.total_errors}` to avoid rounding error

**`src/pages/medication/Reports.jsx`**
- Same pattern as mortality reports
- POST to `http://localhost:8000/api/medication/generate-report`
- Download from `GET /api/medication/download-report?fileName=...`

### 10.4 Infection Control Shared Pages

**`src/pages/infection_control/Upload.jsx`**
- Tabs: VAP | CLABSI | CAUTI (controlled by `defaultTab` prop)
- Fields: Quarter select, Year input, File input
- Floor denominators section: shows input per floor for vent-days / catheter-days
- `onWheel={(e) => e.target.blur()}` on all number inputs
- `max={new Date().getFullYear()}` on year input
- POST endpoint changes per tab:
  - VAP: `POST /api/vap/process-data`
  - CLABSI: `POST /api/clabsi/process-data`
  - CAUTI: `POST /api/cauti/process-data`

**`src/pages/infection_control/Reports.jsx`**
- Receives `type` prop: `"vap"` | `"clabsi"` | `"cauti"`
- Calls `GET /api/{type}/history` to get available quarters
- `POST /api/{type}/generate-report` to generate
- `GET /api/{type}/download-report?fileName=...` to download

### 10.5 IC Dashboard Pages

**`src/pages/infection_control/vap/Dashboard.jsx`**
- Fetches `GET /api/vap/history/latest` on mount
- Floor rate gauges: one per floor, value=rate, target from floor config
- Germ distribution: per-floor pie charts
- Monthly trend line chart
- Risk factor bar chart

**`src/pages/infection_control/clabsi/Dashboard.jsx`**
- Fetches `GET /api/clabsi/history/latest`
- Same layout pattern as VAP dashboard

**`src/pages/infection_control/cauti/Dashboard.jsx`**
- Fetches `GET /api/cauti/history/latest`
- Same layout pattern

---

## 11. API Endpoints Quick Reference

### Mortality (`/api/...` — router prefix is `/api`, NOT `/api/mortality`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/process-data` | Upload Excel file, process, save, return stats |
| GET | `/api/current` | Get latest uploaded quarter (for dashboard on restart) |
| GET | `/api/history` | Get all historical quarters (sorted oldest-first) |
| POST | `/api/generate-report` | Generate DOCX report for a quarter |
| GET | `/api/download-report?fileName=` | Download generated DOCX |
| GET | `/api/test` | Health check |

### Medication Error (`/api/medication/...`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/medication/process-data` | Upload and process |
| GET | `/api/medication/current` | Latest quarter data |
| GET | `/api/medication/history` | All historical quarters |
| POST | `/api/medication/generate-report` | Generate DOCX |
| GET | `/api/medication/download-report?fileName=` | Download DOCX |

### VAP (`/api/vap/...`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/vap/process-data` | Upload and process |
| GET | `/api/vap/history` | All VAP quarters |
| GET | `/api/vap/history/latest` | Latest quarter for dashboard |
| POST | `/api/vap/generate-report` | Generate DOCX |
| GET | `/api/vap/download-report?fileName=` | Download DOCX |
| DELETE | `/api/vap/{quarter}/{year}` | Delete a quarter from history |

### CLABSI (`/api/clabsi/...`)

Same pattern as VAP — replace `vap` with `clabsi`.

### CAUTI (`/api/cauti/...`)

Same pattern as VAP — replace `vap` with `cauti`.

---

## 12. AI Model — How to Use, Improve, and Update

### Current Setup (actual values from code)

| Setting | Mortality | Medication |
|---------|-----------|------------|
| Context window (`n_ctx`) | 1024 tokens | 1024 tokens |
| Temperature | 0.1 | 0.05 |
| top_p | default | 0.90 |
| repeat_penalty | 1.1 | 1.10 |
| max_tokens per call | 150–220 | 90–160 |
| GPU layers | -1 (all on GPU) | -1 (all on GPU) |
| Batch size (`n_batch`) | 512 | 512 |
| Stop sequences | `["###", "---", "\n\n\n"]` | `["\n\n\n", "###"]` |

### How Prompts Are Built (real code pattern)

Data is pre-computed in Python first, then injected into an Arabic prompt string. The model **only writes sentences** — it never calculates anything:

```python
# Step 1: Python calculates everything
trend     = "ارتفاع" if current_rate > prev_rate else "انخفاض"
diff      = abs(current_rate - prev_rate)
vs_target = "أقل من" if current_rate < target_rate else "أعلى من"

# Step 2: Build the user_prompt with real numbers already in it
user_prompt = (
    f"بيانات نسبة الوفيات:\n"
    f"- الفصل الحالي: {quarter} {year}، النسبة {current_rate:.2f}%\n"
    f"- الاتجاه: {trend} بمقدار {diff:.2f}%\n"
    f"اكتب فقرة واحدة تذكر هذه المعطيات."
)

# Step 3: Send system + user to model via chat format
result = self._llm.create_chat_completion(
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_prompt},
    ],
    temperature=0.1, max_tokens=170,
)
text = result['choices'][0]['message']['content'].strip()
```

### Validation Logic (real code)

```python
# Mortality: basic check
if not text or len(text.strip()) < 20:   return False   # too short
if any CJK char in text:                 return False   # hallucinated Chinese

# Medication: stricter check + cleanup before checking
text = re.sub(r'[\u4e00-\u9fff...]', '', text)   # strip any CJK chars
text = re.sub(r'(?m)^\s*\d+[.)]\s*', '', text)  # strip numbered list prefixes
if len(text) <= 30:                        return ""    # too short after cleaning
if re.search(r'(?m)^\s*\d+[.)]\s', text): return ""   # still has numbered list
```

If validation fails → Python **fallback template** is used. The fallback is a hardcoded f-string that produces a correct Arabic sentence from the same data variables — never empty output.

### The Hybrid Approach (Medication Module)

Some sections in the medication AI are built **entirely by Python** without calling the model at all:

| Method | Strategy |
|--------|----------|
| `analyze_summary()` | Pure Python — 6 pre-structured lines built from data dicts |
| `analyze_ncc_merp()` | Pure Python — fills a template with b_count, c_count, b_pct |
| `analyze_detection()` | Pure Python — sorts detected_by dict and builds sentence |
| `analyze_shift()` | Pure Python — sorts shift_counts and builds sentence |
| `analyze_trend_post()` | AI first → Python fallback if AI output invalid |
| `analyze_comparison()` | AI first → Python fallback |
| `analyze_error_cycle()` | AI first → Python fallback |
| `analyze_staff()` | AI first → Python fallback |
| `analyze_causes()` | AI first → Python fallback |

**Why?** Pure Python templates produce more reliable results for structured data. AI prose is only used where flowing paragraph writing adds value.

### Bypassed Methods (Mortality WHO Categories)

Two methods exist in code but always return `""`:
```python
def analyze_who_comparison(...): return ""   # disabled
def analyze_who_diagnosis(...):  return ""   # disabled
```
These were disabled because the model invented disease names. WHO category text is now built from a hardcoded Arabic lookup table in `docx_generator.py` — 100% reliable.

### How to Improve the AI

**1. Use a larger/better quantization:**
```
q3_k_m  → current (fastest, ~4GB VRAM)
q4_k_m  → better quality, still ~5GB VRAM
q5_k_m  → noticeably better, ~6GB VRAM
q8_0    → near-lossless, ~8GB VRAM
```

Download from Hugging Face:
```bash
pip install huggingface-hub

huggingface-cli download \
  bartowski/Qwen2.5-7B-Instruct-GGUF \
  Qwen2.5-7B-Instruct-Q4_K_M.gguf \
  --local-dir C:/models/
```

**2. Increase context window for longer responses (change in each ai_service.py):**
```python
self._llm = Llama(model_path=..., n_ctx=2048, ...)  # was 1024
```
Also increase `max_tokens=300` in each `_generate()` / `_safe()` call.

**3. Use a larger model (Qwen2.5-14B):**
```bash
huggingface-cli download \
  bartowski/Qwen2.5-14B-Instruct-GGUF \
  Qwen2.5-14B-Instruct-Q4_K_M.gguf \
  --local-dir C:/models/
```
Requires ~10GB VRAM. Produces noticeably better Arabic prose.

**5. Replace with OpenAI-compatible API (no local model needed):**
```python
from openai import OpenAI
client = OpenAI(api_key="your-key")

def generate_analysis(self, data):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "أنت محلل طبي..."},
            {"role": "user", "content": self._build_user_message(data)},
        ],
        max_tokens=300,
        temperature=0.3,
    )
    return response.choices[0].message.content
```
This works with OpenAI, Azure OpenAI, or any OpenAI-compatible API. No local GPU needed.

**6. Pre-generate and cache AI text:**
Currently AI runs during report generation (slow). You could pre-generate AI text when data is uploaded and cache it in the JSON, then use the cached text at report time. This would make report generation faster.

```python
# In mortality_routes.py process_mortality_data():
ai_text = ai_service.generate_analysis(stats)
history_manager.save_current_data(..., ai_analysis=ai_text)

# In docx_generator.py:
text = current_data.get('ai_analysis', fallback_text)
```

### Where Each AI Call Happens

| Module | When | File |
|--------|------|------|
| Mortality | Report generation | `mortality/ai_service.py` called by `mortality/docx_generator.py` |
| Medication | Report generation | `medication/ai_service.py` called by `medication/docx_generator.py` |
| VAP | Report generation | `infection_control/vap/ai_service.py` called by `vap/docx_generator.py` |
| CLABSI | Report generation | `infection_control/ic_ai_service.py` called by `ic_docx_generator.py` |
| CAUTI | Report generation | `infection_control/ic_ai_service.py` called by `ic_docx_generator.py` |

The model is loaded fresh for each report and unloaded immediately after to free GPU memory. Sequence matters: if you generate VAP then CLABSI in sequence, the second one must wait for the first to unload before loading its own model (they use the same physical model file).

---

## 13. Common Edit Patterns

This section shows exactly what to change for common update requests.

### Change a target value

**Mortality rate target (2%):**
- `frontend/src/pages/mortality/Dashboard.jsx` line: `const MORTALITY_TARGET = 2`

**Medication error rate target:**
- `frontend/src/pages/medication/Dashboard.jsx` — find the gauge component's `target` prop

**VAP floor-specific targets:**
- `python-service/app/infection_control/vap/history.py` — `FLOOR_TARGETS` dict

**CLABSI floor targets:**
- `python-service/app/infection_control/clabsi/clabsi_targets.py` — `CLABSI_TARGETS` dict

### Add a new floor to VAP/CLABSI/CAUTI

1. Add the floor to `STANDARD_FLOORS` in `vap/history.py` (or clabsi/cauti equivalent)
2. Add target rate to `FLOOR_TARGETS` / `CLABSI_TARGETS` / `CAUTI_TARGETS`
3. Add floor alias to `_match_floor()` in `ic_statistics.py` if the Excel uses a different name
4. Add the floor to the denominator input form in `frontend/src/pages/infection_control/Upload.jsx`

### Add a new chart to a dashboard

1. Add chart data computation in the appropriate `statistics.py` — add to the returned dict
2. Add the field to the history JSON save in `history_manager.py`
3. Add the field to the API response in the route file
4. In the dashboard JSX: destructure the new field from the API response, add a new Recharts component

### Change Arabic text / translations

All Arabic/English text is in `frontend/src/i18n/config.js`. Add new keys there and reference them with `t('key')` in the JSX.

### Add a new error type category (Medication)

1. In `app/medication/data_processor.py`: add new value to `_normalize_error_type()` mapping dict
2. No changes needed elsewhere — statistics and charts are dynamic

### Change the DOCX report layout

1. Find the relevant `docx_generator.py` for the module
2. Each page is a method (e.g., `_build_page1()`, `_build_page2()`)
3. Add/remove `doc.add_paragraph()`, `doc.add_table()`, `_add_bidi_para()` calls
4. For new charts: generate chart in `chart_generator.py`, call `_add_chart_image(chart_bytes)` in the docx generator

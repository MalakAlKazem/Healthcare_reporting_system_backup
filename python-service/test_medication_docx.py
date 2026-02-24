"""
Test: Generate Medication Error DOCX Report
============================================
Run from python-service/ directory:
    python test_medication_docx.py

The script:
  1. Loads the Excel file
  2. Processes data + calculates statistics
  3. Loads/seeds historical data
  4. Calls the DOCX generator
  5. Prints the output path
"""

import sys
import os
import asyncio
from pathlib import Path

# Force UTF-8 output so Arabic text and emoji don't crash the Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── path setup (must run from python-service/) ─────────────────────────────
ROOT = Path(__file__).resolve().parent          # python-service/
sys.path.insert(0, str(ROOT))

PROJECT_ROOT = ROOT.parent                      # healthcare_motality_system/

# ── imports ────────────────────────────────────────────────────────────────
from loguru import logger
from app.medication_error.data_processor  import MedicationErrorProcessor
from app.medication_error.statistics      import MedicationErrorStatistics
from app.medication_error.history_manager import MedicationErrorHistory, INITIAL_HISTORY
from app.medication_error.docx_generator  import MedicationErrorDocxGenerator


# ── config ─────────────────────────────────────────────────────────────────
EXCEL_FILE = str(PROJECT_ROOT / 'sample_data' / 'Medication Error3.xlsx')

# Where reports land (storage/reports/ relative to project root)
REPORTS_DIR = str(PROJECT_ROOT / 'storage' / 'reports')

# History JSON path (relative to where the service normally runs)
HISTORY_PATH = str(ROOT / 'storage' / 'data' / 'medication_error_history.json')


# ── helpers ────────────────────────────────────────────────────────────────

def print_section(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def run_test():
    print_section("MEDICATION ERROR DOCX GENERATOR — TEST")

    # ── STEP 1: validate Excel file ────────────────────────────────────────
    print_section("STEP 1: Locate Excel file")

    excel_path = Path(EXCEL_FILE)
    if not excel_path.exists():
        # Try alternate paths
        candidates = [
            PROJECT_ROOT / 'sample_data' / 'medicationError-Q3.xlsx',
            PROJECT_ROOT / 'sample_data' / 'medication_error.xlsx',
        ]
        for c in candidates:
            if c.exists():
                excel_path = c
                break
        else:
            print(f"  FAIL  Excel file not found. Tried:\n     {EXCEL_FILE}")
            for c in candidates:
                print(f"     {c}")
            sys.exit(1)

    print(f"  OK  Found: {excel_path}")

    # ── STEP 2: process data ───────────────────────────────────────────────
    print_section("STEP 2: Process data")

    processor = MedicationErrorProcessor()
    df_raw  = processor.load_excel(str(excel_path))
    doses   = processor.extract_total_doses(df_raw)

    if not doses:
        print("  WARN  Total doses NOT found in file -- using fallback 431124")
        doses = 431124
    processor.total_doses = doses

    df_clean = processor.clean_data(df_raw)
    quarter, year = processor.calculate_quarter(df_clean)

    print(f"  Quarter    : {quarter} {year}")
    print(f"  Total rows : {len(df_clean)}")
    print(f"  Total doses: {doses:,}")

    # ── STEP 3: statistics ─────────────────────────────────────────────────
    print_section("STEP 3: Calculate statistics")

    stats_calc = MedicationErrorStatistics()
    stats = stats_calc.calculate_all_statistics(df_clean, doses, quarter, year)

    s = stats['summary']
    print(f"  Error rate   : {s['error_rate']:.4f}%")
    print(f"  Total errors : {s['total_errors']}")
    print(f"  Total doses  : {s['total_doses']:,}")

    for key, label in [
        ('error_cycle',   'Chart 3 – Error Cycle'),
        ('detected_by',   'Chart 4 – Detected By'),
        ('duty_shift',    'Chart 5 – Shift'),
        ('staff_involved','Chart 6 – Staff'),
    ]:
        counts = stats[key]['counts']
        total  = stats[key]['total']
        print(f"\n  {label} (total={total}):")
        for k, v in counts.items():
            pct = stats[key]['percentages'][k]
            print(f"    {k}: {v}  ({pct}%)")

    # ── STEP 4: history ────────────────────────────────────────────────────
    print_section("STEP 4: Seed + load history")

    os.makedirs(str(PROJECT_ROOT / 'storage'), exist_ok=True)
    history_mgr = MedicationErrorHistory(HISTORY_PATH)

    # Seed initial history if the JSON is empty
    if len(history_mgr.history) == 0:
        print("  Seeding initial history data...")
        history_mgr.initialize_with_data(INITIAL_HISTORY)
    else:
        print(f"  Loaded {len(history_mgr.history)} existing quarters")

    # Save current quarter
    history_mgr.save_quarter(quarter=quarter, year=year, stats=stats)

    all_history = history_mgr.get_last_n_quarters(100)
    # Pass everything EXCEPT the current quarter to the results table
    history_for_report = [
        h for h in all_history
        if not (h['quarter'] == quarter and h['year'] == str(year))
    ]

    print(f"  History for report: {len(history_for_report)} quarters")
    for h in history_for_report[-6:]:
        print(f"    {h['quarter']} {h['year']}: {h['error_rate']:.4f}%")

    # ── STEP 5: generate DOCX ──────────────────────────────────────────────
    print_section("STEP 5: Generate DOCX report")

    # Patch the generator's storage path so it saves to project-level storage/
    gen = MedicationErrorDocxGenerator()
    # Override _get_reports_dir so the file ends up in project root/storage/reports
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Monkey-patch: save directly to REPORTS_DIR
    _orig_generate = gen.generate_report

    async def _patched_generate(stats_arg, history=None, options=None):
        """Same as generate_report but forces REPORTS_DIR."""
        from app.medication_error.chart_generator import MedicationErrorCharts
        from docx import Document
        import datetime

        options  = options or {}
        summary  = stats_arg.get('summary', {})
        q        = options.get('quarter', summary.get('quarter', 'الفصل الثالث'))
        y        = str(options.get('year', summary.get('year', '2025')))

        chart_gen = MedicationErrorCharts(
            output_dir=str(PROJECT_ROOT / 'storage' / 'charts' / 'medication_error')
        )

        # Append current quarter to history so charts 1 & 2 include it
        current_entry = {
            'quarter':      q,
            'year':         y,
            'error_rate':   summary.get('error_rate', 0),
            'total_errors': summary.get('total_errors', 0),
            'total_doses':  summary.get('total_doses', 0),
        }
        chart_history = list(history or []) + [current_entry]

        charts = chart_gen.generate_all_charts(stats_arg, chart_history)
        logger.info(f"Generated {len(charts)} charts")

        doc = Document()
        gen._setup_section(doc.sections[0])
        gen._build_page1(doc, q, y, stats_arg, charts, history or [])
        gen._build_page2(doc, charts, stats_arg)
        gen._build_page3(doc, charts)
        gen._build_page4(doc, charts, stats_arg)
        gen._build_page5(doc, stats_arg)
        gen._build_last_page(doc)

        ts        = datetime.datetime.now().strftime('%H%M%S')
        file_name = f'medication-error_{q}_{y}_{ts}.docx'
        file_path = os.path.join(REPORTS_DIR, file_name)
        doc.save(file_path)
        logger.success(f"DOCX saved: {file_path}")
        return {'filePath': file_path, 'fileName': file_name}

    result = asyncio.run(
        _patched_generate(stats, history=history_for_report, options={'quarter': quarter, 'year': str(year)})
    )

    # ── RESULT ─────────────────────────────────────────────────────────────
    print_section("RESULT")
    print(f"  OK   Report generated successfully!")
    print(f"  File : {result['fileName']}")
    print(f"  Path : {result['filePath']}")
    print(f"  Size : {os.path.getsize(result['filePath']):,} bytes")
    print()


if __name__ == '__main__':
    run_test()

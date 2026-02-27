"""
Test script: generates a VAP DOCX report by reading the real Excel file.

Run from python-service/ directory:
    python test_vap_docx.py

Output: storage/reports/VAP report الفصل الرابع 2025.docx
"""

import sys
import os
from pathlib import Path

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from app.infection_control.VAP.vap_processor      import process_vap_sheet
from app.infection_control.VAP.vap_statistics     import VAPStatistics
from app.infection_control.VAP.vap_history        import VAPHistory
from app.infection_control.VAP.vap_docx_generator import VAPDocxGenerator
ROOT = Path(__file__).resolve().parent          # python-service/
sys.path.insert(0, str(ROOT))
PROJECT_ROOT = ROOT.parent                      # healthcare_motality_system/

# ── Config ────────────────────────────────────────────────────────────────────
EXCEL_PATH = os.path.join( PROJECT_ROOT / 'sample_data' , 'infection_control.xlsx')
QUARTER    = 'الفصل الرابع'
YEAR       = 2025

# ── Ventilator days entered manually per floor (user input in real app) ───────
FLOOR_VENTILATOR_DAYS = {
    'ICU':      650,
    'CCU':      480,
    'CSU':      120,
    'Ped':      0,
    'ICN':      310,
    'ITU':      0,
    'Neonatal': 200,
}

# ── Step 1: Process Excel → raw case data ────────────────────────────────────
total_vent_days = sum(FLOOR_VENTILATOR_DAYS.values())
print(f"Processing VAP sheet from: {EXCEL_PATH}")
processed = process_vap_sheet(
    filepath=EXCEL_PATH,
    ventilator_days=total_vent_days,
    semester='Fourth',
    year=YEAR,
)

print(f"  → {processed['meta']['total_cases']} cases found")
print(f"  → Floors: {processed['floors']}")
print(f"  → Germs:  {processed['germs']}")

# ── Step 2: Calculate statistics ─────────────────────────────────────────────
calc  = VAPStatistics()
stats = calc.calculate_all_statistics(
    processed_result=processed,
    floor_ventilator_days=FLOOR_VENTILATOR_DAYS,
    quarter=QUARTER,
    year=YEAR,
)

print(f"\nStatistics calculated:")
print(f"  → Overall rate: {stats['summary']['overall_rate']}‰")
for floor, fs in stats['floor_stats'].items():
    if fs['cases'] > 0:
        print(f"  → {floor}: {fs['cases']} cases, {fs['rate']}‰ (target {fs['target']}‰)")

# ── Step 3: Save to test history (upsert) ────────────────────────────────────
HISTORY_PATH = str(os.path.join(ROOT, 'storage', 'data', 'VAP_history_test.json'))
vap_history  = VAPHistory(HISTORY_PATH)
vap_history.save_quarter(QUARTER, YEAR, stats)
print(f"\nHistory saved: {len(vap_history.history)} total quarters in test history")

# History for report = all quarters EXCEPT the current one (avoid duplicate)
history = [
    e for e in vap_history.get_all()
    if not (e['quarter'] == QUARTER and e['year'] == str(YEAR))
]
print(f"History passed to report: {len(history)} previous quarters")

# ── Step 4: Generate DOCX ────────────────────────────────────────────────────
gen    = VAPDocxGenerator()
result = gen.generate_report(
    stats=stats,
    history=history,
    chart_paths={},          # no charts — placeholders will appear
    options={'quarter': QUARTER, 'year': str(YEAR)},
)

print(f"\n✅ Report saved: {result['filePath']}")
print(f"   File name:    {result['fileName']}")
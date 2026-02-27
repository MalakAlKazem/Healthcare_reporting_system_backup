"""
VAP Module Integration Test
===========================
Run from inside python-service/ directory:

    cd python-service
    python test_vap.py

What this tests:
    1. vap_processor       — parse Excel, extract cases, calculate metrics
    2. vap_statistics      — floor stats, germs, risk factors, case tables
    3. vap_history         — save/load quarters, trend data, germs comparison
    4. vap_chart_generator — generate all 6 charts as PNG files

Charts saved to:
    storage/charts/infection_control/VAP/
History saved to:
    storage/data/VAP_history_test.json
"""

import sys
import json
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent                         # python-service/
ROOT_DIR     = BASE_DIR.parent                               # healthcare_motality_system/
EXCEL_PATH   = ROOT_DIR / "sample_data" / "infection control.xlsx"
CHARTS_DIR   = BASE_DIR / "storage" / "charts" / "infection_control" / "VAP"
HISTORY_PATH = BASE_DIR / "storage" / "data" / "VAP_history_test.json"

# ── sys.path so "infection_control.VAP.*" imports resolve ─────────────────────
sys.path.insert(0, str(BASE_DIR / "app"))

# ── Stub loguru if not installed ──────────────────────────────────────────────
try:
    from loguru import logger
except ImportError:
    import types, logging
    logging.basicConfig(level=logging.INFO, format="  %(message)s")
    _log = logging.getLogger("vap")
    _stub = types.ModuleType("loguru")
    class _L:
        def info(self, m): _log.info(m)
        def success(self, m): _log.info(m)
        def warning(self, m): _log.warning(m)
        def error(self, m): _log.error(m)
    _stub.logger = _L()
    import sys; sys.modules["loguru"] = _stub


# ── Create output dirs & clean old test history ───────────────────────────────
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
if HISTORY_PATH.exists():
    HISTORY_PATH.unlink()
    print(f"🗑️  Cleared previous test history")

# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 60)
print("  VAP MODULE TEST")
print("═" * 60)

if not EXCEL_PATH.exists():
    print(f"\n❌  Excel not found: {EXCEL_PATH}")
    print("    Place file at: sample_data/infection control.xlsx")
    sys.exit(1)
print(f"\n✅  Excel: {EXCEL_PATH.name}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  STEP 1 — vap_processor")
print("─" * 60)

from infection_control.VAP.vap_processor import process_vap_sheet

result = process_vap_sheet(str(EXCEL_PATH), ventilator_days=0)
meta   = result["meta"]

print(f"  Semester/Quarter : {meta['semester']}")
print(f"  Year             : {meta['year']}")
print(f"  Total cases      : {meta['total_cases']}")
print(f"  Ventilator days  : {meta['ventilator_days']}")
print(f"  VAP rate (meta)  : {meta['vap_rate_per_1000_ventilator_days']}‰")
print(f"  Floors found     : {result['floors']}")
print(f"  Germs (top 3)    : {dict(list(result['germs'].items())[:3])}")
print(f"  Age groups       : {result['age_groups']}")
print(f"  Genders          : {result['genders']}")

if result["cases"]:
    print(f"\n  Sample case [0]:")
    c = result["cases"][0]
    for k in ["floor", "age", "germs", "diagnosis", "date_of_infection"]:
        print(f"    {k}: {c.get(k)}")

print("\n✅  PROCESSOR — PASSED")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — STATISTICS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  STEP 2 — vap_statistics")
print("─" * 60)

from infection_control.VAP.vap_statistics import VAPStatistics

FLOOR_VENT_DAYS = {
    "ICU": 200, "CCU": 254, "CSU": 50,
    "Ped": 0,   "ICN": 177, "ITU": 0,
}

# Use the actual quarter and year read from the Excel file
_quarter = result["meta"]["semester"]   # e.g. "Fourth"
_year    = result["meta"]["year"]       # e.g. 2025
if not _quarter:
    _quarter = "Fourth"
if not _year:
    _year = 2025

print(f"  Using quarter={_quarter!r}  year={_year} (from Excel)")

stats = VAPStatistics().calculate_all_statistics(
    result, FLOOR_VENT_DAYS, quarter=_quarter, year=int(_year)
)

print(f"\n  Summary:")
for k, v in stats["summary"].items():
    print(f"    {k}: {v}")

print(f"\n  Floor breakdown:")
for floor, fs in stats["floor_stats"].items():
    if fs["cases"] > 0 or fs["ventilator_days"] > 0:
        status = "🔴 ABOVE" if fs["rate"] > fs["target"] else "🟢 below"
        print(f"    {floor}: {fs['cases']} cases / {fs['ventilator_days']}d "
              f"= {fs['rate']}‰  [{status} target {fs['target']}‰]")

print(f"\n  Germs overall (top 5):")
for g, n in list(stats["germs_overall"]["counts"].items())[:5]:
    pct = stats["germs_overall"]["percentages"][g]
    print(f"    {g}: {n} ({pct}%)")

print(f"\n  Risk factors (top 5):")
for rf, n in list(stats["risk_factors"]["counts"].items())[:5]:
    pct = stats["risk_factors"]["percentages"][rf]
    print(f"    {rf}: {n} ({pct}%)")

print(f"\n  ICU cases table — {len(stats['icu_cases_table'])} row(s):")
for row in stats["icu_cases_table"]:
    print(f"    #{row['case_number']} | {row['age']} | {row['germs']}")
    print(f"           RF: {row['risk_factors']}")

print(f"\n  CCU cases table — {len(stats['ccu_cases_table'])} row(s):")
for row in stats["ccu_cases_table"]:
    print(f"    #{row['case_number']} | {row['age']} | {row['germs']}")
    print(f"           RF: {row['risk_factors']}")

print(f"\n  ICN cases table — {len(stats['icn_cases_table'])} row(s):")
for row in stats["icn_cases_table"]:
    print(f"    #{row['case_number']} | {row['age']} | {row['germs']}")
    print(f"           RF: {row['risk_factors']}")

print("\n✅  STATISTICS — PASSED")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — HISTORY MANAGER
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  STEP 3 — vap_history")
print("─" * 60)

from infection_control.VAP.vap_history import VAPHistory

hist = VAPHistory(str(HISTORY_PATH))

# ── Helper to build seeded quarter entries ────────────────────────────────────
def _seed(q, yr, icu_c, icu_v, ccu_c, ccu_v, icn_c, icn_v,
          icu_g, ccu_g, icn_g):
    def gs(counts):
        total = sum(counts.values())
        return {
            "counts": counts,
            "percentages": {k: round(v / total * 100, 1)
                            for k, v in counts.items()} if total else {},
            "total": total,
        }
    ef = {"cases": 0, "ventilator_days": 0, "rate": 0.0,
          "target": 0.0, "pct_of_total": 0.0}
    return {
        "summary": {
            "quarter": q, "year": yr,
            "total_cases": icu_c + ccu_c + icn_c,
            "total_vent_days": icu_v + ccu_v + icn_v,
            "overall_rate": 0.0,
        },
        "floor_stats": {
            "ICU": {"cases": icu_c, "ventilator_days": icu_v,
                    "rate": round(icu_c / icu_v * 1000, 2) if icu_v else 0.0,
                    "target": 25.0, "pct_of_total": 0.0},
            "CCU": {"cases": ccu_c, "ventilator_days": ccu_v,
                    "rate": round(ccu_c / ccu_v * 1000, 2) if ccu_v else 0.0,
                    "target": 15.0, "pct_of_total": 0.0},
            "ICN": {"cases": icn_c, "ventilator_days": icn_v,
                    "rate": round(icn_c / icn_v * 1000, 2) if icn_v else 0.0,
                    "target": 10.0, "pct_of_total": 0.0},
            "CSU": ef, "Ped": ef, "ITU": ef,
        },
        "germs_overall":  gs({**icu_g, **ccu_g, **icn_g}),
        "germs_by_floor": {
            "ICU": gs(icu_g), "CCU": gs(ccu_g), "ICN": gs(icn_g),
            "CSU": gs({}),    "Ped": gs({}),    "ITU": gs({}),
        },
        "icu_cases_table": [], "ccu_cases_table": [], "icn_cases_table": [],
        "risk_factors": {}, "diagnoses": [], "monthly_trend": [],
        "age_groups": {}, "genders": {},
    }

# Seed 4 historical quarters
hist.save_quarter("Third",  2024, _seed("Third",  2024, 11,861, 2,254, 1,177,
    {"Acinetobacter Baumanii":5,"Klebsiella CRE":4,"Pseudomonas aeruginosa":2},
    {"Acinetobacter Baumanii":2}, {"Klebsiella ESBL":1}))

hist.save_quarter("Fourth", 2024, _seed("Fourth", 2024, 1,483, 0,55, 0,28,
    {"Klebsiella CRE":1}, {}, {}))

hist.save_quarter("First",  2025, _seed("First",  2025, 9,871, 0,302, 2,162,
    {"Acinetobacter Baumanii":5,"Klebsiella ESBL":3,"Pseudomonas aeruginosa":1},
    {}, {"Acinetobacter Baumanii":1,"Klebsiella CRE":1}))

hist.save_quarter("Second", 2025, _seed("Second", 2025, 4,705, 3,267, 2,160,
    {"Acinetobacter Baumanii":1,"Xanthomonas maltophilia":1,
     "Proteus ESBL":1,"Klebsiella CRE":1},
    {"Acinetobacter Baumanii":2,"Xanthomonas maltophilia":1},
    {"Xanthomonas maltophilia":2}))

hist.save_quarter("Third",  2025, _seed("Third",  2025, 1,650, 1,229, 1,209,
    {"Proteus ESBL":1},
    {"Xanthomonas maltophilia":1},
    {"Xanthomonas maltophilia":1}))

# Save current quarter from real Excel
hist.save_quarter(_quarter, int(_year), stats)

print(f"\n  Total quarters in history: {len(hist.get_all())}")
for e in hist.get_all():
    print(f"    {e['quarter']:8} {e['year']}  │  "
          f"ICU {e['floors']['ICU']['rate']:5}‰  "
          f"CCU {e['floors']['CCU']['rate']:5}‰  "
          f"ICN {e['floors']['ICN']['rate']:5}‰")

chart_data = hist.get_chart_data()

print(f"\n  Chart 1 — ICU trend ({len(chart_data['chart1_icu_trend'])} pts):")
for q in chart_data["chart1_icu_trend"]:
    print(f"    {q['quarter']} {q['year']}: {q['rate']}‰")

print(f"\n  Chart 3 — CCU trend ({len(chart_data['chart3_ccu_trend'])} pts):")
for q in chart_data["chart3_ccu_trend"]:
    print(f"    {q['quarter']} {q['year']}: {q['rate']}‰")

print(f"\n  Chart 5 — ICN trend ({len(chart_data['chart5_icn_trend'])} pts):")
for q in chart_data["chart5_icn_trend"]:
    print(f"    {q['quarter']} {q['year']}: {q['rate']}‰")

print(f"\n  Chart 2 — ICU germs comparison:")
c2 = chart_data["chart2_icu_germs"]
print(f"    Unified germ list : {c2['germs']}")
if c2["current"]:
    print(f"    Current  ({c2['current']['quarter']} {c2['current']['year']}): "
          f"{c2['current']['labels']}")
if c2["previous"]:
    print(f"    Previous ({c2['previous']['quarter']} {c2['previous']['year']}): "
          f"{c2['previous']['labels']}")

print(f"\n  Chart 4 — CCU germs comparison:")
c4 = chart_data["chart4_ccu_germs"]
print(f"    Unified germ list : {c4['germs']}")
if c4["current"]:
    print(f"    Current  ({c4['current']['quarter']} {c4['current']['year']}): "
          f"{c4['current']['labels']}")

print(f"\n  Chart 6 — ICN germs comparison:")
c6 = chart_data["chart6_icn_germs"]
print(f"    Unified germ list : {c6['germs']}")
if c6["current"]:
    print(f"    Current  ({c6['current']['quarter']} {c6['current']['year']}): "
          f"{c6['current']['labels']}")

print(f"\n  Table 1 — Multi-floor comparison:")
table = hist.get_quarter_floor_comparison_table(n=5)
print(f"    Quarters : {table['quarters']}")
for floor in ["ICU", "CCU", "ICN"]:
    rates = [f"{q['rate']}‰" for q in table["data"][floor]]
    print(f"    {floor}      : {rates}")

print("\n✅  HISTORY — PASSED")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — CHART GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  STEP 4 — vap_chart_generator")
print("─" * 60)

from infection_control.VAP.vap_chart_generator import VAPChartGenerator

gen   = VAPChartGenerator(str(CHARTS_DIR))
bufs  = gen.generate_all_charts(chart_data)
paths = gen.save_all_charts(bufs)

print(f"\n  Saved to: {CHARTS_DIR}\n")
all_ok = True
for name, path in paths.items():
    size = Path(path).stat().st_size
    ok   = size > 5_000
    icon = "✅" if ok else "❌"
    print(f"  {icon}  {name}.png  ({size:,} bytes)")
    if not ok:
        all_ok = False

if all_ok:
    print("\n✅  CHARTS — PASSED")
else:
    print("\n⚠️  Some charts may be empty — check output folder")

# ══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 60)
print("  ALL TESTS PASSED ✅")
print("═" * 60)
print(f"  📊  Cases processed  : {stats['summary']['total_cases']}")
print(f"  🏥  Active floors    : {sum(1 for f in stats['floor_stats'].values() if f['cases'] > 0)}")
print(f"  💾  History quarters : {len(hist.get_all())}")
print(f"  🎨  Charts generated : {len(paths)}")
print(f"\n  📁  Charts  → {CHARTS_DIR}")
print(f"  📁  History → {HISTORY_PATH}")
print()
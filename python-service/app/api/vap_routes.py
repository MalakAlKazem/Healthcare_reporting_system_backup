"""
VAP FastAPI Routes
Prefix: /api/vap
"""

import io
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from loguru import logger

from app.infection_control.vap.processor import process_vap_sheet
from app.infection_control.vap.history import VAPHistory, load_history, load_current, FLOOR_TARGETS, STANDARD_FLOORS
from app.infection_control.ic_statistics import InfectionControlStatistics

router = APIRouter(prefix="/api/vap", tags=["VAP"])

# ── Storage paths ──────────────────────────────────────────────────────────────
UPLOAD_DIR  = Path("storage/uploads/vap")
HISTORY_PATH = Path("storage/data/VAP_history.json")
CHARTS_DIR  = Path("storage/charts/vap")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Shared instances ───────────────────────────────────────────────────────────
_history = VAPHistory(str(HISTORY_PATH))
_ic      = InfectionControlStatistics("vap")


def _compute_vap_stats(processed: dict, floor_vent_days: dict, quarter, year: int) -> dict:
    """Compute VAP statistics — delegates shared logic to InfectionControlStatistics."""
    from app.infection_control.vap.history import _to_arabic_quarter

    cases       = processed["cases"]
    total_cases = processed["meta"]["total_cases"]

    ic              = _ic.calculate_all_statistics(cases, floor_vent_days, quarter, year)
    total_vent_days = ic["total_days"]
    overall_rate    = ic["overall_rate"]

    floor_stats: dict = {}
    for floor in STANDARD_FLOORS:
        fs = ic["summary"].get(floor, {})
        n  = fs.get("cases", 0)
        floor_stats[floor] = {
            "cases":           n,
            "ventilator_days": fs.get("ventilator_days", 0),
            "rate":            fs.get("rate", 0.0),
            "target":          FLOOR_TARGETS.get(floor, 0.0),
            "pct_of_total":    round(n / total_cases * 100, 1) if total_cases > 0 else 0.0,
        }

    germs_by_floor: dict = {}
    for floor in STANDARD_FLOORS:
        flat  = ic["germs_distribution"].get(floor, {})
        total = sum(flat.values())
        flat_sorted = dict(sorted(flat.items(), key=lambda x: x[1], reverse=True))
        germs_by_floor[floor] = {
            "counts":      flat_sorted,
            "total":       total,
            "percentages": {g: round(n / total * 100, 1) for g, n in flat_sorted.items()} if total else {},
        }

    all_counts: dict = {}
    for c in cases:
        g = (c.get("germs") or "Unknown").strip()
        all_counts[g] = all_counts.get(g, 0) + 1
    all_counts    = dict(sorted(all_counts.items(), key=lambda x: x[1], reverse=True))
    total_overall = sum(all_counts.values())
    germs_overall = {
        "counts":      all_counts,
        "percentages": {g: round(n / total_overall * 100, 1) for g, n in all_counts.items()} if total_overall else {},
        "total":       total_overall,
    }

    ar_quarter = _to_arabic_quarter(quarter)

    return {
        "summary": {
            "quarter":         ar_quarter,
            "year":            year,
            "total_cases":     total_cases,
            "total_vent_days": total_vent_days,
            "overall_rate":    overall_rate,
        },
        "floor_stats":    floor_stats,
        "germs_overall":  germs_overall,
        "germs_by_floor": germs_by_floor,
        "risk_factors":   ic["risk_factors"],
        "diagnoses":      processed["diagnoses"],
        "monthly_trend":  processed["monthly_trend"],
        "age_groups":     processed["age_groups"],
        "genders":        processed["genders"],
    }


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/vap/process-data
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/process-data")
async def process_data(
    file:        UploadFile = File(...),
    quarter:     str        = Form(...),
    year:        int        = Form(...),
    icu_days:    int        = Form(0),
    ccu_days:    int        = Form(0),
    csu_days:    int        = Form(0),
    ped_days:    int        = Form(0),
    icn_days:    int        = Form(0),
    itu_days:    int        = Form(0),
):
    """
    Upload VAP Excel file + floor ventilator days.
    Processes the data, saves to history, returns summary stats.
    """
    logger.info(f"📥 VAP upload: {file.filename} | {quarter} {year}")

    # ── Validate file ──────────────────────────────────────────────────────────
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Only Excel files (.xlsx / .xls) are accepted")

    # ── Save file temporarily ──────────────────────────────────────────────────
    tmp_path = UPLOAD_DIR / file.filename
    content  = await file.read()
    tmp_path.write_bytes(content)

    try:
        # ── Process Excel ──────────────────────────────────────────────────────
        # Total vent days = sum of all floors (used by processor meta only)
        total_vent_days = icu_days + ccu_days + csu_days + ped_days + icn_days + itu_days
        processed = process_vap_sheet(str(tmp_path), ventilator_days=total_vent_days)

        # ── Floor ventilator days ──────────────────────────────────────────────
        floor_vent_days = {
            "ICU": icu_days,
            "CCU": ccu_days,
            "CSU": csu_days,
            "Ped": ped_days,
            "ICN": icn_days,
            "ITU": itu_days,
        }

        # ── Calculate statistics ───────────────────────────────────────────────
        stats = _compute_vap_stats(processed, floor_vent_days, quarter, year)

        # ── Save to history ────────────────────────────────────────────────────
        _history.load_history()          # refresh before saving
        _history.save_quarter(quarter, year, stats, processed["cases"])

        logger.success(f"✅ VAP processed & saved: {quarter} {year}")

        return JSONResponse({
            "status":      "success",
            "quarter":     quarter,
            "year":        year,
            "total_cases": stats["summary"]["total_cases"],
            "overall_rate": stats["summary"]["overall_rate"],
            "floor_stats": stats["floor_stats"],
            "message":     f"VAP data for {quarter} {year} processed and saved successfully",
        })

    except Exception as e:
        logger.error(f"❌ VAP processing error: {e}")
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/history
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/history")
async def get_history():
    """Return all saved VAP quarters (oldest → newest)."""
    _history.load_history()
    return JSONResponse(_history.get_all())


@router.get("/current")
async def get_current():
    """Return the current quarter's raw case data."""
    return JSONResponse(load_current())


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/history/latest
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/history/latest")
async def get_latest():
    """Return the most recent quarter's data."""
    _history.load_history()
    all_q = _history.get_all()
    if not all_q:
        raise HTTPException(404, "No VAP history found")
    return JSONResponse(all_q[-1])


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/chart-data
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/chart-data")
async def get_chart_data():
    """
    Return all chart data for the 6 VAP charts.
    Used by frontend dashboard when charts are enabled.
    """
    _history.load_history()
    return JSONResponse(_history.get_chart_data())


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/table-comparison
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/table-comparison")
async def get_table_comparison(n: int = 5):
    """
    Return Table 1: multi-floor quarterly comparison data.
    n = number of recent quarters to include (default 5).
    """
    _history.load_history()
    return JSONResponse(_history.get_quarter_floor_comparison_table(n=n))


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/charts/{chart_name}
# Returns a single chart PNG (for future dashboard use)
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/charts/{chart_name}")
async def get_chart(chart_name: str):
    """
    Return a single VAP chart as a PNG image.
    chart_name: chart1_icu_trend | chart2_icu_germs | chart3_ccu_trend |
                chart4_ccu_germs | chart5_icn_trend | chart6_icn_germs
    """
    valid = {
        "chart1_icu_trend", "chart2_icu_germs",
        "chart3_ccu_trend", "chart4_ccu_germs",
        "chart5_icn_trend", "chart6_icn_germs",
    }
    if chart_name not in valid:
        raise HTTPException(400, f"Unknown chart: {chart_name}. Valid: {sorted(valid)}")

    try:
        from app.infection_control.vap.chart_generator import VAPChartGenerator
        _history.load_history()
        chart_data = _history.get_chart_data()
        gen  = VAPChartGenerator(str(CHARTS_DIR))
        bufs = gen.generate_all_charts(chart_data)
        buf  = bufs.get(chart_name)
        if not buf:
            raise HTTPException(500, "Chart generation failed")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        raise HTTPException(500, str(e))


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /api/vap/history/{quarter}/{year}
# ══════════════════════════════════════════════════════════════════════════════
@router.delete("/history/{quarter}/{year}")
async def delete_quarter(quarter: str, year: int):
    """Delete a specific quarter from history."""
    _history.load_history()
    before = len(_history.history)
    _history.history = [
        e for e in _history.history
        if not (e["quarter"] == quarter and e["year"] == str(year))
    ]
    if len(_history.history) == before:
        raise HTTPException(404, f"{quarter} {year} not found in history")
    _history._save()
    return JSONResponse({"status": "deleted", "quarter": quarter, "year": year})


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/vap/generate-report
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/generate-report")
def generate_vap_report():
    """
    Generate a DOCX VAP report from the full history file.
    All statistics (cases, germs, rates) are already stored in the history JSON.
    """
    history = load_history()
    if not history:
        raise HTTPException(status_code=404, detail="No VAP data available")
    try:
        from app.infection_control.vap.docx_generator import VAPDocxGenerator
        current = load_current()
        gen     = VAPDocxGenerator()
        result  = gen.generate_report(history=history, targets=FLOOR_TARGETS, current=current)
        return {"success": True, "filePath": result["filePath"], "fileName": result["fileName"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/vap/download-report?fileName=...
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/download-report")
async def download_vap_report(fileName: str):
    """
    Download a generated VAP DOCX report by filename.
    Reports are stored in the root storage/reports/ directory.
    """
    safe_name   = os.path.basename(fileName)
    reports_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'reports')
    )
    file_path = os.path.join(reports_dir, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(404, f"Report not found: {safe_name}")

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.get("/targets")
def get_targets():
    """Return VAP targets per 1,000 ventilator-days per department."""
    return FLOOR_TARGETS

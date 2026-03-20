"""
CAUTI API Routes
Prefix: /api/cauti
"""

import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.infection_control.cauti.processor import process_cauti_excel
from app.infection_control.cauti.history import (
    load_history,
    load_current,
    add_or_update_quarter,
    get_current_quarter,
    save_history,
)
from app.infection_control.cauti.cauti_targets import CAUTI_TARGETS
from app.infection_control.ic_statistics import InfectionControlStatistics

router = APIRouter(prefix="/api/cauti", tags=["CAUTI"])

TEMP_DIR = Path("storage/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

_stats = InfectionControlStatistics("cauti")


@router.post("/process-data")
async def process_data(
    file: UploadFile = File(...),
    year: int = Form(...),
    quarter: int = Form(...),
    denominators: str = Form(...),  # JSON: {"ICU": 200, "CCU": 150, ...}
):
    """Process uploaded CAUTI Excel sheet and save to history."""
    tmp_path = TEMP_DIR / f"cauti_{uuid4()}.xlsx"
    try:
        contents = await file.read()
        tmp_path.write_bytes(contents)

        denominators_dict: dict = json.loads(denominators)
        denominators_dict = {k: int(v) for k, v in denominators_dict.items()}

        result = process_cauti_excel(str(tmp_path), int(year), int(quarter), denominators_dict)
        cases  = result["cases"]

        all_stats = _stats.calculate_all_statistics(
            cases=cases,
            floor_device_days=denominators_dict,
            quarter=int(quarter),
            year=int(year),
        )

        record = {
            "year":               int(year),
            "quarter":            int(quarter),
            "summary":            all_stats["summary"],
            "cases":              cases,
            "germs_distribution": all_stats["germs_distribution"],
        }

        add_or_update_quarter(record)

        return JSONResponse(content={
            "status":      "success",
            "message":     "CAUTI data processed and saved successfully",
            "year":        int(year),
            "quarter":     int(quarter),
            "total_cases": all_stats["total_cases"],
        })

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid denominators JSON format")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.get("/history")
def get_history():
    return load_history()


@router.get("/history/latest")
def get_latest():
    latest = get_current_quarter()
    if latest is None:
        raise HTTPException(status_code=404, detail="No CAUTI data available")
    return latest


@router.get("/current")
def get_current():
    """Return the current quarter's raw case data."""
    return load_current()


@router.get("/targets")
def get_targets():
    return CAUTI_TARGETS


@router.post("/generate-report")
def generate_report():
    """Generate a DOCX CAUTI report from history + current quarter data."""
    history = load_history()
    if not history:
        raise HTTPException(status_code=404, detail="No CAUTI data available")
    try:
        from app.infection_control.cauti.docx_generator import CAUTIDocxGenerator
        current = load_current()
        gen     = CAUTIDocxGenerator()
        result  = gen.generate_report(history=history, targets=CAUTI_TARGETS, current=current)
        return {"success": True, "filePath": result["filePath"], "fileName": result["fileName"]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/download-report")
def download_report(fileName: str):
    """Download a generated CAUTI DOCX report by filename."""
    safe_name   = os.path.basename(fileName)
    reports_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'storage', 'reports')
    )
    file_path = os.path.join(reports_dir, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Report not found: {safe_name}")
    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.delete("/history/{year}/{quarter}")
def delete_quarter(year: int, quarter: int):
    history = load_history()
    filtered = [r for r in history if not (r["year"] == year and r["quarter"] == quarter)]
    if len(filtered) == len(history):
        raise HTTPException(status_code=404, detail="Quarter not found")
    save_history(filtered)
    return {"status": "deleted", "year": year, "quarter": quarter}

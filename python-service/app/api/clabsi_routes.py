"""
CLABSI API Routes
"""

import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.clabsi.clabsi_processor import process_clabsi_excel
from app.clabsi.clabsi_history import (
    load_history,
    add_or_update_quarter,
    get_current_quarter,
)

router = APIRouter(prefix="/api/clabsi", tags=["CLABSI"])

TEMP_DIR = Path("storage/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _build_germs_distribution(cases: list) -> dict:
    """Build per-department germ counts from raw case rows."""
    distribution: dict = {}
    for case in cases:
        dept = case.get("Floor")
        germ = case.get("Germs")
        if not dept or not germ:
            continue
        n = int(case.get("Nb of cases") or 1)
        distribution.setdefault(dept, {})
        distribution[dept][germ] = distribution[dept].get(germ, 0) + n
    return distribution


@router.post("/process-data")
async def process_data(
    file: UploadFile = File(...),
    year: int = Form(...),
    quarter: int = Form(...),
    denominators: str = Form(...),   # JSON string: {"ICU": 200, "CCU": 100, ...}
):
    """Process uploaded CLABSI Excel file and save to history."""
    tmp_path = TEMP_DIR / f"clabsi_{uuid4()}.xlsx"

    try:
        contents = await file.read()
        tmp_path.write_bytes(contents)

        denominators_dict: dict = json.loads(denominators)
        # Ensure values are numeric
        denominators_dict = {k: int(v) for k, v in denominators_dict.items()}

        result = process_clabsi_excel(
            str(tmp_path), int(year), int(quarter), denominators_dict
        )

        germs_distribution = _build_germs_distribution(result["cases"])

        record = {
            "year": int(year),
            "quarter": int(quarter),
            "summary": result["summary"],
            "cases": result["cases"],
            "germs_distribution": germs_distribution,
        }

        add_or_update_quarter(record)

        return JSONResponse(
            content={
                "status": "success",
                "message": "CLABSI data processed and saved successfully",
                "year": int(year),
                "quarter": int(quarter),
                "total_cases": sum(
                    v.get("cases", 0) for v in result["summary"].values()
                ),
            }
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid denominators JSON format")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.get("/history")
def get_history():
    """Return all quarters sorted chronologically."""
    return load_history()


@router.get("/history/latest")
def get_latest():
    """Return the most recent quarter."""
    latest = get_current_quarter()
    if latest is None:
        raise HTTPException(status_code=404, detail="No CLABSI data available")
    return latest


@router.delete("/history/{year}/{quarter}")
def delete_quarter(year: int, quarter: int):
    """Delete a specific quarter from history."""
    history = load_history()
    filtered = [
        r for r in history
        if not (r["year"] == year and r["quarter"] == quarter)
    ]
    if len(filtered) == len(history):
        raise HTTPException(status_code=404, detail="Quarter not found")

    from app.clabsi.clabsi_history import save_history
    save_history(filtered)
    return {"status": "deleted", "year": year, "quarter": quarter}

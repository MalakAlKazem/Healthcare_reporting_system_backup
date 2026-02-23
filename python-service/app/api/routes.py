"""
FastAPI Routes - API endpoints for data processing
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from loguru import logger
import os
import shutil
import pandas as pd

import numpy as np

from app.core.data_processor import data_processor
from app.core.statistics import statistics_calculator
from app.core.excel_handler import excel_handler
from app.core.history_manager import history_manager
from app.services.docx_generator import matplotlib_docx_generator

router = APIRouter()


def convert_numpy(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif obj is np.nan or (isinstance(obj, float) and np.isnan(obj)):
        return None
    return obj


@router.post("/process-data")
async def process_mortality_data(
    file: UploadFile = File(...),
    quarter: str = Form(...),
    year: str = Form(...),
    total_patients: int = Form(...)
):
    """
    Process uploaded Excel mortality file (first sheet only).

    Args:
        file: Excel file upload (.xlsx or .xls)
        quarter: Quarter name (e.g., "الفصل الثالث")
        year: Year (e.g., "2025")
        total_patients: Total hospital admissions this quarter

    Returns:
        Processed data with statistics
    """
    temp_path = None

    try:
        logger.info(f"📤 Received file: {file.filename}")
        logger.info(f"📊 Total patients: {total_patients}")

        # Validate file extension
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(400, "Invalid file type. Upload .xlsx, .xls, or .csv")

        # Save uploaded file temporarily
        os.makedirs("../storage/temp", exist_ok=True)
        temp_path = f"../storage/temp/{file.filename}"

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"💾 Saved to: {temp_path}")

        # 1. Parse file (Excel or CSV)
        if file.filename.endswith('.csv'):
            df = pd.read_csv(temp_path)
            who_summary = None
        else:
            df, who_summary, _ = excel_handler.parse_excel(temp_path)
        logger.info(f"📋 Parsed: {len(df)} records")

        # 2. Clean data (auto-detects CSV vs Excel)
        df_cleaned = data_processor.clean_data(df)
        logger.info(f"🧹 Cleaned: {len(df_cleaned)} valid records")

        # 3. Build admission data from the data itself (building column)
        admission_data = None
        if 'building' in df_cleaned.columns:
            bci_deaths = len(df_cleaned[df_cleaned['building'].str.contains('BCI', case=False, na=False)])
            # Fallback: classify cardiac departments as BCI
            if bci_deaths == 0 and 'nursing_department' in df_cleaned.columns:
                cardiac_depts = ['ICVU', 'CSU', 'CCU', 'ITCU', 'Cardiac', 'ICN']
                bci_deaths = len(df_cleaned[df_cleaned['nursing_department'].str.contains(
                    '|'.join(cardiac_depts), case=False, na=False
                )])
            rah_deaths = len(df_cleaned) - bci_deaths

            admission_data = {
                'bci': {
                    'building': 'BCI',
                    'deaths': bci_deaths,
                    'percentage': round((bci_deaths / len(df_cleaned)) * 100, 1) if len(df_cleaned) > 0 else 0
                },
                'rah': {
                    'building': 'RAH',
                    'deaths': rah_deaths,
                    'percentage': round((rah_deaths / len(df_cleaned)) * 100, 1) if len(df_cleaned) > 0 else 0
                },
                'total': {
                    'deaths': len(df_cleaned),
                    'admissions': total_patients
                }
            }

        # 4. Calculate WHO categories from main data if not from sheet
        if who_summary is None and 'who_category_1' in df_cleaned.columns:
            who_counts = df_cleaned['who_category_1'].dropna().value_counts()
            who_summary = [
                {'category': str(cat).strip(), 'count': int(cnt)}
                for cat, cnt in who_counts.items()
                if str(cat).strip() and str(cat).strip() != 'nan'
            ]
            logger.info(f"📊 WHO categories from main data: {len(who_summary)} categories")

        # 5. Calculate statistics
        stats = statistics_calculator.calculate_all_statistics(
            df_cleaned,
            total_patients=total_patients,
            admission_data=admission_data
        )

        # 6. Get validation report
        validation = data_processor.get_validation_report()

        # 7. Convert DataFrame to records (replace NaN/NaT with None for JSON)
        df_json = df_cleaned.replace({np.nan: None, pd.NaT: None})
        # Convert Timestamp objects to strings
        for col in df_json.select_dtypes(include=['datetime64']).columns:
            df_json[col] = df_json[col].astype(str).replace('NaT', None)
        records = df_json.to_dict('records')

        # 8. Build age_groups array (8 categories) for history (KPI=YES, from age_categories)
        age_group_order = [
            'اقل من 5 سنوات', 'من 5 الى 15 سنة', 'من 16 الى 30 سنة',
            'من 31 الى 50 سنة', 'من 51 الى 60 سنة', 'من 61 الى 70 سنة',
            'من 71 الى 80 سنة', 'اكثر من 81 سنة'
        ]
        # Prefer age_categories (from تصنيف العمر, KPI=YES) over age_groups
        age_cats = stats.get('demographics', {}).get('age_categories', [])
        if age_cats:
            age_groups_dict = {ag['group']: ag['count'] for ag in age_cats}
        else:
            age_groups_dict = {ag['group']: ag['count'] for ag in stats.get('demographics', {}).get('age_groups', [])}
        age_groups_array = [age_groups_dict.get(g, 0) for g in age_group_order]

        # 9. Build departments dict for history (KPI=YES)
        departments_dict = {d['name']: d['count'] for d in stats.get('departments', [])}

        # 10. Build WHO categories dict for history (KPI=YES, from تصنيف who category 1)
        who_dict = stats.get('who_categories_kpi', {})
        if not who_dict and who_summary:
            who_dict = {w['category']: w['count'] for w in who_summary}

        # 11. Get mortality rate from statistics (KPI deaths / total patients)
        kpi_deaths = stats.get('kpi_deaths', len(df_cleaned))
        mortality_rate = stats.get('mortality_metrics', {}).get('rate', 0.0)

        # 12. Save to history
        history_manager.save_quarter(
            quarter=quarter,
            year=year,
            rate=mortality_rate,
            deaths=kpi_deaths,
            total_patients=total_patients or 0,
            age_groups=age_groups_array,
            departments=departments_dict,
            who_categories=who_dict
        )

        logger.success(f"✅ Processing complete: {len(records)} records, saved to history")

        return convert_numpy({
            "success": True,
            "data": {
                "records": records,
                "total_records": len(records),
                "statistics": stats,
                "who_categories": who_summary,
                "validation": validation,
                "quarter": quarter,
                "year": year
            }
        })
    
    except Exception as e:
        logger.error(f"❌ Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"🗑️  Cleaned up: {temp_path}")
            except:
                pass


@router.post("/generate-report")
async def generate_report(request: dict):
    """
    Generate DOCX report from processed data.

    Args (JSON body):
        data: dict with 'statistics' and optionally 'who_categories'
        quarter: str (e.g., "الفصل الثالث")
        year: str (e.g., "2025")

    Returns:
        File path and name for the generated report
    """
    try:
        data = request.get('data', {})
        quarter = request.get('quarter', 'الفصل الثالث')
        year = request.get('year', '2025')

        if not data or not data.get('statistics'):
            raise HTTPException(400, "No statistics data provided")

        # Load all history excluding current quarter
        # get_last_n_quarters returns newest-first, reverse for charts (oldest-first)
        history = history_manager.get_last_n_quarters(100, quarter, year)
        history = list(reversed(history))

        logger.info(f"Generating report for {quarter} {year}")

        result = await matplotlib_docx_generator.generate_report(
            data,
            history=history,
            options={'quarter': quarter, 'year': year}
        )

        logger.success(f"Report generated: {result['fileName']}")

        return {
            "success": True,
            "filePath": result['filePath'],
            "fileName": result['fileName']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-report")
async def download_report(fileName: str):
    """
    Download a generated DOCX report by filename.

    Args:
        fileName: The report filename (e.g., "mortality_report_الفصل الثالث_2025_123456.docx")

    Returns:
        The DOCX file as a downloadable attachment
    """
    # Sanitize: prevent path traversal
    safe_name = os.path.basename(fileName)
    # Shared storage directory (same as Node backend)
    # __file__ is in python-service/app/api/ -> go up 3 levels to project root
    reports_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'storage', 'reports'))
    file_path = os.path.join(reports_dir, safe_name)

    if not os.path.exists(file_path):
        raise HTTPException(404, f"Report not found: {safe_name}")

    return FileResponse(
        path=file_path,
        filename=safe_name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "status": "ok",
        "service": "python-data-processor",
        "phase": "1 - AI Disabled"
    }
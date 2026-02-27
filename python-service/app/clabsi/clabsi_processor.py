import pandas as pd
import numpy as np
from datetime import datetime

def clean_columns(df):
    df.columns = df.columns.str.strip()
    return df


def preprocess_dates(df):
    df["Date of insertion Central line"] = pd.to_datetime(
        df["Date of insertion Central line"], errors="coerce"
    )
    df["Date of infection"] = pd.to_datetime(
        df["Date of infection"], errors="coerce"
    )
    return df


def calculate_catheter_days(df):
    df["calculated_catheter_days"] = (
        df["Date of infection"] - df["Date of insertion Central line"]
    ).dt.days

    # Remove invalid rows
    df = df[df["calculated_catheter_days"] > 0]

    return df


def process_clabsi_excel(file_path: str, year: int, quarter: int, denominators: dict):

    df = pd.read_excel(file_path)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Convert date columns safely
    date_columns = [
        "Date of admission",
        "Date of insertion Central line",
        "Date of infection"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    cases = []

    for _, row in df.iterrows():

        case = {}

        for col in df.columns:

            value = row[col]

            # Handle dates
            if isinstance(value, pd.Timestamp):
                case[col] = value.strftime("%Y-%m-%d")

            # Handle NaN
            elif pd.isna(value):
                case[col] = None

            # Handle numpy types
            elif isinstance(value, (np.integer, np.int64)):
                case[col] = int(value)

            elif isinstance(value, (np.floating, np.float64)):
                case[col] = float(value)

            else:
                case[col] = str(value).strip()

        # Add calculated catheter duration (optional advanced metric)
        if (
            pd.notna(row.get("Date of insertion Central line")) and
            pd.notna(row.get("Date of infection"))
        ):
            case["Calculated catheter duration"] = (
                row["Date of infection"] -
                row["Date of insertion Central line"]
            ).days
        else:
            case["Calculated catheter duration"] = None

        cases.append(case)
    summary = {}

    # IMPORTANT: ensure numeric
    df["Nb of cases"] = pd.to_numeric(df["Nb of cases"], errors="coerce").fillna(0)

    for dept, catheter_days in denominators.items():

        # Sum the actual number of cases, NOT count rows
        dept_total_cases = (
            df[df["Floor"] == dept]["Nb of cases"].sum()
        )

        rate = (
            round((dept_total_cases / catheter_days) * 1000, 2)
            if catheter_days > 0 else 0
        )

        summary[dept] = {
            "cases": int(dept_total_cases),
            "catheter_days": catheter_days,
            "rate": rate
        }

    return {
        "year": year,
        "quarter": quarter,
        "denominators": denominators,
        "cases": cases,
        "summary": summary
    }
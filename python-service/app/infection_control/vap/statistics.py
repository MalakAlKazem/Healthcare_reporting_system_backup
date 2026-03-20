"""
VAP (Ventilator-Associated Pneumonia) Statistics Calculator

FIXES applied:
  1. Fixed import path: 'from infection_control.VAP.vap_history import ...'
     → 'from app.infection_control.VAP.vap_history import ...'
     (the old path caused ModuleNotFoundError when running from python-service/)
  2. Wrapped the arabic-quarter import in a proper try/except so it degrades
     gracefully if vap_history is unavailable.
"""

from typing import Dict, List, Optional


# ─── Standard floors & targets (per 1,000 ventilator-days) ──────────────────
STANDARD_FLOORS = ["ICU", "CCU", "CSU", "Ped", "ICN", "ITU", "Neonatal"]

FLOOR_TARGETS = {
    "ICU":      25.0,
    "CCU":      15.0,
    "CSU":       9.5,
    "Ped":       5.5,
    "ICN":      10.0,
    "ITU":      25.0,
    "Neonatal":  0.0,
}

RISK_FACTOR_COLS = [
    "diabetic", "hypertension", "dyslipidemia", "heart_disease",
    "kidney_disease", "copd", "smoker", "obesity",
    "cardiac_congenital_malformation", "advanced_age",
    "cancer", "compromised_immune_system", "respiratory_pb",
]

RISK_FACTOR_LABELS = {
    "diabetic":                        "Diabetic",
    "hypertension":                    "Hypertension",
    "dyslipidemia":                    "Dyslipidemia",
    "heart_disease":                   "Heart Disease",
    "kidney_disease":                  "Kidney Disease",
    "copd":                            "COPD",
    "smoker":                          "Smoker",
    "obesity":                         "Obesity",
    "cardiac_congenital_malformation": "Cardiac Congenital Malformation",
    "advanced_age":                    "Advanced Age",
    "cancer":                          "Cancer",
    "compromised_immune_system":       "Compromised Immune System",
    "respiratory_pb":                  "Respiratory Problem",
}


class VAPStatistics:
    """Calculate all VAP statistics needed for charts, tables and history."""

    def __init__(self):
        self.stats: Dict = {}

    # =========================================================================
    # PUBLIC ENTRY POINT
    # =========================================================================

    def calculate_all_statistics(
        self,
        processed_result: Dict,
        floor_ventilator_days: Dict[str, int],
        quarter: str,
        year: int,
    ) -> Dict:
        """
        Calculate complete statistics for one VAP quarter.

        Parameters
        ----------
        processed_result      : output of vap_processor.process_vap_sheet()
        floor_ventilator_days : { "ICU": 650, "CCU": 254, ... }
        quarter               : e.g. "Fourth"  (English or Arabic)
        year                  : e.g. 2025
        """
        cases       = processed_result["cases"]
        total_cases = processed_result["meta"]["total_cases"]

        floor_stats    = self._calculate_floor_stats(cases, floor_ventilator_days)
        total_vent_days = sum(floor_ventilator_days.values())
        overall_rate   = round((total_cases / total_vent_days) * 1000, 2) if total_vent_days > 0 else 0.0

        germs_overall  = self._calculate_germs(cases)
        germs_by_floor = {
            floor: self._calculate_germs([c for c in cases if _match_floor(c["floor"], floor)])
            for floor in STANDARD_FLOORS
        }

        icu_cases_table = self._build_floor_cases_table(cases, "ICU")
        ccu_cases_table = self._build_floor_cases_table(cases, "CCU")
        icn_cases_table = self._build_floor_cases_table(cases, "ICN", icn_style=True)

        risk_factors  = self._calculate_risk_factors(cases)
        diagnoses     = processed_result["diagnoses"]
        monthly_trend = processed_result["monthly_trend"]
        age_groups    = processed_result["age_groups"]
        genders       = processed_result["genders"]

        # FIX 1: Correct import path (was 'from infection_control.VAP...')
        ar_quarter = quarter
        try:
            from app.infection_control.VAP.vap_history import _to_arabic_quarter
            ar_quarter = _to_arabic_quarter(quarter)
        except Exception:
            # Graceful fallback — use whatever was passed in
            pass

        stats = {
            "summary": {
                "quarter":         ar_quarter,
                "year":            year,
                "total_cases":     total_cases,
                "total_vent_days": total_vent_days,
                "overall_rate":    overall_rate,
            },
            "floor_stats":     floor_stats,
            "germs_overall":   germs_overall,
            "germs_by_floor":  germs_by_floor,
            "icu_cases_table": icu_cases_table,
            "ccu_cases_table": ccu_cases_table,
            "icn_cases_table": icn_cases_table,
            "risk_factors":    risk_factors,
            "diagnoses":       diagnoses,
            "monthly_trend":   monthly_trend,
            "age_groups":      age_groups,
            "genders":         genders,
        }

        self.stats = stats
        return stats

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    def _calculate_floor_stats(
        self,
        cases: List[Dict],
        floor_ventilator_days: Dict[str, int],
    ) -> Dict[str, Dict]:
        total_cases = len(cases)
        result = {}
        for floor in STANDARD_FLOORS:
            floor_cases = [c for c in cases if _match_floor(c["floor"], floor)]
            n_cases   = len(floor_cases)
            vent_days = floor_ventilator_days.get(floor, 0)
            rate = round((n_cases / vent_days) * 1000, 2) if vent_days > 0 else 0.0
            pct  = round((n_cases / total_cases) * 100, 1) if total_cases > 0 else 0.0
            result[floor] = {
                "cases":           n_cases,
                "ventilator_days": vent_days,
                "rate":            rate,
                "target":          FLOOR_TARGETS[floor],
                "pct_of_total":    pct,
            }
        return result

    def _calculate_germs(self, cases: List[Dict]) -> Dict:
        counts: Dict[str, int] = {}
        for c in cases:
            g = (c.get("germs") or "Unknown").strip()
            counts[g] = counts.get(g, 0) + 1
        total  = sum(counts.values())
        counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        return {
            "counts":      counts,
            "percentages": {k: round(v / total * 100, 1) for k, v in counts.items()} if total else {},
            "total":       total,
        }

    def _calculate_risk_factors(self, cases: List[Dict]) -> Dict:
        total  = len(cases)
        counts: Dict[str, int] = {}
        for col in RISK_FACTOR_COLS:
            label = RISK_FACTOR_LABELS[col]
            counts[label] = sum(1 for c in cases if c.get(col) is True)
        counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
        return {
            "counts":      counts,
            "percentages": {k: round(v / total * 100, 1) for k, v in counts.items()} if total else {},
            "total":       total,
        }

    def _build_floor_cases_table(
        self, cases: List[Dict], floor: str, icn_style: bool = False
    ) -> List[Dict]:
        floor_cases = [c for c in cases if _match_floor(c.get("floor"), floor)]
        rows = []
        for c in floor_cases:
            active_rf = [
                RISK_FACTOR_LABELS[col]
                for col in RISK_FACTOR_COLS
                if c.get(col) is True
            ]

            age_raw = c.get("age")
            if age_raw is None:
                age_display = "N/A"
            elif age_raw < 1 and age_raw > 0:
                months = round(age_raw * 12)
                age_display = f"{months}M" if months >= 1 else f"{round(age_raw * 365)}D"
            else:
                age_display = f"{int(age_raw)}Y"

            rf_parts = list(active_rf)
            if icn_style and c.get("duration_of_ventilation") is not None:
                rf_parts.append(f"Duration of ventilation: {c['duration_of_ventilation']}d")
            rf_display = ", ".join(rf_parts) if rf_parts else "None"

            rows.append({
                "case_number":                  c.get("case_number", "—"),
                "nb_of_cases":                  c.get("nb_of_cases"),
                "age":                          age_display,
                "diagnosis":                    c.get("diagnosis", "—"),
                "date_of_admission":            c.get("date_of_admission", "—"),
                "date_of_intubation":           c.get("date_of_intubation", "—"),
                "date_of_infection":            c.get("date_of_infection", "—"),
                "germs":                        c.get("germs", "—"),
                "risk_factors":                 rf_display,
                "length_of_stay":               c.get("length_of_stay"),
                "duration_of_ventilation":      c.get("duration_of_ventilation"),
                "intubation_to_infection_days": c.get("intubation_to_infection_days"),
            })
        return rows


# ─── Floor name matcher ───────────────────────────────────────────────────────

def _match_floor(floor_value: Optional[str], standard: str) -> bool:
    if not floor_value:
        return False
    v = str(floor_value).strip().upper()
    s = standard.strip().upper()
    aliases = {
        "ICU":  {"ICU", "INTENSIVE CARE UNIT", "MICU", "SICU", "TICU"},
        "CCU":  {"CCU", "CARDIAC CARE UNIT", "CORONARY CARE UNIT"},
        "CSU":  {"CSU", "CARDIAC SURGERY UNIT", "CARDIAC STEP DOWN"},
        "PED":  {"PED", "PEDS", "PEDIATRIC", "PAEDIATRIC", "PEDIATRICS"},
        "ICN":  {"ICN", "INFANT CARE NURSERY", "NICU", "NEONATAL ICU"},
        "ITU":  {"ITU", "INTENSIVE THERAPY UNIT"},
    }
    return v in aliases.get(s, {s})
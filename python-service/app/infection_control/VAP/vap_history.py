"""
VAP Historical Data Manager
Stores per-quarter, per-floor VAP statistics in VAP_history.json.
Mirrors MedicationErrorHistory pattern.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from app.infection_control.VAP.vap_statistics import STANDARD_FLOORS, FLOOR_TARGETS


# Map English/numeric quarter input → Arabic display name stored in JSON
QUARTER_AR = {
    # English (any case handled by _to_arabic_quarter lowercasing)
    "first":          "الفصل الأول",
    "second":         "الفصل الثاني",
    "third":          "الفصل الثالث",
    "fourth":         "الفصل الرابع",
    "1":              "الفصل الأول",
    "2":              "الفصل الثاني",
    "3":              "الفصل الثالث",
    "4":              "الفصل الرابع",
    # Already-Arabic passthrough
    "الفصل الأول":   "الفصل الأول",
    "الفصل الثاني":  "الفصل الثاني",
    "الفصل الثالث":  "الفصل الثالث",
    "الفصل الرابع":  "الفصل الرابع",
    "الاول":          "الفصل الأول",
    "الأول":          "الفصل الأول",
    "الثاني":         "الفصل الثاني",
    "الثالث":         "الفصل الثالث",
    "الرابع":         "الفصل الرابع",
}

# Sort order by Arabic name
QUARTER_ORDER = {
    "الفصل الأول":  1,
    "الفصل الثاني": 2,
    "الفصل الثالث": 3,
    "الفصل الرابع": 4,
}


def _to_arabic_quarter(quarter: str) -> str:
    """Normalise any quarter input → Arabic display name (case-insensitive)."""
    q = str(quarter).strip()
    # Try exact match first, then lowercase
    return QUARTER_AR.get(q) or QUARTER_AR.get(q.lower()) or q


def _quarter_sort_key(entry: Dict):
    year = int(entry.get("year", 0))
    q    = str(entry.get("quarter", "")).strip()
    return (year, QUARTER_ORDER.get(q, 99))


class VAPHistory:
    """Manage VAP historical data across quarters."""

    def __init__(self, storage_path: str = "storage/data/VAP_history.json"):
        self.storage_path = Path(storage_path)
        self.history: List[Dict] = []
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_history()

    # ── Persistence ──────────────────────────────────────────────────────────

    def load_history(self) -> List[Dict]:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
                logger.info(f"📂 Loaded {len(self.history)} VAP historical quarters")
            except Exception as e:
                logger.error(f"❌ Error loading VAP history: {e}")
                self.history = []
        else:
            logger.info("📝 No existing VAP history — starting fresh")
            self.history = []
        return self.history

    def _save(self) -> bool:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.success(f"✅ Saved {len(self.history)} VAP quarters → {self.storage_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving VAP history: {e}")
            return False

    # ── Write ─────────────────────────────────────────────────────────────────

    def save_quarter(self, quarter: str, year: int, stats: Dict) -> bool:
        """
        Save (or update) one quarter's VAP data to history.

        Stored fields per quarter
        ─────────────────────────
        quarter, year
        overall_rate, total_cases, total_vent_days

        floors: {
          ICU: { cases, ventilator_days, rate, target },
          CCU: { ... },
          ...
        }

        germs_by_floor: {
          ICU: { counts: {germ: n}, percentages: {germ: %}, total: n },
          ...
        }
        germs_overall:  { counts, percentages, total }
        """
        ar_quarter = _to_arabic_quarter(quarter)
        logger.info(f"💾 Saving VAP quarter: {ar_quarter} {year}")

        summary     = stats.get("summary", {})
        floor_stats = stats.get("floor_stats", {})

        # Strip germs_by_floor of empty floors to keep JSON clean
        germs_by_floor_clean = {
            floor: data
            for floor, data in stats.get("germs_by_floor", {}).items()
            if data.get("total", 0) > 0
        }

        # Build compact entry matching the exact JSON schema
        entry = {
            "quarter":         ar_quarter,
            "year":            str(year),
            "total_cases":     summary.get("total_cases", 0),
            "total_vent_days": summary.get("total_vent_days", 0),
            # Per-floor: cases, ventilator_days, rate, target (no pct_of_total)
            "floors": {
                floor: {
                    "cases":           floor_stats.get(floor, {}).get("cases", 0),
                    "ventilator_days": floor_stats.get(floor, {}).get("ventilator_days", 0),
                    "rate":            floor_stats.get(floor, {}).get("rate", 0.0),
                    "target":          FLOOR_TARGETS.get(floor, 0.0),
                }
                for floor in STANDARD_FLOORS
            },
            # Germs stored for chart comparison across quarters
            "germs_overall":  stats.get("germs_overall", {}),
            "germs_by_floor": germs_by_floor_clean,
        }

        # Upsert — match on Arabic quarter name
        existing_idx = next(
            (i for i, e in enumerate(self.history)
             if e["quarter"] == ar_quarter and e["year"] == str(year)),
            None,
        )
        if existing_idx is not None:
            self.history[existing_idx] = entry
            logger.info(f"✏️  Updated {ar_quarter} {year}")
        else:
            self.history.append(entry)
            logger.info(f"➕ Added {ar_quarter} {year}")

        self.history.sort(key=_quarter_sort_key)
        return self._save()

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_last_n_quarters(self, n: int = 5) -> List[Dict]:
        """Return last N quarters (oldest → newest) for trend charts."""
        return self.history[-n:] if len(self.history) >= n else self.history

    def get_quarter(self, quarter: str, year: int) -> Optional[Dict]:
        for e in self.history:
            if e["quarter"] == quarter and e["year"] == str(year):
                return e
        return None

    def get_all(self) -> List[Dict]:
        return self.history

    # ── Derived helpers for chart data ────────────────────────────────────────

    def get_floor_trend(self, floor: str, n: int = 5) -> List[Dict]:
        """
        Return last N quarters with stats for a specific floor.
        Used by Chart 1 (ICU VAP rate trend).

        Each item: { quarter, year, cases, ventilator_days, rate, target }
        """
        result = []
        for entry in self.history[-n:]:
            f = entry.get("floors", {}).get(floor, {})
            result.append({
                "quarter":         entry["quarter"],
                "year":            entry["year"],
                "cases":           f.get("cases", 0),
                "ventilator_days": f.get("ventilator_days", 0),
                "rate":            f.get("rate", 0.0),
                "target":          FLOOR_TARGETS.get(floor, 0.0),
            })
        return result

    def get_floor_germs_comparison(self, floor: str) -> Dict:
        """
        Return germ comparison data for the last 2 quarters that have cases
        for a specific floor (used by Chart 2 / Chart 4).

        The returned structure has a unified `germs` list that is the
        union of all germs appearing in either quarter, sorted by current-
        quarter count descending (then alphabetically), so bar charts can
        render every germ with zero-filled values where missing.

        Returns
        -------
        {
          current: {
            quarter, year, total,
            counts:      { germ: n },          # 0 if germ absent this quarter
            percentages: { germ: pct },        # 0.0 if absent
            labels:      { germ: "25%(1)" },   # display label for bar
          },
          previous: { same structure } | None,
          germs:    [ "germ1", "germ2", ... ]  # unified sorted list
        }
        """
        # Take all quarters that have at least 1 case for this floor
        quarters_with_data = [
            e for e in self.history
            if e.get("germs_by_floor", {}).get(floor, {}).get("total", 0) > 0
        ]

        if not quarters_with_data:
            return {"current": None, "previous": None, "germs": []}

        def _raw(entry):
            gbd = entry.get("germs_by_floor", {}).get(floor, {})
            return {
                "quarter":     entry["quarter"],
                "year":        entry["year"],
                "total":       gbd.get("total", 0),
                "counts":      gbd.get("counts", {}),
                "percentages": gbd.get("percentages", {}),
            }

        cur_raw  = _raw(quarters_with_data[-1])
        prev_raw = _raw(quarters_with_data[-2]) if len(quarters_with_data) >= 2 else None

        # Build unified germ list: union of both quarters
        all_germs = set(cur_raw["counts"].keys())
        if prev_raw:
            all_germs |= set(prev_raw["counts"].keys())

        # Sort: by current-quarter count desc, then alphabetically
        all_germs_sorted = sorted(
            all_germs,
            key=lambda g: (-cur_raw["counts"].get(g, 0), g)
        )

        def _fill(raw, germs_list):
            """Fill missing germs with 0 and build display labels."""
            total = raw["total"]
            counts = {}
            percentages = {}
            labels = {}
            for g in germs_list:
                n   = raw["counts"].get(g, 0)
                pct = round(n / total * 100, 0) if total > 0 else 0.0
                counts[g]      = n
                percentages[g] = pct
                labels[g]      = f"{int(pct)}%({n})" if n > 0 else "0%(0)"
            return {
                "quarter":     raw["quarter"],
                "year":        raw["year"],
                "total":       total,
                "counts":      counts,
                "percentages": percentages,
                "labels":      labels,
            }

        current  = _fill(cur_raw, all_germs_sorted)
        previous = _fill(prev_raw, all_germs_sorted) if prev_raw else None

        return {
            "current":  current,
            "previous": previous,
            "germs":    all_germs_sorted,
        }

    def get_chart_data(self) -> Dict:
        """
        Return all 4 chart datasets in a single call.

        Chart 1 — ICU VAP rate trend (last 5 quarters)
        Chart 2 — ICU germs: current quarter vs previous quarter
        Chart 3 — CCU VAP rate trend (last 4 quarters)
        Chart 4 — CCU germs: current quarter vs previous quarter

        Each chart key maps directly to the data structure needed
        by the chart renderer — no further transformation required.
        """
        return {
            "chart1_icu_trend":      self.get_floor_trend("ICU", n=5),
            "chart2_icu_germs":      self.get_floor_germs_comparison("ICU"),
            "chart3_ccu_trend":      self.get_floor_trend("CCU", n=5),
            "chart4_ccu_germs":      self.get_floor_germs_comparison("CCU"),
            "chart5_icn_trend":      self.get_floor_trend("ICN", n=5),
            "chart6_icn_germs":      self.get_floor_germs_comparison("ICN"),
        }

    def get_quarter_floor_comparison_table(self, n: int = 5) -> Dict:
        """
        Build the full multi-floor comparison table (Table 1 in the report).

        Returns:
            quarters : list of "Quarter Year" labels (oldest → newest)
            floors   : list of floor names
            targets  : { floor: target }
            data     : {
                floor: [
                    { quarter, year, cases, ventilator_days, rate },
                    ...   (one entry per quarter, in same order as `quarters`)
                ]
            }
        """
        recent = self.history[-n:] if len(self.history) >= n else self.history
        quarter_labels = [f"{e['quarter']} {e['year']}" for e in recent]

        data: Dict[str, List[Dict]] = {floor: [] for floor in STANDARD_FLOORS}

        for entry in recent:
            for floor in STANDARD_FLOORS:
                f = entry.get("floors", {}).get(floor, {})
                data[floor].append({
                    "quarter":         entry["quarter"],
                    "year":            entry["year"],
                    "cases":           f.get("cases", 0),
                    "ventilator_days": f.get("ventilator_days", 0),
                    "rate":            f.get("rate", 0.0),
                })

        return {
            "quarters": quarter_labels,
            "floors":   STANDARD_FLOORS,
            "targets":  FLOOR_TARGETS,
            "data":     data,
        }
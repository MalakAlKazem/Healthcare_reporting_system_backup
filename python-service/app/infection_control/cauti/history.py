import json
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parents[3]
HISTORY_PATH = BASE_DIR / "storage" / "data" / "cauti_history.json"
CURRENT_PATH = BASE_DIR / "storage" / "data" / "cauti_current.json"

_QUARTER_TO_AR = {
    1: "الفصل الاول",
    2: "الفصل الثاني",
    3: "الفصل الثالث",
    4: "الفصل الرابع",
}
_QUARTER_TO_INT = {v: k for k, v in _QUARTER_TO_AR.items()}
# Also handle hamza variants from older data
_QUARTER_TO_INT["الفصل الأول"]  = 1
_QUARTER_TO_INT["الفصل الأولى"] = 1


def _quarter_str(q) -> str:
    """Convert int quarter to Arabic string. Pass-through if already a string."""
    if isinstance(q, int):
        return _QUARTER_TO_AR.get(q, str(q))
    return q


def _quarter_int(q) -> int:
    """Convert Arabic quarter string to int for sorting."""
    if isinstance(q, int):
        return q
    return _QUARTER_TO_INT.get(q, 0)


def load_history():
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def load_current():
    """Return the latest quarter's raw cases (germs_distribution is stored in history)."""
    if not CURRENT_PATH.exists():
        return {}
    with open(CURRENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_current(data: dict):
    """Overwrite the current-quarter file with raw cases only."""
    CURRENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CURRENT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sort_history(history):
    return sorted(history, key=lambda x: (int(x["year"]), _quarter_int(x["quarter"])))


def _deduplicate(history):
    """Keep the last occurrence of each (year, quarter) pair."""
    seen = {}
    for entry in history:
        key = (str(entry["year"]), _quarter_str(entry["quarter"]))
        seen[key] = entry  # overwrite → last upload wins
    return list(seen.values())


def add_or_update_quarter(new_record):
    """
    Save year (string), quarter (Arabic string), summary, and germs_distribution to history.
    Only raw cases are saved separately in cauti_current.json.
    """
    # Normalise year → string, quarter → Arabic string
    new_record["year"]    = str(new_record["year"])
    new_record["quarter"] = _quarter_str(new_record["quarter"])

    # Move cases to the current file only — germs stay in history for comparison
    current_data = {
        "year":    new_record["year"],
        "quarter": new_record["quarter"],
        "cases":   new_record.pop("cases", []),
    }
    save_current(current_data)

    history = load_history()
    updated = False
    for i, record in enumerate(history):
        if str(record["year"]) == new_record["year"] and _quarter_str(record["quarter"]) == new_record["quarter"]:
            history[i] = new_record
            updated = True
            break

    if not updated:
        history.append(new_record)

    history = sort_history(_deduplicate(history))
    save_history(history)
    return history


def get_current_quarter():
    history = sort_history(load_history())
    return history[-1] if history else None

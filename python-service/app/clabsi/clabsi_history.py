import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
HISTORY_PATH = BASE_DIR / "storage" / "data" / "clabsi_history.json"


def load_history():
    if not HISTORY_PATH.exists():
        return []

    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history):
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def sort_history(history):
    return sorted(history, key=lambda x: (x["year"], x["quarter"]))


def add_or_update_quarter(new_record):
    history = load_history()

    updated = False
    for i, record in enumerate(history):
        if record["year"] == new_record["year"] and record["quarter"] == new_record["quarter"]:
            history[i] = new_record
            updated = True
            break

    if not updated:
        history.append(new_record)

    history = sort_history(history)
    save_history(history)

    return history


def get_current_quarter():
    history = sort_history(load_history())
    return history[-1] if history else None
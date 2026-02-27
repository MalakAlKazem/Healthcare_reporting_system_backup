import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
TARGETS_PATH = BASE_DIR / "storage" / "data" / "clabsi_targets.json"


def get_all_targets():
    if not TARGETS_PATH.exists():
        return {}

    with open(TARGETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_target(department: str):
    targets = get_all_targets()
    return targets.get(department)
"""
CAUTI targets per 1000 urinary catheter days.
"""

CAUTI_TARGETS = {
    "ICU":      4.5,
    "CCU":      4.5,
    "CSU":      4.5,
    "Ped":      1.6,
    "ICN":      4.5,
    "3rd West": 4.8,
    "ITU":      4.5,
}

DEPARTMENTS = list(CAUTI_TARGETS.keys())

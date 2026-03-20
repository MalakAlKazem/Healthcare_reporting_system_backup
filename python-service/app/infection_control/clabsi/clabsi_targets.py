"""
CLABSI targets per 1,000 catheter days.
"""

CLABSI_TARGETS = {
    "ICU":       10.0,
    "CCU":        9.0,
    "CSU":        4.0,
    "ICN":       14.0,
    "Pediatric":  8.0,
    "ITU":       10.0,
}

DEPARTMENTS = list(CLABSI_TARGETS.keys())

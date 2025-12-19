from __future__ import annotations
from typing import Dict, List

def make_report(scenario: Dict, violations: List[Dict[str, str]]) -> Dict:
    """
    Build a report dict from a scenario and a list of violation records.

    Expected output shape:
      {
        "scenario": <str>,              # scenario name or "Unnamed" fallback
        "violations": <list[dict]>,     # as provided
        "total_violations": <int>       # len(violations)
      }

    """
    if scenario is None:
        report_name = "Unnamed"
    else:
        name = scenario.get("name")
        if not name or not str(name).strip():
            report_name = "Unnamed"
        else:
            report_name = str(name).strip()

    report = {
        "scenario": report_name,
        "violations": violations,
        "total_violations": len(violations)
    }

    return report

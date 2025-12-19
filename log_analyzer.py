#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# These modules are provided/implemented by students.
# Keep the import names but do NOT call them yet.
import parser as parser_mod          # TODO(student): implement load_scenario(), read_log()
import rules as rules_mod            # TODO(student): implement detect_violations()
import report as report_mod          # TODO(student): implement make_report()
import storage as storage_mod        # TODO(student): implement DB helpers


def main(argv: list[str] | None = None) -> int:
    """
    Incident Log Analyzer (starter)

    Modes:
      1) Summary mode:       --summary N --db DB.sqlite
      2) By-type query:      --by-type SCENARIO_ID TYPE --db DB.sqlite
      3) Analyze a run:      SCENARIO.json LOGFILE.txt [--db DB.sqlite]

    Students: follow the TODOs below to wire up parsing, rule checks, report
    generation, and optional database persistence.
    """
    argv = argv if argv is not None else sys.argv[1:]

    ap = argparse.ArgumentParser(description="Incident Log Analyzer (starter)")
    ap.add_argument("scenario", nargs="?", help="Path to scenario JSON")
    ap.add_argument("logfile", nargs="?", help="Path to event log")
    ap.add_argument("--db", help="Path to SQLite database for persistence")
    ap.add_argument("--summary", type=int, help="Print violation counts for the N most recent runs")
    ap.add_argument("--by-type", nargs=2, metavar=("SCENARIO_ID", "TYPE"),
                    help="List violations of a given TYPE for a scenario ID")
    args = ap.parse_args(argv)

    # ----- Summary mode -------------------------------------------------------
    if args.summary is not None:
        if not args.db:
            print("Error: --summary requires --db", file=sys.stderr)
            return 2

        storage_mod.init_db(args.db)
        data = storage_mod.get_violation_counts(args.summary)
        print(json.dumps(data, indent=2))
        return 0

    # ----- By-type mode -------------------------------------------------------
    if args.by_type is not None:
        if not args.db:
            print("Error: --by-type requires --db", file=sys.stderr)
            return 2

        # Inputs come in as strings; convert scenario id to int.
        sid_str, typ = args.by_type
        try:
            sid = int(sid_str)
        except ValueError:
            print("Error: SCENARIO_ID must be an integer", file=sys.stderr)
            return 2

        storage_mod.init_db(args.db)
        data = storage_mod.get_violations_by_type(sid, vtype)
        print(json.dumps(data, indent=2))
        return 0

    # ----- Analyze a scenario + log ------------------------------------------
    if not args.scenario or not args.logfile:
        ap.print_help()
        return 2

    scenario_path = Path(args.scenario)
    logfile_path = Path(args.logfile)

    # (Optional) basic existence checks — keep or remove per assignment needs.
    if not scenario_path.exists():
        print(f"Error: scenario file not found: {scenario_path}", file=sys.stderr)
        return 2
    if not logfile_path.exists():
        print(f"Error: log file not found: {logfile_path}", file=sys.stderr)
        return 2

    try:
        scenario = parser_mod.load_scenario(scenario_path)
        events = list(parser_mod.read_log(logfile_path))
    except Exception as e:
        print(f"Error loading scenario or log: {e}", file=sys.stderr)
        return 2

        # Detect violations and generate report
    violations = rules_mod.detect_violations(scenario, events)
    rep = report_mod.make_report(scenario, violations)

    # Write report.json
    with open("test_result/report.json", "w", encoding="utf-8") as f:
        json.dump(rep, f, indent=2)
    print("Report written to report.json")

    # Optional DB persistence
    if args.db:
        try:
            storage_mod.init_db(args.db)
            rid = storage_mod.upsert_ruleset(scenario["road_rules"])
            sid = storage_mod.register_scenario(
                scenario.get("name") or "Unnamed",
                scenario.get("description") or "",
                str(scenario_path),
                rid,
                scenario.get("speed_zones"),
            )
            storage_mod.save_report(sid, rep["violations"])
            print(f"Saved scenario and violations to DB: {args.db}")
        except Exception as e:
            print(f"Error saving to database: {e}", file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

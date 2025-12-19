from __future__ import annotations
import sqlite3
from typing import Dict, List, Any, Optional

_DB: Optional[sqlite3.Connection] = None


def _conn() -> sqlite3.Connection:
    """Internal: return the initialized DB connection."""
    assert _DB is not None, "DB not initialized"
    return _DB


def init_db(path: str) -> None:
    """
    Open (or create) the SQLite DB at `path`, enable foreign keys, and apply schema.sql.
    """
    global _DB
    _DB = sqlite3.connect(path)
    _DB.row_factory = sqlite3.Row
    cur = _DB.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    with open("schema.sql","r", encoding="utf-8") as f:
        _DB.executescript(f.read())
    _DB.commit()

def upsert_ruleset(rules: Dict[str, Any]) -> int:
    """
    Return the existing ruleset.rule_id if a row with identical values exists,
    otherwise insert a new row and return its rule_id.

    Schema fields used in `ruleset`:
      (max_speed, min_follow_distance, stop_sign_wait)
    """
    conn = _conn()
    cur = conn.cursor()

    max_speed = float(rules["max_speed"])
    min_follow = float(rules["min_follow_distance"])
    stop_wait = float(rules["stop_sign_wait"])

    cur.execute(
        """
        SELECT rule_id
        FROM ruleset
        WHERE max_speed = ?
          AND min_follow_distance = ?
          AND stop_sign_wait = ?
        """,
        (max_speed, min_follow, stop_wait),
    )
    row = cur.fetchone()
    if row:
        return row["rule_id"]

    cur.execute(
        """
        INSERT INTO ruleset(max_speed, min_follow_distance, stop_sign_wait)
        VALUES (?, ?, ?)
        """,
        (max_speed, min_follow, stop_wait),)
    conn.commit()
    return cur.lastrowid


def register_scenario(
    name: str,
    description: str,
    source_file: str,
    rule_id: int,
    zones: List[Dict[str, Any]] | None,
) -> int:
    """
    Insert a scenario and its optional speed zones; return the new scenario_id.

    Tables:
      - scenario(name, description, source_file, ruleset_id)
      - speed_zone(start_mile, end_mile, speed_limit, scenario_id)
    """
    conn = _conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO scenario(name, description, source_file, ruleset_id) VALUES (?, ?, ?, ?)",
        (name, description, source_file, rule_id),)
    scenario_id = cur.lastrowid

    if zones:
        for zone in zones:
            cur.execute(
                """
                INSERT INTO speed_zone(start_mile, end_mile, speed_limit, scenario_id)
                VALUES (?, ?, ?, ?)
                """,
                (zone["start_mile"], zone["end_mile"], zone["speed_limit"], scenario_id),)
    conn.commit()
    return scenario_id


def save_report(scenario_id: int, violations: List[Dict[str, Any]]) -> None:
    """
    Persist violations for a given scenario.

    Table:
      - violation(scenario_id, tstamp, type, details)

    Input violation dicts are expected to have keys: 'time', 'type', 'details'.

    """
    conn = _conn()
    cur = conn.cursor()

    for v in violations:
        cur.execute(
            """
            INSERT INTO violation(scenario_id, tstamp, type, details)
            VALUES (?, ?, ?, ?)
            """,
            (scenario_id, v["time"], v["type"], v["details"]),)
    conn.commit()


def get_violation_counts(scenario_id: int) -> Dict[str, int]:
    """
    Return {type: count} for a scenario.

    SQL:
      SELECT type, COUNT(*)
      FROM violation
      WHERE scenario_id=?
      GROUP BY type
    """
    conn = _conn()
    cur = conn.cursor()


    cur.execute(
        """
        SELECT type, COUNT(*) AS cnt
        FROM violation
        WHERE scenario_id = ?
        GROUP BY type
        """,
        (scenario_id,),
    )
    return {row["type"]: row["cnt"] for row in cur.fetchall()}


def get_violations_by_type(scenario_id: int, vtype: str) -> List[Dict[str, Any]]:
    """
    Return violations of a given type for a scenario, ordered by timestamp.

    SQL:
      SELECT tstamp, type, details
      FROM violation
      WHERE scenario_id=? AND type=?
      ORDER BY tstamp

    Output shape per row:
      {"time": <str>, "type": <str>, "details": <str>}

    """
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tstamp, type, details
        FROM violation
        WHERE scenario_id = ?
          AND type = ?
        ORDER BY tstamp
        """,
        (scenario_id, vtype),
    )
    return [{"time": row["tstamp"], "type": row["type"], "details": row["details"]} for row in cur.fetchall()]


def get_recent_violations(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Return the most recent `limit` violations across all scenarios (newest first).

    SQL:
      SELECT scenario_id, tstamp, type, details
      FROM violation
      ORDER BY violation_id DESC
      LIMIT ?

    Output shape per row:
      {"scenario_id": <int>, "time": <str>, "type": <str>, "details": <str>}

    """
    conn = _conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT scenario_id, tstamp, type, details
        FROM violation
        ORDER BY violation_id DESC LIMIT ?
        """,
        (limit,),)

    return [{"scenario_id": row["scenario_id"], "time": row["tstamp"], "type": row["type"], "details": row["details"]} for row in cur.fetchall()]

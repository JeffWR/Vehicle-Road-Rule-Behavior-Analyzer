from __future__ import annotations

from pathlib import Path
from typing import Iterator, Dict, Any, Tuple
import json


def load_scenario(path: Path) -> Dict[str, Any]:
    """
    Load a scenario JSON and validate required fields.

    Required:
      - top-level key "road_rules" (dict) with keys:
          * "max_speed"
          * "min_follow_distance"
          * "stop_sign_wait"
    Optional:
      - "speed_zones" (list), default to [] if missing.
    """
    try:
        with open(path,"r",encoding = 'utf-8') as file:
            data = json.load(file)
    except Exception as e:
        raise ValueError(f"Invalid JSON file {e}")

    if "road_rules" not in data:
        raise ValueError("scenario missing 'road_rules'")

    road_rules = data["road_rules"]
    required_keys = ["max_speed", "min_follow_distance", "stop_sign_wait"]


    if road_rules is None or not isinstance(road_rules, dict):
        raise ValueError("road_rules must be a dictionary")
    for key in required_keys:
        if key not in road_rules:
            raise ValueError(f"road_rules missing key: {key}")
    data.setdefault("speed_zones",[])
    if not isinstance(data["speed_zones"],list):
        raise ValueError("speed_zones must be a list")
    return data


def parse_time(ts: str) -> float:
    """
    Convert a timestamp like 'M:SS' or 'M:SS.s' into seconds (float).

    Examples:
      '0:05'   -> 5.0
      '1:02.5' -> 62.5
    """
    try:
        parts = ts.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid time format: {ts}")
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    except Exception:
        raise ValueError(f"bad timestamp: {ts!r}")

def read_log(path: Path) -> Iterator[Tuple[float, str, str]]:
    """
    Parse a plaintext event log.

    Each non-empty line begins with a timestamp, then an event kind, optionally an argument.
    Allowed kinds and formats:
      - SPEED <float>
      - FOLLOW_DISTANCE <float>
      - LANE_CHANGE <LEFT|RIGHT>
      - STOP_SIGN_DETECTED        (no argument)

    Yields:
      (time_seconds: float, kind: str, arg: str)
    """

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) < 2:
                raise ValueError(f"bad line: {line!r}")
            
            time_str, kind = tokens[0], tokens[1]
            time = parse_time(time_str)

            if kind == "SPEED":
                if len(tokens) != 3:
                    raise ValueError(f"bad SPEED: {line!r} (Improper SPEED log)")
                try:
                    float(tokens[2])
                except ValueError:
                    raise ValueError(f"bad SPEED: {line!r} (Improper SPEED log)")
                yield (time, kind, tokens[2])
            elif kind == "FOLLOW_DISTANCE":
                if len(tokens)!= 3:
                    raise ValueError(f"bad FOLLOW_DISTANCE: {line!r} (Improper FOLLOW_DISTANCE log)")
                try:
                    float(tokens[2])
                except ValueError:
                    raise ValueError(f"bad FOLLOW_DISTANCE: {line!r} (Improper FOLLOW_DISTANCE log)")
                yield (time, kind, tokens[2])
            elif kind == "LANE_CHANGE":
                if len(tokens) != 3 or tokens[2] not in {"LEFT", "RIGHT"}:
                    raise ValueError(f"bad LANE_CHANGE: {line!r} (Improper LANE_CHANGE log)")
                yield (time, kind, tokens[2])
            elif kind == "STOP_SIGN_DETECTED":
                if len(tokens) != 2:
                    raise ValueError(f"bad STOP_SIGN_DETECTED: {line!r} (Improper STOP_SIGN_DETECTED log)")
                yield (time, kind, "")
            else:
                raise ValueError(f"unknown kind: {kind}")
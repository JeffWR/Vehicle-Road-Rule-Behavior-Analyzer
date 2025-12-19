from __future__ import annotations
from typing import Dict, Any, Iterable, List, Tuple

Event = Tuple[float, str, str]


def _fmt_time(t: float) -> str:
    """
    Format seconds as MM:SS.s (zero-padded minutes, 1 decimal for seconds).
    Example: 62.5 -> "01:02.5"
    """
    m = int(t // 60)
    s = t - m * 60
    return f"{m:02d}:{s:04.1f}"


def detect_violations(scenario: Dict[str, Any], events: Iterable[Event]) -> List[Dict[str, str]]:
    """
    Apply rule checks to a stream of events.

    Road-rule inputs (scenario['road_rules']):
      - max_speed (mph, float-like)
      - min_follow_distance (meters, float-like)
      - stop_sign_wait (seconds, float-like)

    Event kinds (time: float seconds, kind: str, arg: str):
      - ("...", "SPEED", "<float mph>")
      - ("...", "FOLLOW_DISTANCE", "<float meters>")
      - ("...", "LANE_CHANGE", "LEFT" | "RIGHT")
      - ("...", "STOP_SIGN_DETECTED", "")

    Violations to emit (append dicts shaped as below):
      {"type": <str>, "time": <MM:SS.s>, "details": <str>}

    Required checks (use small epsilon like 1e-9 to avoid FP jitter):
      - SPEEDING when speed > max_speed
        details e.g.: f"{speed:.1f} mph in {max_speed:.0f} mph zone"
      - ROLLING_STOP after STOP_SIGN_DETECTED if the vehicle accelerates past ~1.0 mph
        before waiting stop_sign_wait seconds
        details e.g.: f"Stopped {waited:.1f}s; required {stop_wait:.1f}s"
      - TAILGATING when follow distance < min_follow
        details e.g.: f"{dist:.1f} m < {min_follow:.1f} m"
      - UNSAFE_LANE_CHANGE if a lane change occurs while follow distance < min_follow
        details e.g.: f"follow {dist:.1f} m < {min_follow:.1f} m"

    Ordering:
      - Sort the final list by the human-formatted "time" string.
    """
    max_speed = float(scenario["road_rules"]["max_speed"])
    min_follow = float(scenario["road_rules"]["min_follow_distance"])
    stop_wait = float(scenario["road_rules"]["stop_sign_wait"])

    last_follow: float | None = None
    stop_detect_time: float | None = None

    violations: List[Dict[str, str]] = []

    for t,kind,arg in events:
        if kind == "SPEED":
            speed = float(arg)
            if speed > max_speed:
                details = f"{speed:.1f} mph in {max_speed:.0f} mph zone"
                violations.append({"type": "SPEEDING", "time": _fmt_time(t), "details": details})

            if stop_detect_time is not None and speed > 1.0 and t > stop_detect_time:
                waited = t - stop_detect_time

                if waited < stop_wait:
                    details = f"Stopped {waited:.1f}s; required {stop_wait:.1f}s"
                    violations.append({"type": "ROLLING_STOP", "time": _fmt_time(t), "details": details})
                stop_detect_time = None

        elif kind == "FOLLOW_DISTANCE":
            dist = float(arg)
            last_follow = dist

            if dist < min_follow:
                details = f"{dist:.1f} m < {min_follow:.1f} m"
                violations.append({"type": "TAILGATING", "time": _fmt_time(t), "details": details})

        elif kind == "LANE_CHANGE":
            if last_follow is not None and last_follow < min_follow:
                details = f"follow {last_follow:.1f} m < {min_follow:.1f} m"
                violations.append({"type": "UNSAFE_LANE_CHANGE", "time": _fmt_time(t), "details": details})

        elif kind == "STOP_SIGN_DETECTED":
            stop_detect_time = t

        else:
            raise ValueError(f"unknown kind: {kind}")

    violations.sort(key=lambda v: float(v["time"].replace(":", "").replace(".", "")))
    return violations

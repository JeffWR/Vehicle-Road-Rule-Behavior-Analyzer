import json
import tempfile
import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from parser import load_scenario, parse_time, read_log

def test_load_scenario_valid(tmp_path: Path):

    scenario_data = {
        "name": "Campus Drive Westbound",
        "description": "Short run near stop signs and lane change.",
        "road_rules": {
            "max_speed": 35,
            "min_follow_distance": 5,
            "stop_sign_wait": 3,
        }
    }
    f = tmp_path / "scenario.json"
    f.write_text(json.dumps(scenario_data))

    data = load_scenario(f)
    assert data["road_rules"]["max_speed"] == 35
    assert "speed_zones" in data
    assert data["speed_zones"] == []


def test_load_scenario_with_speed_zones(tmp_path: Path):

    scenario_data = {
        "road_rules": {
            "max_speed": 35,
            "min_follow_distance": 5,
            "stop_sign_wait": 3,
        },
        "speed_zones": [
            {"start_mile": 0.0, "end_mile": 0.5, "speed_limit": 25},
            {"start_mile": 0.5, "end_mile": 1.0, "speed_limit": 35}
        ]
    }
    f = tmp_path / "scenario.json"
    f.write_text(json.dumps(scenario_data))

    data = load_scenario(f)
    assert len(data["speed_zones"]) == 2
    assert data["speed_zones"][0]["speed_limit"] == 25


def test_load_scenario_missing_road_rules(tmp_path: Path):
    scenario_data = {
        "name": "Test Scenario"
        # Missing road_rules
    }
    f = tmp_path / "scenario.json"
    f.write_text(json.dumps(scenario_data))

    with pytest.raises(ValueError, match="missing 'road_rules'"):
        load_scenario(f)


def test_load_scenario_missing_required_keys(tmp_path: Path):
    scenario_data = {
        "road_rules": {
            "max_speed": 35,
            # Missing min_follow_distance and stop_sign_wait
        }
    }
    f = tmp_path / "scenario.json"
    f.write_text(json.dumps(scenario_data))

    with pytest.raises(ValueError):
        load_scenario(f)


def test_load_scenario_invalid_speed_zones(tmp_path: Path):
    scenario_data = {
        "road_rules": {
            "max_speed": 35,
            "min_follow_distance": 5,
            "stop_sign_wait": 3,
        },
        "speed_zones": "not_a_list"  # Should be a list
    }
    f = tmp_path / "scenario.json"
    f.write_text(json.dumps(scenario_data))

    with pytest.raises(ValueError, match="speed_zones must be a list"):
        load_scenario(f)


def test_parse_time_valid():
    assert parse_time("0:00") == 0.0
    assert parse_time("0:05") == 5.0
    assert parse_time("1:00") == 60.0
    assert parse_time("1:02.5") == 62.5
    assert parse_time("10:30.1") == 630.1


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        parse_time("bad")
    with pytest.raises(ValueError):
        parse_time("1:xx")
    with pytest.raises(ValueError):
        parse_time("1:01:01.5")
    with pytest.raises(ValueError):
        parse_time("")
    with pytest.raises(ValueError):
        parse_time("1:")


def test_read_log_valid(tmp_path: Path):
    log_content = """00:00.0 SPEED 0.0
00:01.0 FOLLOW_DISTANCE 10.0
00:02.0 STOP_SIGN_DETECTED
00:03.0 LANE_CHANGE LEFT
00:04.0 LANE_CHANGE RIGHT"""

    f = tmp_path / "log.txt"
    f.write_text(log_content)

    events = list(read_log(f))
    assert events[0] == (0.0, "SPEED", "0.0")
    assert events[1] == (1.0, "FOLLOW_DISTANCE", "10.0")
    assert events[2] == (2.0, "STOP_SIGN_DETECTED", "")
    assert events[3] == (3.0, "LANE_CHANGE", "LEFT")
    assert events[4] == (4.0, "LANE_CHANGE", "RIGHT")


def test_read_log_edge_cases(tmp_path: Path):
    log_content = """00:00.0 SPEED 0.0
00:01.0 FOLLOW_DISTANCE 0.001
00:02.0 FOLLOW_DISTANCE 999.9
00:03.0 SPEED 0.1
00:04.0 SPEED 150.5"""
    f = tmp_path / "log.txt"
    f.write_text(log_content)

    events = list(read_log(f))
    assert len(events) == 5
    assert events[0] == (0.0, "SPEED", "0.0")
    assert events[1] == (1.0, "FOLLOW_DISTANCE", "0.001")
    assert events[2] == (2.0, "FOLLOW_DISTANCE", "999.9")
    assert events[3] == (3.0, "SPEED", "0.1")
    assert events[4] == (4.0, "SPEED", "150.5")


def test_read_log_invalid(tmp_path: Path):
    bad_log = """00:00.0 SPEED number
00:01.0 FOLLOW_DISTANCE xx
00:02.0 STOP_SIGN_DETECTED 1
00:03.0 LANE_CHANGE UP"""
    f = tmp_path / "badlog.txt"
    f.write_text(bad_log)

    with pytest.raises(ValueError):
        list(read_log(f))


def test_read_log_malformed_lines(tmp_path: Path):
    bad_log = """00:00.0 SPEED
00:01.0
00:02.0 STOP_SIGN_DETECTED extra stuff"""
    f = tmp_path / "badlog.txt"
    f.write_text(bad_log)

    with pytest.raises(ValueError):
        list(read_log(f))


def test_read_log_empty_file(tmp_path: Path):
    f = tmp_path / "empty.txt"
    f.write_text("")

    events = list(read_log(f))
    assert events == []


def test_read_log_whitespace_only(tmp_path: Path):
    f = tmp_path / "whitespace.txt"
    f.write_text("   \n  \t  \n   ")

    events = list(read_log(f))
    assert events == []
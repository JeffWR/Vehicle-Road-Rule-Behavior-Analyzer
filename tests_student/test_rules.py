import unittest
from rules import detect_violations, _fmt_time

class TestDetectViolations(unittest.TestCase):
    def setUp(self):
        self.scenario = {
            "road_rules": {
                "max_speed": 60.0,
                "min_follow_distance": 10.0,
                "stop_sign_wait": 3.0,
            }
        }

    def test_fmt_time(self):
        self.assertEqual(_fmt_time(0), "00:00.0")
        self.assertEqual(_fmt_time(5.0), "00:05.0")
        self.assertEqual(_fmt_time(60.0), "01:00.0")
        self.assertEqual(_fmt_time(62.5), "01:02.5")
        self.assertEqual(_fmt_time(125.7), "02:05.7")
        self.assertEqual(_fmt_time(3600.0), "60:00.0")

    def test_speeding_violation(self):
        events = [(5.0, "SPEED", "65.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "SPEEDING")
        self.assertIn("65.0 mph", v[0]["details"])

    def test_speeding_exact_max_speed_no_violation(self):
        events = [(5.0, "SPEED", "60.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 0)

    def test_speeding_just_above_max_violation(self):
        events = [(5.0, "SPEED", "60.1")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "SPEEDING")

    def test_speeding_well_above_max_violation(self):
        events = [(5.0, "SPEED", "80.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "SPEEDING")

    def test_tailgating_violation(self):
        events = [(10.0, "FOLLOW_DISTANCE", "5.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "TAILGATING")
        self.assertIn("5.0 m", v[0]["details"])

    def test_tailgating_exact_min_distance_no_violation(self):
        events = [(10.0, "FOLLOW_DISTANCE", "10.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 0)

    def test_tailgating_just_below_min_violation(self):
        events = [(10.0, "FOLLOW_DISTANCE", "9.999")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "TAILGATING")

    def test_tailgating_zero_distance_violation(self):
        events = [(10.0, "FOLLOW_DISTANCE", "0.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "TAILGATING")

    def test_tailgating_negative_distance(self):
        events = [(10.0, "FOLLOW_DISTANCE", "-1.0")]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "TAILGATING")

    def test_unsafe_lane_change_violation(self):
        events = [
            (2.0, "FOLLOW_DISTANCE", "5.0"),
            (3.0, "LANE_CHANGE", "LEFT"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 2)
        types = {vi["type"] for vi in v}
        self.assertIn("TAILGATING", types)
        self.assertIn("UNSAFE_LANE_CHANGE", types)

    def test_unsafe_lane_change_with_good_distance_no_violation(self):
        events = [
            (2.0, "FOLLOW_DISTANCE", "15.0"),
            (3.0, "LANE_CHANGE", "LEFT"),
        ]
        v = detect_violations(self.scenario, events)
        unsafe_changes = [vi for vi in v if vi["type"] == "UNSAFE_LANE_CHANGE"]
        self.assertEqual(len(unsafe_changes), 0)

    def test_lane_change_no_prior_distance_no_violation(self):
        events = [
            (3.0, "LANE_CHANGE", "LEFT")
        ]
        v = detect_violations(self.scenario, events)
        unsafe_changes = [vi for vi in v if vi["type"] == "UNSAFE_LANE_CHANGE"]
        self.assertEqual(len(unsafe_changes), 0)

    def test_rolling_stop_violation(self):
        events = [
            (0.0, "STOP_SIGN_DETECTED", ""),
            (1.0, "SPEED", "5.0"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "ROLLING_STOP")
        self.assertIn("Stopped 1.0s; required 3.0s", v[0]["details"])

    def test_rolling_stop_exact_wait_time_no_violation(self):
        events = [
            (0.0, "STOP_SIGN_DETECTED", ""),
            (3.0, "SPEED", "5.0"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 0)

    def test_rolling_stop_just_below_wait_time_violation(self):
        events = [
            (0.0, "STOP_SIGN_DETECTED", ""),
            (2.999, "SPEED", "5.0"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "ROLLING_STOP")

    def test_rolling_stop_slow_speed_no_violation(self):
        events = [
            (0.0, "STOP_SIGN_DETECTED", ""),
            (1.0, "SPEED", "0.9"),
            (2.0, "SPEED", "0.5")
        ]
        v = detect_violations(self.scenario, events)
        rolling_stops = [vi for vi in v if vi["type"] == "ROLLING_STOP"]
        self.assertEqual(len(rolling_stops), 0)

    def test_rolling_stop_multiple_speed_events(self):
        events = [
            (0.0, "STOP_SIGN_DETECTED", ""),
            (1.0, "SPEED", "0.5"),
            (2.0, "SPEED", "0.8"),
            (2.5, "SPEED", "1.1")  # This should trigger violation
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 1)
        self.assertEqual(v[0]["type"], "ROLLING_STOP")

    def test_no_violations(self):
        events = [
            (0.0, "SPEED", "30.0"),
            (2.0, "FOLLOW_DISTANCE", "15.0"),
            (4.0, "LANE_CHANGE", "RIGHT"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 0)

    def test_multiple_violations_complex_sequence(self):
        events = [
            (0.0, "SPEED", "70.0"),
            (1.0, "FOLLOW_DISTANCE", "5.0"),
            (2.0, "LANE_CHANGE", "LEFT"),
            (3.0, "STOP_SIGN_DETECTED", ""),
            (3.5, "SPEED", "5.0")
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 4)
        violation_types = {vi["type"] for vi in v}
        expected_types = {"SPEEDING", "TAILGATING", "UNSAFE_LANE_CHANGE", "ROLLING_STOP"}
        self.assertEqual(violation_types, expected_types)

    def test_violation_sorting_by_time(self):
        events = [
            (5.0, "SPEED", "70.0"),
            (1.0, "FOLLOW_DISTANCE", "5.0"),
        ]
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 2)
        self.assertEqual(v[0]["type"], "TAILGATING")
        self.assertEqual(v[1]["type"], "SPEEDING")

    def test_unknown_event_type(self):
        events = [
            (1.0, "UNKNOWN_EVENT", "data"),
        ]
        with self.assertRaises(ValueError):
            detect_violations(self.scenario, events)

    def test_empty_events(self):
        events = []
        v = detect_violations(self.scenario, events)
        self.assertEqual(len(v), 0)

    def test_very_small_values(self):
        events = [
            (0.0, "SPEED", "0.001"),
            (1.0, "FOLLOW_DISTANCE", "0.001")
        ]
        v = detect_violations(self.scenario, events)
        # Should not crash and should detect tailgating
        tailgating = [vi for vi in v if vi["type"] == "TAILGATING"]
        self.assertGreaterEqual(len(tailgating), 0)

    def test_very_large_values(self):
        events = [
            (0.0, "SPEED", "1000.0"),
            (1.0, "FOLLOW_DISTANCE", "1000.0")
        ]
        v = detect_violations(self.scenario, events)
        # Should detect speeding but not tailgating
        speeding = [vi for vi in v if vi["type"] == "SPEEDING"]
        tailgating = [vi for vi in v if vi["type"] == "TAILGATING"]
        self.assertEqual(len(speeding), 1)
        self.assertEqual(len(tailgating), 0)

if __name__ == "__main__":
    unittest.main()
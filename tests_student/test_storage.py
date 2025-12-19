import unittest
import sqlite3
from unittest.mock import patch
import storage


class TestStorage(unittest.TestCase):
    def setUp(self):
        storage.init_db(":memory:")
        self.conn = storage._conn()
        self.conn.row_factory = sqlite3.Row

    def test_upsert_ruleset_insert_and_reuse(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id1 = storage.upsert_ruleset(rules)
        self.assertIsInstance(rule_id1, int)

        rule_id2 = storage.upsert_ruleset(rules)
        self.assertEqual(rule_id1, rule_id2)

        rules2 = {"max_speed": 30, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id3 = storage.upsert_ruleset(rules2)
        self.assertNotEqual(rule_id1, rule_id3)

    def test_upsert_ruleset_float_precision(self):
        rules1 = {"max_speed": 35.0, "min_follow_distance": 5.0, "stop_sign_wait": 3.0}
        rules2 = {"max_speed": 35.0000001, "min_follow_distance": 5.0, "stop_sign_wait": 3.0}

        rule_id1 = storage.upsert_ruleset(rules1)
        rule_id2 = storage.upsert_ruleset(rules2)

        self.assertNotEqual(rule_id1, rule_id2)

    def test_upsert_ruleset_very_small_differences(self):
        rules1 = {"max_speed": 35.0, "min_follow_distance": 5.0, "stop_sign_wait": 3.0}
        rules2 = {"max_speed": 35.0, "min_follow_distance": 5.0000001, "stop_sign_wait": 3.0}

        rule_id1 = storage.upsert_ruleset(rules1)
        rule_id2 = storage.upsert_ruleset(rules2)

        self.assertNotEqual(rule_id1, rule_id2)

    def test_register_scenario_and_save_report(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)

        zones = [{"start_mile": 0.0, "end_mile": 0.5, "speed_limit": 25}]
        scenario_id = storage.register_scenario(
            "Test Drive", "Test scenario", "examples/log.txt", rule_id, zones
        )
        self.assertIsInstance(scenario_id, int)

        violations = [
            {"time": "00:02.0", "type": "SPEEDING", "details": "40 mph in 35 mph zone"},
            {"time": "00:05.0", "type": "TAILGATING", "details": "2 m < 5 m"},
        ]
        storage.save_report(scenario_id, violations)

        counts = storage.get_violation_counts(scenario_id)
        self.assertEqual(counts["SPEEDING"], 1)
        self.assertEqual(counts["TAILGATING"], 1)

        tailgating_list = storage.get_violations_by_type(scenario_id, "TAILGATING")
        self.assertEqual(len(tailgating_list), 1)
        self.assertEqual(tailgating_list[0]["details"], "2 m < 5 m")

        recent = storage.get_recent_violations(limit=10)
        self.assertGreaterEqual(len(recent), 2)

    def test_register_scenario_no_zones(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)

        scenario_id = storage.register_scenario(
            "Test Drive", "Test scenario", "examples/log.txt", rule_id, None
        )
        self.assertIsInstance(scenario_id, int)

    def test_register_scenario_empty_zones(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)

        scenario_id = storage.register_scenario(
            "Test Drive", "Test scenario", "examples/log.txt", rule_id, []
        )
        self.assertIsInstance(scenario_id, int)

    def test_register_scenario_multiple_zones(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)

        zones = [
            {"start_mile": 0.0, "end_mile": 0.5, "speed_limit": 25},
            {"start_mile": 0.5, "end_mile": 1.0, "speed_limit": 35},
            {"start_mile": 1.0, "end_mile": 2.0, "speed_limit": 45}
        ]
        scenario_id = storage.register_scenario(
            "Test Drive", "Test scenario", "examples/log.txt", rule_id, zones
        )
        self.assertIsInstance(scenario_id, int)

    def test_save_report_empty_violations(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        storage.save_report(scenario_id, [])

        counts = storage.get_violation_counts(scenario_id)
        self.assertEqual(counts, {})

    def test_save_report_multiple_violations_same_type(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        violations = [
            {"time": "00:01.0", "type": "SPEEDING", "details": "40 mph"},
            {"time": "00:02.0", "type": "SPEEDING", "details": "45 mph"},
            {"time": "00:03.0", "type": "SPEEDING", "details": "50 mph"}
        ]
        storage.save_report(scenario_id, violations)

        counts = storage.get_violation_counts(scenario_id)
        self.assertEqual(counts["SPEEDING"], 3)

    def test_get_violation_counts_no_violations(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Empty Test", "No violations", "examples/log.txt", rule_id, None)

        counts = storage.get_violation_counts(scenario_id)
        self.assertEqual(counts, {})

    def test_get_violations_by_type_nonexistent_type(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        violations = storage.get_violations_by_type(scenario_id, "NONEXISTENT")
        self.assertEqual(violations, [])

    def test_get_violations_by_type_empty_result(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        violations = storage.get_violations_by_type(scenario_id, "SPEEDING")
        self.assertEqual(violations, [])

    def test_get_recent_violations_empty_db(self):
        recent = storage.get_recent_violations(limit=10)
        self.assertEqual(recent, [])

    def test_get_recent_violations_limit(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        violations = [
            {"time": f"00:{i:02d}.0", "type": "SPEEDING", "details": f"{40 + i} mph"}
            for i in range(10)
        ]
        storage.save_report(scenario_id, violations)

        recent = storage.get_recent_violations(limit=5)
        self.assertEqual(len(recent), 5)

    def test_get_recent_violations_order(self):
        rules = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id = storage.upsert_ruleset(rules)
        scenario_id = storage.register_scenario("Test", "Test", "examples/log.txt", rule_id, None)

        violations = [
            {"time": "00:01.0", "type": "SPEEDING", "details": "40 mph"},
            {"time": "00:02.0", "type": "TAILGATING", "details": "2 m"}
        ]
        storage.save_report(scenario_id, violations)

        recent = storage.get_recent_violations(limit=10)
        self.assertEqual(len(recent), 2)
        # Should be ordered by violation_id DESC (most recent first)
        self.assertEqual(recent[0]["type"], "TAILGATING")
        self.assertEqual(recent[1]["type"], "SPEEDING")

    def test_multiple_scenarios_violation_isolation(self):
        # Create first scenario
        rules1 = {"max_speed": 35, "min_follow_distance": 5, "stop_sign_wait": 3}
        rule_id1 = storage.upsert_ruleset(rules1)
        scenario_id1 = storage.register_scenario("Scenario 1", "Test 1", "log1.txt", rule_id1, None)

        # Create second scenario
        rules2 = {"max_speed": 45, "min_follow_distance": 8, "stop_sign_wait": 4}
        rule_id2 = storage.upsert_ruleset(rules2)
        scenario_id2 = storage.register_scenario("Scenario 2", "Test 2", "log2.txt", rule_id2, None)

        # Add violations to first scenario
        violations1 = [
            {"time": "00:01.0", "type": "SPEEDING", "details": "40 mph"}
        ]
        storage.save_report(scenario_id1, violations1)

        # Add violations to second scenario
        violations2 = [
            {"time": "00:01.0", "type": "SPEEDING", "details": "50 mph"}
        ]
        storage.save_report(scenario_id2, violations2)

        # Check that each scenario only sees its own violations
        counts1 = storage.get_violation_counts(scenario_id1)
        counts2 = storage.get_violation_counts(scenario_id2)

        self.assertEqual(counts1["SPEEDING"], 1)
        self.assertEqual(counts2["SPEEDING"], 1)

        # Check recent violations include both
        recent = storage.get_recent_violations(limit=10)
        self.assertEqual(len(recent), 2)


if __name__ == "__main__":
    unittest.main()
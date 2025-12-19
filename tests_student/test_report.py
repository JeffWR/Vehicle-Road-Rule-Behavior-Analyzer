import unittest
from report import make_report

class TestMakeReport(unittest.TestCase):

    def test_basic_report(self):
        scenario = {"name": "Test Scenario"}
        violations = [
            {"type": "SPEEDING", "time": "00:01.0", "details": "65 mph in 60 mph zone"},
            {"type": "TAILGATING", "time": "00:02.0", "details": "2 m < 10 m"}
        ]
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Test Scenario")
        self.assertEqual(report["violations"], violations)
        self.assertEqual(report["total_violations"], 2)

    def test_empty_violations(self):
        scenario = {"name": "Empty Test"}
        violations = []
        report = make_report(scenario, violations)
        self.assertEqual(report["total_violations"], 0)
        self.assertEqual(report["violations"], [])

    def test_missing_name(self):
        scenario = {}  # No name key
        violations = []
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Unnamed")
        self.assertEqual(report["total_violations"], 0)

    def test_none_name(self):
        scenario = {"name": None}
        violations = []
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Unnamed")

    def test_empty_string_name(self):
        scenario = {"name": ""}
        violations = []
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Unnamed")

    def test_whitespace_name(self):
        scenario = {"name": "   "}
        violations = []
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Unnamed")

    def test_report_with_multiple_violation_types(self):
        scenario = {"name": "Complex Test"}
        violations = [
            {"type": "SPEEDING", "time": "00:01.0", "details": "65 mph"},
            {"type": "TAILGATING", "time": "00:02.0", "details": "2 m"},
            {"type": "ROLLING_STOP", "time": "00:03.0", "details": "1s wait"},
            {"type": "UNSAFE_LANE_CHANGE", "time": "00:04.0", "details": "3 m"}
        ]
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Complex Test")
        self.assertEqual(len(report["violations"]), 4)
        self.assertEqual(report["total_violations"], 4)

    def test_report_with_duplicate_violation_types(self):
        scenario = {"name": "Duplicate Test"}
        violations = [
            {"type": "SPEEDING", "time": "00:01.0", "details": "65 mph"},
            {"type": "SPEEDING", "time": "00:02.0", "details": "70 mph"},
            {"type": "SPEEDING", "time": "00:03.0", "details": "75 mph"}
        ]
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Duplicate Test")
        self.assertEqual(len(report["violations"]), 3)
        self.assertEqual(report["total_violations"], 3)

    def test_report_with_various_time_formats(self):
        scenario = {"name": "Time Format Test"}
        violations = [
            {"type": "SPEEDING", "time": "00:00.1", "details": "details"},
            {"type": "SPEEDING", "time": "01:00.0", "details": "details"},
            {"type": "SPEEDING", "time": "10:30.5", "details": "details"}
        ]
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Time Format Test")
        self.assertEqual(len(report["violations"]), 3)
        self.assertEqual(report["total_violations"], 3)

    def test_report_with_none_scenario(self):
        scenario = None
        violations = []
        # This should not crash and should handle gracefully
        report = make_report(scenario, violations)
        self.assertEqual(report["scenario"], "Unnamed")
        self.assertEqual(report["total_violations"], 0)

if __name__ == "__main__":
    unittest.main()
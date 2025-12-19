# Vehicle Road Rule Behavior Analyzer

The program takes in two inputs the log.txt file for the vehicle onboard behavior documentation and a file scenario.json with the road rules and information. 
From these files the program generate a database for the documentation of all violation and a violation report for the vehicle, to achieve automatic road rule violation detection.

### System Architecture
    
    README.md
    log_analyzer.py
    parser.py
    report.py
    rules.py
    storage.py
    tests_student/
        test_parser.py
        test_report.py
        test_rules.py
        test_storage.py
    run_mutation_suite.py
    mutants/
        rules_rules_ge_speed.py
        rules_rules_lane_always.py
        rules_rules_lane_ignore.py
        rules_rules_never_speed.py
        rules_rules_speed_round.py
        rules_rules_stop_le.py
        rules_rules_stop_minus1.py
        rules_rules_tail_plus1.py
        rules_rules_tail_rev.py
        rules_rules_time_fmt.py
    schema.sql

### Usage
Basic Analysis (Generates report.json only)

    python log_analyzer.py scenario.json log.txt

Full Analysis with Database Storage

    python log_analyzer.py scenario.json log.txt --db scenarios.db

Query Violation Counts

    python log_analyzer.py --summary SCENARIO_ID --db scenarios.db

Query Specific Violation Types

    python log_analyzer.py --by-type SCENARIO_ID VIOLATION_TYPE --db scenarios.db

### Input File Specifications
##### Scenario JSON Format

    {
      "name": "Scenario Name",
      "description": "Scenario description",
      "road_rules": {
        "max_speed": 45,
        "min_follow_distance": 2.5,
        "stop_sign_wait": 3.0
      },
      "speed_zones": [
        {"start_mile": 0.5, "end_mile": 1.2, "speed_limit": 35}
      ]
    }

##### Event Log Format

    Timestamp EventType Argument
    Examples:
    0:05 SPEED 32.5
    0:12 FOLLOW_DISTANCE 3.2
    0:45 STOP_SIGN_DETECTED
    1:02 LANE_CHANGE LEFT

Supported event types: SPEED, FOLLOW_DISTANCE, LANE_CHANGE, STOP_SIGN_DETECTED

## Program Design
**parser.py - Data Input and Validation**

Methods:

    load_scenario(path) - Loads and validates scenario JSON files

    parse_time(ts) - Converts timestamp strings to seconds

    read_log(path) - Parses event log files with format validation

**rules.py - Violation Detection Engine**

Methods:

    detect_violations(scenario, events) - Main analysis function

    _fmt_time(t) - Formats seconds as MM:SS.s

Detects these violation types:

    SPEEDING - Exceeding maximum speed limit

    ROLLING_STOP - Insufficient wait time at stop signs

    TAILGATING - Following too closely

    UNSAFE_LANE_CHANGE - Changing lanes while following too closely

**report.py - Report Generation**

Methods:

    make_report(scenario, violations) - Creates standardized report structure

**storage.py - Database Persistence**

Methods:

    init_db(path) - Initializes database connection

    upsert_ruleset(rules) - Stores road rule configurations

    register_scenario() - Stores scenario information

    save_report() - Persists violation records

    Query methods for retrieving historical data

### Output Specification
Report JSON Format

    {
      "scenario": "Scenario Name",
      "violations": [
        {
          "type": "VIOLATION_TYPE",
          "time": "MM:SS.S",
          "details": "Violation description"
        }
      ],
      "total_violations": 1
    }


The system creates SQLite tables for:

    Rulesets (road rule configurations)

    Scenarios (test scenarios)

    Speed zones (geofenced speed limits)

    Violations (detected infractions)

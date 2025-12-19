
#!/usr/bin/env python3
import json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
MUTANTS = sorted((ROOT / "mutants").glob("rules_*.py"))
RESULTS = {"total_mutants": 0, "killed": 0, "survived": 0, "killed_ids": [], "survived_ids": []}

def run_tests():
    return subprocess.run([sys.executable, "-m", "unittest", "discover", "tests_student", "-v"],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=45)

def main():
    orig = ROOT / "rules.py"
    backup = ROOT / "rules_original_backup.py"
    shutil.copyfile(orig, backup)
    try:
        for mpath in MUTANTS:
            RESULTS["total_mutants"] += 1
            shutil.copyfile(mpath, orig)
            proc = run_tests()
            mid = mpath.stem
            if proc.returncode != 0:
                RESULTS["killed"] += 1
                RESULTS["killed_ids"].append(mid)
            else:
                RESULTS["survived"] += 1
                RESULTS["survived_ids"].append(mid)
        (ROOT / "mutation_results.json").write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")
        print(json.dumps(RESULTS, indent=2))
    finally:
        shutil.copyfile(backup, orig)
        backup.unlink(missing_ok=True)

if __name__ == "__main__":
    main()

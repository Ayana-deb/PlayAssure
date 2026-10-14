"""One command to run the whole QA pipeline:
   1) pytest (writes reports/junit.xml, logs, and bug reports for real failures)
   2) local performance benchmark (writes reports/performance.json)
   3) report generator (writes reports/report.json and reports/report.html)

Usage:  python scripts/run_qa.py [--runs 1000]
Exit code is 0 only if all tests passed (so CI fails when tests fail).
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qa.logger import setup_logging  # noqa: E402
from qa.performance import run_game_benchmarks, save_benchmarks  # noqa: E402
from qa.report_generator import generate_report, print_summary  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Run GameTestPro QA pipeline")
    parser.add_argument("--runs", type=int, default=1000, help="benchmark runs per operation")
    args = parser.parse_args()

    logger = setup_logging()
    (ROOT / "reports").mkdir(exist_ok=True)

    env = dict(os.environ)
    env.pop("GAMETESTPRO_DEMO_BUG", None)  # a real run must never use the demo defect

    print(">> Step 1/3: running pytest ...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--junitxml=reports/junit.xml", "--record-bugs", "-v"],
        cwd=ROOT, env=env)

    print(f">> Step 2/3: running local benchmark ({args.runs} runs per operation) ...")
    save_benchmarks(run_game_benchmarks(args.runs))
    logger.info("Benchmarks saved")

    print(">> Step 3/3: generating report ...")
    report = generate_report()
    print_summary(report)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

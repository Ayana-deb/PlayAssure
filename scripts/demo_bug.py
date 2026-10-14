"""Demonstration: an intentionally introduced defect is caught by the tests.

Phase 1: run tests against demo/buggy_game_engine.py (env GAMETESTPRO_DEMO_BUG=1)
         -> some tests FAIL and bugs are recorded as 'Open'.
Phase 2: run the same tests against the real, correct engine
         -> tests PASS and those bugs are marked 'Fixed'.

The real engine (game/game_engine.py) is never edited.
Usage:  python scripts/demo_bug.py [--fresh]   (--fresh deletes old bug reports first)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qa.bug_reporter import DEFAULT_BUG_FILE, BugReporter  # noqa: E402

CMD = [sys.executable, "-m", "pytest", "tests/test_game_engine.py",
       "--record-bugs", "-q", "--tb=line", "-p", "no:cacheprovider"]


def show_bugs(title):
    print(f"\n--- {title} ---")
    for b in BugReporter().list_bugs():
        print(f"{b['bug_id']} [{b['severity']:<8}] {b['status']:<15} {b['test_case']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fresh", action="store_true", help="delete existing bugs.json first")
    args = parser.parse_args()
    if args.fresh and DEFAULT_BUG_FILE.exists():
        DEFAULT_BUG_FILE.unlink()

    print("=== PHASE 1: tests against the BUGGY engine (failures expected) ===")
    buggy_env = dict(os.environ, GAMETESTPRO_DEMO_BUG="1")
    phase1 = subprocess.run(CMD, cwd=ROOT, env=buggy_env).returncode
    show_bugs("Bug reports after phase 1")

    print("\n=== PHASE 2: same tests against the CORRECT engine (all should pass) ===")
    clean_env = {k: v for k, v in os.environ.items() if k != "GAMETESTPRO_DEMO_BUG"}
    phase2 = subprocess.run(CMD, cwd=ROOT, env=clean_env).returncode
    show_bugs("Bug reports after phase 2")

    ok = phase1 != 0 and phase2 == 0
    print("\nRESULT:", "defect detected, then fixed - demo worked" if ok else "unexpected result, see output above")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

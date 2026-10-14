# GameTestPro — Automated Game QA Testing & Monitoring Framework

A small Python framework that shows how a QA engineer tests a game: automated test cases, bug reports, logs, local performance numbers, test reports, and a CI workflow. The "game" is a text-only simulation, so all the effort goes into the **testing**, not the graphics.

## Problem statement
Game teams ship updates often. Manual testing is slow and misses regressions (old bugs coming back). This project shows how automated checks, structured bug reports, logs and reports make testing repeatable and traceable.

## Objectives
1. Design and run test cases for game features
2. Detect, document and report bugs
3. Automate testing with pytest
4. Record application and test logs
5. Collect local performance metrics
6. Generate test execution reports
7. Run tests automatically on every push (GitHub Actions)

## Features (all implemented)
- `GameEngine` simulation with validation (no negative scores, no scoring after game over, state-transition checks, max-score limit)
- 46 pytest tests (game logic, bug reporter, performance module), with fixtures and parametrized tests
- Bug reporter: unique IDs, severity, status (Open / Fixed / Retest Required), reproduction steps, stored in JSON
- Automatic bug recording with `--record-bugs` (only for failed assertions, never for passing tests)
- Logging with Python `logging` to `logs/gametestpro.log` (folders are created automatically)
- Benchmark with `time.perf_counter()`: runs, average, min, max, total
- Report generator: `reports/report.json` + `reports/report.html` dashboard built from real results
- Demo script that introduces a defect, shows the tests catching it, then shows the fix
- GitHub Actions workflow

## Project structure
```
gametestpro/
├── game/
│   ├── __init__.py
│   └── game_engine.py        # system under test (knows nothing about QA code)
├── qa/
│   ├── __init__.py
│   ├── logger.py             # logging setup
│   ├── bug_reporter.py       # JSON bug reports
│   ├── performance.py        # perf_counter benchmarks
│   └── report_generator.py   # reads junit.xml + data -> JSON/HTML report
├── tests/
│   ├── conftest.py           # fixtures + hooks (logging, auto bug recording)
│   ├── test_game_engine.py
│   ├── test_bug_reporting.py
│   └── test_performance.py
├── demo/
│   └── buggy_game_engine.py  # DEMO ONLY: deliberately broken engine
├── scripts/
│   ├── run_qa.py             # tests + benchmark + report in one command
│   └── demo_bug.py           # bug-detection demonstration
├── .github/workflows/tests.yml
├── pytest.ini
├── requirements.txt
├── .gitignore
└── README.md
```
Created automatically when needed: `logs/`, `reports/`, `bug_reports/`.

**How it fits together:** pytest runs the tests against `game/`. `tests/conftest.py` hooks log each result and (with `--record-bugs`) save failures through `qa/bug_reporter.py`. pytest writes `reports/junit.xml`; `qa/report_generator.py` reads it together with the benchmark and bug data.

## Technologies
Python 3 (tested on 3.12), pytest, `logging`, `time`, `statistics`, `json`, `xml.etree`, Git/GitHub, GitHub Actions. Only one dependency: pytest.

## Installation
```bash
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
```

## Run the tests
```bash
python -m pytest -v
```
Each line shows `PASSED` or `FAILED`. The last line, e.g. `46 passed in 0.10s`, is the summary. A failure shows the failing line and the expected-vs-actual values.

## Generate the report
```bash
python scripts/run_qa.py
```
This runs the tests, the benchmark and the report generator. Then open `reports/report.html` in a browser. To regenerate the report from existing results: `python -m qa.report_generator`.

## Bug-detection demo
```bash
python scripts/demo_bug.py --fresh
```
- Phase 1 loads `demo/buggy_game_engine.py` (two defects: scoring allowed when the game is not running, and negative scores accepted). 3 tests fail and 3 bug reports are created as `Open`.
- Phase 2 runs the same tests against the real engine. They pass and the bugs become `Fixed`.
- The real `game/game_engine.py` is **never edited**. The broken engine is only loaded when the environment variable `GAMETESTPRO_DEMO_BUG=1` is set.

Manual version (macOS/Linux): `GAMETESTPRO_DEMO_BUG=1 python -m pytest tests/test_game_engine.py --record-bugs`.
Windows PowerShell: `$env:GAMETESTPRO_DEMO_BUG="1"; python -m pytest tests/test_game_engine.py --record-bugs; Remove-Item Env:GAMETESTPRO_DEMO_BUG`.

## Example bug report (`bug_reports/bugs.json`)
```json
{
  "bug_id": "BUG-0001",
  "timestamp": "2026-10-14T14:54:34",
  "test_case": "tests/test_game_engine.py::test_negative_score_is_rejected",
  "description": "Automated test failed: test_negative_score_is_rejected",
  "expected_result": "Negative points raise InvalidScoreError.",
  "actual_result": "Failed: DID NOT RAISE InvalidScoreError",
  "severity": "High",
  "reproduction_steps": [
    "Open a terminal in the project root",
    "Set GAMETESTPRO_DEMO_BUG=1 (loads the demo defect)",
    "Run: python -m pytest \"tests/test_game_engine.py::test_negative_score_is_rejected\" -v",
    "Observe the failing assertion"
  ],
  "status": "Open"
}
```
Severity comes from the `@pytest.mark.severity("High")` marker on a test (default: Medium).

## Performance-testing methodology
- `time.perf_counter()` is read just before and after each operation.
- Each operation runs 1000 times (change with `--runs`). A fresh engine is created **outside** the timer each time.
- Engine log output is silenced during the benchmark so disk writes are not measured.
- Reported: executions, average, min, max, total (milliseconds), calculated with the `statistics` module.
- **These are local Python execution times on your computer. They are not cloud-server or network latency.** Results vary between machines and runs.

## Screenshots (add your own)
| What | File |
|---|---|
| Terminal: pytest passing | `docs/screenshots/pytest_pass.png` |
| Terminal: demo with failing tests | `docs/screenshots/demo_failures.png` |
| HTML dashboard | `docs/screenshots/dashboard.png` |
| GitHub Actions green run | `docs/screenshots/actions.png` |

## Limitations
- The game is a simple simulation; there is no graphics, input or network testing
- Benchmarks are local only; no real cloud infrastructure is tested
- Bug recording is rule-based: it records failed assertions, but a human still decides the real severity and root cause
- The bug-reporter unit tests write sample lines to the shared log file (not to `bugs.json`)
- JSON files, no database; not designed for several people writing at once

## Future improvements (not implemented)
- Test a real HTTP game server and measure real latency
- Load/stress tests with many simulated players
- Trend charts across many runs
- Send CI results to Slack/email; link bugs to GitHub Issues
- Test coverage report (`pytest-cov`)

## Upload to GitHub
```bash
git init
git add .
git commit -m "Initial commit: GameTestPro QA framework"
git branch -M main
git remote add origin https://github.com/<your-username>/gametestpro.git
git push -u origin main
```
Create the empty repository on github.com first (no README). The workflow starts automatically: open the **Actions** tab to see the run. It fails if any test fails.

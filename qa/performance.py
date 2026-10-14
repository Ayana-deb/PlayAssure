"""Local performance measurement using time.perf_counter().

IMPORTANT: these numbers measure how long Python functions take on THIS
computer. They are NOT cloud-server latency or network measurements.
"""

import json
import logging
import statistics
import time
from datetime import datetime
from pathlib import Path

from qa.logger import ROOT_DIR

PERF_FILE = ROOT_DIR / "reports" / "performance.json"
NOTE = ("Local execution timings of Python functions measured with time.perf_counter(). "
        "Not cloud-server or network latency.")


def summarize(name, timings_seconds):
    """Turn a list of timings (seconds) into a summary dict (values in milliseconds)."""
    if not timings_seconds:
        raise ValueError("No timings to summarize")
    ms = [t * 1000 for t in timings_seconds]
    return {
        "operation": name,
        "executions": len(ms),
        "average_ms": round(statistics.mean(ms), 6),
        "min_ms": round(min(ms), 6),
        "max_ms": round(max(ms), 6),
        "total_ms": round(sum(ms), 6),
    }


def benchmark(name, operation, runs=1000, setup=None):
    """Run `operation(subject)` `runs` times. Only the operation itself is timed;
    `setup()` (creating a fresh subject) happens outside the timer."""
    if runs < 1:
        raise ValueError("runs must be at least 1")
    setup = setup or (lambda: None)
    timings = []
    for _ in range(runs):
        subject = setup()
        start = time.perf_counter()
        operation(subject)
        timings.append(time.perf_counter() - start)
    return summarize(name, timings)


def run_game_benchmarks(runs=1000):
    """Benchmark selected GameEngine operations. Returns a dict of real results."""
    from game.game_engine import GameEngine  # imported here to keep qa/ loosely coupled

    def started_engine():
        g = GameEngine()
        g.start_game()
        return g

    def full_session(g):
        g.start_game()
        g.update_score(10)
        g.end_game()
        g.reset_game()

    # Silence the engine's own log lines so disk writes are not part of the timing.
    game_logger = logging.getLogger("gametestpro.game")
    old_level = game_logger.level
    game_logger.setLevel(logging.CRITICAL)
    try:
        results = [
            benchmark("start_game", lambda g: g.start_game(), runs, setup=GameEngine),
            benchmark("update_score", lambda g: g.update_score(10), runs, setup=started_engine),
            benchmark("full_session", full_session, runs, setup=GameEngine),
        ]
    finally:
        game_logger.setLevel(old_level)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "runs_per_operation": runs,
        "note": NOTE,
        "results": results,
    }


def save_benchmarks(data, path=PERF_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_benchmarks(path=PERF_FILE):
    path = Path(path)
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

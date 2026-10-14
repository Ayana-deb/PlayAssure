"""Shared fixtures and pytest hooks.

Hooks here do two QA jobs automatically:
  * write every test result to logs/gametestpro.log
  * with --record-bugs, save genuine test FAILURES to bug_reports/bugs.json
"""

import logging
import os

import pytest

from game.game_engine import GameEngine
from qa.bug_reporter import BugReporter
from qa.logger import setup_logging

setup_logging()
logger = logging.getLogger("gametestpro.tests")


def pytest_addoption(parser):
    parser.addoption("--record-bugs", action="store_true", default=False,
                     help="Record failed tests as bug reports in bug_reports/bugs.json")


def _engine_class():
    """Normal runs use the real GameEngine. The demo script sets
    GAMETESTPRO_DEMO_BUG=1 to swap in a deliberately broken engine."""
    if os.environ.get("GAMETESTPRO_DEMO_BUG") == "1":
        from demo.buggy_game_engine import BuggyGameEngine
        logger.warning("DEMO MODE: using BuggyGameEngine")
        return BuggyGameEngine
    return GameEngine


@pytest.fixture
def game():
    """A fresh engine for every test (no shared state between tests)."""
    return _engine_class()()


@pytest.fixture
def running_game(game):
    """An engine that has already been started."""
    game.start_game()
    return game


def pytest_sessionstart(session):
    logger.info("Test session started")


def pytest_sessionfinish(session, exitstatus):
    logger.info("Test session finished (exit status %s)", exitstatus)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    record = item.config.getoption("record_bugs")

    if report.when == "setup":
        if report.skipped:
            logger.info("SKIPPED %s", item.nodeid)
        elif report.failed:
            logger.error("ERROR (setup) %s", item.nodeid)
    elif report.when == "call":
        if report.passed:
            logger.info("PASSED  %s (%.4fs)", item.nodeid, report.duration)
            if record:
                _close_bug_if_fixed(item)
        elif report.failed:
            logger.error("FAILED  %s | %s", item.nodeid, call.excinfo.exconly()[:300])
            if record:
                _record_bug(item, call)


def _record_bug(item, call):
    exc = call.excinfo.value
    # Only failed assertions / pytest.raises mismatches count as bug candidates.
    # Other exceptions (ImportError, TypeError in the test itself...) may be test
    # mistakes, so they are logged but NOT labelled as bugs automatically.
    if not isinstance(exc, (AssertionError, pytest.fail.Exception)):
        logger.warning("%s raised %s - not auto-recorded, triage manually",
                       item.nodeid, type(exc).__name__)
        return

    reporter = BugReporter()
    existing = reporter.find_open_bug(item.nodeid)
    if existing:
        if existing["status"] == "Retest Required":
            reporter.update_status(existing["bug_id"], "Open")
        return  # do not create duplicates

    marker = item.get_closest_marker("severity")
    severity = marker.args[0] if marker and marker.args else "Medium"
    func = getattr(item, "function", None)
    doc = (func.__doc__ or "").strip().splitlines() if func else []
    expected = doc[0] if doc else item.name

    steps = ["Open a terminal in the project root"]
    if os.environ.get("GAMETESTPRO_DEMO_BUG") == "1":
        steps.append("Set GAMETESTPRO_DEMO_BUG=1 (loads the demo defect)")
    steps += [f'Run: python -m pytest "{item.nodeid}" -v', "Observe the failing assertion"]

    reporter.report_bug(
        test_name=item.nodeid,
        description=f"Automated test failed: {item.name}",
        expected=expected,
        actual=call.excinfo.exconly()[:500],
        severity=severity,
        steps=steps,
    )


def _close_bug_if_fixed(item):
    """A test that used to fail now passes -> mark its bug as Fixed."""
    reporter = BugReporter()
    bug = reporter.find_open_bug(item.nodeid)
    if bug:
        reporter.update_status(bug["bug_id"], "Fixed")

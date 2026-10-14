"""Tests for the bug reporter. They use tmp_path so the real bugs.json is never touched."""

import json

import pytest

from qa.bug_reporter import BugReporter


@pytest.fixture
def reporter(tmp_path):
    return BugReporter(tmp_path / "bugs.json")


def _report(reporter, **overrides):
    data = dict(test_name="tests/test_x.py::test_a", description="Score went negative",
                expected="InvalidScoreError", actual="no error", severity="High",
                steps=["Start game", "update_score(-5)"])
    data.update(overrides)
    return reporter.report_bug(**data)


def test_report_bug_stores_all_fields(reporter):
    """A reported bug contains every required field with the given values."""
    bug = _report(reporter)
    assert bug["bug_id"] == "BUG-0001"
    assert bug["status"] == "Open"
    assert bug["severity"] == "High"
    assert bug["test_case"] == "tests/test_x.py::test_a"
    assert bug["reproduction_steps"] == ["Start game", "update_score(-5)"]
    assert bug["timestamp"]


def test_bug_is_saved_as_valid_json(reporter):
    """The JSON file on disk contains the reported bug."""
    _report(reporter)
    data = json.loads(reporter.file_path.read_text())
    assert len(data) == 1 and data[0]["bug_id"] == "BUG-0001"


def test_bug_ids_are_unique_and_sequential(reporter):
    """Each new bug gets the next ID."""
    ids = [_report(reporter)["bug_id"] for _ in range(3)]
    assert ids == ["BUG-0001", "BUG-0002", "BUG-0003"]


def test_empty_reporter_has_no_bugs(reporter):
    """A new reporter with no file returns an empty list (a passing run creates no bugs)."""
    assert reporter.list_bugs() == []


def test_invalid_severity_is_rejected(reporter):
    """Unknown severity values raise ValueError and nothing is saved."""
    with pytest.raises(ValueError):
        _report(reporter, severity="Urgent")
    assert reporter.list_bugs() == []


def test_missing_description_is_rejected(reporter):
    """A bug without a description raises ValueError."""
    with pytest.raises(ValueError):
        _report(reporter, description="")


def test_update_status_changes_bug(reporter):
    """Status can move from Open to Retest Required to Fixed."""
    bug = _report(reporter)
    reporter.update_status(bug["bug_id"], "Retest Required")
    assert reporter.get_bug(bug["bug_id"])["status"] == "Retest Required"
    reporter.update_status(bug["bug_id"], "Fixed")
    assert reporter.get_bug(bug["bug_id"])["status"] == "Fixed"


def test_invalid_status_is_rejected(reporter):
    """Unknown status values raise ValueError."""
    bug = _report(reporter)
    with pytest.raises(ValueError):
        reporter.update_status(bug["bug_id"], "Closed")


def test_update_unknown_bug_raises(reporter):
    """Updating a bug ID that does not exist raises KeyError."""
    with pytest.raises(KeyError):
        reporter.update_status("BUG-9999", "Fixed")


def test_find_open_bug_ignores_fixed_bugs(reporter):
    """find_open_bug only returns unresolved bugs."""
    bug = _report(reporter)
    assert reporter.find_open_bug("tests/test_x.py::test_a") is not None
    reporter.update_status(bug["bug_id"], "Fixed")
    assert reporter.find_open_bug("tests/test_x.py::test_a") is None


def test_corrupted_file_gives_clear_error(tmp_path):
    """A broken JSON file raises ValueError instead of silently losing data."""
    path = tmp_path / "bugs.json"
    path.write_text("{not json")
    with pytest.raises(ValueError):
        BugReporter(path).list_bugs()

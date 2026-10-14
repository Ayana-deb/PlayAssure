"""Store bug reports in a JSON file (bug_reports/bugs.json by default)."""

import json
import logging
from datetime import datetime
from pathlib import Path

from qa.logger import ROOT_DIR

logger = logging.getLogger("gametestpro.bugs")

DEFAULT_BUG_FILE = ROOT_DIR / "bug_reports" / "bugs.json"
SEVERITIES = ("Low", "Medium", "High", "Critical")
STATUSES = ("Open", "Fixed", "Retest Required")


def _now():
    return datetime.now().isoformat(timespec="seconds")


class BugReporter:
    def __init__(self, file_path=DEFAULT_BUG_FILE):
        self.file_path = Path(file_path)

    # ---- file helpers -------------------------------------------------
    def _load(self):
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                bugs = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{self.file_path} is not valid JSON: {exc}") from exc
        if not isinstance(bugs, list):
            raise ValueError(f"{self.file_path} must contain a JSON list")
        return bugs

    def _save(self, bugs):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(bugs, f, indent=2)

    @staticmethod
    def _next_id(bugs):
        numbers = [int(b["bug_id"].split("-")[1]) for b in bugs]
        return f"BUG-{(max(numbers) + 1 if numbers else 1):04d}"

    # ---- public API ---------------------------------------------------
    def report_bug(self, test_name, description, expected, actual,
                   severity="Medium", steps=None, status="Open"):
        if not test_name or not description:
            raise ValueError("test_name and description are required")
        if severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}")
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        if isinstance(steps, str):
            steps = [steps]

        bugs = self._load()
        bug = {
            "bug_id": self._next_id(bugs),
            "timestamp": _now(),
            "test_case": test_name,
            "description": description,
            "expected_result": expected,
            "actual_result": actual,
            "severity": severity,
            "reproduction_steps": list(steps or []),
            "status": status,
        }
        bugs.append(bug)
        self._save(bugs)
        logger.warning("Bug %s recorded for %s (severity=%s)", bug["bug_id"], test_name, severity)
        return bug

    def list_bugs(self, status=None):
        bugs = self._load()
        return [b for b in bugs if status is None or b["status"] == status]

    def get_bug(self, bug_id):
        for bug in self._load():
            if bug["bug_id"] == bug_id:
                return bug
        return None

    def find_open_bug(self, test_name):
        """Return an unresolved bug (Open / Retest Required) for this test, or None."""
        for bug in self._load():
            if bug["test_case"] == test_name and bug["status"] in ("Open", "Retest Required"):
                return bug
        return None

    def update_status(self, bug_id, new_status):
        if new_status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        bugs = self._load()
        for bug in bugs:
            if bug["bug_id"] == bug_id:
                bug["status"] = new_status
                bug["updated_at"] = _now()
                self._save(bugs)
                logger.info("Bug %s status changed to %s", bug_id, new_status)
                return bug
        raise KeyError(f"No bug with id {bug_id}")

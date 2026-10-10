"""
Tests for metrics computation.
Run: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from pathlib import Path

import config
config.DB_PATH = Path(tempfile.mktemp(suffix=".db"))

from database.database import (
    init_db, create_project, create_requirement, create_test_case,
    create_execution, save_execution_result, create_bug, get_project_metrics
)


@pytest.fixture(autouse=True)
def setup():
    config.DB_PATH = Path(tempfile.mktemp(suffix=".db"))
    init_db()
    yield
    try:
        config.DB_PATH.unlink()
    except Exception:
        pass


def _setup_project_with_results(pass_count: int, fail_count: int, bug_count: int):
    pid = create_project("Metrics Project", "", "http://localhost:5000")
    rid = create_requirement(pid, "REQ001", "Login", "", "High")
    tc_ids = []
    for i in range(pass_count + fail_count):
        tc_id = create_test_case(pid, rid, f"TC{i:03d}", f"Test {i}")
        tc_ids.append(tc_id)

    exec_id = create_execution(pid, "Run 1", "chromium", True, "http://localhost:5000")
    for i, tc_id in enumerate(tc_ids):
        result = "Pass" if i < pass_count else "Fail"
        save_execution_result(exec_id, tc_id, result, 1000)

    for i in range(bug_count):
        create_bug(pid, f"BUG-{i+1:03d}", f"Bug {i+1}", severity="High")

    return pid


def test_pass_rate_100():
    pid = _setup_project_with_results(5, 0, 0)
    m = get_project_metrics(pid)
    assert m["pass_rate"] == 100.0
    assert m["passes"] == 5
    assert m["fails"] == 0


def test_pass_rate_0():
    pid = _setup_project_with_results(0, 3, 0)
    m = get_project_metrics(pid)
    assert m["pass_rate"] == 0.0
    assert m["fails"] == 3


def test_pass_rate_mixed():
    pid = _setup_project_with_results(3, 1, 0)  # 3 pass, 1 fail = 75%
    m = get_project_metrics(pid)
    assert m["pass_rate"] == 75.0


def test_bug_counts():
    pid = _setup_project_with_results(2, 1, 3)
    m = get_project_metrics(pid)
    assert m["open_bugs"] == 3


def test_empty_project_metrics():
    pid = create_project("Empty Project", "", "")
    m = get_project_metrics(pid)
    assert m["total_requirements"] == 0
    assert m["total_test_cases"] == 0
    assert m["pass_rate"] == 0.0
    assert m["open_bugs"] == 0


def test_total_requirements():
    pid = create_project("Req Metrics", "", "")
    create_requirement(pid, "R1", "Req 1", "", "High")
    create_requirement(pid, "R2", "Req 2", "", "Medium")
    m = get_project_metrics(pid)
    assert m["total_requirements"] == 2

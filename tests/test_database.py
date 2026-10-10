"""
Tests for database operations.
Run: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from pathlib import Path

# Use a temp DB for testing
import config
_orig_db = config.DB_PATH
config.DB_PATH = Path(tempfile.mktemp(suffix=".db"))

from database.database import (
    init_db, create_project, get_projects, get_project, delete_project,
    create_requirement, get_requirements, delete_requirement,
    create_test_case, get_test_cases, delete_test_case,
    add_test_steps, get_test_steps,
    create_bug, get_bugs, get_next_bug_id,
    get_setting, set_setting,
)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    # cleanup
    try:
        config.DB_PATH.unlink()
    except Exception:
        pass
    config.DB_PATH = Path(tempfile.mktemp(suffix=".db"))
    init_db()


# ── Settings ──────────────────────────────────────────────────────────────────

def test_settings_default():
    val = get_setting("browser", "chromium")
    assert val in ("chromium", "")  # may or may not have default


def test_settings_set_get():
    set_setting("test_key", "test_value")
    assert get_setting("test_key") == "test_value"


def test_settings_update():
    set_setting("test_key", "first")
    set_setting("test_key", "second")
    assert get_setting("test_key") == "second"


# ── Projects ──────────────────────────────────────────────────────────────────

def test_create_project():
    pid = create_project("Test Project", "A test", "http://localhost:3000")
    assert pid > 0


def test_get_projects():
    create_project("P1", "", "")
    create_project("P2", "", "")
    projects = get_projects()
    assert len(projects) >= 2


def test_get_project():
    pid = create_project("Solo Project", "desc", "")
    p = get_project(pid)
    assert p is not None
    assert p["name"] == "Solo Project"


def test_delete_project():
    pid = create_project("To Delete", "", "")
    delete_project(pid)
    p = get_project(pid)
    assert p is None


# ── Requirements ──────────────────────────────────────────────────────────────

def test_create_requirement():
    pid = create_project("Req Project", "", "")
    rid = create_requirement(pid, "REQ001", "User Login", "...", "High")
    assert rid > 0


def test_get_requirements():
    pid = create_project("Req Project 2", "", "")
    create_requirement(pid, "REQ001", "Login", "", "High")
    create_requirement(pid, "REQ002", "Register", "", "Medium")
    reqs = get_requirements(pid)
    assert len(reqs) == 2


def test_delete_requirement():
    pid = create_project("Del Req Project", "", "")
    rid = create_requirement(pid, "REQ001", "To Delete", "", "Low")
    delete_requirement(rid)
    reqs = get_requirements(pid)
    assert len(reqs) == 0


# ── Test Cases ────────────────────────────────────────────────────────────────

def test_create_test_case():
    pid = create_project("TC Project", "", "")
    rid = create_requirement(pid, "REQ001", "Login", "", "High")
    tc_id = create_test_case(pid, rid, "TC001", "Valid Login")
    assert tc_id > 0


def test_get_test_cases():
    pid = create_project("TC Project 2", "", "")
    rid = create_requirement(pid, "REQ001", "Login", "", "High")
    create_test_case(pid, rid, "TC001", "Valid Login")
    create_test_case(pid, rid, "TC002", "Invalid Login")
    tcs = get_test_cases(pid)
    assert len(tcs) == 2


def test_test_case_preserves_details_and_steps():
    """A saved login test case retains its requirement, data, and ordered steps."""
    pid = create_project("Login Test Project", "", "")
    rid = create_requirement(pid, "REQ-LOGIN", "User login", "Users can sign in", "High")
    tc_id = create_test_case(
        pid, rid, "TC-LOGIN-001", "Sign in with valid credentials",
        description="Verify that an active user can access the dashboard.",
        test_type="Functional",
        preconditions="An active user account exists.",
        test_data='{"email":"user@example.com","password":"correct-password"}',
        expected_result="The user is authenticated and the dashboard is displayed.",
        priority="High", severity="Critical", automation="Manual",
        created_by="Tester",
    )
    add_test_steps(tc_id, [
        {"action": "Open the login page and enter valid credentials", "expected": "Credentials are accepted"},
        {"action": "Submit the login form", "expected": "The dashboard is displayed"},
    ])

    cases = get_test_cases(pid, rid)
    assert len(cases) == 1
    case = cases[0]
    assert case["tc_id"] == "TC-LOGIN-001"
    assert case["scenario"] == "Sign in with valid credentials"
    assert case["req_ref"] == "REQ-LOGIN"
    assert case["expected_result"] == "The user is authenticated and the dashboard is displayed."
    steps = get_test_steps(tc_id)
    assert [step["step_number"] for step in steps] == [1, 2]
    assert steps[1]["expected"] == "The dashboard is displayed"


# ── Bugs ──────────────────────────────────────────────────────────────────────

def test_create_bug():
    pid = create_project("Bug Project", "", "")
    bug_id = create_bug(pid, "BUG-001", "Login fails")
    assert bug_id > 0


def test_get_bugs():
    pid = create_project("Bug Project 2", "", "")
    create_bug(pid, "BUG-001", "Bug One")
    create_bug(pid, "BUG-002", "Bug Two")
    bugs = get_bugs(pid)
    assert len(bugs) == 2


def test_next_bug_id():
    pid = create_project("Bug ID Project", "", "")
    assert get_next_bug_id(pid) == "BUG-001"
    create_bug(pid, "BUG-001", "First")
    assert get_next_bug_id(pid) == "BUG-002"

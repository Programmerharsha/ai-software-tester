"""
SQLite database manager — connection, CRUD helpers.
"""

import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from database.schema import SCHEMA_SQL

# ── resolved at import time using config ──────────────────────────────────────
from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor():
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create all tables if they do not exist and seed initial demo project if empty."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    seed_demo_data(force=False)


def seed_demo_data(force: bool = False) -> Optional[int]:
    """Seed a realistic starter project if database is empty or force=True."""
    count_row = fetch_one("SELECT count(*) as cnt FROM projects")
    if not force and count_row and count_row["cnt"] > 0:
        return None

    pid = create_project(
        name="Demo E-Commerce & Auth Project",
        description="Live sample target featuring authentication, API endpoints, and seeded QA edge cases.",
        base_url="http://127.0.0.1:5000",
    )

    # Requirements
    r1 = create_requirement(
        project_id=pid,
        req_id="REQ001",
        title="User Authentication & Login",
        description="The system must authenticate registered users using email and password, redirecting to /dashboard. Incorrect credentials must produce an inline error alert.",
        priority="High",
    )
    r2 = create_requirement(
        project_id=pid,
        req_id="REQ002",
        title="User Registration & Validation",
        description="Allows new users to create an account. Passwords and confirmation passwords must match. Duplicate email registrations must be prevented.",
        priority="Medium",
    )

    # Test Case 1: Valid Login
    tc1_actions = json.dumps({
        "actions": [
            {"type": "navigate", "url": "/login"},
            {"type": "fill", "selector": "input[name='email'], #email", "value": "test@example.com"},
            {"type": "fill", "selector": "input[name='password'], #password", "value": "Test123!"},
            {"type": "click", "selector": "button[type='submit'], #login"},
            {"type": "wait", "ms": 500},
            {"type": "assert_url", "expected_url": "/dashboard"},
            {"type": "screenshot", "label": "login_redirect"}
        ]
    })
    tc1 = create_test_case(
        project_id=pid,
        requirement_id=r1,
        tc_id="TC001",
        scenario="Valid User Login and Dashboard Redirection",
        description="Verify registered user with valid password is authenticated and directed to /dashboard.",
        test_type="Functional",
        preconditions="Registered user account test@example.com exists.",
        test_data=json.dumps({"email": "test@example.com", "password": "Test123!"}),
        expected_result="User successfully redirected to /dashboard.",
        priority="High",
        severity="Critical",
        automation="Automated",
        actions_json=tc1_actions,
        created_by="AI",
    )
    add_test_steps(tc1, [
        {"action": "Navigate to /login", "expected": "Login page loaded"},
        {"action": "Enter registered email and password", "expected": "Fields populated"},
        {"action": "Click Login button", "expected": "Redirects to /dashboard"},
    ])

    # Test Case 2: Invalid Password
    tc2_actions = json.dumps({
        "actions": [
            {"type": "navigate", "url": "/login"},
            {"type": "fill", "selector": "input[name='email'], #email", "value": "test@example.com"},
            {"type": "fill", "selector": "input[name='password'], #password", "value": "WrongPassword99!"},
            {"type": "click", "selector": "button[type='submit'], #login"},
            {"type": "wait", "ms": 500},
            {"type": "assert_visible", "selector": ".error, .alert-danger"},
            {"type": "screenshot", "label": "invalid_credentials"}
        ]
    })
    tc2 = create_test_case(
        project_id=pid,
        requirement_id=r1,
        tc_id="TC002",
        scenario="Invalid Password Submission",
        description="Verify appropriate error message appears when wrong password is used.",
        test_type="Functional",
        preconditions="Registered user account test@example.com exists.",
        test_data=json.dumps({"email": "test@example.com", "password": "WrongPassword99!"}),
        expected_result="Error message 'Invalid email or password' displayed.",
        priority="High",
        severity="High",
        automation="Automated",
        actions_json=tc2_actions,
        created_by="AI",
    )
    add_test_steps(tc2, [
        {"action": "Navigate to /login", "expected": "Login page loaded"},
        {"action": "Enter email and incorrect password", "expected": "Fields populated"},
        {"action": "Click Login button", "expected": "Error message displayed"},
    ])

    # Test Case 3: API Login
    tc3_actions = json.dumps({
        "api_tests": [
            {
                "method": "POST",
                "endpoint": "/api/login",
                "headers": {"Content-Type": "application/json"},
                "body": {"email": "test@example.com", "password": "Test123!"},
                "assertions": [
                    {"type": "status", "operator": "eq", "expected": 200},
                    {"type": "json_field", "path": "status", "operator": "eq", "expected": "success"},
                    {"type": "response_time", "max_ms": 2000}
                ]
            }
        ]
    })
    tc3 = create_test_case(
        project_id=pid,
        requirement_id=r1,
        tc_id="TC003",
        scenario="REST API Authentication Endpoint",
        description="Verify /api/login endpoint returns 200 and success status for valid JSON payload.",
        test_type="API",
        preconditions="API service running.",
        test_data=json.dumps({"email": "test@example.com", "password": "Test123!"}),
        expected_result="HTTP status 200 with status=success JSON response.",
        priority="High",
        severity="High",
        automation="Automated",
        actions_json=tc3_actions,
        created_by="AI",
    )
    add_test_steps(tc3, [
        {"action": "Send POST /api/login with valid credentials", "expected": "HTTP 200 and success status"},
    ])

    return pid


# ─────────────────────────────── Generic helpers ──────────────────────────────

def fetch_all(sql: str, params: tuple = ()) -> List[Dict]:
    with db_cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_one(sql: str, params: tuple = ()) -> Optional[Dict]:
    with db_cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
    return dict(row) if row else None


def execute(sql: str, params: tuple = ()) -> int:
    """Execute INSERT/UPDATE/DELETE. Returns lastrowid for INSERT."""
    with db_cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


# ─────────────────────────────── Settings ────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    row = fetch_one("SELECT value FROM settings WHERE key=?", (key,))
    return row["value"] if row else default


def set_setting(key: str, value: str):
    execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
        (key, value),
    )


def get_all_settings() -> Dict[str, str]:
    rows = fetch_all("SELECT key, value FROM settings")
    return {r["key"]: r["value"] for r in rows}


# ─────────────────────────────── Projects ────────────────────────────────────

def create_project(name: str, description: str = "", base_url: str = "") -> int:
    return execute(
        "INSERT INTO projects (name, description, base_url) VALUES (?, ?, ?)",
        (name, description, base_url),
    )


def get_projects() -> List[Dict]:
    return fetch_all("SELECT * FROM projects ORDER BY created_at DESC")


def get_project(project_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM projects WHERE id=?", (project_id,))


def update_project(project_id: int, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [project_id]
    execute(f"UPDATE projects SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", tuple(values))


def delete_project(project_id: int):
    execute("DELETE FROM projects WHERE id=?", (project_id,))


# ─────────────────────────────── Requirements ─────────────────────────────────

def create_requirement(project_id: int, req_id: str, title: str,
                       description: str = "", priority: str = "Medium") -> int:
    return execute(
        "INSERT INTO requirements (project_id, req_id, title, description, priority) VALUES (?,?,?,?,?)",
        (project_id, req_id, title, description, priority),
    )


def get_requirements(project_id: int) -> List[Dict]:
    return fetch_all(
        "SELECT * FROM requirements WHERE project_id=? ORDER BY created_at DESC",
        (project_id,),
    )


def get_requirement(req_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM requirements WHERE id=?", (req_id,))


def update_requirement_analysis(req_id: int, analysis_json: str):
    execute(
        "UPDATE requirements SET analysis=?, status='Analysed', updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (analysis_json, req_id),
    )


def update_requirement(req_id: int, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [req_id]
    execute(f"UPDATE requirements SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", tuple(values))


def delete_requirement(req_id: int):
    execute("DELETE FROM requirements WHERE id=?", (req_id,))


# ─────────────────────────────── Test Cases ──────────────────────────────────

def create_test_case(project_id: int, requirement_id: Optional[int], tc_id: str,
                     scenario: str, description: str = "", test_type: str = "Functional",
                     preconditions: str = "", test_data: str = "", expected_result: str = "",
                     priority: str = "Medium", severity: str = "Medium",
                     automation: str = "Manual", actions_json: str = "",
                     created_by: str = "AI") -> int:
    return execute(
        """INSERT INTO test_cases
           (project_id, requirement_id, tc_id, scenario, description, test_type,
            preconditions, test_data, expected_result, priority, severity, automation,
            actions_json, created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (project_id, requirement_id, tc_id, scenario, description, test_type,
         preconditions, test_data, expected_result, priority, severity, automation,
         actions_json, created_by),
    )


def get_test_cases(project_id: int, requirement_id: Optional[int] = None) -> List[Dict]:
    if requirement_id:
        return fetch_all(
            "SELECT tc.*, r.req_id as req_ref FROM test_cases tc "
            "LEFT JOIN requirements r ON tc.requirement_id=r.id "
            "WHERE tc.project_id=? AND tc.requirement_id=? ORDER BY tc.created_at DESC",
            (project_id, requirement_id),
        )
    return fetch_all(
        "SELECT tc.*, r.req_id as req_ref FROM test_cases tc "
        "LEFT JOIN requirements r ON tc.requirement_id=r.id "
        "WHERE tc.project_id=? ORDER BY tc.created_at DESC",
        (project_id,),
    )


def get_test_case(tc_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM test_cases WHERE id=?", (tc_id,))


def update_test_case(tc_id: int, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [tc_id]
    execute(f"UPDATE test_cases SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", tuple(values))


def delete_test_case(tc_id: int):
    execute("DELETE FROM test_cases WHERE id=?", (tc_id,))


def add_test_steps(tc_id: int, steps: List[Dict]):
    execute("DELETE FROM test_steps WHERE test_case_id=?", (tc_id,))
    for i, step in enumerate(steps, 1):
        execute(
            "INSERT INTO test_steps (test_case_id, step_number, action, expected) VALUES (?,?,?,?)",
            (tc_id, i, step.get("action", ""), step.get("expected", "")),
        )


def get_test_steps(tc_id: int) -> List[Dict]:
    return fetch_all(
        "SELECT * FROM test_steps WHERE test_case_id=? ORDER BY step_number",
        (tc_id,),
    )


# ─────────────────────────────── Executions ──────────────────────────────────

def create_execution(project_id: int, name: str, browser: str, headless: bool,
                     base_url: str) -> int:
    return execute(
        "INSERT INTO test_executions (project_id, name, browser, headless, base_url, started_at) "
        "VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)",
        (project_id, name, browser, int(headless), base_url),
    )


def get_executions(project_id: int) -> List[Dict]:
    return fetch_all(
        "SELECT * FROM test_executions WHERE project_id=? ORDER BY created_at DESC",
        (project_id,),
    )


def get_execution(exec_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM test_executions WHERE id=?", (exec_id,))


def update_execution_status(exec_id: int, status: str):
    execute(
        "UPDATE test_executions SET status=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
        (status, exec_id),
    )


def save_execution_result(execution_id: int, test_case_id: int, result: str,
                          duration_ms: int = 0, error_message: str = "",
                          failed_step: str = "", actual_result: str = "",
                          url_at_failure: str = "", browser_info: str = "") -> int:
    return execute(
        """INSERT INTO execution_results
           (execution_id, test_case_id, result, duration_ms, error_message,
            failed_step, actual_result, url_at_failure, browser_info)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (execution_id, test_case_id, result, duration_ms, error_message,
         failed_step, actual_result, url_at_failure, browser_info),
    )


def get_execution_results(execution_id: int) -> List[Dict]:
    return fetch_all(
        """SELECT er.*, tc.tc_id, tc.scenario
           FROM execution_results er
           JOIN test_cases tc ON er.test_case_id = tc.id
           WHERE er.execution_id=? ORDER BY er.executed_at""",
        (execution_id,),
    )


def update_result_analysis(result_id: int, analysis_json: str):
    execute(
        "UPDATE execution_results SET ai_analysis=? WHERE id=?",
        (analysis_json, result_id),
    )


# ─────────────────────────────── Bugs ────────────────────────────────────────

def create_bug(project_id: int, bug_id: str, title: str, **kwargs) -> int:
    fields = ["project_id", "bug_id", "title"] + list(kwargs.keys())
    placeholders = ", ".join(["?"] * len(fields))
    values = [project_id, bug_id, title] + list(kwargs.values())
    return execute(
        f"INSERT INTO bugs ({', '.join(fields)}) VALUES ({placeholders})",
        tuple(values),
    )


def get_bugs(project_id: int) -> List[Dict]:
    return fetch_all(
        "SELECT * FROM bugs WHERE project_id=? ORDER BY created_at DESC",
        (project_id,),
    )


def get_bug(bug_id: int) -> Optional[Dict]:
    return fetch_one("SELECT * FROM bugs WHERE id=?", (bug_id,))


def update_bug(bug_id: int, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [bug_id]
    execute(f"UPDATE bugs SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", tuple(values))


def delete_bug(bug_id: int):
    execute("DELETE FROM bugs WHERE id=?", (bug_id,))


def get_next_bug_id(project_id: int) -> str:
    row = fetch_one("SELECT COUNT(*) as cnt FROM bugs WHERE project_id=?", (project_id,))
    n = (row["cnt"] if row else 0) + 1
    return f"BUG-{n:03d}"


# ─────────────────────────────── Screenshots ─────────────────────────────────

def save_screenshot(result_id: int, file_path: str, label: str = "") -> int:
    return execute(
        "INSERT INTO screenshots (result_id, file_path, label) VALUES (?,?,?)",
        (result_id, file_path, label),
    )


def get_screenshots(result_id: int) -> List[Dict]:
    return fetch_all("SELECT * FROM screenshots WHERE result_id=?", (result_id,))


# ─────────────────────────────── AI Analysis ─────────────────────────────────

def save_ai_analysis(result_id: Optional[int], analysis_type: str, prompt_used: str,
                     raw_response: str, parsed_json: str, model_used: str,
                     duration_ms: int) -> int:
    return execute(
        """INSERT INTO ai_analysis
           (result_id, analysis_type, prompt_used, raw_response, parsed_json, model_used, duration_ms)
           VALUES (?,?,?,?,?,?,?)""",
        (result_id, analysis_type, prompt_used, raw_response, parsed_json, model_used, duration_ms),
    )


# ─────────────────────────────── Reports ─────────────────────────────────────

def save_report(project_id: int, execution_id: Optional[int], name: str,
                fmt: str, file_path: str) -> int:
    return execute(
        "INSERT INTO reports (project_id, execution_id, name, format, file_path) VALUES (?,?,?,?,?)",
        (project_id, execution_id, name, fmt, file_path),
    )


def get_reports(project_id: int) -> List[Dict]:
    return fetch_all(
        "SELECT * FROM reports WHERE project_id=? ORDER BY created_at DESC",
        (project_id,),
    )


# ─────────────────────────────── Metrics ─────────────────────────────────────

def get_project_metrics(project_id: int) -> Dict:
    reqs = fetch_one("SELECT COUNT(*) as cnt FROM requirements WHERE project_id=?", (project_id,))
    tcs = fetch_all(
        "SELECT status, COUNT(*) as cnt FROM test_cases WHERE project_id=? GROUP BY status",
        (project_id,),
    )
    bugs = fetch_all(
        "SELECT severity, COUNT(*) as cnt FROM bugs WHERE project_id=? GROUP BY severity",
        (project_id,),
    )
    bug_status = fetch_all(
        "SELECT status, COUNT(*) as cnt FROM bugs WHERE project_id=? GROUP BY status",
        (project_id,),
    )
    exec_results = fetch_all(
        """SELECT er.result, COUNT(*) as cnt FROM execution_results er
           JOIN test_executions te ON er.execution_id=te.id
           WHERE te.project_id=? GROUP BY er.result""",
        (project_id,),
    )
    tc_auto = fetch_all(
        "SELECT automation, COUNT(*) as cnt FROM test_cases WHERE project_id=? GROUP BY automation",
        (project_id,),
    )

    tc_counts = {r["status"]: r["cnt"] for r in tcs}
    result_counts = {r["result"]: r["cnt"] for r in exec_results}
    bug_severity = {r["severity"]: r["cnt"] for r in bugs}
    bug_statuses = {r["status"]: r["cnt"] for r in bug_status}
    auto_counts = {r["automation"]: r["cnt"] for r in tc_auto}

    total_tcs = sum(tc_counts.values())
    total_results = sum(result_counts.values())
    passes = result_counts.get("Pass", 0)
    fails = result_counts.get("Fail", 0)
    pass_rate = round(passes / total_results * 100, 1) if total_results else 0

    automated = auto_counts.get("Automated", 0)
    automation_rate = round(automated / total_tcs * 100, 1) if total_tcs else 0

    open_bugs = bug_statuses.get("Open", 0) + bug_statuses.get("In Progress", 0)
    critical_bugs = bug_severity.get("Critical", 0)

    return {
        "total_requirements": reqs["cnt"] if reqs else 0,
        "total_test_cases": total_tcs,
        "total_executions": total_results,
        "passes": passes,
        "fails": fails,
        "blocked": result_counts.get("Blocked", 0),
        "skipped": result_counts.get("Skipped", 0),
        "not_executed": result_counts.get("Not Executed", 0),
        "pass_rate": pass_rate,
        "automation_rate": automation_rate,
        "open_bugs": open_bugs,
        "critical_bugs": critical_bugs,
        "bug_severity": bug_severity,
        "bug_statuses": bug_statuses,
        "result_counts": result_counts,
    }

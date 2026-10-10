"""Python dataclass models matching the database tables."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Project:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    base_url: str = ""
    status: str = "Active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Requirement:
    id: Optional[int] = None
    project_id: int = 0
    req_id: str = ""
    title: str = ""
    description: str = ""
    priority: str = "Medium"
    status: str = "Draft"
    analysis: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TestCase:
    id: Optional[int] = None
    project_id: int = 0
    requirement_id: Optional[int] = None
    tc_id: str = ""
    scenario: str = ""
    description: str = ""
    test_type: str = "Functional"
    preconditions: str = ""
    test_data: str = ""
    expected_result: str = ""
    priority: str = "Medium"
    severity: str = "Medium"
    automation: str = "Manual"
    status: str = "Not Executed"
    created_by: str = "AI"
    actions_json: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Bug:
    id: Optional[int] = None
    project_id: int = 0
    result_id: Optional[int] = None
    bug_id: str = ""
    title: str = ""
    description: str = ""
    severity: str = "Medium"
    priority: str = "Medium"
    status: str = "Open"
    environment: str = ""
    steps_to_repro: str = ""
    expected_result: str = ""
    actual_result: str = ""
    error_message: str = ""
    possible_cause: str = ""
    assigned_to: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ExecutionResult:
    id: Optional[int] = None
    execution_id: int = 0
    test_case_id: int = 0
    result: str = "Not Executed"
    duration_ms: int = 0
    error_message: str = ""
    failed_step: str = ""
    actual_result: str = ""
    url_at_failure: str = ""
    browser_info: str = ""
    ai_analysis: Optional[str] = None
    executed_at: Optional[str] = None

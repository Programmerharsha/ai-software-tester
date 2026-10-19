"""
Unit tests for multi-provider AI client and smart demo engine.
"""

import json
import pytest
from ai import providers
from ai.response_parser import parse_and_validate
from ai.prompts import (
    REQUIREMENT_ANALYSIS_PROMPT,
    TEST_GENERATION_PROMPT,
    ACTION_GENERATION_PROMPT,
    API_ACTION_GENERATION_PROMPT,
    FAILURE_ANALYSIS_PROMPT,
    BUG_REPORT_PROMPT,
    RECOMMENDATIONS_PROMPT,
)


def test_demo_engine_requirement_analysis():
    prompt = REQUIREMENT_ANALYSIS_PROMPT.format(
        req_id="REQ-TEST",
        title="User Login Feature",
        description="Users must be able to log in with email and password.",
        priority="High"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "analysis")
    assert err is None, f"Analysis schema error: {err}"
    assert "functional_requirements" in data
    assert len(data["functional_requirements"]) > 0


def test_demo_engine_test_case_generation():
    prompt = TEST_GENERATION_PROMPT.format(
        req_id="REQ-TEST",
        title="User Login Feature",
        description="Users must be able to log in with email and password.",
        priority="High",
        analysis_context="{}"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "test_cases")
    assert err is None, f"Test cases schema error: {err}"
    assert "test_cases" in data
    assert len(data["test_cases"]) >= 3
    for tc in data["test_cases"]:
        assert "id" in tc
        assert "scenario" in tc
        assert "steps" in tc
        assert "expected_result" in tc


def test_demo_engine_action_generation():
    prompt = ACTION_GENERATION_PROMPT.format(
        tc_id="TC001",
        scenario="Valid login test",
        steps="- Navigate to /login\n- Enter email\n- Click login",
        test_data="{}",
        expected_result="Dashboard visible",
        base_url="http://localhost:5000"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "actions")
    assert err is None, f"Actions schema error: {err}"
    assert "actions" in data
    assert len(data["actions"]) > 0
    from config import ALLOWED_ACTIONS
    for action in data["actions"]:
        assert action["type"] in ALLOWED_ACTIONS


def test_demo_engine_api_action_generation():
    prompt = API_ACTION_GENERATION_PROMPT.format(
        tc_id="TC002",
        scenario="API Login Status",
        steps="- POST to /api/login",
        test_data="{}",
        expected_result="Status 200",
        base_url="http://localhost:5000"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "api_actions")
    assert err is None, f"API Actions schema error: {err}"
    assert "api_tests" in data
    assert len(data["api_tests"]) > 0


def test_demo_engine_failure_analysis():
    prompt = FAILURE_ANALYSIS_PROMPT.format(
        tc_id="TC001",
        scenario="Login redirect test",
        expected_result="/dashboard",
        actual_result="/home",
        error_message="URL mismatch: Expected /dashboard, Got /home",
        failed_step="Step 4: assert_url",
        url="http://localhost:5000/home",
        browser="chromium",
        timestamp="2026-10-19T00:00:00"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "failure_analysis")
    assert err is None, f"Failure analysis schema error: {err}"
    assert "classification" in data
    assert "likely_root_cause" in data


def test_demo_engine_bug_report():
    prompt = BUG_REPORT_PROMPT.format(
        tc_id="TC001",
        scenario="Login redirect test",
        expected_result="/dashboard",
        actual_result="/home",
        error_message="URL mismatch",
        failed_step="Step 4: assert_url",
        url="http://localhost:5000/home",
        browser="chromium",
        analysis="{}"
    )
    raw = providers.call_demo_engine(prompt)
    data, err = parse_and_validate(raw, "bug_report")
    assert err is None, f"Bug report schema error: {err}"
    assert "title" in data
    assert "steps_to_repro" in data
    assert "suggested_fix" in data


def test_provider_status_demo():
    ok, msg = providers.test_provider_connection("demo")
    assert ok is True
    assert "Demo Engine" in msg

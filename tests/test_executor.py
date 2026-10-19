"""
Tests for the action executor (non-browser portions).
Run: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from testing.action_validator import validate_actions, validate_action


def test_all_allowed_actions_have_validators():
    from config import ALLOWED_ACTIONS
    from testing.action_validator import ACTION_REQUIRED_FIELDS
    for action in ALLOWED_ACTIONS:
        assert action in ACTION_REQUIRED_FIELDS, f"Action '{action}' missing from ACTION_REQUIRED_FIELDS"


def test_navigate_requires_url():
    ok, err = validate_action({"type": "navigate"})
    assert not ok
    assert "url" in err


def test_assert_text_requires_selector_and_text():
    ok, err = validate_action({"type": "assert_text", "selector": "#el"})
    assert not ok
    assert "text" in err

    ok, err = validate_action({"type": "assert_text", "selector": "#el", "text": "hello"})
    assert ok


def test_assert_url_requires_expected_url():
    ok, err = validate_action({"type": "assert_url"})
    assert not ok

    ok, err = validate_action({"type": "assert_url", "expected_url": "/dashboard"})
    assert ok


def test_security_arbitrary_shell_rejected():
    """Critical: shell execution must never be allowed."""
    dangerous_types = ["shell", "exec", "run", "eval", "subprocess", "system", "os.system", "exec_shell"]
    for t in dangerous_types:
        ok, err = validate_action({"type": t, "command": "echo hello"})
        assert not ok, f"Dangerous action '{t}' was NOT rejected!"


def test_empty_actions_list():
    all_valid, errors = validate_actions([])
    assert all_valid  # empty list is technically valid (but executor handles empty case)


def test_non_list_actions():
    all_valid, errors = validate_actions("not a list")
    assert not all_valid


def test_mixed_valid_invalid():
    actions = [
        {"type": "navigate", "url": "/"},
        {"type": "evil"},
        {"type": "click", "selector": "#btn"},
        {"type": "run_code"},
    ]
    all_valid, errors = validate_actions(actions)
    assert not all_valid
    assert len(errors) == 2  # two invalid: evil and run_code


def test_api_engine_resolves_url_with_empty_base():
    from testing.api_engine import APIEngine
    # When base_url is empty, _resolve_url must NEVER return a relative path without host
    engine = APIEngine(base_url="")
    url = engine._resolve_url("/api/users")
    assert url.startswith("http://")
    assert "127.0.0.1:5000/api/users" in url or "localhost:5000/api/users" in url


def test_api_engine_resolves_url_without_scheme():
    from testing.api_engine import APIEngine
    engine = APIEngine(base_url="localhost:8000")
    url = engine._resolve_url("/api/items")
    assert url == "http://localhost:8000/api/items"


def test_api_engine_handles_invalid_url_gracefully():
    from testing.api_engine import APIEngine
    engine = APIEngine(base_url="")
    # Purposely malformed URL with invalid characters or no host that raises InvalidURL
    result = engine.run_api_test({
        "method": "GET",
        "endpoint": "http://bad_url:abc",
        "assertions": [],
    })
    # Must NOT raise unhandled requests.exceptions.InvalidURL; must return Fail result dict
    assert isinstance(result, dict)
    assert result["result"] == "Fail"
    assert "Invalid URL" in result["error_message"]


def test_api_engine_handles_unreachable_host_gracefully():
    from testing.api_engine import APIEngine
    engine = APIEngine(base_url="http://127.0.0.1:59999", timeout=1)
    result = engine.run_api_test({
        "method": "GET",
        "endpoint": "/unreachable",
        "assertions": [],
    })
    assert isinstance(result, dict)
    assert result["result"] == "Fail"
    assert len(result["error_message"]) > 0

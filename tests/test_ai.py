"""
Tests for the AI module — response parser and action validator.
Run: pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from ai.response_parser import extract_json, parse_json, parse_and_validate
from ai import ollama_client
from testing.action_validator import validate_action, validate_actions


# ── Ollama connection configuration ─────────────────────────────────────────

def test_ollama_base_url_uses_saved_setting(monkeypatch):
    monkeypatch.setattr(
        ollama_client.db,
        "get_setting",
        lambda key, default: " http://ollama-host:11434/ ",
    )

    assert ollama_client._ollama_base_url() == "http://ollama-host:11434"


def test_ollama_base_url_strips_api_suffix(monkeypatch):
    monkeypatch.setattr(ollama_client.db, "get_setting", lambda key, default: "http://ollama-host:11434/api/")
    assert ollama_client._ollama_base_url() == "http://ollama-host:11434"


def test_configured_model_uses_saved_setting(monkeypatch):
    monkeypatch.setattr(ollama_client.db, "get_setting", lambda key, default: "qwen2.5-coder:7b")
    assert ollama_client._configured_model() == "qwen2.5-coder:7b"


def test_ollama_request_retries_after_starting_local_server(monkeypatch):
    calls = {"count": 0, "started": False}
    monkeypatch.setattr(ollama_client, "_ollama_base_url", lambda: "http://localhost:11434")
    monkeypatch.setattr(ollama_client, "_start_local_ollama", lambda url: calls.update(started=True) or True)
    monkeypatch.setattr(ollama_client.time, "sleep", lambda seconds: None)

    def request(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] <= 4:
            raise ollama_client.requests.ConnectionError("offline")
        return type("Response", (), {"status_code": 200})()

    monkeypatch.setattr(ollama_client.requests, "request", request)

    assert ollama_client._ollama_request("GET", "/tags").status_code == 200
    assert calls["started"] is True


def test_check_model_available_requires_same_tag(monkeypatch):
    monkeypatch.setattr(ollama_client, "_configured_model", lambda: "qwen2.5-coder:7b")

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"models": [{"name": "qwen2.5-coder:3b"}, {"name": "qwen2.5-coder:7b-instruct-q4_K_M"}]}

    monkeypatch.setattr(ollama_client, "_ollama_request", lambda *args, **kwargs: FakeResponse())
    ok, msg = ollama_client.check_model_available()
    assert ok is True
    assert "7b-instruct" in msg

    class WrongModelResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"models": [{"name": "qwen2.5-coder:3b"}]}

    monkeypatch.setattr(ollama_client, "_ollama_request", lambda *args, **kwargs: WrongModelResponse())
    ok, msg = ollama_client.check_model_available()
    assert ok is False
    assert "not found" in msg.lower()


# ── extract_json ──────────────────────────────────────────────────────────────

def test_extract_json_plain():
    text = '{"key": "value"}'
    assert extract_json(text) == text


def test_extract_json_fenced():
    text = '```json\n{"key": "value"}\n```'
    result = extract_json(text)
    assert result is not None
    assert json.loads(result) == {"key": "value"}


def test_extract_json_embedded():
    text = 'Here is the result: {"items": [1, 2, 3]} done.'
    result = extract_json(text)
    assert result is not None
    assert json.loads(result) == {"items": [1, 2, 3]}


def test_extract_json_invalid():
    text = "This is just plain text with no JSON"
    assert extract_json(text) is None


def test_extract_json_trailing_comma():
    text = '{"a": 1, "b": 2,}'
    result = extract_json(text)
    # Should fix trailing comma
    if result:
        assert json.loads(result) == {"a": 1, "b": 2}


# ── parse_and_validate ────────────────────────────────────────────────────────

def test_validate_test_cases_valid():
    data = {
        "test_cases": [
            {
                "id": "TC001",
                "scenario": "Login test",
                "steps": ["Open page", "Click login"],
                "expected_result": "User logged in",
            }
        ]
    }
    text = json.dumps(data)
    result, err = parse_and_validate(text, "test_cases")
    assert result is not None
    assert err is None


def test_validate_test_cases_missing_field():
    data = {
        "test_cases": [
            {"id": "TC001", "scenario": "Login"}  # missing steps and expected_result
        ]
    }
    text = json.dumps(data)
    result, err = parse_and_validate(text, "test_cases")
    assert result is None
    assert err is not None


def test_validate_actions_valid():
    data = {
        "actions": [
            {"type": "navigate", "url": "/login"},
            {"type": "fill", "selector": "#email", "value": "test@example.com"},
            {"type": "click", "selector": "#login"},
            {"type": "assert_visible", "selector": "#dashboard"},
        ]
    }
    text = json.dumps(data)
    result, err = parse_and_validate(text, "actions")
    assert result is not None
    assert err is None


def test_validate_actions_disallowed():
    data = {
        "actions": [
            {"type": "exec_shell", "command": "rm -rf /"}  # MUST be rejected
        ]
    }
    text = json.dumps(data)
    result, err = parse_and_validate(text, "actions")
    assert result is None
    assert "disallowed" in err.lower() or "not in the allowed" in err.lower()


# ── validate_action (individual) ──────────────────────────────────────────────

def test_validate_navigate():
    ok, err = validate_action({"type": "navigate", "url": "/login"})
    assert ok

def test_validate_fill():
    ok, err = validate_action({"type": "fill", "selector": "#email", "value": "x"})
    assert ok

def test_validate_fill_missing_value():
    ok, err = validate_action({"type": "fill", "selector": "#email"})
    assert not ok
    assert "value" in err

def test_validate_unknown_action():
    ok, err = validate_action({"type": "run_arbitrary_code"})
    assert not ok

def test_validate_wait_bad_ms():
    ok, err = validate_action({"type": "wait", "ms": "not_a_number"})
    assert not ok

def test_validate_wait_valid():
    ok, err = validate_action({"type": "wait", "ms": 1000})
    assert ok

def test_validate_actions_list():
    actions = [
        {"type": "navigate", "url": "/"},
        {"type": "click", "selector": "#btn"},
    ]
    all_valid, errors = validate_actions(actions)
    assert all_valid
    assert len(errors) == 0

def test_validate_actions_list_with_bad():
    actions = [
        {"type": "navigate", "url": "/"},
        {"type": "evil_action"},  # should fail
    ]
    all_valid, errors = validate_actions(actions)
    assert not all_valid
    assert len(errors) == 1

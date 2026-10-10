"""
Response parser — extracts and validates JSON from Qwen responses.
NEVER executes malformed output. Retries up to 3 times via ai_service.
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple


def extract_json(text: str) -> Optional[str]:
    """Try to pull a JSON object or array from raw LLM output."""
    text = text.strip()

    # Already valid JSON?
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]+?)```", text)
    if fenced:
        candidate = fenced.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Find first { ... } or [ ... ] block
    for pattern in (r"\{[\s\S]+\}", r"\[[\s\S]+\]"):
        m = re.search(pattern, text)
        if m:
            candidate = m.group(0)
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                # Attempt to fix trailing commas
                fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
                try:
                    json.loads(fixed)
                    return fixed
                except json.JSONDecodeError:
                    pass

    return None


def parse_json(text: str) -> Tuple[Optional[Dict], Optional[str]]:
    """Returns (parsed_dict, error_message)."""
    extracted = extract_json(text)
    if extracted is None:
        return None, "No valid JSON found in response"
    try:
        parsed = json.loads(extracted)
        return parsed, None
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"


# ── Schema validators ─────────────────────────────────────────────────────────

def validate_analysis(data: Dict) -> Tuple[bool, str]:
    required = [
        "functional_requirements", "inputs", "outputs", "preconditions",
        "validation_rules", "edge_cases", "recommended_tests",
    ]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Missing fields: {missing}"
    return True, "OK"


def validate_test_cases(data: Dict) -> Tuple[bool, str]:
    if "test_cases" not in data or not isinstance(data["test_cases"], list):
        return False, "Expected 'test_cases' list"
    tc_required = ["id", "scenario", "steps", "expected_result"]
    for i, tc in enumerate(data["test_cases"]):
        missing = [k for k in tc_required if k not in tc]
        if missing:
            return False, f"Test case {i} missing: {missing}"
    return True, "OK"


def validate_actions(data: Dict) -> Tuple[bool, str]:
    if "actions" not in data or not isinstance(data["actions"], list):
        return False, "Expected 'actions' list"
    from config import ALLOWED_ACTIONS
    for i, action in enumerate(data["actions"]):
        if "type" not in action:
            return False, f"Action {i} missing 'type'"
        if action["type"] not in ALLOWED_ACTIONS:
            return False, f"Action {i} has disallowed type: '{action['type']}'"
    return True, "OK"


def validate_failure_analysis(data: Dict) -> Tuple[bool, str]:
    required = ["classification", "failure_explanation", "likely_root_cause", "confidence"]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Missing fields: {missing}"
    return True, "OK"


def validate_bug_report(data: Dict) -> Tuple[bool, str]:
    required = ["title", "severity", "priority", "steps_to_repro", "expected_result", "actual_result"]
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Missing fields: {missing}"
    return True, "OK"


def validate_api_actions(data: Dict) -> Tuple[bool, str]:
    if "api_tests" not in data or not isinstance(data["api_tests"], list):
        return False, "Expected 'api_tests' list"
    for i, t in enumerate(data["api_tests"]):
        if "method" not in t or "endpoint" not in t:
            return False, f"API test {i} missing method or endpoint"
        valid_methods = {"GET", "POST", "PUT", "PATCH", "DELETE"}
        if t["method"].upper() not in valid_methods:
            return False, f"API test {i} has invalid method: {t['method']}"
    return True, "OK"


VALIDATORS = {
    "analysis": validate_analysis,
    "test_cases": validate_test_cases,
    "actions": validate_actions,
    "failure_analysis": validate_failure_analysis,
    "bug_report": validate_bug_report,
    "api_actions": validate_api_actions,
}


def parse_and_validate(text: str, schema: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Parse JSON from LLM output and validate against a named schema.
    Returns (data, error). If error is not None, data is None.
    """
    data, err = parse_json(text)
    if err:
        return None, err
    validator = VALIDATORS.get(schema)
    if validator:
        ok, msg = validator(data)
        if not ok:
            return None, f"Schema validation failed ({schema}): {msg}"
    return data, None

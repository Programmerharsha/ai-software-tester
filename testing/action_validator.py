"""
Action validator — ensures only approved actions pass through to Playwright/API.
NEVER allows arbitrary code execution.
"""

from typing import Dict, List, Tuple
from config import ALLOWED_ACTIONS

# Required fields for each action type
ACTION_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "navigate": ["url"],
    "click": ["selector"],
    "fill": ["selector", "value"],
    "select": ["selector", "value"],
    "check": ["selector"],
    "uncheck": ["selector"],
    "press": ["selector", "key"],
    "wait": ["ms"],
    "assert_visible": ["selector"],
    "assert_hidden": ["selector"],
    "assert_text": ["selector", "text"],
    "assert_url": ["expected_url"],
    "screenshot": [],
}

# Optional fields (allowed but not required)
ACTION_OPTIONAL_FIELDS: Dict[str, List[str]] = {
    "navigate": [],
    "click": ["timeout"],
    "fill": ["timeout"],
    "select": [],
    "check": [],
    "uncheck": [],
    "press": [],
    "wait": [],
    "assert_visible": ["timeout"],
    "assert_hidden": ["timeout"],
    "assert_text": ["exact"],
    "assert_url": [],
    "screenshot": ["label"],
}


def validate_action(action: Dict) -> Tuple[bool, str]:
    """Validate a single action dict. Returns (ok, error_message)."""
    if not isinstance(action, dict):
        return False, f"Action must be a dict, got {type(action)}"

    action_type = action.get("type", "")
    if not action_type:
        return False, "Action missing 'type' field"

    if action_type not in ALLOWED_ACTIONS:
        return False, (
            f"Action type '{action_type}' is not in the allowed list. "
            f"Allowed: {sorted(ALLOWED_ACTIONS)}"
        )

    required = ACTION_REQUIRED_FIELDS.get(action_type, [])
    for field in required:
        if field not in action:
            return False, f"Action '{action_type}' missing required field: '{field}'"

    # Validate data types for known numeric fields
    if action_type == "wait":
        ms = action.get("ms")
        try:
            ms_val = int(ms)
            if ms_val < 0:
                return False, "Wait 'ms' must be non-negative"
        except (TypeError, ValueError):
            return False, f"Wait 'ms' must be an integer, got: {ms}"

    return True, ""


def validate_actions(actions: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate a full list of actions.
    Returns (all_valid, list_of_errors).
    """
    if not isinstance(actions, list):
        return False, ["actions must be a list"]

    errors = []
    for i, action in enumerate(actions):
        ok, err = validate_action(action)
        if not ok:
            errors.append(f"Action[{i}]: {err}")

    return len(errors) == 0, errors

"""
High-level AI service — orchestrates ollama_client + prompts + response_parser.
Handles retry logic (up to 3 attempts) for invalid responses.
"""

import json
import time
from typing import Dict, List, Optional, Tuple

from ai.ollama_client import chat, get_ai_status
from ai.prompts import (
    SYSTEM_PROMPT,
    REQUIREMENT_ANALYSIS_PROMPT,
    TEST_GENERATION_PROMPT,
    ACTION_GENERATION_PROMPT,
    API_ACTION_GENERATION_PROMPT,
    FAILURE_ANALYSIS_PROMPT,
    BUG_REPORT_PROMPT,
    RECOMMENDATIONS_PROMPT,
)
from ai.response_parser import parse_and_validate, parse_json
from config import MODEL_NAME

MAX_RETRIES = 3


def _call_with_retry(prompt: str, schema: str, context: str = "") -> Tuple[Optional[Dict], str, str]:
    """
    Call Qwen and retry up to MAX_RETRIES times on parse/validation failure.
    Returns (data, raw_response, error).
    """
    raw = ""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = chat(prompt=prompt, system=SYSTEM_PROMPT)
            data, err = parse_and_validate(raw, schema)
            if data is not None:
                return data, raw, ""
            # If invalid, append correction instruction
            if attempt < MAX_RETRIES:
                prompt = (
                    f"{prompt}\n\nYour previous response had an error: {err}\n"
                    "Please provide ONLY valid JSON with the exact structure requested."
                )
        except RuntimeError as e:
            return None, raw, str(e)
    return None, raw, f"Failed after {MAX_RETRIES} attempts. Last raw output:\n{raw[:500]}"


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_requirement(req_id: str, title: str, description: str,
                        priority: str) -> Tuple[Optional[Dict], str, str]:
    prompt = REQUIREMENT_ANALYSIS_PROMPT.format(
        req_id=req_id, title=title, description=description, priority=priority
    )
    return _call_with_retry(prompt, "analysis")


def generate_test_cases(req_id: str, title: str, description: str,
                        priority: str, analysis: Optional[Dict] = None) -> Tuple[Optional[Dict], str, str]:
    analysis_context = json.dumps(analysis, indent=2) if analysis else "No prior analysis."
    prompt = TEST_GENERATION_PROMPT.format(
        req_id=req_id, title=title, description=description,
        priority=priority, analysis_context=analysis_context,
    )
    return _call_with_retry(prompt, "test_cases")


def generate_actions(tc_id: str, scenario: str, steps: List[str],
                     test_data: Dict, expected_result: str,
                     base_url: str) -> Tuple[Optional[Dict], str, str]:
    prompt = ACTION_GENERATION_PROMPT.format(
        tc_id=tc_id,
        scenario=scenario,
        steps="\n".join(f"- {s}" for s in steps),
        test_data=json.dumps(test_data) if test_data else "{}",
        expected_result=expected_result,
        base_url=base_url,
    )
    return _call_with_retry(prompt, "actions")


def generate_api_actions(tc_id: str, scenario: str, steps: List[str],
                         test_data: Dict, expected_result: str,
                         base_url: str) -> Tuple[Optional[Dict], str, str]:
    prompt = API_ACTION_GENERATION_PROMPT.format(
        tc_id=tc_id,
        scenario=scenario,
        steps="\n".join(f"- {s}" for s in steps),
        test_data=json.dumps(test_data) if test_data else "{}",
        expected_result=expected_result,
        base_url=base_url,
    )
    return _call_with_retry(prompt, "api_actions")


def analyze_failure(tc_id: str, scenario: str, expected: str, actual: str,
                    error: str, failed_step: str, url: str,
                    browser: str, timestamp: str) -> Tuple[Optional[Dict], str, str]:
    prompt = FAILURE_ANALYSIS_PROMPT.format(
        tc_id=tc_id, scenario=scenario, expected_result=expected,
        actual_result=actual, error_message=error, failed_step=failed_step,
        url=url, browser=browser, timestamp=timestamp,
    )
    return _call_with_retry(prompt, "failure_analysis")


def generate_bug_report(tc_id: str, scenario: str, expected: str, actual: str,
                        error: str, failed_step: str, url: str, browser: str,
                        analysis: Optional[Dict] = None) -> Tuple[Optional[Dict], str, str]:
    prompt = BUG_REPORT_PROMPT.format(
        tc_id=tc_id, scenario=scenario, expected_result=expected,
        actual_result=actual, error_message=error, failed_step=failed_step,
        url=url, browser=browser,
        analysis=json.dumps(analysis, indent=2) if analysis else "None",
    )
    return _call_with_retry(prompt, "bug_report")


def get_recommendations(req_title: str, existing_tests: List[str],
                        execution_summary: str) -> Tuple[Optional[Dict], str, str]:
    prompt = RECOMMENDATIONS_PROMPT.format(
        req_title=req_title,
        existing_tests="\n".join(f"- {t}" for t in existing_tests),
        execution_summary=execution_summary,
    )
    data, raw, err = _call_with_retry(prompt, "")
    if data is None:
        # Graceful fallback: try to parse freely
        data, perr = parse_json(raw)
        if data is None:
            return None, raw, err
    return data, raw, ""

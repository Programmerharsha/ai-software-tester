"""
Test executor — orchestrates action validation → Playwright/API engine → result recording.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional

from testing.playwright_engine import PlaywrightEngine
from testing.api_engine import APIEngine
from testing.action_validator import validate_actions
import database.database as db
from config import DEFAULT_BROWSER, HEADLESS_MODE


def execute_test_case(
    test_case: Dict,
    execution_id: int,
    base_url: str,
    browser: str = DEFAULT_BROWSER,
    headless: bool = HEADLESS_MODE,
    capture_screenshot: bool = True,
) -> Dict:
    """
    Execute a single test case (UI or API).
    Returns result dict and saves to DB.
    """
    tc_id = test_case["id"]
    tc_db_id = test_case["id"]  # actual DB row id
    actions_json_str = test_case.get("actions_json", "")

    # Determine test mode (API vs UI)
    is_api = test_case.get("test_type", "").upper() == "API"

    result = {
        "result": "Not Executed",
        "error_message": "",
        "failed_step": "",
        "actual_result": "",
        "screenshot_path": "",
        "duration_ms": 0,
        "url_at_failure": "",
        "browser_info": browser,
    }

    if not actions_json_str:
        result["result"] = "Blocked"
        result["error_message"] = "No automation actions defined. Generate actions first."
    else:
        try:
            actions_data = json.loads(actions_json_str)
        except json.JSONDecodeError as e:
            result["result"] = "Fail"
            result["error_message"] = f"Invalid actions JSON: {e}"
            actions_data = {}

        if not result.get("error_message"):
            eff_base_url = (base_url or "").strip() or "http://127.0.0.1:5000"
            if is_api or "api_tests" in actions_data:
                api_tests = actions_data.get("api_tests", [])
                if not api_tests:
                    result["result"] = "Blocked"
                    result["error_message"] = "Empty API test definitions."
                else:
                    engine = APIEngine(base_url=eff_base_url)
                    try:
                        api_results = engine.run_all(api_tests)
                    except Exception as exc:
                        api_results = [{
                            "result": "Fail",
                            "error_message": f"API execution failed: {exc}",
                            "endpoint": api_tests[0].get("endpoint", "") if api_tests else "",
                            "duration_ms": 0,
                        }]
                    failed = [r for r in api_results if r["result"] == "Fail"]
                    if failed:
                        result["result"] = "Fail"
                        result["error_message"] = "; ".join(r["error_message"] for r in failed if r["error_message"])
                        result["failed_step"] = failed[0].get("endpoint", "")
                        result["actual_result"] = str(failed)
                    else:
                        result["result"] = "Pass"
                        result["actual_result"] = "All API assertions passed"
                    result["duration_ms"] = sum(r.get("duration_ms", 0) for r in api_results)
            else:
                actions = actions_data.get("actions", [])
                if not actions:
                    result["result"] = "Blocked"
                    result["error_message"] = "Empty actions list."
                else:
                    engine = PlaywrightEngine(browser_type=browser, headless=headless)
                    try:
                        result = engine.run_test(actions, base_url=eff_base_url)
                    except Exception as pw_err:
                        result["result"] = "Fail"
                        result["error_message"] = f"Execution engine error: {pw_err}"
                        result["actual_result"] = str(pw_err)

    # Save result to DB
    result_id = db.save_execution_result(
        execution_id=execution_id,
        test_case_id=tc_db_id,
        result=result["result"],
        duration_ms=result.get("duration_ms", 0),
        error_message=result.get("error_message", ""),
        failed_step=result.get("failed_step", ""),
        actual_result=result.get("actual_result", ""),
        url_at_failure=result.get("url_at_failure", ""),
        browser_info=result.get("browser_info", browser),
    )

    # Save screenshot if captured
    screenshot_path = result.get("screenshot_path", "")
    if screenshot_path:
        db.save_screenshot(result_id, screenshot_path, label="failure")

    result["result_id"] = result_id
    return result


def run_execution(
    execution_id: int,
    test_cases: List[Dict],
    base_url: str,
    browser: str = DEFAULT_BROWSER,
    headless: bool = HEADLESS_MODE,
    progress_callback=None,
) -> List[Dict]:
    """
    Run all test cases in an execution run.
    Optional progress_callback(index, total, tc, result) for Streamlit updates.
    """
    db.execute(
        "UPDATE test_executions SET status='Running', started_at=CURRENT_TIMESTAMP WHERE id=?",
        (execution_id,),
    )

    all_results = []
    total = len(test_cases)

    for i, tc in enumerate(test_cases):
        result = execute_test_case(tc, execution_id, base_url, browser, headless)
        all_results.append({"test_case": tc, "result": result})

        if progress_callback:
            progress_callback(i + 1, total, tc, result)

    # Update test case statuses in bulk
    for item in all_results:
        tc = item["test_case"]
        res = item["result"]["result"]
        db.update_test_case(tc["id"], status=res)

    # Mark execution complete
    passed = sum(1 for r in all_results if r["result"]["result"] == "Pass")
    failed = sum(1 for r in all_results if r["result"]["result"] == "Fail")
    final_status = "Completed"
    if failed > 0 and passed == 0:
        final_status = "Completed (All Failed)"
    elif failed > 0:
        final_status = f"Completed ({passed}P/{failed}F)"

    db.update_execution_status(execution_id, final_status)
    return all_results

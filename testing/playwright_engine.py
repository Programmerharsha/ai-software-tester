"""
Playwright engine — executes validated action lists against real web applications.
Uses sync_playwright to avoid asyncio conflicts with Streamlit.
"""

import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Error as PlaywrightError

from testing.action_validator import validate_actions
from config import SCREENSHOTS_DIR, TEST_TIMEOUT


class PlaywrightEngine:
    """
    Controlled Playwright executor.
    Only executes pre-validated actions from the allowed action set.
    """

    def __init__(self, browser_type: str = "chromium", headless: bool = True,
                 timeout: int = TEST_TIMEOUT):
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.timeout = timeout
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    def _start(self):
        self._playwright = sync_playwright().start()
        launcher = {
            "chromium": self._playwright.chromium,
            "firefox": self._playwright.firefox,
            "webkit": self._playwright.webkit,
        }.get(self.browser_type, self._playwright.chromium)
        self._browser = launcher.launch(headless=self.headless)
        self._context = self._browser.new_context()
        self._context.set_default_timeout(self.timeout)
        self._page = self._context.new_page()

    def _stop(self):
        try:
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def _take_screenshot(self, label: str = "screenshot") -> str:
        """Capture a screenshot, return file path."""
        filename = f"{label}_{int(time.time())}.png"
        path = str(SCREENSHOTS_DIR / filename)
        try:
            self._page.screenshot(path=path, full_page=True)
        except Exception:
            pass
        return path

    def _execute_action(self, action: Dict) -> Tuple[bool, str]:
        """
        Execute a single validated action.
        Returns (success, error_message).
        """
        t = action["type"]
        p = self._page

        try:
            if t == "navigate":
                p.goto(action["url"])

            elif t == "click":
                p.locator(action["selector"]).click()

            elif t == "fill":
                p.locator(action["selector"]).fill(action["value"])

            elif t == "select":
                p.locator(action["selector"]).select_option(action["value"])

            elif t == "check":
                p.locator(action["selector"]).check()

            elif t == "uncheck":
                p.locator(action["selector"]).uncheck()

            elif t == "press":
                p.locator(action["selector"]).press(action["key"])

            elif t == "wait":
                p.wait_for_timeout(int(action["ms"]))

            elif t == "assert_visible":
                p.locator(action["selector"]).wait_for(state="visible")

            elif t == "assert_hidden":
                p.locator(action["selector"]).wait_for(state="hidden")

            elif t == "assert_text":
                loc = p.locator(action["selector"])
                actual = loc.inner_text()
                expected = action["text"]
                if action.get("exact", False):
                    if actual.strip() != expected.strip():
                        return False, f"Text mismatch. Expected: '{expected}', Got: '{actual}'"
                else:
                    if expected.lower() not in actual.lower():
                        return False, f"Text '{expected}' not found in '{actual}'"

            elif t == "assert_url":
                actual_url = p.url
                expected_url = action["expected_url"]
                if expected_url not in actual_url:
                    return False, f"URL mismatch. Expected to contain: '{expected_url}', Got: '{actual_url}'"

            elif t == "screenshot":
                label = action.get("label", "manual")
                self._take_screenshot(label)

            return True, ""

        except PlaywrightError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {traceback.format_exc()}"

    def run_test(self, actions: List[Dict], base_url: str = "") -> Dict:
        """
        Execute a validated list of actions.
        Returns result dict with pass/fail, duration, failed_step, etc.
        """
        # Validate actions first (safety check)
        valid, errors = validate_actions(actions)
        if not valid:
            return {
                "result": "Fail",
                "error_message": "Action validation failed: " + "; ".join(errors),
                "failed_step": "Pre-execution validation",
                "actual_result": "Actions rejected before execution",
                "screenshot_path": "",
                "duration_ms": 0,
                "url_at_failure": "",
                "browser_info": self.browser_type,
            }

        t_start = time.time()
        screenshot_path = ""

        try:
            self._start()

            for i, action in enumerate(actions):
                # Prepend base_url to relative navigate URLs
                if action["type"] == "navigate" and base_url:
                    url = action["url"]
                    if not url.startswith("http"):
                        action = {**action, "url": base_url.rstrip("/") + "/" + url.lstrip("/")}

                ok, err = self._execute_action(action)

                if not ok:
                    screenshot_path = self._take_screenshot(f"failure_step_{i}")
                    duration = int((time.time() - t_start) * 1000)
                    self._stop()
                    return {
                        "result": "Fail",
                        "error_message": err,
                        "failed_step": f"Step {i + 1}: {action}",
                        "actual_result": f"Action failed: {action['type']}",
                        "screenshot_path": screenshot_path,
                        "duration_ms": duration,
                        "url_at_failure": self._page.url if self._page else "",
                        "browser_info": self.browser_type,
                    }

            duration = int((time.time() - t_start) * 1000)
            self._stop()
            return {
                "result": "Pass",
                "error_message": "",
                "failed_step": "",
                "actual_result": "All steps completed successfully",
                "screenshot_path": screenshot_path,
                "duration_ms": duration,
                "url_at_failure": "",
                "browser_info": self.browser_type,
            }

        except Exception as e:
            screenshot_path = self._take_screenshot("unexpected_error")
            duration = int((time.time() - t_start) * 1000)
            self._stop()
            return {
                "result": "Fail",
                "error_message": str(e),
                "failed_step": "Engine startup or unknown",
                "actual_result": str(e),
                "screenshot_path": screenshot_path,
                "duration_ms": duration,
                "url_at_failure": "",
                "browser_info": self.browser_type,
            }

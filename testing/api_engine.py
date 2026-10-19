"""
API testing engine — executes structured HTTP test cases using requests.
Supports GET, POST, PUT, PATCH, DELETE with assertions.
"""

import time
from typing import Dict, List, Optional, Tuple

import requests


ALLOWED_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


class APIEngine:
    def __init__(self, base_url: str = "", timeout: int = 30):
        base = (base_url or "").strip()
        if base and not base.startswith(("http://", "https://")):
            base = f"http://{base}"
        self.base_url = base.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # If targeting local demo server, ensure it is active in background
        try:
            from demo_app.server import ensure_demo_server_if_local
            ensure_demo_server_if_local(self.base_url or "http://127.0.0.1:5000")
        except Exception:
            pass

    def _resolve_url(self, endpoint: str) -> str:
        ep = (endpoint or "").strip()
        if not ep:
            ep = "/"

        # If already an absolute URL
        if ep.startswith(("http://", "https://")):
            return ep

        # If host-like without scheme e.g. localhost:5000/api
        if ep.startswith(("localhost:", "127.0.0.1:", "www.")):
            return f"http://{ep}"

        # Resolve base URL with safe fallback
        base = self.base_url.strip() if self.base_url else ""
        if not base:
            base = "http://127.0.0.1:5000"

        if not base.startswith(("http://", "https://")):
            base = f"http://{base}"

        return f"{base.rstrip('/')}/{ep.lstrip('/')}"

    def _evaluate_assertion(self, assertion: Dict, response: requests.Response,
                            duration_ms: float) -> Tuple[bool, str]:
        """Check a single assertion against the response."""
        atype = assertion.get("type", "")
        operator = assertion.get("operator", "eq")
        expected = assertion.get("expected")

        try:
            if atype == "status":
                actual = response.status_code
                expected = int(expected)
                if operator == "eq":
                    ok = actual == expected
                elif operator == "ne":
                    ok = actual != expected
                elif operator == "gt":
                    ok = actual > expected
                elif operator == "lt":
                    ok = actual < expected
                else:
                    ok = actual == expected
                return ok, f"Status {actual} {'==' if ok else '!='} {expected}"

            elif atype == "response_time":
                max_ms = int(assertion.get("max_ms", 5000))
                ok = duration_ms <= max_ms
                return ok, f"Response time {duration_ms:.0f}ms {'<=' if ok else '>'} {max_ms}ms"

            elif atype == "json_field":
                path = assertion.get("path", "")
                try:
                    data = response.json()
                except Exception:
                    return False, "Response is not valid JSON"

                parts = path.split(".") if path else []
                current = data
                for part in parts:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    else:
                        if operator == "exists":
                            return False, f"Field '{path}' does not exist"
                        return False, f"Field '{path}' not found in response"

                if operator == "exists":
                    return True, f"Field '{path}' exists"
                elif operator == "eq":
                    ok = str(current) == str(expected)
                    return ok, f"Field '{path}': '{current}' {'==' if ok else '!='} '{expected}'"
                elif operator == "contains":
                    ok = str(expected) in str(current)
                    return ok, f"Field '{path}': '{expected}' {'in' if ok else 'not in'} '{current}'"
                else:
                    return True, f"Field '{path}' = '{current}'"

            elif atype == "header":
                header_name = assertion.get("path", "")
                actual = response.headers.get(header_name, "")
                if operator == "exists":
                    ok = header_name in response.headers
                    return ok, f"Header '{header_name}' {'exists' if ok else 'missing'}"
                elif operator == "eq":
                    ok = actual == str(expected)
                    return ok, f"Header '{header_name}': '{actual}' == '{expected}': {ok}"
                elif operator == "contains":
                    ok = str(expected) in actual
                    return ok, f"Header '{header_name}' contains '{expected}': {ok}"
                return True, f"Header '{header_name}' = '{actual}'"

        except Exception as e:
            return False, f"Assertion error: {e}"

        return True, "Unknown assertion type"

    def run_api_test(self, api_test: Dict) -> Dict:
        """Run a single API test definition. Returns result dict."""
        method = api_test.get("method", "GET").upper()
        if method not in ALLOWED_METHODS:
            return {
                "result": "Fail",
                "error_message": f"Invalid HTTP method: {method}",
                "assertions_passed": [],
                "assertions_failed": [f"Method '{method}' not allowed"],
                "duration_ms": 0,
                "status_code": 0,
                "response_body": "",
            }

        endpoint_val = api_test.get("endpoint") or api_test.get("url") or api_test.get("path") or "/"
        url = self._resolve_url(endpoint_val)
        headers = api_test.get("headers", {}) or {}
        body = api_test.get("body", {})
        assertions = api_test.get("assertions", []) or []

        t_start = time.time()
        response = None
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=self.timeout,
            )
            duration_ms = (time.time() - t_start) * 1000
        except requests.exceptions.InvalidURL as e:
            return {
                "result": "Fail",
                "error_message": f"Invalid URL '{url}': {e}",
                "assertions_passed": [],
                "assertions_failed": [f"Invalid URL: {e}"],
                "duration_ms": 0,
                "status_code": 0,
                "response_body": "",
            }
        except requests.exceptions.MissingSchema as e:
            return {
                "result": "Fail",
                "error_message": f"Missing URL schema for '{url}': {e}",
                "assertions_passed": [],
                "assertions_failed": [f"Missing URL schema: {e}"],
                "duration_ms": 0,
                "status_code": 0,
                "response_body": "",
            }
        except requests.exceptions.Timeout:
            return {
                "result": "Fail",
                "error_message": f"Request timed out after {self.timeout}s",
                "assertions_passed": [],
                "assertions_failed": ["Timeout"],
                "duration_ms": int((time.time() - t_start) * 1000),
                "status_code": 0,
                "response_body": "",
            }
        except requests.exceptions.ConnectionError as e:
            return {
                "result": "Fail",
                "error_message": f"Connection error: {e}",
                "assertions_passed": [],
                "assertions_failed": ["Connection failed"],
                "duration_ms": int((time.time() - t_start) * 1000),
                "status_code": 0,
                "response_body": "",
            }
        except Exception as e:
            return {
                "result": "Fail",
                "error_message": f"HTTP request failed: {e}",
                "assertions_passed": [],
                "assertions_failed": [f"Request error: {e}"],
                "duration_ms": int((time.time() - t_start) * 1000),
                "status_code": 0,
                "response_body": "",
            }

        passed = []
        failed = []
        for assertion in assertions:
            ok, msg = self._evaluate_assertion(assertion, response, duration_ms)
            if ok:
                passed.append(msg)
            else:
                failed.append(msg)

        try:
            response_body = response.text[:2000] if response is not None else ""
        except Exception:
            response_body = ""

        status_code = response.status_code if response is not None else 0

        return {
            "result": "Pass" if not failed else "Fail",
            "error_message": "; ".join(failed) if failed else "",
            "assertions_passed": passed,
            "assertions_failed": failed,
            "duration_ms": int(duration_ms),
            "status_code": status_code,
            "response_body": response_body,
        }

    def run_all(self, api_tests: List[Dict]) -> List[Dict]:
        """Run all API tests in sequence. Returns list of result dicts."""
        results = []
        for test in api_tests:
            result = self.run_api_test(test)
            result["endpoint"] = test.get("endpoint") or test.get("url") or ""
            result["method"] = test.get("method", "")
            results.append(result)
        return results

"""
Multi-Provider AI Client for Online & Local Deployment.
Supports:
- Google Gemini (Free cloud tier via REST API)
- Groq Cloud (Ultra-fast cloud inference via REST API)
- OpenAI / OpenRouter / DeepSeek (OpenAI-compatible REST API)
- Ollama (Local or Remote REST API)
- Built-in Smart Heuristic Engine (100% offline/demo mode with zero setup)
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple

import requests

import config
from database import database as db


PROVIDER_DISPLAY_NAMES = {
    "demo": "✨ Smart Demo Engine (Instant, No API Key)",
    "gemini": "⚡ Google Gemini (Free Cloud AI)",
    "groq": "🚀 Groq (Fast Cloud AI)",
    "openai": "🧠 OpenAI / DeepSeek / Custom",
    "ollama": "🦙 Ollama (Local / Remote)",
}


# ── Configuration & Resolution Helpers ────────────────────────────────────────

def _safe_session_state_get(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        if hasattr(st, "session_state") and key in st.session_state:
            val = st.session_state[key]
            if val is not None and str(val).strip():
                return str(val).strip()
    except Exception:
        pass
    return default


def get_provider_api_key(provider: str) -> str:
    """Retrieve API key for the requested provider from session_state, DB, secrets, or env."""
    provider = provider.lower()
    val = _safe_session_state_get(f"{provider}_api_key")
    if val:
        return val

    db_val = db.get_setting(f"{provider}_api_key", "").strip()
    if db_val:
        return db_val

    if provider == "gemini":
        return config.get_config_val("GEMINI_API_KEY", "")
    elif provider == "groq":
        return config.get_config_val("GROQ_API_KEY", "")
    elif provider == "openai":
        return config.get_config_val("OPENAI_API_KEY", "")
    return ""


def get_provider_model(provider: str) -> str:
    """Retrieve configured model for the provider."""
    provider = provider.lower()
    val = _safe_session_state_get(f"{provider}_model")
    if val:
        return val

    db_val = db.get_setting(f"{provider}_model", "").strip()
    if db_val:
        return db_val

    if provider == "gemini":
        return config.get_config_val("GEMINI_MODEL", config.DEFAULT_GEMINI_MODEL)
    elif provider == "groq":
        return config.get_config_val("GROQ_MODEL", config.DEFAULT_GROQ_MODEL)
    elif provider == "openai":
        return config.get_config_val("OPENAI_MODEL", config.DEFAULT_OPENAI_MODEL)
    elif provider == "ollama":
        return db.get_setting("ai_model", config.MODEL_NAME).strip() or config.MODEL_NAME
    return "smart-heuristic-v1"


def get_provider_base_url(provider: str) -> str:
    """Retrieve base endpoint URL for providers that support custom servers."""
    provider = provider.lower()
    if provider == "openai":
        val = _safe_session_state_get("openai_base_url")
        if val:
            return val
        db_val = db.get_setting("openai_base_url", "").strip()
        if db_val:
            return db_val
        return config.get_config_val("OPENAI_BASE_URL", config.DEFAULT_OPENAI_BASE_URL)
    elif provider == "ollama":
        val = _safe_session_state_get("ollama_url")
        if val:
            return val
        db_val = db.get_setting("ollama_url", "").strip()
        if db_val:
            return db_val
        return config.get_config_val("OLLAMA_URL", config.OLLAMA_URL)
    return ""


def is_ollama_reachable(timeout: float = 1.0) -> bool:
    """Fast check whether configured Ollama server responds."""
    base_url = get_provider_base_url("ollama").rstrip("/")
    if base_url.lower().endswith("/api"):
        base_url = base_url[:-4].rstrip("/")
    try:
        r = requests.get(f"{base_url}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def get_active_provider() -> str:
    """
    Determine the active AI provider.
    Priority:
    1. Session state ('active_ai_provider')
    2. Database setting ('ai_provider')
    3. Streamlit secrets / environment ('AI_PROVIDER')
    4. Auto-detection:
       - if GEMINI_API_KEY set -> 'gemini'
       - elif GROQ_API_KEY set -> 'groq'
       - elif OPENAI_API_KEY set -> 'openai'
       - elif Ollama responds -> 'ollama'
       - else -> 'demo'
    """
    chosen = _safe_session_state_get("active_ai_provider")
    if not chosen:
        chosen = db.get_setting("ai_provider", "").strip()
    if not chosen:
        chosen = config.get_config_val("AI_PROVIDER", "auto").strip().lower()

    if chosen in ("gemini", "groq", "openai", "ollama", "demo"):
        return chosen

    # Auto-detection
    if get_provider_api_key("gemini"):
        return "gemini"
    if get_provider_api_key("groq"):
        return "groq"
    if get_provider_api_key("openai"):
        return "openai"
    if is_ollama_reachable():
        return "ollama"
    return "demo"


# ── Provider API Call Implementations ─────────────────────────────────────────

def call_gemini(
    prompt: str,
    system: str = "",
    model: str = "",
    api_key: str = "",
    temperature: float = 0.2,
) -> str:
    """Call Google Gemini REST API without extra dependencies."""
    key = api_key or get_provider_api_key("gemini")
    if not key:
        raise RuntimeError("Google Gemini API key not configured. Add it in Settings or Streamlit Secrets.")

    model_name = model or get_provider_model("gemini")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"

    full_text = f"{system.strip()}\n\n{prompt.strip()}" if system else prompt.strip()

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": full_text}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": 4096,
        }
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers, timeout=config.AI_TIMEOUT)

    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = err_data.get("error", {}).get("message", response.text)
        except Exception:
            err_msg = response.text
        raise RuntimeError(f"Gemini API error ({response.status_code}): {err_msg}")

    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("Gemini returned empty candidate list.")

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise RuntimeError("Gemini returned no text in content parts.")

    return parts[0].get("text", "")


def call_groq(
    prompt: str,
    system: str = "",
    model: str = "",
    api_key: str = "",
    temperature: float = 0.2,
) -> str:
    """Call Groq Cloud chat completions API."""
    key = api_key or get_provider_api_key("groq")
    if not key:
        raise RuntimeError("Groq API key not configured. Add it in Settings or Streamlit Secrets.")

    model_name = model or get_provider_model("groq")
    url = "https://api.groq.com/openai/v1/chat/completions"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096,
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=config.AI_TIMEOUT)

    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = err_data.get("error", {}).get("message", response.text)
        except Exception:
            err_msg = response.text
        raise RuntimeError(f"Groq API error ({response.status_code}): {err_msg}")

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("Groq returned empty choices.")

    return choices[0].get("message", {}).get("content", "")


def call_openai_compatible(
    prompt: str,
    system: str = "",
    model: str = "",
    api_key: str = "",
    base_url: str = "",
    temperature: float = 0.2,
) -> str:
    """Call OpenAI or OpenAI-compatible endpoint (OpenRouter, DeepSeek, LocalAI, etc.)."""
    key = api_key or get_provider_api_key("openai")
    endpoint_base = (base_url or get_provider_base_url("openai")).strip().rstrip("/")
    if not endpoint_base:
        endpoint_base = "https://api.openai.com/v1"

    url = f"{endpoint_base}/chat/completions"
    model_name = model or get_provider_model("openai")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    response = requests.post(url, json=payload, headers=headers, timeout=config.AI_TIMEOUT)
    if response.status_code != 200:
        try:
            err_data = response.json()
            err_msg = err_data.get("error", {}).get("message", response.text)
        except Exception:
            err_msg = response.text
        raise RuntimeError(f"OpenAI endpoint error ({response.status_code}): {err_msg}")

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenAI endpoint returned empty choices.")

    return choices[0].get("message", {}).get("content", "")


# ── Built-in Smart Heuristic Engine (Instant, Zero-setup Demo Mode) ───────────

def call_demo_engine(prompt: str, system: str = "") -> str:
    """
    Intelligent heuristic engine that synthesizes context-aware, schema-compliant JSON.
    Guarantees 100% successful execution without external network or API keys.
    """
    p_lower = prompt.lower()

    # 1. Requirement Analysis Prompt
    if "functional_requirements" in prompt or "inputs" in prompt and "outputs" in prompt:
        # Extract title and description
        title_m = re.search(r"Title:\s*(.+)", prompt)
        title = title_m.group(1).strip() if title_m else "User Module"
        desc_m = re.search(r"Description:\s*([\s\S]+?)(?:Priority:|$)", prompt)
        desc = desc_m.group(1).strip() if desc_m else ""

        is_auth = any(k in (title + " " + desc).lower() for k in ["login", "sign in", "auth", "credential", "password"])
        is_reg = any(k in (title + " " + desc).lower() for k in ["register", "sign up", "registration"])
        is_api = any(k in (title + " " + desc).lower() for k in ["api", "endpoint", "rest", "json"])

        if is_auth:
            return json.dumps({
                "functional_requirements": [
                    "User must authenticate using email and password",
                    "System verifies credentials against registered accounts",
                    "Redirects to dashboard upon successful authentication",
                    "Displays error alert on incorrect credentials",
                ],
                "inputs": ["Email address (string)", "Password (string)"],
                "outputs": ["Session cookie / Auth token", "Redirect to /dashboard", "Error banner"],
                "preconditions": ["User account exists in system", "Authentication service is running"],
                "validation_rules": ["Email format must be valid", "Password field cannot be empty"],
                "business_rules": ["Lock account after 5 consecutive failed attempts", "Case-insensitive email matching"],
                "edge_cases": ["Whitespace in email", "Special characters in password", "Concurrent login sessions"],
                "boundary_conditions": ["Maximum email length 255 chars", "Password min 8 chars"],
                "security_concerns": ["SQL injection in login fields", "Brute-force password guessing", "Cleartext password transmission"],
                "missing_requirements": ["Remember Me checkbox behavior", "Forgot password workflow"],
                "possible_risks": ["Auth service timeout under load", "Session fixation vulnerabilities"],
                "recommended_tests": [
                    "Valid user login with correct credentials",
                    "Invalid password shows proper error message",
                    "Empty credentials form submission",
                    "SQL injection probe on email input",
                    "API login endpoint verification",
                ]
            }, indent=2)

        elif is_reg:
            return json.dumps({
                "functional_requirements": [
                    "Allows new users to create account",
                    "Validates email uniqueness and password complexity",
                    "Ensures password and confirm_password match",
                    "Creates user record in database upon submission",
                ],
                "inputs": ["Name", "Email", "Password", "Confirm Password"],
                "outputs": ["New user account", "Confirmation feedback", "Redirect to login"],
                "preconditions": ["Registration service reachable"],
                "validation_rules": ["Email must be valid email format", "Passwords must match"],
                "business_rules": ["Duplicate emails are disallowed"],
                "edge_cases": ["Mismatched password confirmation", "Leading/trailing whitespace in fields"],
                "boundary_conditions": ["Password length >= 8", "Name <= 100 characters"],
                "security_concerns": ["Cross-site scripting in name field", "Weak password acceptance"],
                "missing_requirements": ["Email verification link mechanism"],
                "possible_risks": ["Spam bot registration flooding"],
                "recommended_tests": [
                    "Successful registration with valid details",
                    "Mismatched passwords rejected with error",
                    "Duplicate email registration rejected",
                    "Weak password policy enforcement",
                ]
            }, indent=2)

        else:
            return json.dumps({
                "functional_requirements": [
                    f"Core functionality for: {title}",
                    "Processes user input according to business specifications",
                    "Returns standard feedback and updates system state",
                ],
                "inputs": ["User parameters", "Action triggers"],
                "outputs": ["Success/Error status", "Updated view"],
                "preconditions": ["System is online and initialized"],
                "validation_rules": ["Mandatory fields must be populated", "Data types must conform"],
                "business_rules": ["Standard role-based access rules apply"],
                "edge_cases": ["Network latency during submission", "Boundary input thresholds"],
                "boundary_conditions": ["Min/Max character lengths", "Numeric ranges"],
                "security_concerns": ["Input sanitization", "Authorization verification"],
                "missing_requirements": ["Audit logging specification"],
                "possible_risks": ["Validation bypass"],
                "recommended_tests": [
                    f"Happy path execution for {title}",
                    "Negative validation with invalid inputs",
                    "Boundary value boundary checks",
                ]
            }, indent=2)

    # 2. Test Case Generation Prompt
    if "test_cases" in prompt and "TC001" in prompt:
        req_id_m = re.search(r"ID:\s*([A-Za-z0-9_-]+)", prompt)
        req_id = req_id_m.group(1).strip() if req_id_m else "REQ001"
        title_m = re.search(r"Title:\s*(.+)", prompt)
        title = title_m.group(1).strip() if title_m else "Feature"

        is_auth = any(k in prompt.lower() for k in ["login", "sign in", "auth", "credential", "password"])

        if is_auth:
            return json.dumps({
                "test_cases": [
                    {
                        "id": f"TC-{req_id}-01",
                        "scenario": "Successful Login with Valid Credentials",
                        "description": "Verify that a registered user can log in with valid credentials and redirect to dashboard.",
                        "type": "Positive",
                        "priority": "High",
                        "severity": "Critical",
                        "preconditions": ["User account exists (test@example.com / Test123!)", "Application is on login page"],
                        "steps": [
                            "Navigate to /login",
                            "Fill email field with 'test@example.com'",
                            "Fill password field with 'Test123!'",
                            "Click Login button",
                            "Verify redirection to dashboard",
                        ],
                        "test_data": {"email": "test@example.com", "password": "Test123!"},
                        "expected_result": "User is authenticated and redirected to /dashboard",
                        "automation_feasible": True
                    },
                    {
                        "id": f"TC-{req_id}-02",
                        "scenario": "Login Attempt with Invalid Password",
                        "description": "Verify system rejects login and shows error when wrong password is supplied.",
                        "type": "Negative",
                        "priority": "High",
                        "severity": "High",
                        "preconditions": ["User account exists (test@example.com)"],
                        "steps": [
                            "Navigate to /login",
                            "Fill email field with 'test@example.com'",
                            "Fill password field with 'WrongPass!'",
                            "Click Login button",
                            "Verify error alert is displayed",
                        ],
                        "test_data": {"email": "test@example.com", "password": "WrongPass!"},
                        "expected_result": "Error alert 'Invalid credentials' displayed, user remains on /login",
                        "automation_feasible": True
                    },
                    {
                        "id": f"TC-{req_id}-03",
                        "scenario": "Login Form Empty Fields Validation",
                        "description": "Verify client/server validation prevents empty form submission.",
                        "type": "Validation",
                        "priority": "Medium",
                        "severity": "Medium",
                        "preconditions": ["Application on login page"],
                        "steps": [
                            "Navigate to /login",
                            "Leave email and password empty",
                            "Click Login button",
                            "Verify required field validation is triggered",
                        ],
                        "test_data": {"email": "", "password": ""},
                        "expected_result": "Validation prevents submission and highlights required inputs",
                        "automation_feasible": True
                    },
                    {
                        "id": f"TC-{req_id}-04",
                        "scenario": "API Authentication Endpoint Status",
                        "description": "Verify POST /api/login returns status 200 with token for valid JSON payload.",
                        "type": "API",
                        "priority": "High",
                        "severity": "High",
                        "preconditions": ["API server online"],
                        "steps": [
                            "POST to /api/login with valid JSON credentials",
                            "Assert HTTP status code is 200",
                            "Assert response contains success status",
                        ],
                        "test_data": {"email": "test@example.com", "password": "Test123!"},
                        "expected_result": "Status 200 with authentication payload",
                        "automation_feasible": True
                    }
                ]
            }, indent=2)
        else:
            return json.dumps({
                "test_cases": [
                    {
                        "id": f"TC-{req_id}-01",
                        "scenario": f"Positive Workflow for {title}",
                        "description": f"Verify complete end-to-end operation of {title} with valid input.",
                        "type": "Positive",
                        "priority": "High",
                        "severity": "High",
                        "preconditions": ["System is initialized and on start view"],
                        "steps": [
                            "Navigate to application root",
                            "Enter valid input parameters",
                            "Click Submit/Action button",
                            "Verify successful response status",
                        ],
                        "test_data": {"input": "sample_valid_data"},
                        "expected_result": f"Action completed successfully for {title}",
                        "automation_feasible": True
                    },
                    {
                        "id": f"TC-{req_id}-02",
                        "scenario": f"Input Validation Boundary Test for {title}",
                        "description": "Verify system appropriately handles empty or boundary parameters.",
                        "type": "Validation",
                        "priority": "Medium",
                        "severity": "Medium",
                        "preconditions": ["System online"],
                        "steps": [
                            "Navigate to target page",
                            "Submit empty input",
                            "Verify validation message appears",
                        ],
                        "test_data": {"input": ""},
                        "expected_result": "Validation error displayed without crash",
                        "automation_feasible": True
                    },
                    {
                        "id": f"TC-{req_id}-03",
                        "scenario": f"API Health and Contract Test for {title}",
                        "description": "Verify REST endpoint returns expected JSON structure.",
                        "type": "API",
                        "priority": "Medium",
                        "severity": "Medium",
                        "preconditions": ["REST API online"],
                        "steps": [
                            "GET /api/health",
                            "Assert status code eq 200",
                        ],
                        "test_data": {},
                        "expected_result": "Status 200 with healthy state",
                        "automation_feasible": True
                    }
                ]
            }, indent=2)

    # 3. Automation Action Generation Prompt (UI Playwright)
    if "actions" in prompt and "assert_visible" in prompt:
        is_invalid = any(k in prompt.lower() for k in ["invalid", "wrong", "fail", "empty", "mismatch"])
        is_dashboard = "dashboard" in prompt.lower() or "login" in prompt.lower()

        if is_invalid:
            return json.dumps({
                "actions": [
                    {"type": "navigate", "url": "/login"},
                    {"type": "fill", "selector": "input[name='email'], #email", "value": "test@example.com"},
                    {"type": "fill", "selector": "input[name='password'], #password", "value": "WrongPassword123!"},
                    {"type": "click", "selector": "button[type='submit'], #login"},
                    {"type": "wait", "ms": 500},
                    {"type": "assert_visible", "selector": ".error, .alert-danger, [role='alert']"},
                    {"type": "screenshot", "label": "invalid_credentials_error"}
                ]
            }, indent=2)
        else:
            return json.dumps({
                "actions": [
                    {"type": "navigate", "url": "/login"},
                    {"type": "fill", "selector": "input[name='email'], #email", "value": "test@example.com"},
                    {"type": "fill", "selector": "input[name='password'], #password", "value": "Test123!"},
                    {"type": "click", "selector": "button[type='submit'], #login"},
                    {"type": "wait", "ms": 500},
                    {"type": "assert_url", "expected_url": "/dashboard"},
                    {"type": "assert_visible", "selector": "h1, .dashboard-title, #dashboard"},
                    {"type": "screenshot", "label": "login_success"}
                ]
            }, indent=2)

    # 4. API Action Generation Prompt
    if "api_tests" in prompt:
        return json.dumps({
            "api_tests": [
                {
                    "method": "POST",
                    "endpoint": "/api/login",
                    "headers": {"Content-Type": "application/json"},
                    "body": {"email": "test@example.com", "password": "Test123!"},
                    "assertions": [
                        {"type": "status", "operator": "eq", "expected": 200},
                        {"type": "json_field", "path": "status", "operator": "eq", "expected": "success"},
                        {"type": "response_time", "max_ms": 1500}
                    ]
                }
            ]
        }, indent=2)

    # 5. Failure Analysis Prompt
    if "likely_root_cause" in prompt or "is_environment_issue" in prompt:
        error_m = re.search(r"ERROR:\s*(.+)", prompt)
        err = error_m.group(1).strip() if error_m else "Assertion failed"

        is_redirect_bug = "/home" in prompt or "url mismatch" in prompt.lower()
        is_selector = "selector" in prompt.lower() or "timeout" in prompt.lower()

        if is_redirect_bug:
            return json.dumps({
                "classification": "Application Bug",
                "confidence": "High",
                "failure_explanation": "The test expected a redirect to '/dashboard' upon successful authentication, but the application routed to '/home'.",
                "likely_root_cause": "The login controller has a hardcoded redirect to '/home' instead of the intended '/dashboard' route (seeded defect BUG-DEMO-001).",
                "evidence": [
                    "URL assertion expected '/dashboard'",
                    f"Reported error: {err}",
                    "HTTP redirect response was 302 to /home"
                ],
                "recommended_investigation": [
                    "Inspect redirect path in Flask/Backend auth handler",
                    "Verify dashboard route authorization middleware"
                ],
                "suggested_fix": "Update auth route redirect in app code: return redirect(url_for('dashboard')) instead of /home.",
                "is_environment_issue": False,
                "should_retry": False
            }, indent=2)
        elif is_selector:
            return json.dumps({
                "classification": "Selector Problem",
                "confidence": "Medium",
                "failure_explanation": "Playwright could not locate the targeted DOM element before timeout expired.",
                "likely_root_cause": "Element selector is too brittle or target page was still rendering asynchronously.",
                "evidence": [f"Error: {err}"],
                "recommended_investigation": ["Check rendered HTML DOM structure", "Use resilient role or text locator"],
                "suggested_fix": "Replace brittle CSS selector with resilient locator or add an explicit wait_for_selector.",
                "is_environment_issue": False,
                "should_retry": True
            }, indent=2)
        else:
            return json.dumps({
                "classification": "Application Bug",
                "confidence": "Medium",
                "failure_explanation": f"Observed failure during step execution: {err}",
                "likely_root_cause": "Mismatch between application behavior and expected test criteria.",
                "evidence": [f"Error details: {err}"],
                "recommended_investigation": ["Examine application server logs at time of test run"],
                "suggested_fix": "Correct application logic or adjust test assertion if requirements changed.",
                "is_environment_issue": False,
                "should_retry": False
            }, indent=2)

    # 6. Bug Report Prompt
    if "steps_to_repro" in prompt and "possible_cause" in prompt:
        return json.dumps({
            "title": "Authentication Redirect Mismatch: Login Routes to /home instead of /dashboard",
            "severity": "High",
            "priority": "High",
            "environment": "Streamlit Cloud / Web Deployment",
            "description": "When a registered user enters valid credentials and submits the login form, the application improperly redirects to '/home' which fails expected dashboard loading.",
            "steps_to_repro": [
                "1. Navigate to the login page (/login)",
                "2. Enter registered user email 'test@example.com'",
                "3. Enter valid password 'Test123!'",
                "4. Click the 'Sign In' / 'Login' button",
                "5. Observe the destination URL in the address bar"
            ],
            "expected_result": "User is authenticated and redirected to /dashboard with welcome message.",
            "actual_result": "User is redirected to /home or receives 404 page.",
            "error_message": "URL mismatch. Expected to contain: '/dashboard', Got: 'http://localhost:5000/home'",
            "possible_cause": "Controller return redirect(url_for('dashboard')) is incorrectly pointing to '/home'.",
            "suggested_fix": "Change the login success redirect route from '/home' to '/dashboard' in the authentication controller."
        }, indent=2)

    # 7. Recommendations Prompt
    if "recommendations" in prompt:
        return json.dumps({
            "recommendations": [
                {
                    "scenario": "Session Expiration & Token Revocation",
                    "reason": "Ensure security compliance when user session becomes stale after timeout.",
                    "priority": "High",
                    "type": "Security"
                },
                {
                    "scenario": "Special Character & SQL Injection Immunity",
                    "reason": "Validate database resilience against malicious payload injection.",
                    "priority": "High",
                    "type": "Security"
                },
                {
                    "scenario": "Cross-Browser Viewport Responsiveness",
                    "reason": "Verify mobile and desktop viewports render layout without clipped buttons.",
                    "priority": "Medium",
                    "type": "UI"
                }
            ]
        }, indent=2)

    # Fallback generic JSON
    return json.dumps({"status": "ok", "message": "Demo Engine response generated successfully."})


# ── Unified Chat Function ─────────────────────────────────────────────────────

def chat_provider(
    prompt: str,
    system: str = "",
    model: Optional[str] = None,
    temperature: float = 0.2,
) -> str:
    """Send a chat completion request to the active AI provider."""
    provider = get_active_provider()

    if provider == "demo":
        return call_demo_engine(prompt=prompt, system=system)

    elif provider == "gemini":
        m = model or get_provider_model("gemini")
        return call_gemini(prompt=prompt, system=system, model=m, temperature=temperature)

    elif provider == "groq":
        m = model or get_provider_model("groq")
        return call_groq(prompt=prompt, system=system, model=m, temperature=temperature)

    elif provider == "openai":
        m = model or get_provider_model("openai")
        return call_openai_compatible(prompt=prompt, system=system, model=m, temperature=temperature)

    elif provider == "ollama":
        # Import dynamically to avoid circular dependencies
        from ai.ollama_client import _ollama_request
        configured_m = model or get_provider_model("ollama")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": configured_m,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": config.AI_NUM_CTX},
        }
        r = _ollama_request("POST", "/chat", json=payload, timeout=config.AI_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")

    else:
        # Fallback to demo engine
        return call_demo_engine(prompt=prompt, system=system)


# ── Health & Connection Test ──────────────────────────────────────────────────

def test_provider_connection(
    provider: str,
    api_key: str = "",
    model: str = "",
    base_url: str = "",
) -> Tuple[bool, str]:
    """Test connectivity and measure latency for a provider."""
    provider = provider.lower()
    t0 = time.time()

    try:
        if provider == "demo":
            return True, "✨ Smart Demo Engine is ready. Provides instant, high-quality test generation with zero configuration."

        elif provider == "gemini":
            key = api_key or get_provider_api_key("gemini")
            if not key:
                return False, "Gemini API key is required. Get one free at: https://aistudio.google.com/app/apikey"
            m = model or get_provider_model("gemini")
            res = call_gemini("Reply with valid JSON: {\"status\": \"ok\"}", model=m, api_key=key)
            elapsed = int((time.time() - t0) * 1000)
            return True, f"✅ Google Gemini ({m}) connected successfully! Latency: {elapsed}ms"

        elif provider == "groq":
            key = api_key or get_provider_api_key("groq")
            if not key:
                return False, "Groq API key is required. Get one free at: https://console.groq.com/keys"
            m = model or get_provider_model("groq")
            res = call_groq("Reply with valid JSON: {\"status\": \"ok\"}", model=m, api_key=key)
            elapsed = int((time.time() - t0) * 1000)
            return True, f"✅ Groq ({m}) connected successfully! Latency: {elapsed}ms"

        elif provider == "openai":
            m = model or get_provider_model("openai")
            res = call_openai_compatible("Reply with valid JSON: {\"status\": \"ok\"}", model=m, api_key=api_key, base_url=base_url)
            elapsed = int((time.time() - t0) * 1000)
            return True, f"✅ OpenAI endpoint connected successfully! Latency: {elapsed}ms"

        elif provider == "ollama":
            from ai.ollama_client import check_ollama_running, check_model_available
            ok_ollama, msg_ollama = check_ollama_running()
            if not ok_ollama:
                return False, f"Ollama unreachable: {msg_ollama}"
            ok_model, msg_model = check_model_available(model)
            if not ok_model:
                return False, f"Ollama connected, but {msg_model}"
            elapsed = int((time.time() - t0) * 1000)
            return True, f"✅ Ollama connected ({model or get_provider_model('ollama')}). Latency: {elapsed}ms"

        return False, f"Unknown provider '{provider}'"

    except Exception as e:
        return False, f"Connection failed: {str(e)}"

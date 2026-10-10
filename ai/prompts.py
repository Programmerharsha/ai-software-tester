"""
All prompt templates for Qwen2.5-Coder 7B interactions.
Structured to always request JSON output when used programmatically.
"""

# ── System prompt (used across all calls) ─────────────────────────────────────
SYSTEM_PROMPT = """You are an expert software tester and QA engineer powered by Qwen2.5-Coder.
Your role is to assist with requirement analysis, test case generation, test automation planning,
failure analysis, and bug report generation.

IMPORTANT RULES:
1. When asked for structured data, ALWAYS respond with valid JSON only.
2. Do NOT include markdown fences, explanations, or extra text outside the JSON.
3. Be thorough, precise, and professional.
4. Never fabricate test data that could cause real damage (use example.com, test@example.com, etc.).
5. When analyzing failures, do not claim certainty unless evidence supports it.
"""


# ── Requirement analysis ──────────────────────────────────────────────────────
REQUIREMENT_ANALYSIS_PROMPT = """Analyze the following software requirement and return a JSON object.

REQUIREMENT:
ID: {req_id}
Title: {title}
Description:
{description}
Priority: {priority}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "functional_requirements": ["string", ...],
  "inputs": ["string", ...],
  "outputs": ["string", ...],
  "preconditions": ["string", ...],
  "validation_rules": ["string", ...],
  "business_rules": ["string", ...],
  "edge_cases": ["string", ...],
  "boundary_conditions": ["string", ...],
  "security_concerns": ["string", ...],
  "missing_requirements": ["string", ...],
  "possible_risks": ["string", ...],
  "recommended_tests": ["string", ...]
}}"""


# ── Test case generation ──────────────────────────────────────────────────────
TEST_GENERATION_PROMPT = """Generate comprehensive test cases for the following software requirement.
Include positive, negative, boundary, validation, security, UI, and API tests as applicable.

REQUIREMENT:
ID: {req_id}
Title: {title}
Description:
{description}
Priority: {priority}

ANALYSIS CONTEXT:
{analysis_context}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "test_cases": [
    {{
      "id": "TC001",
      "scenario": "short scenario name",
      "description": "detailed description",
      "type": "Positive|Negative|Boundary|Validation|Security|Functional|Regression|UI|API",
      "priority": "High|Medium|Low",
      "severity": "Critical|High|Medium|Low",
      "preconditions": ["string", ...],
      "steps": ["step 1", "step 2", ...],
      "test_data": {{}},
      "expected_result": "string",
      "automation_feasible": true
    }}
  ]
}}"""


# ── Automation action generation ──────────────────────────────────────────────
ACTION_GENERATION_PROMPT = """Convert the following test case into structured browser/API test actions.
Use ONLY these allowed action types:
navigate, click, fill, select, check, uncheck, press, wait,
assert_visible, assert_hidden, assert_text, assert_url, screenshot

TEST CASE:
ID: {tc_id}
Scenario: {scenario}
Steps: {steps}
Test Data: {test_data}
Expected Result: {expected_result}

BASE URL: {base_url}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "actions": [
    {{
      "type": "navigate|click|fill|select|check|uncheck|press|wait|assert_visible|assert_hidden|assert_text|assert_url|screenshot",
      "url": "optional - for navigate",
      "selector": "optional - CSS/text selector",
      "value": "optional - for fill/select",
      "key": "optional - for press",
      "ms": "optional - for wait (milliseconds as number)",
      "text": "optional - for assert_text",
      "expected_url": "optional - for assert_url",
      "label": "optional - for screenshot"
    }}
  ]
}}"""


# ── API test action generation ────────────────────────────────────────────────
API_ACTION_GENERATION_PROMPT = """Convert the following API test case into structured HTTP test actions.

TEST CASE:
ID: {tc_id}
Scenario: {scenario}
Steps: {steps}
Test Data: {test_data}
Expected Result: {expected_result}

BASE URL: {base_url}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "api_tests": [
    {{
      "method": "GET|POST|PUT|PATCH|DELETE",
      "endpoint": "/path",
      "headers": {{}},
      "body": {{}},
      "assertions": [
        {{
          "type": "status|json_field|response_time|header",
          "path": "optional field path e.g. data.token",
          "operator": "eq|ne|gt|lt|contains|exists",
          "expected": "expected value",
          "max_ms": 2000
        }}
      ]
    }}
  ]
}}"""


# ── Failure analysis ──────────────────────────────────────────────────────────
FAILURE_ANALYSIS_PROMPT = """Analyze the following test failure and classify the root cause.

TEST CASE: {tc_id} - {scenario}
EXPECTED: {expected_result}
ACTUAL: {actual_result}
ERROR: {error_message}
FAILED STEP: {failed_step}
URL: {url}
BROWSER: {browser}
TIMESTAMP: {timestamp}

Classify the failure and provide analysis. Return ONLY this JSON:
{{
  "classification": "Application Bug|Test Automation Bug|Selector Problem|Network Problem|Authentication Problem|Environment Problem|Data Problem|Unknown",
  "confidence": "High|Medium|Low",
  "failure_explanation": "string",
  "likely_root_cause": "string",
  "evidence": ["string", ...],
  "recommended_investigation": ["string", ...],
  "suggested_fix": "string",
  "is_environment_issue": false,
  "should_retry": false
}}"""


# ── Bug report generation ─────────────────────────────────────────────────────
BUG_REPORT_PROMPT = """Generate a professional bug report from the following test failure.

TEST CASE: {tc_id} - {scenario}
EXPECTED: {expected_result}
ACTUAL: {actual_result}
ERROR: {error_message}
FAILED STEP: {failed_step}
URL: {url}
BROWSER: {browser}
ANALYSIS: {analysis}

Return ONLY this JSON structure:
{{
  "title": "string - concise bug title",
  "severity": "Critical|High|Medium|Low",
  "priority": "High|Medium|Low",
  "environment": "string",
  "description": "string",
  "steps_to_repro": ["1. step", "2. step", ...],
  "expected_result": "string",
  "actual_result": "string",
  "error_message": "string",
  "possible_cause": "string",
  "suggested_fix": "string"
}}"""


# ── Test recommendations ──────────────────────────────────────────────────────
RECOMMENDATIONS_PROMPT = """Based on the current test coverage, suggest additional test cases
that may have been missed.

REQUIREMENT: {req_title}
EXISTING TESTS: {existing_tests}
EXECUTION RESULTS: {execution_summary}

Return ONLY this JSON:
{{
  "recommendations": [
    {{
      "scenario": "string",
      "reason": "string",
      "priority": "High|Medium|Low",
      "type": "string"
    }}
  ]
}}"""

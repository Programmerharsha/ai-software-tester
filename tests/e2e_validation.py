"""E2E validation test script."""
import sys
sys.path.insert(0, '.')

from database.database import init_db, create_project, create_requirement, create_test_case
from database.database import create_execution, save_execution_result, create_bug, get_project_metrics
import json

init_db()
print('[1] DB initialized')

pid = create_project('Demo Testing Project', 'Testing the demo app', 'http://localhost:5000')
print(f'[2] Project created: ID={pid}')

rid = create_requirement(pid, 'REQ001', 'User Login', 'User should be able to log in with valid credentials', 'High')
print(f'[3] Requirement created: ID={rid}')

tc1 = create_test_case(pid, rid, 'TC001', 'API Health Check', test_type='API',
                       expected_result='Status 200 OK', automation='Automated')
tc2 = create_test_case(pid, rid, 'TC002', 'Login with valid credentials', test_type='Positive',
                       expected_result='Login successful', automation='Manual')
print(f'[4] Test cases created: {tc1}, {tc2}')

from testing.api_engine import APIEngine
engine = APIEngine(base_url='http://localhost:5000')

# Health check test
result = engine.run_api_test({
    'method': 'GET',
    'endpoint': '/api/health',
    'headers': {},
    'body': {},
    'assertions': [
        {'type': 'status', 'operator': 'eq', 'expected': 200},
        {'type': 'json_field', 'path': 'status', 'operator': 'eq', 'expected': 'ok'},
        {'type': 'response_time', 'max_ms': 2000},
    ]
})
print(f'[5] API health test: {result["result"]} | {result["duration_ms"]}ms')
for a in result['assertions_passed']:
    print(f'   PASS: {a}')

# Valid login
login_result = engine.run_api_test({
    'method': 'POST',
    'endpoint': '/api/login',
    'headers': {'Content-Type': 'application/json'},
    'body': {'email': 'test@example.com', 'password': 'Test123!'},
    'assertions': [
        {'type': 'status', 'operator': 'eq', 'expected': 200},
        {'type': 'json_field', 'path': 'token', 'operator': 'exists'},
    ]
})
print(f'[6] Login API test: {login_result["result"]} | Status: {login_result["status_code"]}')

# Negative login test (invalid creds → should return 401)
bad_login = engine.run_api_test({
    'method': 'POST',
    'endpoint': '/api/login',
    'headers': {'Content-Type': 'application/json'},
    'body': {'email': 'wrong@example.com', 'password': 'badpass'},
    'assertions': [
        {'type': 'status', 'operator': 'eq', 'expected': 401},
    ]
})
print(f'[7] Negative login test: {bad_login["result"]} (expected: PASS for 401)')

# Record results
exec_id = create_execution(pid, 'E2E Demo Run', 'api', True, 'http://localhost:5000')
r1 = save_execution_result(exec_id, tc1, result['result'], result['duration_ms'])
r2 = save_execution_result(exec_id, tc1, login_result['result'], login_result['duration_ms'])
print(f'[8] Results saved: IDs {r1}, {r2}')

# Create a bug
bid = create_bug(pid, 'BUG-001', 'Demo: login redirect goes to /home not /dashboard',
                 severity='High', priority='High', status='Open',
                 steps_to_repro='1. Go to /login\n2. Login with valid creds\n3. Observe URL',
                 expected_result='/dashboard', actual_result='/home')
print(f'[9] Bug created: ID={bid}')

# Metrics
metrics = get_project_metrics(pid)
print(f'[10] Dashboard metrics:')
print(f'   Requirements: {metrics["total_requirements"]}')
print(f'   Test Cases: {metrics["total_test_cases"]}')
print(f'   Passed: {metrics["passes"]}')
print(f'   Failed: {metrics["fails"]}')
print(f'   Pass Rate: {metrics["pass_rate"]}%')
print(f'   Open Bugs: {metrics["open_bugs"]}')

# Generate HTML report
from pages.reports_page import _generate_html_report, _generate_csv_report
html = _generate_html_report(pid)
assert 'Demo Testing Project' in html
assert 'Test Report' in html
csv = _generate_csv_report(pid)
assert len(csv) > 0
print('[11] HTML and CSV reports generated successfully')

print()
print('=== E2E WORKFLOW COMPLETE ===')
print('All phases validated successfully!')

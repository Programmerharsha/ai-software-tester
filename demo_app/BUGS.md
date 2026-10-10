# Intentional Bugs in Demo Application

This document lists all intentional bugs introduced into the demo application for testing demonstration purposes.

## BUG-DEMO-001: Wrong Redirect After Login

**File**: `demo_app/app.py` — login() route  
**Severity**: High  
**Priority**: High  
**Type**: Application Bug — Navigation

**Description**: After successful login, the app redirects to `/home` instead of `/dashboard`.  
The route `/home` exists and itself redirects to `/dashboard`, adding an extra hop.  
This can cause test failures when asserting the URL after login is `/dashboard`.

**Steps to Reproduce**:
1. Go to `http://localhost:5000/login`
2. Enter valid credentials (test@example.com / Test123!)
3. Click Login
4. Observe: brief redirect through `/home` before landing on `/dashboard`

**Expected**: URL after login = `/dashboard`  
**Actual**: Intermediate redirect through `/home`

**Code location**: Line ~87 `return redirect("/home")` — should be `redirect("/dashboard")`

---

## BUG-DEMO-002: Registration Skips Password Confirmation Validation

**File**: `demo_app/app.py` — register() route  
**Severity**: Medium  
**Priority**: Medium  
**Type**: Application Bug — Validation

**Description**: The registration form accepts different values in "Password" and "Confirm Password" fields without error.

**Steps to Reproduce**:
1. Go to `http://localhost:5000/register`
2. Fill in name and email
3. Enter "password123" in Password
4. Enter "different456" in Confirm Password
5. Click Register

**Expected**: Error message "Passwords do not match"  
**Actual**: Registration succeeds with the original password

**Code location**: Lines where `confirm` is received — validation check is intentionally commented out.

---

## BUG-DEMO-003: Dashboard Shows Hardcoded "Demo User" Instead of Actual Name

**File**: `demo_app/app.py` — dashboard() route / DASHBOARD_HTML template  
**Severity**: Low  
**Priority**: Low  
**Type**: Application Bug — UI

**Description**: The dashboard welcome message always shows "Demo User!" regardless of who is logged in.

**Steps to Reproduce**:
1. Login as test@example.com
2. Navigate to `/dashboard`
3. Observe the welcome message says "Welcome, Demo User!"

**Expected**: "Welcome, Test User!" (using session['user_name'])  
**Actual**: "Welcome, Demo User!" (hardcoded in template)

**Code location**: DASHBOARD_HTML template `id="user-greeting"` content is hardcoded.

---

## BUG-DEMO-004: demo@test.com Accepts Any Non-Empty Password

**File**: `demo_app/app.py` — login() route  
**Severity**: Critical  
**Priority**: High  
**Type**: Security Bug — Authentication

**Description**: The account `demo@test.com` bypasses password verification and logs in with any non-empty password.

**Steps to Reproduce**:
1. Go to `/login`
2. Enter email: `demo@test.com`
3. Enter any password (e.g., "wrongpassword")
4. Click Login

**Expected**: Login fails with "Invalid email or password"  
**Actual**: Login succeeds

**Code location**: The `if email == "demo@test.com": pass` block intentionally skips auth.

---

## Using These Bugs for Testing

These bugs are perfect for demonstrating:
1. **BUG-001** → Tests `assert_url` action failing on `/dashboard` check
2. **BUG-002** → Tests negative validation test case catching missing validation
3. **BUG-003** → Tests `assert_text` action finding wrong user name
4. **BUG-004** → Tests security test cases finding authentication bypass

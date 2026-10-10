"""
Demo Web Application for AI Software Tester.
A minimal Flask app with intentional bugs for demonstration.

=== INTENTIONAL BUGS (for testing demonstration) ===
BUG-DEMO-001: Login redirects to /home instead of /dashboard (wrong redirect path)
BUG-DEMO-002: Registration does not validate that password == confirm_password
BUG-DEMO-003: Dashboard shows hardcoded welcome message instead of logged-in user's name
BUG-DEMO-004: Login accepts any non-empty password for demo@test.com (no real auth)
=== END INTENTIONAL BUGS ===
"""

from flask import Flask, request, jsonify, redirect, url_for, session, render_template_string
import os

app = Flask(__name__)
app.secret_key = "demo-secret-key-not-for-production"

# Dummy user database
USERS = {
    "test@example.com": {"password": "Test123!", "name": "Test User"},
    "admin@example.com": {"password": "Admin123!", "name": "Admin User"},
    "demo@test.com": {"password": "password", "name": "Demo User"},
}

# ── HTML Templates ─────────────────────────────────────────────────────────────
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login — Demo App</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: Inter, sans-serif; }
    body { min-height: 100vh; background: #0f1117; display: flex; align-items: center; justify-content: center; }
    .card { background: #1e2130; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px;
            padding: 40px; width: 380px; }
    h1 { color: #a78bfa; margin-bottom: 8px; font-size: 1.8rem; }
    .subtitle { color: #9ca3af; font-size: 0.85rem; margin-bottom: 30px; }
    label { color: #e8eaf6; font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 4px; margin-top: 16px; }
    input { width: 100%; padding: 10px 14px; background: #252836; border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; color: #e8eaf6; font-size: 0.95rem; outline: none; }
    input:focus { border-color: #6c63ff; box-shadow: 0 0 0 2px rgba(108,99,255,0.2); }
    button { width: 100%; margin-top: 24px; padding: 12px; background: linear-gradient(135deg, #6c63ff, #9b59b6);
             border: none; border-radius: 8px; color: white; font-size: 1rem; font-weight: 600; cursor: pointer; }
    button:hover { opacity: 0.9; }
    .error { background: rgba(255,83,112,0.1); border: 1px solid rgba(255,83,112,0.3);
             border-radius: 8px; padding: 10px 14px; margin-top: 14px; color: #ff5370; font-size: 0.85rem; }
    .success { background: rgba(0,230,118,0.1); border: 1px solid rgba(0,230,118,0.3);
               border-radius: 8px; padding: 10px 14px; margin-top: 14px; color: #00e676; font-size: 0.85rem; }
    .hint { margin-top: 16px; color: #9ca3af; font-size: 0.78rem; text-align: center; }
    a { color: #a78bfa; text-decoration: none; }
    .badge { display: inline-block; background: rgba(255,83,112,0.15); color: #ff5370;
             border: 1px solid rgba(255,83,112,0.3); border-radius: 20px; padding: 2px 10px;
             font-size: 0.7rem; font-weight: 600; margin-left: 8px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Login <span class="badge">DEMO</span></h1>
    <p class="subtitle">AI Software Tester Demo Application</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    {% if msg %}<div class="success">{{ msg }}</div>{% endif %}
    <form method="POST" action="/login">
      <label for="email">Email</label>
      <input type="email" id="email" name="email" placeholder="test@example.com" required>
      <label for="password">Password</label>
      <input type="password" id="password" name="password" placeholder="Enter password" required>
      <button type="submit" id="login-btn">Login</button>
    </form>
    <p class="hint">Test credentials: test@example.com / Test123!<br>
      <a href="/register">Don't have an account? Register</a></p>
  </div>
</body>
</html>
"""

REGISTER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Register — Demo App</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: Inter, sans-serif; }
    body { min-height: 100vh; background: #0f1117; display: flex; align-items: center; justify-content: center; }
    .card { background: #1e2130; border: 1px solid rgba(255,255,255,0.08); border-radius: 20px;
            padding: 40px; width: 400px; }
    h1 { color: #a78bfa; margin-bottom: 8px; font-size: 1.8rem; }
    .subtitle { color: #9ca3af; font-size: 0.85rem; margin-bottom: 24px; }
    label { color: #e8eaf6; font-size: 0.85rem; font-weight: 500; display: block; margin-bottom: 4px; margin-top: 14px; }
    input { width: 100%; padding: 10px 14px; background: #252836; border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px; color: #e8eaf6; font-size: 0.95rem; outline: none; }
    input:focus { border-color: #6c63ff; }
    button { width: 100%; margin-top: 24px; padding: 12px; background: linear-gradient(135deg, #6c63ff, #9b59b6);
             border: none; border-radius: 8px; color: white; font-size: 1rem; font-weight: 600; cursor: pointer; }
    .error { background: rgba(255,83,112,0.1); border: 1px solid rgba(255,83,112,0.3);
             border-radius: 8px; padding: 10px; margin-top: 14px; color: #ff5370; font-size: 0.85rem; }
    .success { background: rgba(0,230,118,0.1); border: 1px solid rgba(0,230,118,0.3);
               border-radius: 8px; padding: 10px; margin-top: 14px; color: #00e676; font-size: 0.85rem; }
    a { color: #a78bfa; text-decoration: none; }
    .hint { margin-top: 14px; color: #9ca3af; font-size: 0.78rem; text-align: center; }
    .bug-note { background: rgba(255,204,2,0.08); border: 1px solid rgba(255,204,2,0.2);
                border-radius: 8px; padding: 8px 12px; margin-bottom: 14px; color: #ffcc02; font-size: 0.75rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Register</h1>
    <p class="subtitle">Create a new demo account</p>
    <div class="bug-note">[INTENTIONAL BUG] Confirm password is not validated server-side.</div>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    {% if msg %}<div class="success">{{ msg }}</div>{% endif %}
    <form method="POST" action="/register">
      <label for="name">Full Name</label>
      <input type="text" id="name" name="name" placeholder="John Doe" required>
      <label for="email">Email</label>
      <input type="email" id="email" name="email" placeholder="you@example.com" required>
      <label for="password">Password</label>
      <input type="password" id="password" name="password" placeholder="Min 8 characters" required>
      <label for="confirm_password">Confirm Password</label>
      <input type="password" id="confirm_password" name="confirm_password" placeholder="Repeat password" required>
      <button type="submit" id="register-btn">Create Account</button>
    </form>
    <p class="hint"><a href="/">Already have an account? Login</a></p>
  </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dashboard — Demo App</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: Inter, sans-serif; }
    body { background: #0f1117; color: #e8eaf6; min-height: 100vh; }
    nav { background: #1e2130; padding: 16px 32px; display: flex; justify-content: space-between;
          align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .logo { font-size: 1.2rem; font-weight: 700; color: #a78bfa; }
    .nav-links a { color: #9ca3af; margin-left: 20px; text-decoration: none; }
    .nav-links a:hover { color: #e8eaf6; }
    .main { padding: 40px 32px; max-width: 1000px; margin: 0 auto; }
    h1 { font-size: 2rem; margin-bottom: 8px; }
    .welcome { color: #a78bfa; }
    .subtitle { color: #9ca3af; margin-bottom: 32px; }
    .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 32px; }
    .card { background: #1e2130; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; }
    .card-icon { font-size: 2rem; margin-bottom: 12px; }
    .card-title { font-weight: 600; margin-bottom: 4px; }
    .card-val { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
    .profile { background: #1e2130; border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 24px; }
    .profile h2 { margin-bottom: 16px; }
    .profile-row { display: flex; gap: 12px; margin-bottom: 10px; color: #9ca3af; }
    .profile-val { color: #e8eaf6; }
    .logout-btn { display: inline-block; margin-top: 20px; padding: 10px 24px;
                  background: rgba(255,83,112,0.1); border: 1px solid rgba(255,83,112,0.3);
                  border-radius: 8px; color: #ff5370; text-decoration: none; font-weight: 600; }
    .bug-note { background: rgba(255,204,2,0.08); border: 1px solid rgba(255,204,2,0.2);
                border-radius: 8px; padding: 10px 16px; margin-bottom: 20px; color: #ffcc02; font-size: 0.8rem; }
  </style>
</head>
<body>
  <nav>
  <div class="logo">DemoApp</div>
    <div class="nav-links" id="nav-bar">
      <a href="/profile" id="profile-link">Profile</a>
      <a href="/logout" id="logout-link">Logout</a>
    </div>
  </nav>
  <div class="main">
    <div class="bug-note">
      [INTENTIONAL BUG] Welcome message shows "Welcome, Demo User!" regardless of who is logged in.
    </div>
    <!-- BUG-DEMO-003: should show logged-in user name but always shows "Demo User" -->
    <h1>Welcome, <span class="welcome" id="user-greeting">Demo User!</span></h1>
    <p class="subtitle">You're successfully logged in to the demo application.</p>

    <div class="cards">
      <div class="card">
        <div class="card-icon"></div>
        <div class="card-title">Projects</div>
        <div class="card-val">12</div>
      </div>
      <div class="card">
        <div class="card-icon"></div>
        <div class="card-title">Tasks Done</div>
        <div class="card-val">47</div>
      </div>
      <div class="card">
        <div class="card-icon"></div>
        <div class="card-title">Open Issues</div>
        <div class="card-val">3</div>
      </div>
    </div>

    <div class="profile">
      <h2>Profile</h2>
      <div class="profile-row">
        <span>Email:</span>
        <span class="profile-val" id="user-email">{{ email }}</span>
      </div>
      <div class="profile-row">
        <span>Role:</span>
        <span class="profile-val">Standard User</span>
      </div>
      <div class="profile-row">
        <span>Account Status:</span>
        <span class="profile-val" style="color:#00e676;">Active</span>
      </div>
      <a href="/logout" class="logout-btn" id="logout-btn">Logout</a>
    </div>
  </div>
</body>
</html>
"""

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/login")
def login_page():
    msg = request.args.get("msg", "")
    return render_template_string(LOGIN_HTML, error="", msg=msg)


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template_string(LOGIN_HTML, error="Email and password are required.", msg="")

    user = USERS.get(email)
    if not user:
        return render_template_string(LOGIN_HTML, error="Invalid email or password.", msg="")

    # BUG-DEMO-004: demo@test.com accepts any non-empty password
    if email == "demo@test.com":
        pass  # intentional: no password check for demo account
    elif user["password"] != password:
        return render_template_string(LOGIN_HTML, error="Invalid email or password.", msg="")

    session["user_email"] = email
    session["user_name"] = user["name"]

    # BUG-DEMO-001: redirects to /home instead of /dashboard
    return redirect("/home")  # INTENTIONAL BUG: should be /dashboard


@app.route("/home")
def home_redirect():
    """This route exists because of BUG-DEMO-001 — it redirects to dashboard."""
    if "user_email" not in session:
        return redirect("/")
    return redirect("/dashboard")


@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect("/")
    # BUG-DEMO-003: uses hardcoded name instead of session["user_name"]
    email = session.get("user_email", "unknown@example.com")
    return render_template_string(DASHBOARD_HTML, email=email)


@app.route("/register")
def register_page():
    return render_template_string(REGISTER_HTML, error="", msg="")


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not name or not email or not password:
        return render_template_string(REGISTER_HTML, error="All fields are required.", msg="")

    if email in USERS:
        return render_template_string(REGISTER_HTML, error="Email already registered.", msg="")

    # BUG-DEMO-002: password != confirm_password is NOT checked
    # Intentionally skipping: if password != confirm: return error
    USERS[email] = {"password": password, "name": name}
    return redirect("/?msg=Registration successful! Please login.")


@app.route("/profile")
def profile():
    if "user_email" not in session:
        return redirect("/")
    return render_template_string(DASHBOARD_HTML, email=session["user_email"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ── API Endpoints ──────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401
    return jsonify({"success": True, "token": "demo-jwt-token-123", "name": user["name"]}), 200


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(force=True) or {}
    email = data.get("email", "").strip()
    name = data.get("name", "").strip()
    password = data.get("password", "")
    if not email or not name or not password:
        return jsonify({"success": False, "error": "Missing fields"}), 400
    if email in USERS:
        return jsonify({"success": False, "error": "Email already exists"}), 409
    USERS[email] = {"password": password, "name": name}
    return jsonify({"success": True, "message": "User registered"}), 201


@app.route("/api/users", methods=["GET"])
def api_users():
    return jsonify({"users": list(USERS.keys()), "count": len(USERS)}), 200


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "app": "Demo App", "version": "1.0.0"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\nDemo App running at http://localhost:{port}")
    print("Test credentials: test@example.com / Test123!")
    print("\nKnown Intentional Bugs:")
    print("  BUG-001: Login redirects to /home instead of /dashboard")
    print("  BUG-002: Registration does not validate password == confirm_password")
    print("  BUG-003: Dashboard shows hardcoded 'Demo User' instead of actual name")
    print("  BUG-004: demo@test.com accepts any non-empty password\n")
    app.run(host="0.0.0.0", port=port, debug=False)

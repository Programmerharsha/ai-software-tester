"""Settings page — configure Ollama, browser, and test execution settings."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import platform
import streamlit as st

import database.database as db
from config import MODEL_NAME, OLLAMA_URL, DB_PATH, SCREENSHOTS_DIR, REPORTS_DIR


def render():
    st.markdown("## Settings")

    # Load current settings from DB
    settings = db.get_all_settings()

    # ── AI Status (live check) ────────────────────────────────────────────────
    st.markdown("### AI Status")
    col_status, col_btn = st.columns([3, 1])

    with col_btn:
        check_now = st.button("Check Now", use_container_width=True)

    if check_now or st.session_state.get("ai_status_checked"):
        from ai.ollama_client import get_ai_status
        with st.spinner("Checking Ollama..."):
            status = get_ai_status()
            st.session_state.ai_status = status
            st.session_state.ai_status_checked = True

        with col_status:
            if status.get("ready"):
                st.markdown("""
                <div style="background:rgba(0,230,118,0.08); border:1px solid rgba(0,230,118,0.25);
                            border-radius:12px; padding:16px 20px;">
                  <div style="font-weight:700; margin-bottom:8px;">AI STATUS</div>
                  <div>✅ Ollama Connected</div>
                  <div>✅ {status.get("model_msg", "Model available")}</div>
                  <div style="margin-top:8px; color:#00e676; font-weight:600;">AI Testing Engine: READY</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                ollama_msg = status.get("ollama_msg", "")
                model_msg = status.get("model_msg", "")
                recovery_hint = (
                    "Start Ollama by running: <code>ollama serve</code>"
                    if not status.get("ollama")
                    else f"Run: <code>ollama pull {status.get('configured_model', settings.get('ai_model', MODEL_NAME))}</code>"
                )
                st.markdown(f"""
                <div style="background:rgba(255,83,112,0.08); border:1px solid rgba(255,83,112,0.25);
                            border-radius:12px; padding:16px 20px;">
                  <div style="font-weight:700; margin-bottom:8px; color:#ff5370;">Ollama not ready</div>
                  {'<div>' + ollama_msg + '</div>' if not status.get("ollama") else '<div>Ollama Connected</div>'}
                  {'<div>' + model_msg + '</div>' if not status.get("model") else '<div>Model Available</div>'}
                  <div style="margin-top:10px; font-size:0.85rem; color:#ff5370;">
                    {recovery_hint}
                  </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        with col_status:
            st.info("Click 'Check Now' to verify Ollama and Qwen status.")

    st.divider()

    # ── Configuration Form ────────────────────────────────────────────────────
    st.markdown("### Configuration")
    st.caption("Do NOT change the AI Model unless you explicitly want to switch models. Silently switching is not allowed.")

    with st.form("settings_form"):
        c1, c2 = st.columns(2)

        with c1:
            ollama_url = st.text_input(
                "Ollama URL",
                value=settings.get("ollama_url", OLLAMA_URL),
                help="Default: http://localhost:11434",
            )
            ai_model = st.text_input(
                "AI Model",
                value=settings.get("ai_model", MODEL_NAME),
                help=f"⚠️ Default must be: {MODEL_NAME}. Do not change without reason.",
            )
            browser = st.selectbox(
                "Browser",
                ["chromium", "firefox", "webkit"],
                index=["chromium", "firefox", "webkit"].index(settings.get("browser", "chromium")),
            )

        with c2:
            headless = st.checkbox(
                "Headless Mode",
                value=settings.get("headless", "1") == "1",
                help="Run browsers without visible window",
            )
            test_timeout = st.number_input(
                "Test Timeout (ms)",
                value=int(settings.get("test_timeout", "30000")),
                min_value=1000,
                max_value=120000,
                step=1000,
            )
            screenshot_on_failure = st.checkbox(
                "Screenshot on Failure",
                value=settings.get("screenshot_on_failure", "1") == "1",
                help="Auto-capture screenshot when test fails",
            )

        if st.form_submit_button("Save Settings", use_container_width=True):
            if ai_model != MODEL_NAME and not st.session_state.get("model_override_confirmed"):
                st.warning(f"⚠️ You are changing the AI model from `{MODEL_NAME}` to `{ai_model}`. "
                           "This is not recommended. Please confirm by saving again.")
                st.session_state["model_override_confirmed"] = True
            else:
                db.set_setting("ollama_url", ollama_url)
                db.set_setting("ai_model", ai_model)
                db.set_setting("browser", browser)
                db.set_setting("headless", "1" if headless else "0")
                db.set_setting("test_timeout", str(int(test_timeout)))
                db.set_setting("screenshot_on_failure", "1" if screenshot_on_failure else "0")
                st.session_state.pop("model_override_confirmed", None)
                st.success("Settings saved!")
                st.rerun()

    st.divider()

    # ── System Info ───────────────────────────────────────────────────────────
    st.markdown("### System Information")

    col_sys, col_paths = st.columns(2)
    with col_sys:
        st.markdown(f"**OS:** {platform.system()} {platform.release()}")
        st.markdown(f"**Python:** {platform.python_version()}")
        try:
            import playwright
            pw_ver = playwright.__version__
        except Exception:
            pw_ver = "Not installed"
        st.markdown(f"**Playwright:** {pw_ver}")
        try:
            import streamlit
            st.markdown(f"**Streamlit:** {streamlit.__version__}")
        except Exception:
            pass

    with col_paths:
        st.markdown(f"**Database:** `{DB_PATH}`")
        st.markdown(f"**Screenshots:** `{SCREENSHOTS_DIR}`")
        st.markdown(f"**Reports:** `{REPORTS_DIR}`")

    st.divider()

    # ── Demo App ──────────────────────────────────────────────────────────────
    st.markdown("### Demo Application")
    st.markdown("""
    The demo app is a small Flask web application with intentional bugs for testing.

    **Start the demo app:**
    ```bash
    cd demo_app
    pip install flask
    python app.py
    ```

    The demo app runs at: `http://localhost:5000`

    **Test credentials:**
    - `test@example.com` / `Test123!`
    - `admin@example.com` / `Admin123!`
    - `demo@test.com` / (any password — intentional bug!)

    **Known intentional bugs:**
    - BUG-001: Login redirects to `/home` instead of `/dashboard`
    - BUG-002: Registration skips password confirmation validation
    - BUG-003: Dashboard shows hardcoded "Demo User" name
    - BUG-004: demo@test.com accepts any non-empty password
    """)

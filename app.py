"""
AI Software Tester — Main Streamlit Application Entry Point
"""

import os
import sys
import time
from datetime import datetime

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

# ── Must be the FIRST Streamlit call ────────────────────────────────────────
st.set_page_config(
    page_title="AI Software Tester",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import APP_VERSION, MODEL_NAME
from database.database import init_db
from ai.ollama_client import get_ai_status

# ── Initialize DB ────────────────────────────────────────────────────────────
init_db()

# ── Global CSS ────────────────────────────────────────────────────────────────
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg-primary: #0f1117;
  --bg-secondary: #1a1d27;
  --bg-card: #1e2130;
  --bg-input: #252836;
  --accent: #6c63ff;
  --accent-light: #8b84ff;
  --accent-glow: rgba(108, 99, 255, 0.3);
  --success: #00e676;
  --danger: #ff5370;
  --warning: #ffcc02;
  --info: #40c4ff;
  --text-primary: #e8eaf6;
  --text-secondary: #9ca3af;
  --border: rgba(255, 255, 255, 0.08);
  --border-accent: rgba(108, 99, 255, 0.4);
  --radius: 12px;
  --radius-lg: 20px;
}

* { font-family: 'Inter', sans-serif; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

/* Ambient animated backdrop glow */
[data-testid="stAppViewContainer"]::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(600px circle at 15% -10%, rgba(108,99,255,0.10), transparent 55%),
    radial-gradient(500px circle at 100% 10%, rgba(155,89,182,0.08), transparent 55%);
  animation: driftGlow 18s ease-in-out infinite alternate;
}
@keyframes driftGlow {
  0%   { opacity: 0.6; transform: translateY(0px); }
  100% { opacity: 1;   transform: translateY(20px); }
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #13162d 0%, #1a1d27 100%) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* Metric cards */
[data-testid="metric-container"] {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="metric-container"]:hover {
  transform: translateY(-3px);
  border-color: var(--border-accent);
  box-shadow: 0 8px 24px rgba(0,0,0,0.35);
}
[data-testid="stMetricValue"] { color: var(--accent-light) !important; font-weight: 700; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), #9b59b6) !important;
  color: white !important;
  border: none !important;
  border-radius: 8px !important;
  font-weight: 600 !important;
  padding: 0.5rem 1.5rem !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease !important;
  box-shadow: 0 4px 15px var(--accent-glow) !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px var(--accent-glow) !important;
  filter: brightness(1.08) !important;
}
.stButton > button:active {
  transform: translateY(0px) scale(0.98) !important;
}

/* Secondary (inactive nav) buttons — quieter, so the active page pops */
.stButton > button[kind="secondary"] {
  background: var(--bg-input) !important;
  color: var(--text-secondary) !important;
  box-shadow: none !important;
  border: 1px solid transparent !important;
}
.stButton > button[kind="secondary"]:hover {
  border: 1px solid var(--border-accent) !important;
  color: var(--text-primary) !important;
  transform: translateX(3px) !important;
}
.stButton > button[kind="primary"] {
  box-shadow: 0 4px 18px var(--accent-glow) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  border-radius: 8px !important;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px var(--accent-glow) !important;
}

/* Tables */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden;
}

/* Tabs */
[data-testid="stTabs"] button {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  transition: color 0.2s ease;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--accent-light) !important;
  border-bottom-color: var(--accent) !important;
}

/* Expanders */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  transition: border-color 0.2s ease;
}
[data-testid="stExpander"]:hover {
  border-color: var(--border-accent) !important;
}

/* Dividers */
hr { border-color: var(--border) !important; }

/* Status badges */
.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-pass    { background: rgba(0,230,118,0.15);  color: #00e676; border: 1px solid rgba(0,230,118,0.3); }
.badge-fail    { background: rgba(255,83,112,0.15); color: #ff5370; border: 1px solid rgba(255,83,112,0.3); }
.badge-blocked { background: rgba(255,204,2,0.15);  color: #ffcc02; border: 1px solid rgba(255,204,2,0.3); }
.badge-skipped { background: rgba(156,163,175,0.15);color: #9ca3af; border: 1px solid rgba(156,163,175,0.3); }
.badge-open    { background: rgba(255,83,112,0.15); color: #ff5370; border: 1px solid rgba(255,83,112,0.3); }
.badge-closed  { background: rgba(0,230,118,0.15);  color: #00e676; border: 1px solid rgba(0,230,118,0.3); }

/* Cards */
.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 16px;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.glass-card:hover {
  border-color: var(--border-accent);
}

.ai-status-card {
  background: linear-gradient(135deg, rgba(108,99,255,0.1), rgba(155,89,182,0.1));
  border: 1px solid var(--border-accent);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 16px;
  animation: cardIn 0.35s ease;
}

.ai-status-card-error {
  background: rgba(255,83,112,0.1);
  border: 1px solid rgba(255,83,112,0.3);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 12px;
  animation: cardIn 0.35s ease;
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(-6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Status dot */
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  position: relative;
  top: -1px;
}
.status-dot-live {
  background: var(--success);
  box-shadow: 0 0 0 0 rgba(0,230,118,0.6);
  animation: pulseDot 1.8s infinite;
}
.status-dot-down { background: var(--danger); }
.status-dot-idle { background: var(--text-secondary); }
@keyframes pulseDot {
  0%   { box-shadow: 0 0 0 0 rgba(0,230,118,0.55); }
  70%  { box-shadow: 0 0 0 8px rgba(0,230,118,0); }
  100% { box-shadow: 0 0 0 0 rgba(0,230,118,0); }
}

/* Sidebar nav items */
[data-testid="stSidebarNavLink"] {
  border-radius: 8px !important;
  margin: 2px 0 !important;
}

/* Page content entrance animation */
[data-testid="stAppViewContainer"] > .main {
  animation: fadeInUp 0.28s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Header breadcrumb */
.app-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 2px 14px 2px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 18px;
}
.app-topbar-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}
.app-topbar-clock {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--text-secondary);
  letter-spacing: 0.02em;
}

/* Code blocks */
code { font-family: 'JetBrains Mono', monospace !important; }

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.001ms !important; animation-iteration-count: 1 !important; transition-duration: 0.001ms !important; }
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# ── Page registry ─────────────────────────────────────────────────────────────
# Maps each nav label to the module path that implements it.
PAGES = {
    "Dashboard": "pages.dashboard",
    "Projects": "pages.projects",
    "Requirements": "pages.requirements_page",
    "AI Test Generator": "pages.test_generator",
    "Test Cases": "pages.test_cases_page",
    "Test Execution": "pages.execution",
    "API Testing": "pages.api_testing",
    "Bug Management": "pages.bugs",
    "AI Failure Analysis": "pages.ai_analysis",
    "Reports": "pages.reports_page",
    "Settings": "pages.settings",
}
DEFAULT_PAGE = "Dashboard"

# ── Session state defaults ──────────────────────────────────────────────────
st.session_state.setdefault("selected_project_id", None)
st.session_state.setdefault("ai_status", None)
st.session_state.setdefault("ai_status_checked", False)
st.session_state.setdefault("ai_status_last_checked", None)
st.session_state.setdefault("current_page", DEFAULT_PAGE)
st.session_state.setdefault("auto_refresh_ai", False)


def _refresh_ai_status() -> None:
    st.session_state.ai_status = get_ai_status()
    st.session_state.ai_status_checked = True
    st.session_state.ai_status_last_checked = datetime.now()


def render_ai_status_card() -> None:
    """Render the AI/Ollama connectivity status block in the sidebar."""
    if not st.session_state.ai_status_checked or not st.session_state.ai_status:
        st.info(f"Model: `{MODEL_NAME}`\nClick above to check AI status.")
        return

    status = st.session_state.ai_status
    last_checked = st.session_state.ai_status_last_checked
    checked_str = last_checked.strftime("%H:%M:%S") if last_checked else "—"

    provider_name = status.get("provider_display", "AI Testing Engine")
    provider = status.get("provider", "ollama")

    if status.get("ready"):
        st.markdown(
            f"""
            <div class="ai-status-card">
              <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
                <div style="font-weight:700; color:#00e676;">
                  <span class="status-dot status-dot-live"></span>AI STATUS
                </div>
                <div style="font-size:0.7rem; color:#9ca3af;">as of {checked_str}</div>
              </div>
              <div style="font-weight:600; color:#e8eaf6;">{provider_name}</div>
              <div style="font-size:0.8rem; color:#9ca3af;">{status.get("model_msg", "Model ready")}</div>
              <div style="margin-top:8px; font-size:0.75rem; color:#a78bfa; font-weight:600;">
                AI Engine: READY
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if provider == "ollama":
        engine_line = (
            f'<div>{status.get("ollama_msg", "")}</div>'
            if not status.get("ollama")
            else "<div>✅ Ollama Connected</div>"
        )
        model_line = (
            f'<div>{status.get("model_msg", "")}</div>'
            if not status.get("model")
            else "<div>✅ Model Available</div>"
        )
        recovery_hint = (
            "Start Ollama by running: <code>ollama serve</code>"
            if not status.get("ollama")
            else f"Run: <code>ollama pull {status.get('configured_model', MODEL_NAME)}</code>"
        )
    else:
        engine_line = f'<div>{provider_name}</div>'
        model_line = f'<div>{status.get("ollama_msg", "API Key Required")}</div>'
        recovery_hint = "Configure your API key in <b>Settings &rarr; AI Provider</b> or switch to Demo Mode."

    st.markdown(
        f"""
        <div class="ai-status-card-error">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
            <div style="font-weight:700; color:#ff5370;">
              <span class="status-dot status-dot-down"></span>AI STATUS
            </div>
            <div style="font-size:0.7rem; color:#9ca3af;">as of {checked_str}</div>
          </div>
          {engine_line}
          {model_line}
          <div style="margin-top:8px; font-size:0.75rem; color:#ff5370;">
            {recovery_hint}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    """Render the sidebar: branding, AI status, and page navigation."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 20px 0 10px;">
              <div style="font-size:2.5rem;"></div>
              <div style="font-size:1.3rem; font-weight:800; background: linear-gradient(135deg, #6c63ff, #a78bfa);
                          -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                AI Software Tester
              </div>
              <div style="font-size:0.7rem; color:#9ca3af; margin-top:2px;">v{APP_VERSION}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        status_col, toggle_col = st.columns([2, 1])
        with status_col:
            if st.button("Check AI Status", use_container_width=True):
                with st.spinner("Checking AI Engine..."):
                    _refresh_ai_status()
        with toggle_col:
            st.session_state.auto_refresh_ai = st.toggle(
                "Auto", value=st.session_state.auto_refresh_ai, help="Re-check AI status every 30s"
            )

        render_ai_status_card()

        st.divider()
        st.markdown("**Navigation**")

        current = st.session_state.get("current_page", DEFAULT_PAGE)
        for label in PAGES:
            is_active = label == current
            if st.button(
                label,
                use_container_width=True,
                key=f"nav_{label}",
                type="primary" if is_active else "secondary",
            ):
                if not is_active:
                    st.session_state.current_page = label
                    st.rerun()

        st.divider()
        st.markdown(
            f"""
            <div style="font-size:0.7rem; color:#9ca3af; text-align:center; padding-top:4px;">
              Session started<br>{st.session_state.get('_session_start', datetime.now()).strftime('%H:%M:%S')}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_topbar(label: str) -> None:
    """Render a live breadcrumb/clock header above the active page."""
    st.markdown(
        f"""
        <div class="app-topbar">
          <div class="app-topbar-title">{label}</div>
          <div class="app-topbar-clock">{datetime.now().strftime('%A, %b %d — %H:%M:%S')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page(label: str) -> None:
    """Dynamically import and render the module associated with a nav label."""
    import importlib

    module_path = PAGES.get(label, PAGES[DEFAULT_PAGE])
    page_module = importlib.import_module(module_path)
    page_module.render()


# ── App entry point ─────────────────────────────────────────────────────────
st.session_state.setdefault("_session_start", datetime.now())

render_sidebar()

active_page = st.session_state.get("current_page", DEFAULT_PAGE)
render_topbar(active_page)
render_page(active_page)

# Optional lightweight auto-refresh loop for AI status, without extra deps.
if st.session_state.auto_refresh_ai:
    last = st.session_state.ai_status_last_checked
    if last is None or (datetime.now() - last).total_seconds() >= 30:
        _refresh_ai_status()
        st.rerun()
    else:
        time.sleep(1)
        st.rerun()

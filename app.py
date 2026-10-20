"""
AI Software Tester — Main Streamlit Application Entry Point
"""

import html as _html
import os
import sys
import time
from datetime import datetime

# Ensure the project root is on the Python path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import streamlit.components.v1 as components

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

# ── Design tokens ────────────────────────────────────────────────────────────
# Ink-blue surfaces, a single cobalt accent, and semantic status colours that
# a testing tool actually needs (pass / fail / blocked / info).
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  /* surfaces */
  --bg-primary:   #0b1016;
  --bg-secondary: #0f161e;
  --bg-card:      #131c26;
  --bg-raised:    #19242f;
  --bg-input:     #101921;

  /* accent + semantics */
  --accent:        #5b8cff;
  --accent-light:  #8fb0ff;
  --accent-glow:   rgba(91, 140, 255, 0.28);
  --accent-soft:   rgba(91, 140, 255, 0.12);
  --success: #34d399;
  --danger:  #f87171;
  --warning: #fbbf24;
  --info:    #38bdf8;

  /* text */
  --text-primary:   #e6edf5;
  --text-secondary: #8b9bb0;
  --text-muted:     #5f6f84;

  /* lines + shape */
  --border:        rgba(148, 170, 200, 0.12);
  --border-strong: rgba(148, 170, 200, 0.22);
  --border-accent: rgba(91, 140, 255, 0.45);
  --radius:    10px;
  --radius-lg: 14px;

  --font-ui:   'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, 'SFMono-Regular', Menlo, monospace;
}

/* ── Base ─────────────────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: var(--bg-primary) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui);
}
[data-testid="stAppViewContainer"] p,
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3,
[data-testid="stAppViewContainer"] h4 {
  font-family: var(--font-ui);
}
h1, h2, h3, h4 { letter-spacing: -0.01em; color: var(--text-primary); }
h1 { font-weight: 700; }
h2, h3 { font-weight: 600; }

/* Thin accent line across the top of the viewport */
[data-testid="stApp"]::before {
  content: "";
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 2px;
  z-index: 1000;
  background: linear-gradient(90deg, transparent, var(--accent) 30%, var(--info) 70%, transparent);
  opacity: 0.85;
}

/* Header: transparent (keeps the sidebar toggle usable), hide Streamlit chrome */
[data-testid="stHeader"] { background: transparent !important; }
footer, [data-testid="stFooter"], #MainMenu { visibility: hidden; }

/* Layout rhythm */
.block-container, [data-testid="stMainBlockContainer"] {
  padding-top: 1.6rem !important;
  padding-bottom: 4rem !important;
  max-width: 1400px;
}

/* Scrollbars */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--bg-raised);
  border: 2px solid var(--bg-primary);
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: #26354a; }

/* Visible keyboard focus everywhere */
button:focus-visible, a:focus-visible, [role="tab"]:focus-visible {
  outline: 2px solid var(--accent-light) !important;
  outline-offset: 2px !important;
}

/* ── Sidebar ──────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--bg-secondary) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 0.5rem; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: var(--text-primary); }
[data-testid="stSidebar"] hr { margin: 0.9rem 0 !important; }

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 4px 6px;
}
.brand-mark {
  flex: 0 0 auto;
  width: 38px; height: 38px;
  border-radius: 10px;
  display: grid; place-items: center;
  background: var(--accent-soft);
  border: 1px solid var(--border-accent);
}
.brand-name {
  font-size: 1.02rem;
  font-weight: 700;
  line-height: 1.15;
  color: var(--text-primary);
}
.brand-version {
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.nav-heading {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin: 2px 4px 6px;
}

/* ── Buttons ──────────────────────────────────────────────────────────── */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
  font-family: var(--font-ui) !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  padding: 0.5rem 1.2rem !important;
  transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease !important;
}

/* Primary actions in the main area */
[data-testid="stMain"] .stButton > button[kind="primary"],
section.main .stButton > button[kind="primary"],
[data-testid="stMain"] .stFormSubmitButton > button,
section.main .stFormSubmitButton > button {
  background: var(--accent) !important;
  color: #fff !important;
  border: 1px solid transparent !important;
  box-shadow: 0 1px 0 rgba(255,255,255,0.18) inset, 0 6px 18px -6px var(--accent-glow) !important;
}
[data-testid="stMain"] .stButton > button[kind="primary"]:hover,
section.main .stButton > button[kind="primary"]:hover,
[data-testid="stMain"] .stFormSubmitButton > button:hover,
section.main .stFormSubmitButton > button:hover {
  background: #7aa1ff !important;
  box-shadow: 0 1px 0 rgba(255,255,255,0.22) inset, 0 8px 22px -6px var(--accent-glow) !important;
}
/* Secondary actions in the main area */
[data-testid="stMain"] .stButton > button[kind="secondary"],
section.main .stButton > button[kind="secondary"],
.stDownloadButton > button {
  background: var(--bg-raised) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border-strong) !important;
  box-shadow: none !important;
}
[data-testid="stMain"] .stButton > button[kind="secondary"]:hover,
section.main .stButton > button[kind="secondary"]:hover,
.stDownloadButton > button:hover {
  border-color: var(--border-accent) !important;
  color: var(--accent-light) !important;
}
.stButton > button:active { transform: scale(0.985); }

/* Sidebar: utility button (Check AI Status) */
[data-testid="stSidebar"] .stButton > button {
  background: var(--bg-raised);
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
  box-shadow: none;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--border-accent);
  color: var(--accent-light);
}

/* Sidebar: navigation items (keyed nav_*) read as a list, not as buttons */
[class*="st-key-nav_"] .stButton > button,
[class*="st-key-nav_"] button {
  justify-content: flex-start !important;
  text-align: left !important;
  gap: 10px;
  padding: 0.5rem 0.8rem !important;
  min-height: 2.45rem;
  border-radius: 8px !important;
  position: relative;
  font-weight: 500 !important;
}
[class*="st-key-nav_"] button[kind="secondary"],
[class*="st-key-nav_"] button[data-testid="stBaseButton-secondary"] {
  background: transparent !important;
  border: 1px solid transparent !important;
  color: var(--text-secondary) !important;
}
[class*="st-key-nav_"] button[kind="secondary"]:hover,
[class*="st-key-nav_"] button[data-testid="stBaseButton-secondary"]:hover {
  background: var(--bg-raised) !important;
  color: var(--text-primary) !important;
  border-color: var(--border) !important;
  padding-left: 1rem !important;
}
[class*="st-key-nav_"] button[kind="primary"],
[class*="st-key-nav_"] button[data-testid="stBaseButton-primary"] {
  background: var(--accent-soft) !important;
  color: var(--accent-light) !important;
  border: 1px solid var(--border-accent) !important;
  box-shadow: none !important;
  font-weight: 600 !important;
}
[class*="st-key-nav_"] button[kind="primary"]::before,
[class*="st-key-nav_"] button[data-testid="stBaseButton-primary"]::before {
  content: "";
  position: absolute;
  left: -1px; top: 20%; bottom: 20%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
  box-shadow: 0 0 10px var(--accent-glow);
}
[class*="st-key-nav_"] button p { text-align: left; }

/* ── Inputs ───────────────────────────────────────────────────────────── */
[data-baseweb="input"],
[data-baseweb="textarea"],
[data-baseweb="select"] > div,
.stNumberInput [data-baseweb="input"] {
  background: var(--bg-input) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 8px !important;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
  background: transparent !important;
  color: var(--text-primary) !important;
  font-family: var(--font-ui);
}
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"] > div:focus-within {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
[data-baseweb="popover"] [role="listbox"],
[data-baseweb="menu"] {
  background: var(--bg-raised) !important;
  border: 1px solid var(--border-strong) !important;
  border-radius: 8px !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stNumberInput label, .stMultiSelect label, .stSlider label {
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  color: var(--text-secondary) !important;
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--bg-input) !important;
  border: 1px dashed var(--border-strong) !important;
  border-radius: var(--radius) !important;
  transition: border-color 0.15s ease, background 0.15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--accent) !important;
  background: var(--accent-soft) !important;
}

/* ── Metrics ──────────────────────────────────────────────────────────── */
[data-testid="stMetric"], [data-testid="metric-container"] {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s ease;
}
[data-testid="stMetric"]::before, [data-testid="metric-container"]::before {
  content: "";
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--accent);
  opacity: 0.8;
}
[data-testid="stMetric"]:hover, [data-testid="metric-container"]:hover {
  border-color: var(--border-accent);
}
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-weight: 500; }
[data-testid="stMetricValue"] {
  color: var(--text-primary) !important;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
}

/* ── Tables ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  overflow: hidden;
}

/* ── Tabs ─────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
  gap: 4px;
  border-bottom: 1px solid var(--border);
}
[data-testid="stTabs"] button[role="tab"] {
  color: var(--text-secondary) !important;
  font-weight: 500 !important;
  border-radius: 8px 8px 0 0;
  padding: 0.55rem 1rem;
  transition: color 0.15s ease, background 0.15s ease;
}
[data-testid="stTabs"] button[role="tab"]:hover {
  color: var(--text-primary) !important;
  background: var(--bg-raised);
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: var(--accent-light) !important;
  font-weight: 600 !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 2px; }
[data-testid="stTabs"] [data-baseweb="tab-border"] { background: transparent !important; }

/* ── Expanders, alerts, progress ──────────────────────────────────────── */
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  transition: border-color 0.2s ease;
}
[data-testid="stExpander"]:hover { border-color: var(--border-strong) !important; }
[data-testid="stExpander"] summary { font-weight: 500; }

[data-testid="stAlert"] {
  border-radius: var(--radius) !important;
  border: 1px solid var(--border-strong) !important;
  background: var(--bg-card) !important;
}
[data-testid="stProgress"] > div > div { background: var(--bg-raised) !important; border-radius: 10px; }
[data-testid="stProgress"] > div > div > div { background: var(--accent) !important; border-radius: 10px; }

hr { border-color: var(--border) !important; }

/* ── Reusable components (used by the pages) ──────────────────────────── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 6px;
  font-size: 0.74rem;
  font-weight: 600;
  line-height: 1.6;
}
.badge::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.badge-pass    { background: rgba(52,211,153,0.12);  color: #34d399; border: 1px solid rgba(52,211,153,0.28); }
.badge-fail    { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.28); }
.badge-blocked { background: rgba(251,191,36,0.12);  color: #fbbf24; border: 1px solid rgba(251,191,36,0.28); }
.badge-skipped { background: rgba(139,155,176,0.12); color: #8b9bb0; border: 1px solid rgba(139,155,176,0.28); }
.badge-open    { background: rgba(248,113,113,0.12); color: #f87171; border: 1px solid rgba(248,113,113,0.28); }
.badge-closed  { background: rgba(52,211,153,0.12);  color: #34d399; border: 1px solid rgba(52,211,153,0.28); }

.glass-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 22px 24px;
  margin-bottom: 16px;
  transition: border-color 0.2s ease;
}
.glass-card:hover { border-color: var(--border-strong); }

/* AI status block (sidebar) */
.ai-status-card, .ai-status-card-error {
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-strong);
  border-left-width: 3px;
}
.ai-status-card       { border-left-color: var(--success); }
.ai-status-card-error { border-left-color: var(--danger); }
.ai-status-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.ai-status-title { font-weight: 600; font-size: 0.8rem; display: flex; align-items: center; }
.ai-status-time  { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); }
.ai-status-body  { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }
.ai-status-body b, .ai-status-body strong { color: var(--text-primary); }
.ai-status-foot  { margin-top: 10px; font-size: 0.75rem; }
.ai-status-foot code {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 1px 6px;
}

/* Status dot — only the "live" state is animated */
.status-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-right: 8px;
  position: relative; top: -1px;
}
.status-dot-live {
  background: var(--success);
  box-shadow: 0 0 0 0 rgba(52,211,153,0.6);
  animation: pulseDot 2s infinite;
}
.status-dot-down { background: var(--danger); }
.status-dot-idle { background: var(--text-muted); }
@keyframes pulseDot {
  0%   { box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }
  70%  { box-shadow: 0 0 0 8px rgba(52,211,153,0); }
  100% { box-shadow: 0 0 0 0 rgba(52,211,153,0); }
}

/* Sidebar footer */
.session-note {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  color: var(--text-muted);
  padding-top: 2px;
}

/* Code */
code, pre, kbd { font-family: var(--font-mono) !important; }
[data-testid="stCode"], pre {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
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

# Icons for the navigation (Material Symbols). Purely cosmetic: if the installed
# Streamlit version doesn't support button icons, nav falls back to text only.
NAV_ICONS = {
    "Dashboard": ":material/dashboard:",
    "Projects": ":material/folder_open:",
    "Requirements": ":material/checklist:",
    "AI Test Generator": ":material/auto_awesome:",
    "Test Cases": ":material/fact_check:",
    "Test Execution": ":material/play_circle:",
    "API Testing": ":material/api:",
    "Bug Management": ":material/bug_report:",
    "AI Failure Analysis": ":material/troubleshoot:",
    "Reports": ":material/assessment:",
    "Settings": ":material/settings:",
}

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
              <div class="ai-status-head">
                <div class="ai-status-title" style="color:var(--success);">
                  <span class="status-dot status-dot-live"></span>AI engine ready
                </div>
                <div class="ai-status-time">{checked_str}</div>
              </div>
              <div class="ai-status-body">
                <b>{provider_name}</b><br>
                {status.get("model_msg", "Model ready")}
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
          <div class="ai-status-head">
            <div class="ai-status-title" style="color:var(--danger);">
              <span class="status-dot status-dot-down"></span>AI engine unavailable
            </div>
            <div class="ai-status-time">{checked_str}</div>
          </div>
          <div class="ai-status-body">
            {engine_line}
            {model_line}
          </div>
          <div class="ai-status-foot" style="color:var(--text-secondary);">
            {recovery_hint}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _nav_button(label: str, is_active: bool) -> bool:
    """Render one nav item. Uses an icon when the Streamlit version supports it."""
    kwargs = dict(
        use_container_width=True,
        key=f"nav_{label}",
        type="primary" if is_active else "secondary",
    )
    try:
        return st.button(label, icon=NAV_ICONS.get(label), **kwargs)
    except TypeError:
        return st.button(label, **kwargs)


def render_sidebar() -> None:
    """Render the sidebar: branding, AI status, and page navigation."""
    with st.sidebar:
        st.markdown(
            f"""
            <div class="brand">
              <div class="brand-mark">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
                     stroke="#8fb0ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M8 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h3"/>
                  <path d="M16 4h3a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-3"/>
                  <path d="m8.5 12 2.5 2.5 4.5-5"/>
                </svg>
              </div>
              <div>
                <div class="brand-name">AI Software Tester</div>
                <div class="brand-version">v{APP_VERSION}</div>
              </div>
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
        st.markdown('<div class="nav-heading">Navigation</div>', unsafe_allow_html=True)

        current = st.session_state.get("current_page", DEFAULT_PAGE)
        for label in PAGES:
            is_active = label == current
            if _nav_button(label, is_active):
                if not is_active:
                    st.session_state.current_page = label
                    st.rerun()

        st.divider()
        started = st.session_state.get("_session_start", datetime.now()).strftime("%H:%M:%S")
        st.markdown(
            f"""
            <div class="session-note">
              <span class="status-dot status-dot-idle" style="margin-right:0;"></span>
              Session started {started}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _ai_pill_state() -> tuple:
    """Return (css class, text) describing AI state for the top bar."""
    if not st.session_state.ai_status_checked or not st.session_state.ai_status:
        return "idle", "AI not checked"
    if st.session_state.ai_status.get("ready"):
        return "live", "AI ready"
    return "down", "AI offline"


def render_topbar(label: str) -> None:
    """Render the breadcrumb header with a live-ticking clock above the active page.

    Rendered in a small iframe so the clock can update every second in the
    browser without re-running the Streamlit script.
    """
    pill_state, pill_text = _ai_pill_state()
    safe_label = _html.escape(label)

    components.html(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
          * {{ box-sizing: border-box; margin: 0; }}
          body {{
            background: transparent;
            font-family: 'IBM Plex Sans', system-ui, sans-serif;
            color: #e6edf5;
          }}
          .bar {{
            display: flex; align-items: center; justify-content: space-between;
            height: 52px; padding: 0 2px 10px;
            border-bottom: 1px solid rgba(148,170,200,0.12);
          }}
          .crumb {{ display: flex; align-items: baseline; gap: 10px; min-width: 0; }}
          .crumb .root {{ font-size: 0.82rem; color: #5f6f84; white-space: nowrap; }}
          .crumb .sep  {{ color: #3a485a; }}
          .crumb .page {{ font-size: 1.15rem; font-weight: 700; letter-spacing: -0.01em;
                          white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
          .right {{ display: flex; align-items: center; gap: 14px; }}
          .pill {{
            display: inline-flex; align-items: center; gap: 8px;
            padding: 4px 11px; border-radius: 999px;
            font-size: 0.75rem; font-weight: 500;
            border: 1px solid rgba(148,170,200,0.2);
            background: #131c26; color: #8b9bb0;
          }}
          .dot {{ width: 7px; height: 7px; border-radius: 50%; background: #5f6f84; }}
          .pill.live {{ color: #34d399; border-color: rgba(52,211,153,0.3); background: rgba(52,211,153,0.08); }}
          .pill.live .dot {{ background: #34d399; animation: pulse 2s infinite; }}
          .pill.down {{ color: #f87171; border-color: rgba(248,113,113,0.3); background: rgba(248,113,113,0.08); }}
          .pill.down .dot {{ background: #f87171; }}
          .clock {{ text-align: right; line-height: 1.25; }}
          .clock .time {{ font-family: 'IBM Plex Mono', monospace; font-size: 0.95rem;
                          font-weight: 500; font-variant-numeric: tabular-nums; }}
          .clock .date {{ font-size: 0.7rem; color: #5f6f84; }}
          @keyframes pulse {{
            0%   {{ box-shadow: 0 0 0 0 rgba(52,211,153,0.5); }}
            70%  {{ box-shadow: 0 0 0 7px rgba(52,211,153,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(52,211,153,0); }}
          }}
          @media (max-width: 560px) {{ .crumb .root, .crumb .sep, .clock .date {{ display: none; }} }}
          @media (prefers-reduced-motion: reduce) {{ .dot {{ animation: none !important; }} }}
        </style>
        <div class="bar">
          <div class="crumb">
            <span class="root">AI Software Tester</span>
            <span class="sep">/</span>
            <span class="page">{safe_label}</span>
          </div>
          <div class="right">
            <span class="pill {pill_state}"><span class="dot"></span>{pill_text}</span>
            <div class="clock">
              <div class="time" id="t">--:--:--</div>
              <div class="date" id="d"></div>
            </div>
          </div>
        </div>
        <script>
          const t = document.getElementById('t'), d = document.getElementById('d');
          function tick() {{
            const n = new Date();
            t.textContent = n.toLocaleTimeString('en-GB', {{ hour12: false }});
            d.textContent = n.toLocaleDateString('en-US', {{ weekday: 'long', month: 'short', day: '2-digit' }});
          }}
          tick(); setInterval(tick, 1000);
        </script>
        """,
        height=62,
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
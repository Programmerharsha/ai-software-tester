"""
Central configuration for AI Software Tester.
All model names and URLs are defined ONCE here.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "ai_tester.db"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
REPORTS_DIR = BASE_DIR / "reports"

SCREENSHOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# ── Helper for Streamlit Secrets / Env ─────────────────────────────────────────
def get_config_val(key: str, default: str = "") -> str:
    """Read configuration value safely from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets.get(key)
            if val is not None:
                return str(val).strip()
    except Exception:
        pass
    return os.environ.get(key, default)


# ── AI Providers Configuration ────────────────────────────────────────────────
# Supported providers: "gemini" | "groq" | "openai" | "ollama" | "demo"
AI_PROVIDER = get_config_val("AI_PROVIDER", "auto")

GEMINI_API_KEY = get_config_val("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = get_config_val("GEMINI_MODEL", "gemini-1.5-flash")

GROQ_API_KEY = get_config_val("GROQ_API_KEY", "")
DEFAULT_GROQ_MODEL = get_config_val("GROQ_MODEL", "llama-3.3-70b-versatile")

OPENAI_API_KEY = get_config_val("OPENAI_API_KEY", "")
DEFAULT_OPENAI_MODEL = get_config_val("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_OPENAI_BASE_URL = get_config_val("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ── Ollama / AI ────────────────────────────────────────────────────────────────
OLLAMA_URL = get_config_val("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = get_config_val("AI_MODEL", "qwen2.5-coder:7b")   # NEVER change silently

AI_TEMPERATURE = 0.2
AI_NUM_CTX = 8192
AI_TIMEOUT = 300          # seconds – generation can be slow locally

# ── Playwright ─────────────────────────────────────────────────────────────────
DEFAULT_BROWSER = "chromium"     # chromium | firefox | webkit
HEADLESS_MODE = True
TEST_TIMEOUT = 30_000            # ms

# ── Action Allowlist ───────────────────────────────────────────────────────────
ALLOWED_ACTIONS = {
    "navigate",
    "click",
    "fill",
    "select",
    "check",
    "uncheck",
    "press",
    "wait",
    "assert_visible",
    "assert_hidden",
    "assert_text",
    "assert_url",
    "screenshot",
}

# ── App metadata ───────────────────────────────────────────────────────────────
APP_NAME = "AI Software Tester"
APP_VERSION = "1.0.0"
APP_ICON = ""

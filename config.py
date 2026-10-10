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

# ── Ollama / AI ────────────────────────────────────────────────────────────────
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.environ.get("AI_MODEL", "qwen2.5-coder:7b")   # NEVER change silently

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

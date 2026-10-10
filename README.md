# 🤖 AI Software Tester

A complete **AI-Powered Software Testing Application** using:
- **Python** + **Streamlit** (UI)
- **Qwen2.5-Coder 7B** via **Ollama** (AI engine)
- **Playwright** (browser automation)
- **requests** (API testing)
- **SQLite** (database)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 Requirement Analysis | Qwen analyzes requirements to extract functional specs, edge cases, risks |
| 🧪 AI Test Generation | Generates comprehensive positive/negative/boundary/security test cases |
| ⚙️ Test Automation | Converts test cases to validated Playwright/API actions |
| 🛡️ Safe Execution | All AI-generated actions validated against strict allowlist before execution |
| 📸 Failure Capture | Screenshots, error messages, and context captured on failure |
| 🔬 AI Failure Analysis | Qwen classifies failures and suggests root causes |
| 🐛 Bug Reports | AI-generated professional bug reports, editable before saving |
| 📊 Dashboard | Live KPI metrics, Plotly charts, traceability matrix |
| 📋 Reports | HTML/CSV/PDF export |

---

## 🚀 Quick Start

### Prerequisites
1. Python 3.10+
2. [Ollama](https://ollama.com/) installed and running
3. Qwen2.5-Coder 7B model

### Step 1 — Install Qwen model
```bash
ollama pull qwen2.5-coder:7b
```

### Step 2 — Create virtualenv
```bash
python -m venv venv
venv\Scripts\activate      # Windows
# or: source venv/bin/activate  (Linux/Mac)
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
playwright install
```

### Step 4 — (Optional) Start Demo App
In a separate terminal:
```bash
cd demo_app
pip install flask
python app.py
# Runs at http://localhost:5000
```

### Step 5 — Run the app
```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## 📁 Project Structure

```
ai_software_tester/
│
├── app.py                    # Main Streamlit entry point
├── config.py                 # Central config (OLLAMA_URL, MODEL_NAME)
├── requirements.txt
│
├── ai/
│   ├── ollama_client.py      # Ollama REST API client + health checks
│   ├── ai_service.py         # High-level AI orchestrator
│   ├── prompts.py            # All prompt templates (JSON-structured)
│   └── response_parser.py    # JSON extraction + schema validators
│
├── database/
│   ├── schema.py             # DDL for all 10 SQLite tables
│   ├── database.py           # CRUD helpers
│   └── models.py             # Python dataclasses
│
├── testing/
│   ├── action_validator.py   # Strict action allowlist enforcement
│   ├── playwright_engine.py  # Playwright executor
│   ├── api_engine.py         # HTTP API test executor
│   └── test_executor.py      # Orchestrates full test runs
│
├── pages/                    # 11 Streamlit pages
│   ├── dashboard.py
│   ├── projects.py
│   ├── requirements_page.py
│   ├── test_generator.py
│   ├── test_cases_page.py
│   ├── execution.py
│   ├── api_testing.py
│   ├── bugs.py
│   ├── ai_analysis.py
│   ├── reports_page.py
│   └── settings.py
│
├── demo_app/                 # Demo Flask app with intentional bugs
│   ├── app.py
│   ├── BUGS.md               # Intentional bug documentation
│   └── README.md
│
├── screenshots/              # Test failure screenshots
├── reports/                  # Generated reports
└── tests/                    # Unit tests
    ├── test_ai.py
    ├── test_database.py
    ├── test_executor.py
    └── test_metrics.py
```

---

## 🔒 Security Model

The AI **never executes arbitrary code**. Qwen generates structured JSON actions:

```json
{
  "actions": [
    {"type": "navigate", "url": "/login"},
    {"type": "fill", "selector": "#email", "value": "test@example.com"},
    {"type": "click", "selector": "#login"},
    {"type": "assert_visible", "selector": "#dashboard"}
  ]
}
```

Only these action types are allowed:
`navigate`, `click`, `fill`, `select`, `check`, `uncheck`, `press`, `wait`,
`assert_visible`, `assert_hidden`, `assert_text`, `assert_url`, `screenshot`

Any other action type is **rejected before execution**.

---

## 🤖 AI Configuration

Central config in `config.py`:
```python
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:7b"
```

The model is **never silently switched**. All settings are configurable from the Settings page.

---

## 🏗️ E2E Workflow

```
Create Project → Add Requirement → Analyze with Qwen
→ Generate Test Cases → Approve & Save
→ Generate Actions → Validate → Execute via Playwright
→ Capture Results → AI Failure Analysis
→ Generate Bug Report → Dashboard → Export Report
```

---

## 🧪 Running Unit Tests

```bash
cd ai_software_tester
pytest tests/ -v
```

---

## 📝 Demo App Intentional Bugs

See `demo_app/BUGS.md` for documentation of 4 intentional bugs:
- BUG-001: Wrong redirect after login
- BUG-002: Missing password confirmation validation
- BUG-003: Hardcoded welcome message
- BUG-004: Authentication bypass for demo account

These bugs are intentional so the testing tool can demonstrate real failure detection.

---

## ⚙️ Settings

Configurable from the Settings page (stored in SQLite):

| Setting | Default | Description |
|---------|---------|-------------|
| Ollama URL | http://localhost:11434 | Ollama endpoint |
| AI Model | qwen2.5-coder:7b | Must not be silently changed |
| Browser | chromium | chromium / firefox / webkit |
| Headless Mode | true | Run browsers headlessly |
| Test Timeout | 30000ms | Per-action timeout |
| Screenshot on Failure | true | Auto-capture on failure |

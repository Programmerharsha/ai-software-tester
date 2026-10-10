"""
Database schema — DDL for all 10 tables.
"""

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS settings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    key           TEXT UNIQUE NOT NULL,
    value         TEXT,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    description   TEXT,
    base_url      TEXT,
    status        TEXT DEFAULT 'Active',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requirements (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    req_id        TEXT NOT NULL,
    title         TEXT NOT NULL,
    description   TEXT,
    priority      TEXT DEFAULT 'Medium',
    status        TEXT DEFAULT 'Draft',
    analysis      TEXT,          -- JSON blob from Qwen
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    requirement_id  INTEGER REFERENCES requirements(id) ON DELETE SET NULL,
    tc_id           TEXT NOT NULL,
    scenario        TEXT NOT NULL,
    description     TEXT,
    test_type       TEXT DEFAULT 'Functional',
    preconditions   TEXT,
    test_data       TEXT,
    expected_result TEXT,
    priority        TEXT DEFAULT 'Medium',
    severity        TEXT DEFAULT 'Medium',
    automation      TEXT DEFAULT 'Manual',   -- Manual | Automated | Partial
    status          TEXT DEFAULT 'Not Executed',
    created_by      TEXT DEFAULT 'AI',
    actions_json    TEXT,        -- validated Playwright/API actions
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_steps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    test_case_id    INTEGER NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    step_number     INTEGER NOT NULL,
    action          TEXT NOT NULL,
    expected        TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_executions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name            TEXT,
    browser         TEXT DEFAULT 'chromium',
    headless        INTEGER DEFAULT 1,
    base_url        TEXT,
    status          TEXT DEFAULT 'Pending',   -- Pending | Running | Completed | Aborted
    started_at      DATETIME,
    completed_at    DATETIME,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id    INTEGER NOT NULL REFERENCES test_executions(id) ON DELETE CASCADE,
    test_case_id    INTEGER NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    result          TEXT DEFAULT 'Not Executed',  -- Pass | Fail | Blocked | Skipped | Not Executed
    duration_ms     INTEGER,
    error_message   TEXT,
    failed_step     TEXT,
    actual_result   TEXT,
    url_at_failure  TEXT,
    browser_info    TEXT,
    ai_analysis     TEXT,        -- JSON blob from Qwen failure analysis
    executed_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bugs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    result_id       INTEGER REFERENCES execution_results(id) ON DELETE SET NULL,
    bug_id          TEXT NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT,
    severity        TEXT DEFAULT 'Medium',
    priority        TEXT DEFAULT 'Medium',
    status          TEXT DEFAULT 'Open',      -- Open | In Progress | Resolved | Closed | Wont Fix
    environment     TEXT,
    steps_to_repro  TEXT,
    expected_result TEXT,
    actual_result   TEXT,
    error_message   TEXT,
    possible_cause  TEXT,
    assigned_to     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS screenshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id       INTEGER REFERENCES execution_results(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,
    label           TEXT,
    captured_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_analysis (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id       INTEGER REFERENCES execution_results(id) ON DELETE CASCADE,
    analysis_type   TEXT,        -- failure | bug_report | requirement | test_gen
    prompt_used     TEXT,
    raw_response    TEXT,
    parsed_json     TEXT,
    model_used      TEXT,
    tokens_used     INTEGER,
    duration_ms     INTEGER,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    execution_id    INTEGER REFERENCES test_executions(id) ON DELETE SET NULL,
    name            TEXT,
    format          TEXT,        -- HTML | CSV | PDF
    file_path       TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Default settings
INSERT OR IGNORE INTO settings (key, value) VALUES
    ('ollama_url', 'http://localhost:11434'),
    ('ai_model', 'qwen2.5-coder:7b'),
    ('browser', 'chromium'),
    ('headless', '1'),
    ('test_timeout', '30000'),
    ('screenshot_on_failure', '1');
"""

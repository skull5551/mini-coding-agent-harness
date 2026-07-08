CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    max_steps INTEGER NOT NULL DEFAULT 20,
    workspace_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS execution_steps (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    action TEXT NOT NULL,
    input_summary TEXT,
    output_summary TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS tool_calls (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    input TEXT,
    output TEXT,
    exit_code INTEGER,
    status TEXT NOT NULL DEFAULT 'success',
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (step_id) REFERENCES execution_steps(id)
);

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL UNIQUE,
    key_masked TEXT NOT NULL,
    key_value TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
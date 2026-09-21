-- Conversation threads attached to a student
CREATE TABLE IF NOT EXISTS thread (
    id          TEXT PRIMARY KEY,
    student_id  TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Individual interaction messages within a conversation thread
CREATE TABLE IF NOT EXISTS message (
    id          TEXT PRIMARY KEY,
    thread_id   TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (thread_id) REFERENCES thread(id) ON DELETE CASCADE
);

-- Agent execution runs
CREATE TABLE IF NOT EXISTS run (
    id           TEXT PRIMARY KEY,
    thread_id    TEXT NOT NULL,
    status       TEXT NOT NULL CHECK (status IN ('queued', 'in_progress', 'requires_action', 'completed', 'failed', 'cancelled')),
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,
    error        TEXT,
    FOREIGN KEY (thread_id) REFERENCES thread(id) ON DELETE CASCADE
);

-- Sequential steps inside an execution run
CREATE TABLE IF NOT EXISTS run_step (
    id           TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL,
    step_seq     INTEGER NOT NULL,
    type         TEXT NOT NULL CHECK (type IN ('message_creation', 'tool_calls')),
    status       TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completed_at TEXT,
    FOREIGN KEY (run_id) REFERENCES run(id) ON DELETE CASCADE,
    UNIQUE (run_id, step_seq)
);

-- Tool calls executed during a specific run step
CREATE TABLE IF NOT EXISTS tool_call (
    id         TEXT PRIMARY KEY,
    step_id    TEXT NOT NULL,
    tool_name  TEXT NOT NULL,
    args       TEXT NOT NULL, -- JSON formatted arguments
    output     TEXT,          -- JSON string or return text
    status     TEXT NOT NULL CHECK (status IN ('in_progress', 'completed', 'failed')),
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (step_id) REFERENCES run_step(id) ON DELETE CASCADE
);
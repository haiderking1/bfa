SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    source_path TEXT NOT NULL UNIQUE,
    source_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strings (
    id INTEGER PRIMARY KEY,
    source_text TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS occurrences (
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    string_id INTEGER NOT NULL REFERENCES strings(id) ON DELETE CASCADE,
    json_path TEXT NOT NULL,
    PRIMARY KEY (document_id, json_path)
);

CREATE TABLE IF NOT EXISTS translations (
    string_id INTEGER NOT NULL REFERENCES strings(id) ON DELETE CASCADE,
    target_language TEXT NOT NULL,
    translated_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_text TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (string_id, target_language)
);

CREATE INDEX IF NOT EXISTS idx_translations_status
    ON translations(target_language, status);
CREATE INDEX IF NOT EXISTS idx_occurrences_string
    ON occurrences(string_id);
"""

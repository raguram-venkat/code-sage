-- Migration 001: Initial Schema
-- Description: Create core tables for repos, files, chunks, and call graph

-- Migrations tracking table already created by the migration manager

-- Configuration table (for global settings)
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default config
INSERT OR IGNORE INTO config (key, value) VALUES 
    ('auto_embed', 'true'),
    ('max_tokens_per_chunk', '512'),
    ('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2');

-- Repositories
CREATE TABLE repos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    url TEXT,
    last_parsed TIMESTAMP,
    commit_hash TEXT,
    total_files INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Files in repositories
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,        -- SHA256 for incremental updates
    size_bytes INTEGER,
    last_modified TIMESTAMP,
    is_parsed BOOLEAN DEFAULT 0,
    parse_error TEXT,               -- NULL if parsed successfully
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id) ON DELETE CASCADE,
    UNIQUE(repo_id, relative_path)
);

-- Code chunks (functions, classes, methods)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    node_type TEXT NOT NULL,        -- function, class, method, module
    name TEXT NOT NULL,
    qualified_name TEXT,            -- MyClass.my_method (for methods)
    signature TEXT,
    docstring TEXT,
    code TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    token_count INTEGER,
    parent_chunk_id INTEGER,        -- For nested structures (methods in classes)
    embedding_id INTEGER,           -- NULL = needs embedding
    enhanced_text TEXT,             -- Pre-computed enriched text for embedding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

-- Function calls (call graph edges)
CREATE TABLE function_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caller_chunk_id INTEGER NOT NULL,
    callee_name TEXT NOT NULL,      -- Function name being called
    callee_chunk_id INTEGER,        -- NULL if external/unresolved
    call_line INTEGER,              -- Line where call happens
    call_col INTEGER,               -- Column where call happens
    is_external BOOLEAN DEFAULT 0,  -- True if stdlib/3rd party
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (caller_chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    FOREIGN KEY (callee_chunk_id) REFERENCES chunks(id) ON DELETE SET NULL
);

-- Imports (track dependencies)
CREATE TABLE imports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    module_name TEXT NOT NULL,      -- os, requests, myapp.utils
    imported_names TEXT,            -- JSON: ["func1", "Class2"]
    is_local BOOLEAN DEFAULT 0,     -- True if from same repo
    line_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Embedding queue (chunks that need embeddings)
CREATE TABLE embedding_queue (
    chunk_id INTEGER PRIMARY KEY,
    priority INTEGER DEFAULT 0,     -- Higher = process first
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_files_repo ON files(repo_id);
CREATE INDEX idx_files_hash ON files(file_hash);
CREATE INDEX idx_files_parsed ON files(is_parsed);

CREATE INDEX idx_chunks_file ON chunks(file_id);
CREATE INDEX idx_chunks_name ON chunks(name);
CREATE INDEX idx_chunks_type ON chunks(node_type);
CREATE INDEX idx_chunks_embedding ON chunks(embedding_id);
CREATE INDEX idx_chunks_parent ON chunks(parent_chunk_id);

CREATE INDEX idx_calls_caller ON function_calls(caller_chunk_id);
CREATE INDEX idx_calls_callee_id ON function_calls(callee_chunk_id);
CREATE INDEX idx_calls_callee_name ON function_calls(callee_name);

CREATE INDEX idx_imports_file ON imports(file_id);
CREATE INDEX idx_imports_module ON imports(module_name);

CREATE INDEX idx_queue_priority ON embedding_queue(priority DESC, added_at);


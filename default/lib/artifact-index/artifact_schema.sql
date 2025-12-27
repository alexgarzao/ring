-- Ring Artifact Index Schema
-- Database location: $PROJECT_ROOT/.ring/cache/artifact-index/context.db
--
-- This schema supports indexing and querying Ring session artifacts:
-- - Handoffs (completed tasks with post-mortems)
-- - Plans (design documents)
-- - Continuity ledgers (session state snapshots)
-- - Queries (compound learning from Q&A)
--
-- FTS5 is used for full-text search with porter stemming.
-- Triggers keep FTS5 indexes in sync with main tables.
-- Adapted from Continuous-Claude-v2 for Ring plugin architecture.

-- Enable WAL mode for better concurrent read performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- ============================================================================
-- MAIN TABLES
-- ============================================================================

-- Handoffs (completed tasks with post-mortems)
CREATE TABLE IF NOT EXISTS handoffs (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,
    task_number INTEGER,
    file_path TEXT NOT NULL,

    -- Core content
    task_summary TEXT,
    what_worked TEXT,
    what_failed TEXT,
    key_decisions TEXT,
    files_modified TEXT,  -- JSON array

    -- Outcome (from user annotation)
    outcome TEXT CHECK(outcome IN ('SUCCEEDED', 'PARTIAL_PLUS', 'PARTIAL_MINUS', 'FAILED', 'UNKNOWN')),
    outcome_notes TEXT,
    confidence TEXT CHECK(confidence IN ('HIGH', 'INFERRED')) DEFAULT 'INFERRED',

    -- Trace correlation (for debugging and analysis)
    session_id TEXT,         -- Claude session ID
    trace_id TEXT,           -- Optional external trace ID

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plans (design documents)
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    session_name TEXT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL,

    -- Content
    overview TEXT,
    approach TEXT,
    phases TEXT,  -- JSON array
    constraints TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Continuity snapshots (session state at key moments)
CREATE TABLE IF NOT EXISTS continuity (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,

    -- State
    goal TEXT,
    state_done TEXT,  -- JSON array
    state_now TEXT,
    state_next TEXT,
    key_learnings TEXT,
    key_decisions TEXT,

    -- Context
    snapshot_reason TEXT CHECK(snapshot_reason IN ('phase_complete', 'session_end', 'milestone', 'manual', 'clear', 'compact')),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queries (compound learning from Q&A)
CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,

    -- Matches
    handoffs_matched TEXT,  -- JSON array of IDs
    plans_matched TEXT,
    continuity_matched TEXT,

    -- Feedback
    was_helpful BOOLEAN,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learnings (extracted patterns from successful/failed sessions)
CREATE TABLE IF NOT EXISTS learnings (
    id TEXT PRIMARY KEY,
    pattern_type TEXT CHECK(pattern_type IN ('success', 'failure', 'efficiency', 'antipattern')),

    -- Content
    description TEXT NOT NULL,
    context TEXT,  -- When this applies
    recommendation TEXT,  -- What to do

    -- Source tracking
    source_handoffs TEXT,  -- JSON array of handoff IDs
    occurrence_count INTEGER DEFAULT 1,

    -- Status
    promoted_to TEXT,  -- 'rule', 'skill', 'hook', or NULL
    promoted_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FTS5 INDEXES (Full-Text Search)
-- ============================================================================

-- FTS5 indexes for full-text search
-- Using porter tokenizer for stemming + prefix index for code identifiers
CREATE VIRTUAL TABLE IF NOT EXISTS handoffs_fts USING fts5(
    task_summary, what_worked, what_failed, key_decisions, files_modified,
    content='handoffs', content_rowid='rowid',
    tokenize='porter ascii',
    prefix='2 3'
);

CREATE VIRTUAL TABLE IF NOT EXISTS plans_fts USING fts5(
    title, overview, approach, phases, constraints,
    content='plans', content_rowid='rowid',
    tokenize='porter ascii',
    prefix='2 3'
);

CREATE VIRTUAL TABLE IF NOT EXISTS continuity_fts USING fts5(
    goal, key_learnings, key_decisions, state_now,
    content='continuity', content_rowid='rowid',
    tokenize='porter ascii'
);

CREATE VIRTUAL TABLE IF NOT EXISTS queries_fts USING fts5(
    question, answer,
    content='queries', content_rowid='rowid',
    tokenize='porter ascii'
);

CREATE VIRTUAL TABLE IF NOT EXISTS learnings_fts USING fts5(
    description, context, recommendation,
    content='learnings', content_rowid='rowid',
    tokenize='porter ascii'
);

-- ============================================================================
-- SYNC TRIGGERS (Keep FTS5 in sync with main tables)
-- ============================================================================

-- HANDOFFS triggers
CREATE TRIGGER IF NOT EXISTS handoffs_ai AFTER INSERT ON handoffs BEGIN
    INSERT INTO handoffs_fts(rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES (NEW.rowid, NEW.task_summary, NEW.what_worked, NEW.what_failed, NEW.key_decisions, NEW.files_modified);
END;

CREATE TRIGGER IF NOT EXISTS handoffs_ad AFTER DELETE ON handoffs BEGIN
    INSERT INTO handoffs_fts(handoffs_fts, rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES('delete', OLD.rowid, OLD.task_summary, OLD.what_worked, OLD.what_failed, OLD.key_decisions, OLD.files_modified);
END;

CREATE TRIGGER IF NOT EXISTS handoffs_au AFTER UPDATE ON handoffs BEGIN
    INSERT INTO handoffs_fts(handoffs_fts, rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES('delete', OLD.rowid, OLD.task_summary, OLD.what_worked, OLD.what_failed, OLD.key_decisions, OLD.files_modified);
    INSERT INTO handoffs_fts(rowid, task_summary, what_worked, what_failed, key_decisions, files_modified)
    VALUES (NEW.rowid, NEW.task_summary, NEW.what_worked, NEW.what_failed, NEW.key_decisions, NEW.files_modified);
END;

-- PLANS triggers
CREATE TRIGGER IF NOT EXISTS plans_ai AFTER INSERT ON plans BEGIN
    INSERT INTO plans_fts(rowid, title, overview, approach, phases, constraints)
    VALUES (NEW.rowid, NEW.title, NEW.overview, NEW.approach, NEW.phases, NEW.constraints);
END;

CREATE TRIGGER IF NOT EXISTS plans_ad AFTER DELETE ON plans BEGIN
    INSERT INTO plans_fts(plans_fts, rowid, title, overview, approach, phases, constraints)
    VALUES('delete', OLD.rowid, OLD.title, OLD.overview, OLD.approach, OLD.phases, OLD.constraints);
END;

CREATE TRIGGER IF NOT EXISTS plans_au AFTER UPDATE ON plans BEGIN
    INSERT INTO plans_fts(plans_fts, rowid, title, overview, approach, phases, constraints)
    VALUES('delete', OLD.rowid, OLD.title, OLD.overview, OLD.approach, OLD.phases, OLD.constraints);
    INSERT INTO plans_fts(rowid, title, overview, approach, phases, constraints)
    VALUES (NEW.rowid, NEW.title, NEW.overview, NEW.approach, NEW.phases, NEW.constraints);
END;

-- CONTINUITY triggers
CREATE TRIGGER IF NOT EXISTS continuity_ai AFTER INSERT ON continuity BEGIN
    INSERT INTO continuity_fts(rowid, goal, key_learnings, key_decisions, state_now)
    VALUES (NEW.rowid, NEW.goal, NEW.key_learnings, NEW.key_decisions, NEW.state_now);
END;

CREATE TRIGGER IF NOT EXISTS continuity_ad AFTER DELETE ON continuity BEGIN
    INSERT INTO continuity_fts(continuity_fts, rowid, goal, key_learnings, key_decisions, state_now)
    VALUES('delete', OLD.rowid, OLD.goal, OLD.key_learnings, OLD.key_decisions, OLD.state_now);
END;

CREATE TRIGGER IF NOT EXISTS continuity_au AFTER UPDATE ON continuity BEGIN
    INSERT INTO continuity_fts(continuity_fts, rowid, goal, key_learnings, key_decisions, state_now)
    VALUES('delete', OLD.rowid, OLD.goal, OLD.key_learnings, OLD.key_decisions, OLD.state_now);
    INSERT INTO continuity_fts(rowid, goal, key_learnings, key_decisions, state_now)
    VALUES (NEW.rowid, NEW.goal, NEW.key_learnings, NEW.key_decisions, NEW.state_now);
END;

-- QUERIES triggers
CREATE TRIGGER IF NOT EXISTS queries_ai AFTER INSERT ON queries BEGIN
    INSERT INTO queries_fts(rowid, question, answer)
    VALUES (NEW.rowid, NEW.question, NEW.answer);
END;

CREATE TRIGGER IF NOT EXISTS queries_ad AFTER DELETE ON queries BEGIN
    INSERT INTO queries_fts(queries_fts, rowid, question, answer)
    VALUES('delete', OLD.rowid, OLD.question, OLD.answer);
END;

CREATE TRIGGER IF NOT EXISTS queries_au AFTER UPDATE ON queries BEGIN
    INSERT INTO queries_fts(queries_fts, rowid, question, answer)
    VALUES('delete', OLD.rowid, OLD.question, OLD.answer);
    INSERT INTO queries_fts(rowid, question, answer)
    VALUES (NEW.rowid, NEW.question, NEW.answer);
END;

-- LEARNINGS triggers
CREATE TRIGGER IF NOT EXISTS learnings_ai AFTER INSERT ON learnings BEGIN
    INSERT INTO learnings_fts(rowid, description, context, recommendation)
    VALUES (NEW.rowid, NEW.description, NEW.context, NEW.recommendation);
END;

CREATE TRIGGER IF NOT EXISTS learnings_ad AFTER DELETE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, description, context, recommendation)
    VALUES('delete', OLD.rowid, OLD.description, OLD.context, OLD.recommendation);
END;

CREATE TRIGGER IF NOT EXISTS learnings_au AFTER UPDATE ON learnings BEGIN
    INSERT INTO learnings_fts(learnings_fts, rowid, description, context, recommendation)
    VALUES('delete', OLD.rowid, OLD.description, OLD.context, OLD.recommendation);
    INSERT INTO learnings_fts(rowid, description, context, recommendation)
    VALUES (NEW.rowid, NEW.description, NEW.context, NEW.recommendation);
END;

-- ============================================================================
-- INDEXES (Performance optimization)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_handoffs_session ON handoffs(session_name);
CREATE INDEX IF NOT EXISTS idx_handoffs_outcome ON handoffs(outcome);
CREATE INDEX IF NOT EXISTS idx_handoffs_created ON handoffs(created_at);

CREATE INDEX IF NOT EXISTS idx_plans_session ON plans(session_name);
CREATE INDEX IF NOT EXISTS idx_plans_created ON plans(created_at);

CREATE INDEX IF NOT EXISTS idx_continuity_session ON continuity(session_name);
CREATE INDEX IF NOT EXISTS idx_continuity_reason ON continuity(snapshot_reason);

CREATE INDEX IF NOT EXISTS idx_learnings_type ON learnings(pattern_type);
CREATE INDEX IF NOT EXISTS idx_learnings_promoted ON learnings(promoted_to);

-- ============================================================================
-- VIEWS (Convenience queries)
-- ============================================================================

-- Recent handoffs with outcomes
CREATE VIEW IF NOT EXISTS recent_handoffs AS
SELECT
    id,
    session_name,
    task_summary,
    outcome,
    created_at
FROM handoffs
ORDER BY created_at DESC
LIMIT 100;

-- Success patterns (for compound learning)
CREATE VIEW IF NOT EXISTS success_patterns AS
SELECT
    h.task_summary,
    h.what_worked,
    h.key_decisions,
    COUNT(*) as occurrence_count
FROM handoffs h
WHERE h.outcome IN ('SUCCEEDED', 'PARTIAL_PLUS')
GROUP BY h.what_worked
HAVING COUNT(*) >= 2
ORDER BY occurrence_count DESC;

-- Failure patterns (for compound learning)
CREATE VIEW IF NOT EXISTS failure_patterns AS
SELECT
    h.task_summary,
    h.what_failed,
    h.outcome_notes,
    COUNT(*) as occurrence_count
FROM handoffs h
WHERE h.outcome IN ('FAILED', 'PARTIAL_MINUS')
GROUP BY h.what_failed
HAVING COUNT(*) >= 2
ORDER BY occurrence_count DESC;

-- Unpromoted learnings ready for review
CREATE VIEW IF NOT EXISTS pending_learnings AS
SELECT *
FROM learnings
WHERE promoted_to IS NULL
  AND occurrence_count >= 3
ORDER BY occurrence_count DESC, created_at DESC;

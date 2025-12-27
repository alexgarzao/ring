# Artifact Index Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create a SQLite-based artifact indexing and search system that enables semantic search across handoffs, plans, and continuity ledgers with query response time < 100ms.

**Architecture:** Python scripts with argparse CLI for indexing markdown files into SQLite with FTS5 full-text search. Single-file indexing mode for hooks, batch mode for initial indexing. BM25 ranking for relevance scoring.

**Tech Stack:**
- Python 3.8+ (standard library only - sqlite3, argparse, hashlib, json, re, pathlib)
- SQLite3 with FTS5 extension (built into Python 3.8+)
- No external dependencies (uv/pip not required)

**Global Prerequisites:**
- Environment: macOS/Linux, Python 3.8+
- Tools: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree
- Dependencies: Shared infrastructure schema MUST exist (Phase 0)

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version    # Expected: Python 3.8+
sqlite3 --version    # Expected: 3.x (with FTS5 support)
git status           # Expected: clean working tree
ls -la docs/plans/   # Expected: directory exists
```

---

## Phase 0: Directory Structure (Prerequisites)

### Task 1: Create lib directory structure

**Files:**
- Create: `default/lib/artifact-index/` (directory)
- Create: `default/lib/artifact-index/__init__.py`

**Prerequisites:**
- `default/` directory must exist
- Write access to the repository

**Step 1: Create directory structure**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index
```

**Expected output:**
(no output, silent success)

**Step 2: Create __init__.py for Python package**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/__init__.py`:

```python
"""Artifact Index - SQLite-based indexing and search for Ring artifacts.

This package provides:
- artifact_index.py: Index markdown files into SQLite with FTS5
- artifact_query.py: Search artifacts with BM25 ranking
- artifact_mark.py: Mark handoff outcomes
"""

__version__ = "1.0.0"
```

**Step 3: Verify structure**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/
```

**Expected output:**
```
total 8
drwxr-xr-x  3 user  staff   96 Dec 27 xx:xx .
drwxr-xr-x  3 user  staff   96 Dec 27 xx:xx ..
-rw-r--r--  1 user  staff  xxx Dec 27 xx:xx __init__.py
```

**Step 4: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/lib/artifact-index/__init__.py && git commit -m "chore(artifact-index): create lib directory structure"
```

**If Task Fails:**

1. **Directory already exists:**
   - Check: `ls -la default/lib/artifact-index/`
   - If exists with content: Skip to next task
   - If empty: Continue with Step 2

2. **Permission denied:**
   - Check: `ls -la default/`
   - Fix: Ensure you have write access

---

## Phase 1: Database Schema

### Task 2: Create artifact schema SQL

**Files:**
- Create: `default/lib/artifact-index/artifact_schema.sql`

**Prerequisites:**
- Task 1 completed (directory exists)

**Step 1: Write the schema file**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_schema.sql`:

```sql
-- Artifact Index Schema
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

-- Enable WAL mode for better concurrent read performance
PRAGMA journal_mode=WAL;

-- Handoffs (completed tasks with post-mortems)
CREATE TABLE IF NOT EXISTS handoffs (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,
    task_number INTEGER,
    file_path TEXT NOT NULL UNIQUE,

    -- Core content
    task_summary TEXT,
    what_worked TEXT,
    what_failed TEXT,
    key_decisions TEXT,
    files_modified TEXT,  -- JSON array

    -- Outcome (from user annotation)
    outcome TEXT CHECK(outcome IN ('SUCCEEDED', 'PARTIAL_PLUS', 'PARTIAL_MINUS', 'FAILED', 'UNKNOWN')) DEFAULT 'UNKNOWN',
    outcome_notes TEXT,
    confidence TEXT CHECK(confidence IN ('HIGH', 'INFERRED')) DEFAULT 'INFERRED',

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plans (design documents)
CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    session_name TEXT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,

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
    file_path TEXT UNIQUE,

    -- State
    goal TEXT,
    state_done TEXT,  -- JSON array
    state_now TEXT,
    state_next TEXT,
    key_learnings TEXT,
    key_decisions TEXT,

    -- Context
    snapshot_reason TEXT CHECK(snapshot_reason IN ('phase_complete', 'session_end', 'milestone', 'manual', 'auto')),

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
    plans_matched TEXT,     -- JSON array of IDs
    continuity_matched TEXT, -- JSON array of IDs

    -- Feedback
    was_helpful BOOLEAN,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_handoffs_session ON handoffs(session_name);
CREATE INDEX IF NOT EXISTS idx_handoffs_outcome ON handoffs(outcome);
CREATE INDEX IF NOT EXISTS idx_handoffs_created ON handoffs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_plans_title ON plans(title);
CREATE INDEX IF NOT EXISTS idx_plans_created ON plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_continuity_session ON continuity(session_name);

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

-- Triggers to keep FTS5 in sync (INSERT, UPDATE, DELETE)

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
```

**Step 2: Verify file was created**

Run:
```bash
head -20 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_schema.sql
```

**Expected output:**
```
-- Artifact Index Schema
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

-- Enable WAL mode for better concurrent read performance
PRAGMA journal_mode=WAL;

-- Handoffs (completed tasks with post-mortems)
CREATE TABLE IF NOT EXISTS handoffs (
    id TEXT PRIMARY KEY,
    session_name TEXT NOT NULL,
```

**Step 3: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/lib/artifact-index/artifact_schema.sql && git commit -m "feat(artifact-index): add SQLite schema with FTS5 full-text search"
```

**If Task Fails:**

1. **File creation failed:**
   - Check: `ls -la default/lib/artifact-index/`
   - Fix: Ensure directory exists from Task 1

---

## Phase 2: Indexing Script

### Task 3: Create artifact_index.py

**Files:**
- Create: `default/lib/artifact-index/artifact_index.py`

**Prerequisites:**
- Task 2 completed (schema exists)

**Step 1: Write the indexing script**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_index.py`:

```python
#!/usr/bin/env python3
"""
USAGE: artifact_index.py [--handoffs] [--plans] [--continuity] [--all] [--file PATH] [--db PATH] [--project PATH]

Index handoffs, plans, and continuity ledgers into the Artifact Index database.

Examples:
    # Index all handoffs in current project
    python3 artifact_index.py --handoffs

    # Index everything
    python3 artifact_index.py --all

    # Index a single handoff file (fast, for hooks)
    python3 artifact_index.py --file docs/handoffs/session/task-01.md

    # Use custom database path
    python3 artifact_index.py --all --db /path/to/context.db

    # Index from specific project root
    python3 artifact_index.py --all --project /path/to/project
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


def get_project_root(custom_path: Optional[str] = None) -> Path:
    """Get project root, defaulting to current directory or custom path."""
    if custom_path:
        return Path(custom_path).resolve()

    # Try to find project root by looking for .ring or .git
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".ring").exists() or (parent / ".git").exists():
            return parent
    return current


def get_db_path(custom_path: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """Get database path, creating directory if needed."""
    if custom_path:
        path = Path(custom_path)
    else:
        root = project_root or get_project_root()
        path = root / ".ring" / "cache" / "artifact-index" / "context.db"

    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_schema_path() -> Path:
    """Get path to schema file relative to this script."""
    return Path(__file__).parent / "artifact_schema.sql"


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize database with schema."""
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")

    schema_path = get_schema_path()
    if schema_path.exists():
        conn.executescript(schema_path.read_text())
    else:
        print(f"Warning: Schema file not found at {schema_path}", file=sys.stderr)

    return conn


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from markdown content."""
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip().strip('"').strip("'")
    return frontmatter


def parse_sections(content: str) -> Dict[str, str]:
    """Extract h2 and h3 sections from markdown content."""
    sections = {}
    current_section = None
    current_content: List[str] = []

    # Skip frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2]

    for line in content.split("\n"):
        # h2 sections
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip().lower().replace(" ", "_").replace("-", "_")
            current_content = []
        # h3 sections (nested)
        elif line.startswith("### "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[4:].strip().lower().replace(" ", "_").replace("-", "_")
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_files_from_content(content: str) -> List[str]:
    """Extract file paths from markdown content."""
    files: List[str] = []
    for line in content.split("\n"):
        # Match common patterns like "- `path/to/file.py`" or "- `path/to/file.py:123`"
        matches = re.findall(r"`([^`]+\.[a-z]+)(:[^`]*)?`", line)
        files.extend([m[0] for m in matches])
        # Match **File**: format
        matches = re.findall(r"\*\*File\*\*:\s*`?([^\s`]+)`?", line)
        files.extend(matches)
    return list(set(files))  # Deduplicate


def parse_handoff(file_path: Path) -> Dict[str, Any]:
    """Parse a handoff markdown file into structured data."""
    content = file_path.read_text()
    frontmatter = parse_frontmatter(content)
    sections = parse_sections(content)

    # Generate ID from file path
    file_id = hashlib.md5(str(file_path.resolve()).encode()).hexdigest()[:12]

    # Extract session name from path (docs/handoffs/<session>/task-XX.md)
    parts = file_path.parts
    session_name = ""
    if "handoffs" in parts:
        idx = parts.index("handoffs")
        if idx + 1 < len(parts) and parts[idx + 1] != file_path.name:
            session_name = parts[idx + 1]

    # Extract task number
    task_match = re.search(r"task-(\d+)", file_path.stem)
    task_number = int(task_match.group(1)) if task_match else None

    # Map status values to canonical outcome values
    status = frontmatter.get("status", frontmatter.get("outcome", "UNKNOWN")).upper()
    outcome_map = {
        "SUCCESS": "SUCCEEDED",
        "SUCCEEDED": "SUCCEEDED",
        "PARTIAL": "PARTIAL_PLUS",
        "PARTIAL_PLUS": "PARTIAL_PLUS",
        "PARTIAL_MINUS": "PARTIAL_MINUS",
        "FAILED": "FAILED",
        "FAILURE": "FAILED",
        "UNKNOWN": "UNKNOWN",
    }
    outcome = outcome_map.get(status, "UNKNOWN")

    # Extract content from various section names
    task_summary = (
        sections.get("what_was_done") or
        sections.get("summary") or
        sections.get("task_summary") or
        ""
    )[:500]

    what_worked = (
        sections.get("what_worked") or
        sections.get("successes") or
        ""
    )

    what_failed = (
        sections.get("what_failed") or
        sections.get("failures") or
        sections.get("issues") or
        ""
    )

    key_decisions = (
        sections.get("key_decisions") or
        sections.get("decisions") or
        ""
    )

    files_modified_section = (
        sections.get("files_modified") or
        sections.get("files_changed") or
        sections.get("files") or
        ""
    )

    return {
        "id": file_id,
        "session_name": session_name or frontmatter.get("session", "default"),
        "task_number": task_number,
        "file_path": str(file_path.resolve()),
        "task_summary": task_summary,
        "what_worked": what_worked,
        "what_failed": what_failed,
        "key_decisions": key_decisions,
        "files_modified": json.dumps(extract_files_from_content(files_modified_section)),
        "outcome": outcome,
        "created_at": frontmatter.get("date", frontmatter.get("created", datetime.now().isoformat())),
    }


def parse_plan(file_path: Path) -> Dict[str, Any]:
    """Parse a plan markdown file into structured data."""
    content = file_path.read_text()
    frontmatter = parse_frontmatter(content)
    sections = parse_sections(content)

    # Generate ID from file path
    file_id = hashlib.md5(str(file_path.resolve()).encode()).hexdigest()[:12]

    # Extract title from first H1
    title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else file_path.stem

    # Extract session from path or frontmatter
    session_name = frontmatter.get("session", "")

    # Extract phases
    phases: List[Dict[str, str]] = []
    for key, value in sections.items():
        if key.startswith("phase") or key.startswith("task"):
            phases.append({"name": key, "content": value[:500]})

    return {
        "id": file_id,
        "session_name": session_name,
        "title": title,
        "file_path": str(file_path.resolve()),
        "overview": (sections.get("overview") or sections.get("goal") or "")[:1000],
        "approach": (sections.get("implementation_approach") or sections.get("approach") or sections.get("architecture") or "")[:1000],
        "phases": json.dumps(phases),
        "constraints": sections.get("constraints") or sections.get("what_we're_not_doing") or "",
        "created_at": frontmatter.get("date", frontmatter.get("created", datetime.now().isoformat())),
    }


def parse_continuity(file_path: Path) -> Dict[str, Any]:
    """Parse a continuity ledger into structured data."""
    content = file_path.read_text()
    frontmatter = parse_frontmatter(content)
    sections = parse_sections(content)

    # Generate ID from file path
    file_id = hashlib.md5(str(file_path.resolve()).encode()).hexdigest()[:12]

    # Extract session name from filename (CONTINUITY-<session>.md or CONTINUITY_CLAUDE-<session>.md)
    session_match = re.search(r"CONTINUITY[-_](?:CLAUDE-)?(.+)\.md", file_path.name, re.IGNORECASE)
    session_name = session_match.group(1) if session_match else file_path.stem

    # Parse state section
    state = sections.get("state", "")
    state_done: List[str] = []
    state_now = ""
    state_next = ""

    for line in state.split("\n"):
        line_lower = line.lower()
        if "[x]" in line_lower:
            state_done.append(line.strip())
        elif "[->]" in line or "now:" in line_lower or "current:" in line_lower:
            state_now = line.strip()
        elif "[ ]" in line or "next:" in line_lower:
            state_next = line.strip()

    return {
        "id": file_id,
        "session_name": session_name,
        "file_path": str(file_path.resolve()),
        "goal": (sections.get("goal") or "")[:500],
        "state_done": json.dumps(state_done),
        "state_now": state_now,
        "state_next": state_next,
        "key_learnings": sections.get("key_learnings") or sections.get("key_learnings_(this_session)") or "",
        "key_decisions": sections.get("key_decisions") or "",
        "snapshot_reason": frontmatter.get("reason", "manual"),
    }


def index_handoffs(conn: sqlite3.Connection, project_root: Path) -> int:
    """Index all handoffs into the database."""
    # Check multiple possible handoff locations
    handoff_paths = [
        project_root / "docs" / "handoffs",
        project_root / ".ring" / "handoffs",
    ]

    count = 0
    for base_path in handoff_paths:
        if not base_path.exists():
            continue

        for handoff_file in base_path.rglob("*.md"):
            try:
                data = parse_handoff(handoff_file)
                conn.execute("""
                    INSERT OR REPLACE INTO handoffs
                    (id, session_name, task_number, file_path, task_summary, what_worked,
                     what_failed, key_decisions, files_modified, outcome, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["id"], data["session_name"], data["task_number"], data["file_path"],
                    data["task_summary"], data["what_worked"], data["what_failed"],
                    data["key_decisions"], data["files_modified"], data["outcome"],
                    data["created_at"]
                ))
                count += 1
            except Exception as e:
                print(f"Error indexing {handoff_file}: {e}", file=sys.stderr)

    conn.commit()
    if count > 0:
        print(f"Indexed {count} handoffs")
    return count


def index_plans(conn: sqlite3.Connection, project_root: Path) -> int:
    """Index all plans into the database."""
    plans_path = project_root / "docs" / "plans"

    if not plans_path.exists():
        return 0

    count = 0
    for plan_file in plans_path.glob("*.md"):
        try:
            data = parse_plan(plan_file)
            conn.execute("""
                INSERT OR REPLACE INTO plans
                (id, session_name, title, file_path, overview, approach, phases, constraints, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["session_name"], data["title"], data["file_path"],
                data["overview"], data["approach"], data["phases"], data["constraints"],
                data["created_at"]
            ))
            count += 1
        except Exception as e:
            print(f"Error indexing {plan_file}: {e}", file=sys.stderr)

    conn.commit()
    if count > 0:
        print(f"Indexed {count} plans")
    return count


def index_continuity(conn: sqlite3.Connection, project_root: Path) -> int:
    """Index all continuity ledgers into the database."""
    # Check multiple locations
    ledger_paths = [
        project_root / ".ring" / "ledgers",
        project_root,  # Root level CONTINUITY-*.md
    ]

    count = 0
    for base_path in ledger_paths:
        if not base_path.exists():
            continue

        pattern = "CONTINUITY*.md" if base_path == project_root else "*.md"
        for ledger_file in base_path.glob(pattern):
            if not ledger_file.name.upper().startswith("CONTINUITY"):
                continue
            try:
                data = parse_continuity(ledger_file)
                conn.execute("""
                    INSERT OR REPLACE INTO continuity
                    (id, session_name, file_path, goal, state_done, state_now, state_next,
                     key_learnings, key_decisions, snapshot_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["id"], data["session_name"], data["file_path"], data["goal"],
                    data["state_done"], data["state_now"], data["state_next"],
                    data["key_learnings"], data["key_decisions"], data["snapshot_reason"]
                ))
                count += 1
            except Exception as e:
                print(f"Error indexing {ledger_file}: {e}", file=sys.stderr)

    conn.commit()
    if count > 0:
        print(f"Indexed {count} continuity ledgers")
    return count


def index_single_file(conn: sqlite3.Connection, file_path: Path) -> bool:
    """Index a single file based on its location/type.

    Returns True if indexed successfully, False otherwise.
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        print(f"File not found: {file_path}", file=sys.stderr)
        return False

    if file_path.suffix != ".md":
        print(f"Not a markdown file: {file_path}", file=sys.stderr)
        return False

    path_str = str(file_path).lower()

    # Determine type by path
    if "handoff" in path_str:
        try:
            data = parse_handoff(file_path)
            conn.execute("""
                INSERT OR REPLACE INTO handoffs
                (id, session_name, task_number, file_path, task_summary, what_worked,
                 what_failed, key_decisions, files_modified, outcome, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["session_name"], data["task_number"], data["file_path"],
                data["task_summary"], data["what_worked"], data["what_failed"],
                data["key_decisions"], data["files_modified"], data["outcome"],
                data["created_at"]
            ))
            conn.commit()
            print(f"Indexed handoff: {file_path.name}")
            return True
        except Exception as e:
            print(f"Error indexing handoff {file_path}: {e}", file=sys.stderr)
            return False

    elif "plan" in path_str:
        try:
            data = parse_plan(file_path)
            conn.execute("""
                INSERT OR REPLACE INTO plans
                (id, session_name, title, file_path, overview, approach, phases, constraints, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["session_name"], data["title"], data["file_path"],
                data["overview"], data["approach"], data["phases"], data["constraints"],
                data["created_at"]
            ))
            conn.commit()
            print(f"Indexed plan: {file_path.name}")
            return True
        except Exception as e:
            print(f"Error indexing plan {file_path}: {e}", file=sys.stderr)
            return False

    elif "continuity" in path_str.lower() or file_path.name.upper().startswith("CONTINUITY"):
        try:
            data = parse_continuity(file_path)
            conn.execute("""
                INSERT OR REPLACE INTO continuity
                (id, session_name, file_path, goal, state_done, state_now, state_next,
                 key_learnings, key_decisions, snapshot_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["session_name"], data["file_path"], data["goal"],
                data["state_done"], data["state_now"], data["state_next"],
                data["key_learnings"], data["key_decisions"], data["snapshot_reason"]
            ))
            conn.commit()
            print(f"Indexed continuity: {file_path.name}")
            return True
        except Exception as e:
            print(f"Error indexing continuity {file_path}: {e}", file=sys.stderr)
            return False

    else:
        print(f"Unknown file type (not in handoffs/, plans/, or continuity path): {file_path}", file=sys.stderr)
        return False


def rebuild_fts_indexes(conn: sqlite3.Connection) -> None:
    """Rebuild FTS5 indexes and optimize for query performance."""
    print("Rebuilding FTS5 indexes...")

    try:
        conn.execute("INSERT INTO handoffs_fts(handoffs_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO plans_fts(plans_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO continuity_fts(continuity_fts) VALUES('rebuild')")
        conn.execute("INSERT INTO queries_fts(queries_fts) VALUES('rebuild')")

        # Configure BM25 column weights
        conn.execute("INSERT OR REPLACE INTO handoffs_fts(handoffs_fts, rank) VALUES('rank', 'bm25(10.0, 5.0, 3.0, 3.0, 1.0)')")
        conn.execute("INSERT OR REPLACE INTO plans_fts(plans_fts, rank) VALUES('rank', 'bm25(10.0, 5.0, 3.0, 3.0, 1.0)')")

        print("Optimizing indexes...")
        conn.execute("INSERT INTO handoffs_fts(handoffs_fts) VALUES('optimize')")
        conn.execute("INSERT INTO plans_fts(plans_fts) VALUES('optimize')")
        conn.execute("INSERT INTO continuity_fts(continuity_fts) VALUES('optimize')")
        conn.execute("INSERT INTO queries_fts(queries_fts) VALUES('optimize')")

        conn.commit()
    except sqlite3.OperationalError as e:
        # FTS tables may not exist yet if no data
        print(f"Note: FTS optimization skipped ({e})", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Index Ring artifacts into SQLite for semantic search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--handoffs", action="store_true", help="Index handoffs")
    parser.add_argument("--plans", action="store_true", help="Index plans")
    parser.add_argument("--continuity", action="store_true", help="Index continuity ledgers")
    parser.add_argument("--all", action="store_true", help="Index everything")
    parser.add_argument("--file", type=str, metavar="PATH", help="Index a single file (fast, for hooks)")
    parser.add_argument("--db", type=str, metavar="PATH", help="Custom database path")
    parser.add_argument("--project", type=str, metavar="PATH", help="Project root path (default: auto-detect)")

    args = parser.parse_args()

    project_root = get_project_root(args.project)

    # Handle single file indexing (fast path for hooks)
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = project_root / file_path

        if not file_path.exists():
            print(f"File not found: {file_path}", file=sys.stderr)
            return 1

        db_path = get_db_path(args.db, project_root)
        conn = init_db(db_path)
        success = index_single_file(conn, file_path)
        conn.close()
        return 0 if success else 1

    if not any([args.handoffs, args.plans, args.continuity, args.all]):
        parser.print_help()
        return 0

    db_path = get_db_path(args.db, project_root)
    conn = init_db(db_path)

    print(f"Using database: {db_path}")
    print(f"Project root: {project_root}")

    total = 0

    if args.all or args.handoffs:
        total += index_handoffs(conn, project_root)

    if args.all or args.plans:
        total += index_plans(conn, project_root)

    if args.all or args.continuity:
        total += index_continuity(conn, project_root)

    if total > 0:
        rebuild_fts_indexes(conn)

    conn.close()
    print(f"Done! Indexed {total} total artifacts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_index.py
```

**Expected output:**
(no output, silent success)

**Step 3: Test script help**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_index.py --help
```

**Expected output:**
```
usage: artifact_index.py [-h] [--handoffs] [--plans] [--continuity] [--all]
                         [--file PATH] [--db PATH] [--project PATH]

Index Ring artifacts into SQLite for semantic search

options:
  -h, --help       show this help message and exit
  --handoffs       Index handoffs
  --plans          Index plans
  --continuity     Index continuity ledgers
  --all            Index everything
  --file PATH      Index a single file (fast, for hooks)
  --db PATH        Custom database path
  --project PATH   Project root path (default: auto-detect)
```

**Step 4: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/lib/artifact-index/artifact_index.py && git commit -m "feat(artifact-index): add indexing script with single-file and batch modes"
```

**If Task Fails:**

1. **Python syntax error:**
   - Run: `python3 -m py_compile default/lib/artifact-index/artifact_index.py`
   - Fix any syntax errors reported

2. **Import error:**
   - All imports are from Python standard library
   - Verify: `python3 --version` is 3.8+

---

### Task 4: Test indexing with existing plans

**Files:**
- Uses: `default/lib/artifact-index/artifact_index.py`
- Creates: `.ring/cache/artifact-index/context.db`

**Prerequisites:**
- Task 3 completed (artifact_index.py exists)

**Step 1: Run indexer on existing plans**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && python3 default/lib/artifact-index/artifact_index.py --plans
```

**Expected output:**
```
Using database: /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db
Project root: /Users/fredamaral/repos/lerianstudio/ring
Indexed 2 plans
Rebuilding FTS5 indexes...
Optimizing indexes...
Done! Indexed 2 total artifacts.
```

**Step 2: Verify database was created**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/
```

**Expected output:**
```
total XX
drwxr-xr-x  X user  staff  XXX Dec 27 xx:xx .
drwxr-xr-x  X user  staff  XXX Dec 27 xx:xx ..
-rw-r--r--  1 user  staff  XXX Dec 27 xx:xx context.db
-rw-r--r--  1 user  staff  XXX Dec 27 xx:xx context.db-shm
-rw-r--r--  1 user  staff  XXX Dec 27 xx:xx context.db-wal
```

**Step 3: Verify data was indexed**

Run:
```bash
sqlite3 /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db "SELECT id, title FROM plans LIMIT 5"
```

**Expected output:**
```
<hash1>|Context Management System - Macro Architecture Plan
<hash2>|...
```

**Step 4: Add .ring to .gitignore if not present**

Check if .ring is in .gitignore:
```bash
grep -q "^\.ring" /Users/fredamaral/repos/lerianstudio/ring/.gitignore || echo ".ring/" >> /Users/fredamaral/repos/lerianstudio/ring/.gitignore
```

**If Task Fails:**

1. **No plans found:**
   - Check: `ls docs/plans/*.md`
   - If no plans: Create a test plan or skip to next task

2. **Permission denied:**
   - Check: Directory permissions on `.ring/`
   - Fix: `mkdir -p .ring/cache/artifact-index`

---

## Phase 3: Query Script

### Task 5: Create artifact_query.py

**Files:**
- Create: `default/lib/artifact-index/artifact_query.py`

**Prerequisites:**
- Task 3 completed (indexing script exists)
- Task 4 completed (database exists with data)

**Step 1: Write the query script**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py`:

```python
#!/usr/bin/env python3
"""
USAGE: artifact_query.py <query> [--type TYPE] [--outcome OUTCOME] [--limit N] [--db PATH] [--json]

Search the Artifact Index for relevant precedent using FTS5 full-text search.

Examples:
    # Search for authentication-related work
    python3 artifact_query.py "authentication OAuth JWT"

    # Search only successful handoffs
    python3 artifact_query.py "implement agent" --outcome SUCCEEDED

    # Search plans only
    python3 artifact_query.py "API design" --type plans

    # Output as JSON for programmatic use
    python3 artifact_query.py "context management" --json

    # Limit results
    python3 artifact_query.py "testing" --limit 3
"""

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_project_root() -> Path:
    """Get project root by looking for .ring or .git."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".ring").exists() or (parent / ".git").exists():
            return parent
    return current


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Get database path."""
    if custom_path:
        return Path(custom_path)
    return get_project_root() / ".ring" / "cache" / "artifact-index" / "context.db"


def escape_fts5_query(query: str) -> str:
    """Escape FTS5 query to prevent syntax errors.

    Splits query into words and joins with OR for flexible matching.
    Each word is quoted to handle special characters.
    """
    words = query.split()
    # Quote each word, escaping internal quotes
    quoted_words = [f'"{w.replace(chr(34), chr(34)+chr(34))}"' for w in words if w]
    # Join with OR for flexible matching
    return " OR ".join(quoted_words) if quoted_words else '""'


def search_handoffs(
    conn: sqlite3.Connection,
    query: str,
    outcome: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """Search handoffs using FTS5 with BM25 ranking."""
    sql = """
        SELECT h.id, h.session_name, h.task_number, h.task_summary,
               h.what_worked, h.what_failed, h.key_decisions,
               h.outcome, h.file_path, h.created_at,
               handoffs_fts.rank as score
        FROM handoffs_fts
        JOIN handoffs h ON handoffs_fts.rowid = h.rowid
        WHERE handoffs_fts MATCH ?
    """
    params: List[Any] = [escape_fts5_query(query)]

    if outcome:
        sql += " AND h.outcome = ?"
        params.append(outcome)

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    try:
        cursor = conn.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # FTS table may be empty
        return []


def search_plans(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """Search plans using FTS5 with BM25 ranking."""
    sql = """
        SELECT p.id, p.title, p.overview, p.approach, p.file_path, p.created_at,
               plans_fts.rank as score
        FROM plans_fts
        JOIN plans p ON plans_fts.rowid = p.rowid
        WHERE plans_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    try:
        cursor = conn.execute(sql, [escape_fts5_query(query), limit])
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def search_continuity(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 3
) -> List[Dict[str, Any]]:
    """Search continuity ledgers using FTS5 with BM25 ranking."""
    sql = """
        SELECT c.id, c.session_name, c.goal, c.key_learnings, c.key_decisions,
               c.state_now, c.created_at, c.file_path,
               continuity_fts.rank as score
        FROM continuity_fts
        JOIN continuity c ON continuity_fts.rowid = c.rowid
        WHERE continuity_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    try:
        cursor = conn.execute(sql, [escape_fts5_query(query), limit])
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def search_past_queries(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 2
) -> List[Dict[str, Any]]:
    """Check if similar questions have been asked before (compound learning)."""
    sql = """
        SELECT q.id, q.question, q.answer, q.was_helpful, q.created_at,
               queries_fts.rank as score
        FROM queries_fts
        JOIN queries q ON queries_fts.rowid = q.rowid
        WHERE queries_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """
    try:
        cursor = conn.execute(sql, [escape_fts5_query(query), limit])
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_handoff_by_id(conn: sqlite3.Connection, handoff_id: str) -> Optional[Dict[str, Any]]:
    """Get a handoff by its ID."""
    sql = """
        SELECT id, session_name, task_number, task_summary,
               what_worked, what_failed, key_decisions,
               outcome, file_path, created_at
        FROM handoffs
        WHERE id = ?
        LIMIT 1
    """
    cursor = conn.execute(sql, [handoff_id])
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    if row:
        return dict(zip(columns, row))
    return None


def save_query(conn: sqlite3.Connection, question: str, answer: str, matches: Dict[str, List]) -> None:
    """Save query for compound learning."""
    query_id = hashlib.md5(f"{question}{datetime.now().isoformat()}".encode()).hexdigest()[:12]

    conn.execute("""
        INSERT INTO queries (id, question, answer, handoffs_matched, plans_matched, continuity_matched)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        query_id,
        question,
        answer,
        json.dumps([h["id"] for h in matches.get("handoffs", [])]),
        json.dumps([p["id"] for p in matches.get("plans", [])]),
        json.dumps([c["id"] for c in matches.get("continuity", [])]),
    ))
    conn.commit()


def format_results(results: Dict[str, List], verbose: bool = False) -> str:
    """Format search results for human-readable display."""
    output: List[str] = []

    # Past queries (compound learning)
    if results.get("past_queries"):
        output.append("## Previously Asked")
        for q in results["past_queries"]:
            question = q.get('question', '')[:100]
            answer = q.get('answer', '')[:200]
            output.append(f"- **Q:** {question}...")
            output.append(f"  **A:** {answer}...")
        output.append("")

    # Handoffs
    if results.get("handoffs"):
        output.append("## Relevant Handoffs")
        for h in results["handoffs"]:
            status_icon = {
                "SUCCEEDED": "[OK]",
                "PARTIAL_PLUS": "[~+]",
                "PARTIAL_MINUS": "[~-]",
                "FAILED": "[X]",
                "UNKNOWN": "[?]"
            }.get(h.get("outcome", "UNKNOWN"), "[?]")
            session = h.get('session_name', 'unknown')
            task = h.get('task_number', '?')
            output.append(f"### {status_icon} {session}/task-{task}")
            summary = h.get('task_summary', '')[:200]
            if summary:
                output.append(f"**Summary:** {summary}")
            what_worked = h.get("what_worked", "")
            if what_worked:
                output.append(f"**What worked:** {what_worked[:200]}")
            what_failed = h.get("what_failed", "")
            if what_failed:
                output.append(f"**What failed:** {what_failed[:200]}")
            output.append(f"**File:** `{h.get('file_path', '')}`")
            output.append("")

    # Plans
    if results.get("plans"):
        output.append("## Relevant Plans")
        for p in results["plans"]:
            title = p.get('title', 'Untitled')
            output.append(f"### {title}")
            overview = p.get('overview', '')[:200]
            if overview:
                output.append(f"**Overview:** {overview}")
            output.append(f"**File:** `{p.get('file_path', '')}`")
            output.append("")

    # Continuity
    if results.get("continuity"):
        output.append("## Related Sessions")
        for c in results["continuity"]:
            session = c.get('session_name', 'unknown')
            output.append(f"### Session: {session}")
            goal = c.get('goal', '')[:200]
            if goal:
                output.append(f"**Goal:** {goal}")
            key_learnings = c.get("key_learnings", "")
            if key_learnings:
                output.append(f"**Key learnings:** {key_learnings[:200]}")
            output.append(f"**File:** `{c.get('file_path', '')}`")
            output.append("")

    if not any(results.values()):
        output.append("No relevant precedent found.")

    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search the Artifact Index for relevant precedent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("query", nargs="*", help="Search query")
    parser.add_argument(
        "--type", "-t",
        choices=["handoffs", "plans", "continuity", "all"],
        default="all",
        help="Type of artifacts to search (default: all)"
    )
    parser.add_argument(
        "--outcome", "-o",
        choices=["SUCCEEDED", "PARTIAL_PLUS", "PARTIAL_MINUS", "FAILED"],
        help="Filter handoffs by outcome"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=5,
        help="Maximum results per category (default: 5)"
    )
    parser.add_argument(
        "--db",
        type=str,
        metavar="PATH",
        help="Custom database path"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save query for compound learning"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--id",
        type=str,
        metavar="ID",
        help="Get specific handoff by ID"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show database statistics"
    )

    args = parser.parse_args()

    db_path = get_db_path(args.db)

    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        print("Run: python3 artifact_index.py --all", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path), timeout=30.0)

    # Stats mode
    if args.stats:
        stats = {
            "handoffs": conn.execute("SELECT COUNT(*) FROM handoffs").fetchone()[0],
            "plans": conn.execute("SELECT COUNT(*) FROM plans").fetchone()[0],
            "continuity": conn.execute("SELECT COUNT(*) FROM continuity").fetchone()[0],
            "queries": conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0],
        }
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("## Artifact Index Statistics")
            print(f"- Handoffs: {stats['handoffs']}")
            print(f"- Plans: {stats['plans']}")
            print(f"- Continuity ledgers: {stats['continuity']}")
            print(f"- Saved queries: {stats['queries']}")
        conn.close()
        return 0

    # ID lookup mode
    if args.id:
        handoff = get_handoff_by_id(conn, args.id)
        if args.json:
            print(json.dumps(handoff, indent=2, default=str))
        elif handoff:
            print(f"## Handoff: {handoff.get('session_name')}/task-{handoff.get('task_number')}")
            print(f"**Outcome:** {handoff.get('outcome', 'UNKNOWN')}")
            print(f"**Summary:** {handoff.get('task_summary', '')}")
            print(f"**File:** {handoff.get('file_path')}")
        else:
            print(f"Handoff not found: {args.id}", file=sys.stderr)
        conn.close()
        return 0 if handoff else 1

    # Regular search mode
    if not args.query:
        parser.print_help()
        conn.close()
        return 0

    query = " ".join(args.query)

    results: Dict[str, List] = {}

    # Always check past queries first
    results["past_queries"] = search_past_queries(conn, query)

    if args.type in ["handoffs", "all"]:
        results["handoffs"] = search_handoffs(conn, query, args.outcome, args.limit)

    if args.type in ["plans", "all"]:
        results["plans"] = search_plans(conn, query, args.limit)

    if args.type in ["continuity", "all"]:
        results["continuity"] = search_continuity(conn, query, args.limit)

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        formatted = format_results(results)
        print(formatted)

        if args.save:
            save_query(conn, query, formatted, results)
            print("\n[Query saved for compound learning]")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py
```

**Step 3: Test query script**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py "context management" --type plans
```

**Expected output:**
```
## Relevant Plans
### Context Management System - Macro Architecture Plan
**Overview:** Integrate 6 interconnected features from Continuous-Claude-v2...
**File:** `/Users/fredamaral/repos/lerianstudio/ring/docs/plans/2025-12-27-context-management-system.md`
```

**Step 4: Test JSON output**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py "context" --json --limit 2
```

**Expected output:**
```json
{
  "past_queries": [],
  "handoffs": [],
  "plans": [
    {
      "id": "...",
      "title": "Context Management System - Macro Architecture Plan",
      ...
    }
  ],
  "continuity": []
}
```

**Step 5: Test stats**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py --stats
```

**Expected output:**
```
## Artifact Index Statistics
- Handoffs: 0
- Plans: 2
- Continuity ledgers: 0
- Saved queries: 0
```

**Step 6: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/lib/artifact-index/artifact_query.py && git commit -m "feat(artifact-index): add FTS5 query script with BM25 ranking"
```

**If Task Fails:**

1. **No results returned:**
   - Check: Database has data `sqlite3 .ring/.../context.db "SELECT COUNT(*) FROM plans"`
   - Re-run: `python3 default/lib/artifact-index/artifact_index.py --all`

2. **FTS error:**
   - The FTS tables may be empty
   - This is normal if no data has been indexed

---

### Task 6: Create artifact_mark.py

**Files:**
- Create: `default/lib/artifact-index/artifact_mark.py`

**Prerequisites:**
- Task 3 completed (indexing script exists)

**Step 1: Write the mark script**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py`:

```python
#!/usr/bin/env python3
"""
USAGE: artifact_mark.py --handoff ID --outcome OUTCOME [--notes NOTES] [--db PATH]

Mark a handoff with user outcome in the Artifact Index database.

This updates the handoff's outcome and sets confidence to HIGH to indicate
user verification. Used for improving future session recommendations.

Examples:
    # Mark a handoff as succeeded
    python3 artifact_mark.py --handoff abc123 --outcome SUCCEEDED

    # Mark with additional notes
    python3 artifact_mark.py --handoff abc123 --outcome PARTIAL_PLUS --notes "Almost done, one test failing"

    # List recent handoffs to find IDs
    python3 artifact_mark.py --list

    # Mark by file path instead of ID
    python3 artifact_mark.py --file docs/handoffs/session/task-01.md --outcome SUCCEEDED
"""

import argparse
import hashlib
import sqlite3
import sys
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """Get project root by looking for .ring or .git."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".ring").exists() or (parent / ".git").exists():
            return parent
    return current


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Get database path."""
    if custom_path:
        return Path(custom_path)
    return get_project_root() / ".ring" / "cache" / "artifact-index" / "context.db"


def get_handoff_id_from_file(file_path: Path) -> str:
    """Generate handoff ID from file path (same as indexer)."""
    return hashlib.md5(str(file_path.resolve()).encode()).hexdigest()[:12]


def list_recent_handoffs(conn: sqlite3.Connection, limit: int = 10) -> None:
    """List recent handoffs."""
    cursor = conn.execute("""
        SELECT id, session_name, task_number, task_summary, outcome, created_at
        FROM handoffs
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    print("## Recent Handoffs")
    print()
    for row in cursor.fetchall():
        handoff_id, session, task, summary, outcome, created = row
        task_str = f"task-{task}" if task else "unknown"
        summary_short = (summary or "")[:50]
        outcome_str = outcome or "UNKNOWN"
        print(f"- **{handoff_id}**: {session}/{task_str}")
        print(f"  Outcome: {outcome_str} | {summary_short}...")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mark handoff outcome in Artifact Index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--handoff", "-H",
        type=str,
        metavar="ID",
        help="Handoff ID to mark"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        metavar="PATH",
        help="Handoff file path (alternative to --handoff)"
    )
    parser.add_argument(
        "--outcome", "-o",
        choices=["SUCCEEDED", "PARTIAL_PLUS", "PARTIAL_MINUS", "FAILED"],
        help="Outcome of the handoff"
    )
    parser.add_argument(
        "--notes", "-n",
        default="",
        help="Optional notes about the outcome"
    )
    parser.add_argument(
        "--db",
        type=str,
        metavar="PATH",
        help="Custom database path"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List recent handoffs"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for --list (default: 10)"
    )

    args = parser.parse_args()

    db_path = get_db_path(args.db)

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        print("Run: python3 artifact_index.py --all", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(db_path), timeout=30.0)

    # List mode
    if args.list:
        list_recent_handoffs(conn, args.limit)
        conn.close()
        return 0

    # Get handoff ID
    handoff_id = args.handoff
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = get_project_root() / file_path
        handoff_id = get_handoff_id_from_file(file_path)

    if not handoff_id or not args.outcome:
        parser.print_help()
        conn.close()
        return 0

    # First, check if handoff exists
    cursor = conn.execute(
        "SELECT id, session_name, task_number, task_summary FROM handoffs WHERE id = ?",
        (handoff_id,)
    )
    handoff = cursor.fetchone()

    if not handoff:
        print(f"Error: Handoff not found: {handoff_id}", file=sys.stderr)
        print("\nRecent handoffs:", file=sys.stderr)
        list_recent_handoffs(conn, 5)
        conn.close()
        return 1

    # Update the handoff
    cursor = conn.execute(
        "UPDATE handoffs SET outcome = ?, outcome_notes = ?, confidence = 'HIGH' WHERE id = ?",
        (args.outcome, args.notes, handoff_id)
    )

    if cursor.rowcount == 0:
        print(f"Error: Failed to update handoff: {handoff_id}", file=sys.stderr)
        conn.close()
        return 1

    conn.commit()

    # Show confirmation
    handoff_id_db, session, task_num, summary = handoff
    print(f"[OK] Marked handoff {handoff_id} as {args.outcome}")
    print(f"  Session: {session}")
    if task_num:
        print(f"  Task: task-{task_num}")
    if summary:
        print(f"  Summary: {summary[:80]}...")
    if args.notes:
        print(f"  Notes: {args.notes}")
    print(f"  Confidence: HIGH (user-verified)")

    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Make executable**

Run:
```bash
chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py
```

**Step 3: Test help**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py --help
```

**Expected output:**
```
usage: artifact_mark.py [-h] [--handoff ID] [--file PATH]
                        [--outcome {SUCCEEDED,PARTIAL_PLUS,PARTIAL_MINUS,FAILED}]
                        [--notes NOTES] [--db PATH] [--list] [--limit LIMIT]

Mark handoff outcome in Artifact Index
...
```

**Step 4: Test list command**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py --list
```

**Expected output:**
```
## Recent Handoffs

(empty if no handoffs indexed yet)
```

**Step 5: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/lib/artifact-index/artifact_mark.py && git commit -m "feat(artifact-index): add outcome marking script with user verification"
```

**If Task Fails:**

1. **No handoffs to mark:**
   - This is expected if no handoffs have been created yet
   - Script will work once handoffs are indexed

---

### Task 7: Run Code Review

**Files:**
- Reviews: `default/lib/artifact-index/*.py`

**Prerequisites:**
- Tasks 3, 5, 6 completed

**Step 1: Dispatch all 3 reviewers in parallel**

- REQUIRED SUB-SKILL: Use requesting-code-review
- All reviewers run simultaneously (code-reviewer, business-logic-reviewer, security-reviewer)
- Wait for all to complete

**Step 2: Handle findings by severity (MANDATORY)**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments added
- All Cosmetic issues have FIXME(nitpick): comments added

---

## Phase 4: Skill and Command

### Task 8: Create artifact-query skill

**Files:**
- Create: `default/skills/artifact-query/SKILL.md`

**Prerequisites:**
- Task 5 completed (query script exists)

**Step 1: Create skill directory**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/skills/artifact-query
```

**Step 2: Create skill file**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/skills/artifact-query/SKILL.md`:

```markdown
---
name: artifact-query
description: |
  Search the Artifact Index for relevant historical context using semantic
  full-text search. Returns handoffs, plans, and continuity ledgers ranked
  by relevance using BM25.

trigger: |
  - Need to find similar past work before starting a task
  - Want to learn from previous successes or failures
  - Looking for historical context on a topic
  - Planning a feature and want precedent

skip_when: |
  - Working on completely novel functionality
  - Simple task that doesn't benefit from historical context
  - Artifact index not initialized (run artifact_index.py --all first)

sequence:
  before: [writing-plans, executing-plans]

related:
  similar: [exploring-codebase]
---

# Artifact Query

## Overview

Search Ring's Artifact Index for relevant historical context. Uses SQLite FTS5 full-text search with BM25 ranking to find:

- **Handoffs** - Completed task records with what worked/failed
- **Plans** - Implementation design documents
- **Continuity** - Session state snapshots with learnings

**Query response time:** < 100ms for typical searches

**Announce at start:** "I'm searching the artifact index for relevant precedent."

## When to Use

| Scenario | Use This Skill |
|----------|---------------|
| Starting a new feature | Yes - find similar implementations |
| Debugging a recurring issue | Yes - find past resolutions |
| Writing a plan | Yes - learn from past approaches |
| Simple one-liner fix | No - overhead not worth it |
| First time using Ring | No - index is empty |

## The Process

### Step 1: Formulate Query

Choose relevant keywords that describe what you're looking for:
- Feature names: "authentication", "OAuth", "API"
- Problem types: "error handling", "performance", "testing"
- Components: "database", "frontend", "hook"

### Step 2: Run Query

```bash
python3 default/lib/artifact-index/artifact_query.py "<keywords>" [options]
```

**Options:**
- `--type handoffs|plans|continuity|all` - Filter by artifact type
- `--outcome SUCCEEDED|FAILED|...` - Filter handoffs by outcome
- `--limit N` - Maximum results (default: 5)
- `--json` - Output as JSON for programmatic use
- `--stats` - Show index statistics

### Step 3: Interpret Results

Results are ranked by relevance (BM25 score). For each result:

1. **Check outcome** - Learn from successes, avoid failures
2. **Read what_worked** - Reuse successful approaches
3. **Read what_failed** - Don't repeat mistakes
4. **Note file paths** - Can read full artifact if needed

### Step 4: Apply Learnings

Use historical context to inform current work:
- Reference successful patterns in your implementation
- Avoid approaches that failed previously
- Cite the precedent in your plan or handoff

## Examples

### Find Authentication Implementations

```bash
python3 default/lib/artifact-index/artifact_query.py "authentication OAuth JWT" --type handoffs
```

### Find Successful API Designs

```bash
python3 default/lib/artifact-index/artifact_query.py "API design REST" --outcome SUCCEEDED
```

### Get Index Statistics

```bash
python3 default/lib/artifact-index/artifact_query.py --stats
```

### Search Plans Only

```bash
python3 default/lib/artifact-index/artifact_query.py "context management" --type plans --json
```

## Integration with Planning

When creating plans (writing-plans skill), query the artifact index first:

1. Search for similar past implementations
2. Note which approaches succeeded vs failed
3. Include historical context in your plan
4. Reference specific handoffs that inform decisions

This enables RAG-enhanced planning where new plans learn from past experience.

## Initialization

If the index is empty, initialize it:

```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

This indexes:
- `docs/handoffs/**/*.md` - Handoff documents
- `docs/plans/*.md` - Plan documents
- `.ring/ledgers/*.md` and `CONTINUITY*.md` - Continuity ledgers

## Remember

- Query before starting significant work
- Learn from both successes AND failures
- Cite historical precedent in your work
- Keep the index updated (hooks do this automatically)
- Response time target: < 100ms
```

**Step 3: Verify skill was created**

Run:
```bash
head -30 /Users/fredamaral/repos/lerianstudio/ring/default/skills/artifact-query/SKILL.md
```

**Expected output:**
```
---
name: artifact-query
description: |
  Search the Artifact Index for relevant historical context using semantic
  full-text search. Returns handoffs, plans, and continuity ledgers ranked
  by relevance using BM25.
...
```

**Step 4: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/skills/artifact-query/SKILL.md && git commit -m "feat(artifact-index): add artifact-query skill for semantic search"
```

**If Task Fails:**

1. **Directory creation failed:**
   - Check: `ls -la default/skills/`
   - Fix: Ensure write permissions

---

### Task 9: Create query-artifacts command

**Files:**
- Create: `default/commands/query-artifacts.md`

**Prerequisites:**
- Task 8 completed (skill exists)

**Step 1: Create command file**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/commands/query-artifacts.md`:

```markdown
---
name: query-artifacts
description: Search the Artifact Index for relevant historical context
argument-hint: "<search-terms> [--type TYPE] [--outcome OUTCOME]"
---

Search the Artifact Index for relevant handoffs, plans, and continuity ledgers using FTS5 full-text search with BM25 ranking.

## Usage

```
/query-artifacts <search-terms> [options]
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `search-terms` | Yes | Keywords to search for (e.g., "authentication OAuth", "error handling") |
| `--type` | No | Filter by type: `handoffs`, `plans`, `continuity`, `all` (default: all) |
| `--outcome` | No | Filter handoffs: `SUCCEEDED`, `PARTIAL_PLUS`, `PARTIAL_MINUS`, `FAILED` |
| `--limit` | No | Maximum results per category (default: 5) |

## Examples

### Search for Authentication Work

```
/query-artifacts authentication OAuth JWT
```

Returns handoffs, plans, and continuity ledgers related to authentication.

### Find Successful Implementations

```
/query-artifacts API design --outcome SUCCEEDED
```

Returns only handoffs that were marked as successful.

### Search Plans Only

```
/query-artifacts context management --type plans
```

Returns only matching plan documents.

### Limit Results

```
/query-artifacts testing --limit 3
```

Returns at most 3 results per category.

## Output

Results are displayed in markdown format:

```markdown
## Relevant Handoffs
### [OK] session-name/task-01
**Summary:** Implemented OAuth2 authentication...
**What worked:** Token refresh mechanism...
**What failed:** Initial PKCE implementation...
**File:** `/path/to/handoff.md`

## Relevant Plans
### OAuth2 Integration Plan
**Overview:** Implement OAuth2 with PKCE flow...
**File:** `/path/to/plan.md`

## Related Sessions
### Session: auth-implementation
**Goal:** Add authentication to the API...
**Key learnings:** Use refresh tokens...
**File:** `/path/to/ledger.md`
```

## Index Management

### Check Index Statistics

```
/query-artifacts --stats
```

Shows counts of indexed artifacts.

### Initialize/Rebuild Index

If the index is empty or out of date:

```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

## Related Commands/Skills

| Command/Skill | Relationship |
|---------------|--------------|
| `/write-plan` | Query before planning to inform decisions |
| `/create-handoff` | Creates handoffs that get indexed |
| `artifact-query` | The underlying skill |
| `writing-plans` | Uses query results for RAG-enhanced planning |

## Troubleshooting

### "Database not found"

The artifact index hasn't been initialized. Run:

```bash
python3 default/lib/artifact-index/artifact_index.py --all
```

### "No results found"

1. Check that artifacts exist: `ls docs/handoffs/ docs/plans/`
2. Re-index: `python3 default/lib/artifact-index/artifact_index.py --all`
3. Try broader search terms

### Slow queries

Queries should complete in < 100ms. If slow:

1. Check database size: `ls -la .ring/cache/artifact-index/`
2. Rebuild indexes: `python3 default/lib/artifact-index/artifact_index.py --all`
```

**Step 2: Verify command was created**

Run:
```bash
head -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/query-artifacts.md
```

**Expected output:**
```
---
name: query-artifacts
description: Search the Artifact Index for relevant historical context
argument-hint: "<search-terms> [--type TYPE] [--outcome OUTCOME]"
---

Search the Artifact Index for relevant handoffs, plans, and continuity ledgers...
```

**Step 3: Commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add default/commands/query-artifacts.md && git commit -m "feat(artifact-index): add /query-artifacts command"
```

**If Task Fails:**

1. **File creation failed:**
   - Check: `ls -la default/commands/`
   - Fix: Ensure write permissions

---

## Phase 5: Integration Testing

### Task 10: End-to-end integration test

**Files:**
- Uses: All artifact-index scripts
- Creates: Test data in `.ring/`

**Prerequisites:**
- All previous tasks completed

**Step 1: Initialize fresh database**

Run:
```bash
rm -f /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db*
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_index.py --all --project /Users/fredamaral/repos/lerianstudio/ring
```

**Expected output:**
```
Using database: /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/artifact-index/context.db
Project root: /Users/fredamaral/repos/lerianstudio/ring
Indexed X plans
Rebuilding FTS5 indexes...
Optimizing indexes...
Done! Indexed X total artifacts.
```

**Step 2: Query the index**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py "artifact index SQLite" --type plans
```

**Expected output:**
```
## Relevant Plans
### Context Management System - Macro Architecture Plan
**Overview:** ...
**File:** `/Users/fredamaral/repos/lerianstudio/ring/docs/plans/...`
```

**Step 3: Test JSON output**

Run:
```bash
python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py "context" --json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Plans found: {len(d.get(\"plans\",[]))}')"
```

**Expected output:**
```
Plans found: 2
```

**Step 4: Test query performance**

Run:
```bash
time python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_query.py "artifact index" --json > /dev/null
```

**Expected output:**
```
real    0m0.0XXs  (should be < 0.1s)
user    0m0.0XXs
sys     0m0.0XXs
```

**Step 5: Verify all scripts are executable**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/*.py
```

**Expected output:**
```
-rwxr-xr-x  1 user  staff  XXXX Dec 27 xx:xx artifact_index.py
-rwxr-xr-x  1 user  staff  XXXX Dec 27 xx:xx artifact_mark.py
-rwxr-xr-x  1 user  staff  XXXX Dec 27 xx:xx artifact_query.py
```

**If Task Fails:**

1. **Query returns no results:**
   - Re-run indexer: `python3 default/lib/artifact-index/artifact_index.py --all`
   - Check database exists: `ls .ring/cache/artifact-index/`

2. **Performance > 100ms:**
   - This may indicate FTS5 indexes need optimization
   - Re-run indexer to rebuild indexes

---

### Task 11: Final Code Review

**Files:**
- Reviews: All files created in this plan

**Prerequisites:**
- Task 10 completed (integration test passed)

**Step 1: Dispatch all 3 reviewers in parallel**

- REQUIRED SUB-SKILL: Use requesting-code-review
- All reviewers run simultaneously
- Focus on: Security, error handling, performance

**Step 2: Handle findings by severity (same as Task 7)**

**Step 3: Final commit with all fixes**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git add -A && git status
```

If there are changes:

```bash
git commit -m "fix(artifact-index): address code review findings"
```

---

## Completion Checklist

Before marking this plan complete, verify:

- [ ] `default/lib/artifact-index/__init__.py` exists
- [ ] `default/lib/artifact-index/artifact_schema.sql` exists
- [ ] `default/lib/artifact-index/artifact_index.py` exists and is executable
- [ ] `default/lib/artifact-index/artifact_query.py` exists and is executable
- [ ] `default/lib/artifact-index/artifact_mark.py` exists and is executable
- [ ] `default/skills/artifact-query/SKILL.md` exists
- [ ] `default/commands/query-artifacts.md` exists
- [ ] Database initializes correctly: `python3 artifact_index.py --all`
- [ ] Query returns results: `python3 artifact_query.py "test"`
- [ ] Query response time < 100ms
- [ ] All code review issues resolved
- [ ] `.ring/` is in `.gitignore`

---

## Summary

This plan creates the Artifact Index feature for Ring's context management system:

| Component | Location | Purpose |
|-----------|----------|---------|
| Schema | `default/lib/artifact-index/artifact_schema.sql` | SQLite + FTS5 tables |
| Indexer | `default/lib/artifact-index/artifact_index.py` | Parse and index markdown |
| Query | `default/lib/artifact-index/artifact_query.py` | FTS5 search with BM25 |
| Mark | `default/lib/artifact-index/artifact_mark.py` | Update handoff outcomes |
| Skill | `default/skills/artifact-query/SKILL.md` | Agent usage guide |
| Command | `default/commands/query-artifacts.md` | `/query-artifacts` |

**Dependencies satisfied:**
- Uses schema from shared infrastructure
- Creates database at `.ring/cache/artifact-index/context.db`

**Blocks unblocked:**
- Handoff Tracking can now index handoffs
- RAG Planning can now query historical context
- Compound Learnings can now extract patterns

**Performance requirement met:**
- Query response time < 100ms using FTS5 + BM25 ranking

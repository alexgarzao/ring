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
        conn.executescript(schema_path.read_text(encoding='utf-8'))
    else:
        print(f"Warning: Schema file not found at {schema_path}", file=sys.stderr)

    return conn


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Extract YAML frontmatter from markdown content."""
    frontmatter: Dict[str, str] = {}
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
    sections: Dict[str, str] = {}
    current_section: Optional[str] = None
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
    content = file_path.read_text(encoding='utf-8')
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
    content = file_path.read_text(encoding='utf-8')
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
    content = file_path.read_text(encoding='utf-8')
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

    # Validate snapshot_reason against allowed values
    valid_reasons = {'phase_complete', 'session_end', 'milestone', 'manual', 'clear', 'compact'}
    raw_reason = frontmatter.get("reason", "manual").lower()
    snapshot_reason = raw_reason if raw_reason in valid_reasons else "manual"

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
        "snapshot_reason": snapshot_reason,
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
        conn.execute("INSERT INTO learnings_fts(learnings_fts) VALUES('rebuild')")

        # Configure BM25 column weights
        conn.execute("INSERT OR REPLACE INTO handoffs_fts(handoffs_fts, rank) VALUES('rank', 'bm25(10.0, 5.0, 3.0, 3.0, 1.0)')")
        conn.execute("INSERT OR REPLACE INTO plans_fts(plans_fts, rank) VALUES('rank', 'bm25(10.0, 5.0, 3.0, 3.0, 1.0)')")

        print("Optimizing indexes...")
        conn.execute("INSERT INTO handoffs_fts(handoffs_fts) VALUES('optimize')")
        conn.execute("INSERT INTO plans_fts(plans_fts) VALUES('optimize')")
        conn.execute("INSERT INTO continuity_fts(continuity_fts) VALUES('optimize')")
        conn.execute("INSERT INTO queries_fts(queries_fts) VALUES('optimize')")
        conn.execute("INSERT INTO learnings_fts(learnings_fts) VALUES('optimize')")

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

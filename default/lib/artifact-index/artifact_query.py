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
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import get_project_root, get_db_path, validate_limit


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


def query_for_planning(conn: sqlite3.Connection, topic: str, limit: int = 5) -> Dict[str, Any]:
    """Query artifact index for planning context.

    Returns structured data optimized for plan generation:
    - Successful implementations (what worked)
    - Failed implementations (what to avoid)
    - Relevant past plans

    Performance target: <200ms total query time.
    """
    start_time = time.time()

    results: Dict[str, Any] = {
        "topic": topic,
        "successful_handoffs": [],
        "failed_handoffs": [],
        "relevant_plans": [],
        "query_time_ms": 0,
        "is_empty_index": False
    }

    # Check if index has any data
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM handoffs")
        total_handoffs = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # Treat as empty index if schema is corrupted or table doesn't exist
        results["is_empty_index"] = True
        results["query_time_ms"] = int((time.time() - start_time) * 1000)
        return results

    if total_handoffs == 0:
        results["is_empty_index"] = True
        results["query_time_ms"] = int((time.time() - start_time) * 1000)
        return results

    # Query all handoffs matching topic
    # TODO(review): Consider separate queries for success/failure categories to ensure
    # failed handoffs aren't missed when successes dominate top results.
    # Current approach is acceptable for performance. (business-logic-reviewer, Medium)
    all_handoffs = search_handoffs(conn, topic, outcome=None, limit=limit * 3)

    # Filter by outcome
    results["successful_handoffs"] = [
        h for h in all_handoffs
        if h.get("outcome") in ("SUCCEEDED", "PARTIAL_PLUS")
    ][:limit]

    results["failed_handoffs"] = [
        h for h in all_handoffs
        if h.get("outcome") in ("FAILED", "PARTIAL_MINUS")
    ][:limit]

    # Query relevant plans (capped at 3 for context size, limit controls handoffs only)
    results["relevant_plans"] = search_plans(conn, topic, limit=min(limit, 3))

    results["query_time_ms"] = int((time.time() - start_time) * 1000)

    return results


def format_planning_results(results: Dict[str, Any]) -> str:
    """Format planning query results for agent consumption."""
    output: List[str] = []

    output.append("## Historical Precedent")
    output.append("")

    if results.get("is_empty_index"):
        output.append("**Note:** No historical data available (new project or empty index).")
        output.append("Proceed with standard planning approach.")
        output.append("")
        return "\n".join(output)

    # Successful implementations
    successful = results.get("successful_handoffs", [])
    if successful:
        output.append("### Successful Implementations (Reference These)")
        output.append("")
        for h in successful:
            session = h.get('session_name', 'unknown')
            task = h.get('task_number', '?')
            outcome = h.get('outcome', 'UNKNOWN')
            output.append(f"**[{session}/task-{task}]** ({outcome})")

            summary = h.get('task_summary', '')
            if summary:
                output.append(f"- Summary: {summary[:200]}")

            what_worked = h.get('what_worked', '')
            if what_worked:
                output.append(f"- What worked: {what_worked[:300]}")

            output.append(f"- File: `{h.get('file_path', 'unknown')}`")
            output.append("")
    else:
        output.append("### Successful Implementations")
        output.append("No relevant successful implementations found.")
        output.append("")

    # Failed implementations
    failed = results.get("failed_handoffs", [])
    if failed:
        output.append("### Failed Implementations (AVOID These Patterns)")
        output.append("")
        for h in failed:
            session = h.get('session_name', 'unknown')
            task = h.get('task_number', '?')
            outcome = h.get('outcome', 'UNKNOWN')
            output.append(f"**[{session}/task-{task}]** ({outcome})")

            summary = h.get('task_summary', '')
            if summary:
                output.append(f"- Summary: {summary[:200]}")

            what_failed = h.get('what_failed', '')
            if what_failed:
                output.append(f"- What failed: {what_failed[:300]}")

            output.append(f"- File: `{h.get('file_path', 'unknown')}`")
            output.append("")
    else:
        output.append("### Failed Implementations")
        output.append("No relevant failures found (good sign!).")
        output.append("")

    # Relevant plans
    plans = results.get("relevant_plans", [])
    if plans:
        output.append("### Relevant Past Plans")
        output.append("")
        for p in plans:
            title = p.get('title', 'Untitled')
            output.append(f"**{title}**")

            overview = p.get('overview', '')
            if overview:
                output.append(f"- Overview: {overview[:200]}")

            output.append(f"- File: `{p.get('file_path', 'unknown')}`")
            output.append("")

    query_time = results.get("query_time_ms", 0)
    output.append("---")
    output.append(f"*Query completed in {query_time}ms*")

    return "\n".join(output)


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
        "--mode", "-m",
        choices=["search", "planning"],
        default="search",
        help="Query mode: 'search' for general queries, 'planning' for structured planning context"
    )
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
        type=validate_limit,
        default=5,
        help="Maximum results per category (1-100, default: 5)"
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

    # Graceful handling for missing database in planning mode
    if not db_path.exists():
        if args.mode == "planning":
            # Planning mode: return empty index result (normal for new projects)
            query = " ".join(args.query) if args.query else ""
            results = {
                "topic": query,
                "successful_handoffs": [],
                "failed_handoffs": [],
                "relevant_plans": [],
                "query_time_ms": 0,
                "is_empty_index": True,
                "message": "No artifact index found. This is normal for new projects."
            }
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                print(format_planning_results(results))
            return 0
        else:
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

    # Planning mode - structured output for plan generation
    if args.mode == "planning":
        if not args.query:
            print("Error: Query required for planning mode", file=sys.stderr)
            print("Usage: python3 artifact_query.py --mode planning 'topic keywords'", file=sys.stderr)
            conn.close()
            return 1

        query = " ".join(args.query)
        results = query_for_planning(conn, query, args.limit)
        conn.close()

        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            print(format_planning_results(results))
        return 0

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

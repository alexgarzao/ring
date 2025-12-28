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

from utils import get_project_root, get_db_path, validate_limit


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
        type=validate_limit,
        default=10,
        help="Limit for --list (1-100, default: 10)"
    )

    args = parser.parse_args()

    # Check mutual exclusivity of --handoff and --file
    if args.handoff and args.file:
        print("Error: Cannot use both --handoff and --file. Choose one.", file=sys.stderr)
        return 1

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

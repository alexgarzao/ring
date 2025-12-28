#!/usr/bin/env python3
"""
Plan Precedent Validation

Validates a plan file against known failure patterns from the artifact index.
Warns if the plan's approach overlaps significantly with past failures.

Usage:
    python3 validate-plan-precedent.py <plan-file> [--threshold 30] [--json]

Exit codes:
    0 - Plan passes validation (or index unavailable)
    1 - Plan has significant overlap with failure patterns (warning)
    2 - Error (invalid arguments, file not found, etc.)
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def get_project_root() -> Path:
    """Get project root by looking for .ring or .git."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".ring").exists() or (parent / ".git").exists():
            return parent
    return current


def get_db_path() -> Path:
    """Get artifact index database path."""
    return get_project_root() / ".ring" / "cache" / "artifact-index" / "context.db"


def extract_keywords_from_plan(plan_path: Path) -> Set[str]:
    """Extract significant keywords from plan file.

    Focuses on:
    - Goal section
    - Architecture section
    - Tech Stack section
    - Task names
    - Technical terms
    """
    try:
        content = plan_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, IOError, PermissionError):
        # Return empty set on read error - caller will handle
        return set()

    keywords: Set[str] = set()

    # Extract from Goal section
    goal_match = re.search(r'\*\*Goal:\*\*\s*(.+?)(?:\n\n|\*\*)', content, re.DOTALL)
    if goal_match:
        keywords.update(extract_words(goal_match.group(1)))

    # Extract from Architecture section
    arch_match = re.search(r'\*\*Architecture:\*\*\s*(.+?)(?:\n\n|\*\*)', content, re.DOTALL)
    if arch_match:
        keywords.update(extract_words(arch_match.group(1)))

    # Extract from Tech Stack section (key failure indicator)
    tech_match = re.search(r'\*\*Tech Stack:\*\*\s*(.+?)(?:\n|$)', content)
    if tech_match:
        keywords.update(extract_words(tech_match.group(1)))

    # Extract from Task names
    task_names = re.findall(r'### Task \d+:\s*(.+)', content)
    for name in task_names:
        keywords.update(extract_words(name))

    # Extract from Historical Precedent query if present
    query_match = re.search(r'\*\*Query:\*\*\s*"([^"]+)"', content)
    if query_match:
        keywords.update(extract_words(query_match.group(1)))

    return keywords


def extract_words(text: str) -> Set[str]:
    """Extract significant words from text (lowercase, >3 chars, alphanumeric)."""
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]{2,}\b', text.lower())
    # Filter out common words
    stopwords = {
        'the', 'and', 'for', 'this', 'that', 'with', 'from', 'will', 'have',
        'are', 'was', 'been', 'being', 'has', 'had', 'does', 'did', 'doing',
        'would', 'could', 'should', 'must', 'can', 'may', 'might', 'shall',
        'into', 'onto', 'upon', 'about', 'above', 'below', 'between',
        'through', 'during', 'before', 'after', 'under', 'over',
        'then', 'than', 'when', 'where', 'what', 'which', 'who', 'how', 'why',
        'each', 'every', 'all', 'any', 'some', 'most', 'many', 'few',
        'file', 'files', 'code', 'step', 'task', 'test', 'tests', 'run', 'add',
        'create', 'update', 'implement', 'use', 'using', 'used'
    }
    return {w for w in words if w not in stopwords}


def get_failed_handoffs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Get all failed handoffs from the index."""
    sql = """
        SELECT id, session_name, task_number, task_summary, what_failed, outcome
        FROM handoffs
        WHERE outcome IN ('FAILED', 'PARTIAL_MINUS')
    """
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def extract_keywords_from_handoff(handoff: Dict[str, Any]) -> Set[str]:
    """Extract keywords from a handoff record.

    Extracts from task_summary, what_failed, and key_decisions fields
    to capture full failure context.
    """
    keywords: Set[str] = set()

    task_summary = handoff.get('task_summary', '') or ''
    what_failed = handoff.get('what_failed', '') or ''
    key_decisions = handoff.get('key_decisions', '') or ''

    keywords.update(extract_words(task_summary))
    keywords.update(extract_words(what_failed))
    keywords.update(extract_words(key_decisions))

    return keywords


def calculate_overlap(plan_keywords: Set[str], handoff_keywords: Set[str]) -> float:
    """Calculate keyword overlap using bidirectional maximum.

    Checks overlap in both directions to avoid dilution bias:
    - What % of plan keywords match failure? (catches small plans)
    - What % of failure keywords appear in plan? (catches large plans)

    Returns: Maximum of both percentages (0-100).
    """
    if not plan_keywords or not handoff_keywords:
        return 0.0

    intersection = plan_keywords & handoff_keywords

    # Bidirectional: Check both directions, return higher
    # This prevents large plans from escaping detection via keyword dilution
    plan_coverage = (len(intersection) / len(plan_keywords)) * 100
    failure_coverage = (len(intersection) / len(handoff_keywords)) * 100

    return max(plan_coverage, failure_coverage)


def validate_plan(
    plan_path: Path,
    threshold: int = 30
) -> Dict[str, Any]:
    """Validate plan against failure patterns.

    Returns validation result with:
    - passed: True if no significant overlap found
    - warnings: List of overlapping handoffs
    - plan_keywords: Keywords extracted from plan
    - threshold: Overlap threshold used
    """
    result: Dict[str, Any] = {
        "passed": True,
        "warnings": [],
        "plan_file": str(plan_path),
        "plan_keywords": [],
        "threshold": threshold,
        "index_available": True
    }

    # Check plan file exists
    if not plan_path.exists():
        result["passed"] = False
        result["error"] = f"Plan file not found: {plan_path}"
        return result

    # Extract keywords from plan
    plan_keywords = extract_keywords_from_plan(plan_path)
    result["plan_keywords"] = sorted(plan_keywords)

    if not plan_keywords:
        result["warning"] = "No significant keywords extracted from plan"
        return result

    # Check database exists
    db_path = get_db_path()
    if not db_path.exists():
        result["index_available"] = False
        result["message"] = "Artifact index not available - skipping validation"
        return result

    # Query failed handoffs (use context manager to ensure connection is closed)
    try:
        with sqlite3.connect(str(db_path), timeout=30.0) as conn:
            failed_handoffs = get_failed_handoffs(conn)
    except sqlite3.Error as e:
        result["index_available"] = False
        result["error"] = "Database error: unable to query artifact index"
        return result

    if not failed_handoffs:
        result["message"] = "No failed handoffs in index - nothing to validate against"
        return result

    # Check overlap with each failed handoff
    for handoff in failed_handoffs:
        handoff_keywords = extract_keywords_from_handoff(handoff)
        overlap_pct = calculate_overlap(plan_keywords, handoff_keywords)

        if overlap_pct >= threshold:
            result["passed"] = False
            overlapping_keywords = sorted(plan_keywords & handoff_keywords)
            result["warnings"].append({
                "handoff_id": handoff["id"],
                "session": handoff.get("session_name", "unknown"),
                "task": handoff.get("task_number", "?"),
                "outcome": handoff.get("outcome", "UNKNOWN"),
                "overlap_percent": round(overlap_pct, 1),
                "overlapping_keywords": overlapping_keywords,
                "what_failed": (handoff.get("what_failed", "") or "")[:200]
            })

    return result


def format_result(result: Dict[str, Any]) -> str:
    """Format validation result for human-readable output."""
    output: List[str] = []

    output.append("## Plan Precedent Validation")
    output.append("")
    output.append(f"**Plan:** `{result['plan_file']}`")
    output.append(f"**Threshold:** {result['threshold']}% overlap")
    output.append("")

    if result.get("error"):
        output.append(f"**ERROR:** {result['error']}")
        return "\n".join(output)

    if not result.get("index_available"):
        output.append(f"**Note:** {result.get('message', 'Index not available')}")
        output.append("")
        output.append("**Result:** PASS (no validation data)")
        return "\n".join(output)

    if result.get("message"):
        output.append(f"**Note:** {result['message']}")
        output.append("")

    keywords = result.get("plan_keywords", [])
    if keywords:
        output.append(f"**Keywords extracted:** {len(keywords)}")
        output.append(f"```\n{', '.join(keywords[:20])}{'...' if len(keywords) > 20 else ''}\n```")
        output.append("")

    if result["passed"]:
        output.append("### Result: PASS")
        output.append("")
        output.append("No significant overlap with known failure patterns.")
    else:
        output.append("### Result: WARNING - Overlap Detected")
        output.append("")
        output.append(f"Found {len(result['warnings'])} failure pattern(s) with >={result['threshold']}% keyword overlap:")
        output.append("")

        for warning in result["warnings"]:
            session = warning.get("session", "unknown")
            task = warning.get("task", "?")
            overlap = warning.get("overlap_percent", 0)
            outcome = warning.get("outcome", "UNKNOWN")

            output.append(f"#### [{session}/task-{task}] ({outcome}) - {overlap}% overlap")
            output.append("")

            overlapping = warning.get("overlapping_keywords", [])
            if overlapping:
                output.append(f"**Overlapping keywords:** `{', '.join(overlapping)}`")

            what_failed = warning.get("what_failed", "")
            if what_failed:
                output.append(f"**What failed:** {what_failed}")

            output.append("")

        output.append("---")
        output.append("**Action Required:** Review the failure patterns above and ensure your plan addresses these issues.")

    return "\n".join(output)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate plan against known failure patterns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "plan_file",
        type=str,
        help="Path to plan file to validate"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=30,
        help="Overlap percentage threshold for warnings (default: 30)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    # Validate threshold
    if args.threshold < 0 or args.threshold > 100:
        print("Error: Threshold must be between 0 and 100", file=sys.stderr)
        return 2

    plan_path = Path(args.plan_file)
    result = validate_plan(plan_path, args.threshold)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_result(result))

    if result.get("error"):
        return 2
    elif not result["passed"]:
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())

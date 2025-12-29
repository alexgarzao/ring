#!/usr/bin/env python3
"""Outcome inference module for automatic handoff outcome detection.

This module analyzes session state to infer task outcomes:
- SUCCEEDED: All todos complete, no errors
- PARTIAL_PLUS: Most todos complete, minor issues
- PARTIAL_MINUS: Some progress, significant blockers
- FAILED: No meaningful progress or abandoned

Usage:
    from outcome_inference import infer_outcome
    outcome = infer_outcome(project_root)
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Outcome definitions
OUTCOME_SUCCEEDED = "SUCCEEDED"
OUTCOME_PARTIAL_PLUS = "PARTIAL_PLUS"
OUTCOME_PARTIAL_MINUS = "PARTIAL_MINUS"
OUTCOME_FAILED = "FAILED"
OUTCOME_UNKNOWN = "UNKNOWN"


def get_project_root() -> Path:
    """Get the project root directory."""
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(os.environ["CLAUDE_PROJECT_DIR"])
    return Path.cwd()


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID for safe use in filenames."""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    if not sanitized:
        return "unknown"
    return sanitized[:64]


def analyze_todos(todos: List[Dict]) -> Tuple[int, int, int, int]:
    """Analyze todo list and return counts.

    Returns:
        Tuple of (total, completed, in_progress, pending)
    """
    if not todos:
        return (0, 0, 0, 0)

    total = len(todos)
    completed = sum(1 for t in todos if t.get("status") == "completed")
    in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
    pending = sum(1 for t in todos if t.get("status") == "pending")

    return (total, completed, in_progress, pending)


def infer_outcome_from_todos(
    total: int,
    completed: int,
    in_progress: int,
    pending: int
) -> Tuple[str, str]:
    """Infer outcome from todo counts.

    Returns:
        Tuple of (outcome, reason)
    """
    if total == 0:
        return (OUTCOME_FAILED, "No todos tracked - unable to measure completion")

    completion_ratio = completed / total

    if completed == total:
        return (OUTCOME_SUCCEEDED, f"All {total} tasks completed")

    if completion_ratio >= 0.8:
        remaining = total - completed
        return (OUTCOME_PARTIAL_PLUS, f"{completed}/{total} tasks done, {remaining} minor items remain")

    if completion_ratio >= 0.5:
        return (OUTCOME_PARTIAL_MINUS, f"{completed}/{total} tasks done, significant work remains")

    # <50% completion is FAILED - insufficient progress
    # Note: in_progress tasks without completion don't count toward progress
    return (OUTCOME_FAILED, f"Insufficient progress: only {completed}/{total} tasks completed ({int(completion_ratio * 100)}%)")


def infer_outcome(
    todos: Optional[List[Dict]] = None,
) -> Dict:
    """Infer session outcome from available state.

    Args:
        todos: Optional pre-parsed todos list

    Returns:
        Dict with 'outcome', 'reason', and 'confidence' keys
    """
    result = {
        "outcome": OUTCOME_UNKNOWN,
        "reason": "Unable to determine outcome",
        "confidence": "low",
        "sources": [],
    }

    if todos is not None:
        total, completed, in_progress, pending = analyze_todos(todos)
        # Always infer outcome from todos - even if empty (total=0 -> FAILED)
        result["outcome"], result["reason"] = infer_outcome_from_todos(
            total, completed, in_progress, pending
        )
        result["sources"].append("todos")
        # Confidence based on completion clarity
        if total == 0:
            # Empty todos = high confidence it's a failure
            result["confidence"] = "high"
        elif completed == total or completed == 0:
            result["confidence"] = "high"
        elif completed / total >= 0.8 or completed / total <= 0.2:
            result["confidence"] = "medium"
        else:
            result["confidence"] = "low"

    return result


def main():
    """CLI entry point for testing."""
    import sys

    # Read optional todos from stdin
    todos = None
    if not sys.stdin.isatty():
        try:
            input_data = json.loads(sys.stdin.read())
            todos = input_data.get("todos")
        except json.JSONDecodeError:
            pass

    result = infer_outcome(todos=todos)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

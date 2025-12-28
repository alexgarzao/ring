#!/usr/bin/env python3
"""Learning extraction hook for SessionEnd.

This hook runs on SessionEnd (Stop event) to extract learnings from
the current session and save them to .ring/cache/learnings/.

Input (stdin JSON):
{
    "type": "stop",
    "session_id": "optional session identifier",
    "reason": "user_stop|error|complete"
}

Output (stdout JSON):
{
    "result": "continue",
    "message": "Optional system reminder about learnings"
}
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime


def read_stdin() -> dict:
    """Read JSON input from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def get_project_root() -> Path:
    """Get the project root directory."""
    # Try CLAUDE_PROJECT_DIR first
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(os.environ["CLAUDE_PROJECT_DIR"])
    # Fall back to current directory
    return Path.cwd()


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID for safe use in filenames.

    SECURITY: Prevents path traversal attacks via malicious session_id.
    Only allows alphanumeric characters, hyphens, and underscores.
    """
    import re
    # Remove any path separators or special characters
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    # Ensure non-empty and reasonable length
    if not sanitized:
        return "unknown"
    return sanitized[:64]  # Limit length


def get_session_id(input_data: dict) -> str:
    """Get session identifier from input or generate one."""
    if input_data.get("session_id"):
        # SECURITY: Sanitize user-provided session_id
        return sanitize_session_id(input_data["session_id"])
    # Generate based on timestamp with microseconds to prevent collision
    return datetime.now().strftime("%H%M%S-%f")[:13]


def extract_learnings_from_handoffs(project_root: Path, session_id: str) -> dict:
    """Extract learnings from recent handoffs in the artifact index.

    This queries the artifact index for handoffs from this session
    and extracts their what_worked, what_failed, and key_decisions.
    """
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Try to query artifact index if available
    db_path = project_root / ".ring" / "cache" / "artifact-index" / "context.db"
    if not db_path.exists():
        return learnings

    try:
        import sqlite3
        # Use context manager for proper connection cleanup
        with sqlite3.connect(str(db_path), timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row

            # Get recent handoffs (from today)
            today = datetime.now().strftime("%Y-%m-%d")
            cursor = conn.execute(
                """
                SELECT outcome, what_worked, what_failed, key_decisions
                FROM handoffs
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT 10
                """,
                (today,)
            )

            seen_worked = set()
            seen_failed = set()

            for row in cursor.fetchall():
                outcome = row["outcome"]
                if outcome in ("SUCCEEDED", "PARTIAL_PLUS"):
                    if row["what_worked"] and row["what_worked"] not in seen_worked:
                        learnings["what_worked"].append(row["what_worked"])
                        seen_worked.add(row["what_worked"])
                elif outcome in ("FAILED", "PARTIAL_MINUS"):
                    if row["what_failed"] and row["what_failed"] not in seen_failed:
                        learnings["what_failed"].append(row["what_failed"])
                        seen_failed.add(row["what_failed"])

                if row["key_decisions"]:
                    learnings["key_decisions"].append(row["key_decisions"])

    except Exception as e:
        # Log error for debugging but continue gracefully
        import sys
        print(f"Warning: Failed to extract learnings from handoffs: {e}", file=sys.stderr)

    return learnings


def extract_learnings_from_outcomes(project_root: Path, session_id: str) -> dict:
    """Extract learnings from session outcomes file (if exists).

    This reads from .ring/state/session-outcome.json if it exists.
    Note: This file is optional - primary learnings come from handoffs database.
    The file can be created manually or by future session outcome capture tools.
    """
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Check for outcome file (optional - may not exist)
    state_dir = project_root / ".ring" / "state"
    outcome_file = state_dir / "session-outcome.json"

    if not outcome_file.exists():
        # File doesn't exist - this is normal, learnings come from handoffs
        return learnings

    try:
        with open(outcome_file, encoding='utf-8') as f:
            outcome = json.load(f)

        status = outcome.get("status", "unknown")
        if status in ["SUCCEEDED", "PARTIAL_PLUS"]:
            if outcome.get("summary"):
                learnings["what_worked"].append(outcome["summary"])
        elif status in ["FAILED", "PARTIAL_MINUS"]:
            if outcome.get("summary"):
                learnings["what_failed"].append(outcome["summary"])

        if outcome.get("key_decisions"):
            if isinstance(outcome["key_decisions"], list):
                learnings["key_decisions"].extend(outcome["key_decisions"])
            else:
                learnings["key_decisions"].append(outcome["key_decisions"])

    except (json.JSONDecodeError, KeyError, IOError) as e:
        import sys
        print(f"Warning: Failed to read session outcome file: {e}", file=sys.stderr)

    return learnings


def save_learnings(project_root: Path, session_id: str, learnings: dict) -> Path:
    """Save learnings to cache file.

    Args:
        project_root: Project root directory
        session_id: Session identifier (must be pre-sanitized)
        learnings: Extracted learnings dictionary

    Returns:
        Path to saved learnings file

    Raises:
        ValueError: If resolved path escapes learnings directory
    """
    # Create learnings directory
    learnings_dir = project_root / ".ring" / "cache" / "learnings"
    learnings_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{session_id}.md"
    file_path = learnings_dir / filename

    # SECURITY: Verify the resolved path is within learnings_dir
    resolved_path = file_path.resolve()
    resolved_learnings = learnings_dir.resolve()
    if not str(resolved_path).startswith(str(resolved_learnings)):
        raise ValueError(
            f"Security: session_id would escape learnings directory: {session_id}"
        )

    # Generate content
    content = f"""# Learnings from Session {session_id}

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## What Worked

"""
    for item in learnings.get("what_worked", []):
        content += f"- {item}\n"
    if not learnings.get("what_worked"):
        content += "- (No successful patterns recorded)\n"

    content += """
## What Failed

"""
    for item in learnings.get("what_failed", []):
        content += f"- {item}\n"
    if not learnings.get("what_failed"):
        content += "- (No failures recorded)\n"

    content += """
## Key Decisions

"""
    for item in learnings.get("key_decisions", []):
        content += f"- {item}\n"
    if not learnings.get("key_decisions"):
        content += "- (No key decisions recorded)\n"

    content += """
## Patterns

"""
    for item in learnings.get("patterns", []):
        content += f"- {item}\n"
    if not learnings.get("patterns"):
        content += "- (No patterns identified)\n"

    # Write file
    file_path.write_text(content, encoding='utf-8')
    return file_path


def main():
    """Main hook entry point."""
    input_data = read_stdin()

    # Only process on actual session end (not errors)
    if input_data.get("type") != "stop":
        print(json.dumps({"result": "continue"}))
        return

    project_root = get_project_root()
    session_id = get_session_id(input_data)

    # Combine learnings from different sources
    learnings = {
        "what_worked": [],
        "what_failed": [],
        "key_decisions": [],
        "patterns": [],
    }

    # Extract from handoffs (if artifact index available)
    handoff_learnings = extract_learnings_from_handoffs(project_root, session_id)
    for key in learnings:
        learnings[key].extend(handoff_learnings.get(key, []))

    # Extract from outcomes (if outcome tracking available)
    outcome_learnings = extract_learnings_from_outcomes(project_root, session_id)
    for key in learnings:
        learnings[key].extend(outcome_learnings.get(key, []))

    # Check if we have any learnings to save
    has_learnings = any(learnings.get(key) for key in learnings)

    if has_learnings:
        file_path = save_learnings(project_root, session_id, learnings)
        message = f"Session learnings saved to {file_path.relative_to(project_root)}"
    else:
        message = "No learnings extracted from this session (no handoffs or outcomes recorded)"

    # Output hook response
    output = {
        "result": "continue",
        "message": message,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()

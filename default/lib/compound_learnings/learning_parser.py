"""Parse learning markdown files into structured data.

This module extracts structured information from session learning files
stored in .ring/cache/learnings/.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional


def _extract_session_id(filename: str) -> str:
    """Extract session ID from filename, expecting YYYY-MM-DD-<session>.md format.

    Args:
        filename: File stem without extension (e.g., "2025-12-27-abc123")

    Returns:
        Session ID portion, or empty string if no valid session ID found
    """
    parts = filename.split("-")
    # Validate date prefix: must have at least 4 parts (YYYY-MM-DD-session)
    if len(parts) >= 4:
        year, month, day = parts[0], parts[1], parts[2]
        # Verify first 3 parts look like a date
        if len(year) == 4 and len(month) == 2 and len(day) == 2:
            if year.isdigit() and month.isdigit() and day.isdigit():
                # Join remaining parts as session ID
                return "-".join(parts[3:])
    # No hyphen or no valid date prefix - return filename as-is
    if "-" not in filename:
        return filename
    # Has hyphens but not valid date format - return empty
    return ""


def parse_learning_file(file_path: Path) -> Dict:
    """Parse a learning markdown file into structured data.

    Args:
        file_path: Path to the learning markdown file

    Returns:
        Dictionary with session_id, date, what_worked, what_failed,
        key_decisions, and patterns
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except (UnicodeDecodeError, IOError, PermissionError):
        return {
            "session_id": "",
            "date": "",
            "file_path": str(file_path),
            "what_worked": [],
            "what_failed": [],
            "key_decisions": [],
            "patterns": [],
            "error": "Failed to read file",
        }

    # Extract session ID from filename: YYYY-MM-DD-<session-id>.md
    filename = file_path.stem  # e.g., "2025-12-27-abc123"
    session_id = _extract_session_id(filename)

    # Extract date from content
    date_match = re.search(r'\*\*Date:\*\*\s*(.+)', content)
    date = date_match.group(1).strip() if date_match else ""

    return {
        "session_id": session_id,
        "date": date,
        "file_path": str(file_path),
        "what_worked": extract_what_worked(content),
        "what_failed": extract_what_failed(content),
        "key_decisions": extract_key_decisions(content),
        "patterns": extract_patterns(content),
    }


def _extract_section_items(content: str, section_name: str) -> List[str]:
    """Extract bullet items from a markdown section.

    Args:
        content: Full markdown content
        section_name: Name of section (e.g., "What Worked")

    Returns:
        List of bullet point items (without the leading "- ")
    """
    # Match section header and capture until next ## or end
    pattern = rf'##\s*{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

    if not match:
        return []

    section_content = match.group(1)

    # Extract bullet points (lines starting with "- ")
    items = []
    for line in section_content.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())

    return items


def extract_what_worked(content: str) -> List[str]:
    """Extract items from 'What Worked' section."""
    return _extract_section_items(content, "What Worked")


def extract_what_failed(content: str) -> List[str]:
    """Extract items from 'What Failed' section."""
    return _extract_section_items(content, "What Failed")


def extract_key_decisions(content: str) -> List[str]:
    """Extract items from 'Key Decisions' section."""
    return _extract_section_items(content, "Key Decisions")


def extract_patterns(content: str) -> List[str]:
    """Extract items from 'Patterns' section."""
    return _extract_section_items(content, "Patterns")


def load_all_learnings(learnings_dir: Path) -> List[Dict]:
    """Load all learning files from a directory.

    Args:
        learnings_dir: Path to .ring/cache/learnings/ directory

    Returns:
        List of parsed learning dictionaries, sorted by date (newest first)
    """
    if not learnings_dir.exists():
        return []

    learnings = []
    for file_path in learnings_dir.glob("*.md"):
        try:
            learning = parse_learning_file(file_path)
            if not learning.get("error"):
                learnings.append(learning)
        except Exception as e:
            # Log but continue processing other files
            print(f"Warning: Failed to parse {file_path}: {e}")

    # Sort by date (newest first)
    learnings.sort(key=lambda x: x.get("date", ""), reverse=True)
    return learnings

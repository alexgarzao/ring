"""Shared utilities for artifact-index modules."""

import argparse
from pathlib import Path
from typing import Optional


def get_project_root(custom_path: Optional[str] = None) -> Path:
    """Get project root by finding .ring or .git directory.

    Args:
        custom_path: Optional explicit path to use as root

    Returns:
        Path to project root, or current directory if not found
    """
    if custom_path:
        return Path(custom_path).resolve()
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".ring").exists() or (parent / ".git").exists():
            return parent
    return current


def get_db_path(custom_path: Optional[str] = None, project_root: Optional[Path] = None) -> Path:
    """Get database path, creating parent directory if needed.

    Args:
        custom_path: Optional explicit database path
        project_root: Optional project root (computed if not provided)

    Returns:
        Path to SQLite database file
    """
    if custom_path:
        path = Path(custom_path)
    else:
        root = project_root or get_project_root()
        path = root / ".ring" / "cache" / "artifact-index" / "context.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def validate_limit(value: str) -> int:
    """Validate limit argument is integer between 1 and 100.

    Args:
        value: String value from argparse

    Returns:
        Validated integer

    Raises:
        argparse.ArgumentTypeError: If value invalid
    """
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")
    if ivalue < 1 or ivalue > 100:
        raise argparse.ArgumentTypeError(f"Limit must be between 1 and 100, got: {ivalue}")
    return ivalue

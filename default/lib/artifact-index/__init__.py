"""Artifact Index - SQLite-based indexing and search for Ring artifacts.

This package provides:
- artifact_index.py: Index markdown files into SQLite with FTS5
- artifact_query.py: Search artifacts with BM25 ranking
- artifact_mark.py: Mark handoff outcomes
- utils.py: Shared utilities (get_project_root, get_db_path, validate_limit)
"""

from utils import get_project_root, get_db_path, validate_limit

__version__ = "1.0.0"
__all__ = ["get_project_root", "get_db_path", "validate_limit"]

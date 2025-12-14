#!/usr/bin/env python3
"""
SQLite database builder with FTS5 for Ring component search.

Creates and populates the ring-index.db database.
"""

import sqlite3
import sys
from pathlib import Path
from typing import List

try:
    from .models import Component
except ImportError:
    from models import Component


# SQL schema
SCHEMA_SQL = """
-- Main components table
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY,
    plugin TEXT NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    fqn TEXT NOT NULL UNIQUE,
    description TEXT,
    use_cases TEXT,
    keywords TEXT,
    file_path TEXT,
    full_content TEXT,
    model TEXT,
    trigger TEXT,
    skip_when TEXT,
    argument_hint TEXT
);

-- FTS5 virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS components_fts USING fts5(
    name,
    description,
    use_cases,
    keywords,
    trigger,
    content='components',
    content_rowid='id'
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS components_ai AFTER INSERT ON components BEGIN
    INSERT INTO components_fts(rowid, name, description, use_cases, keywords, trigger)
    VALUES (new.id, new.name, new.description, new.use_cases, new.keywords, new.trigger);
END;

CREATE TRIGGER IF NOT EXISTS components_ad AFTER DELETE ON components BEGIN
    INSERT INTO components_fts(components_fts, rowid, name, description, use_cases, keywords, trigger)
    VALUES ('delete', old.id, old.name, old.description, old.use_cases, old.keywords, old.trigger);
END;

CREATE TRIGGER IF NOT EXISTS components_au AFTER UPDATE ON components BEGIN
    INSERT INTO components_fts(components_fts, rowid, name, description, use_cases, keywords, trigger)
    VALUES ('delete', old.id, old.name, old.description, old.use_cases, old.keywords, old.trigger);
    INSERT INTO components_fts(rowid, name, description, use_cases, keywords, trigger)
    VALUES (new.id, new.name, new.description, new.use_cases, new.keywords, new.trigger);
END;

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_components_plugin ON components(plugin);
CREATE INDEX IF NOT EXISTS idx_components_type ON components(type);
CREATE INDEX IF NOT EXISTS idx_components_fqn ON components(fqn);
"""


def create_database(db_path: Path) -> sqlite3.Connection:
    """Create database with schema."""
    # Remove existing database
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()

    print(f"Created database: {db_path}", file=sys.stderr)
    return conn


def insert_components(conn: sqlite3.Connection, components: List[Component]) -> int:
    """Insert components into database."""
    cursor = conn.cursor()

    insert_sql = """
    INSERT INTO components (
        plugin, type, name, fqn, description, use_cases, keywords,
        file_path, full_content, model, trigger, skip_when, argument_hint
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    inserted = 0
    for component in components:
        try:
            cursor.execute(insert_sql, (
                component.plugin,
                component.type.value,
                component.name,
                component.fqn,
                component.description,
                component.use_cases_json(),
                component.keywords_json(),
                component.file_path,
                component.full_content,
                component.model,
                component.trigger,
                component.skip_when,
                component.argument_hint,
            ))
            inserted += 1
        except sqlite3.IntegrityError as e:
            print(f"Warning: Duplicate FQN {component.fqn}: {e}", file=sys.stderr)

    conn.commit()
    return inserted


def rebuild_fts_index(conn: sqlite3.Connection):
    """Rebuild FTS index (useful after bulk inserts)."""
    conn.execute("INSERT INTO components_fts(components_fts) VALUES('rebuild')")
    conn.commit()
    print("Rebuilt FTS index", file=sys.stderr)


def get_database_stats(conn: sqlite3.Connection) -> dict:
    """Get statistics about the database."""
    cursor = conn.cursor()

    # Total components
    cursor.execute("SELECT COUNT(*) FROM components")
    total = cursor.fetchone()[0]

    # By type
    cursor.execute("SELECT type, COUNT(*) FROM components GROUP BY type")
    by_type = dict(cursor.fetchall())

    # By plugin
    cursor.execute("SELECT plugin, COUNT(*) FROM components GROUP BY plugin")
    by_plugin = dict(cursor.fetchall())

    return {
        "total": total,
        "by_type": by_type,
        "by_plugin": by_plugin,
    }


def search_fts(conn: sqlite3.Connection, query: str, limit: int = 10) -> List[dict]:
    """Search components using FTS5."""
    cursor = conn.cursor()

    # FTS5 search with ranking
    sql = """
    SELECT
        c.fqn,
        c.type,
        c.name,
        c.description,
        c.plugin,
        bm25(components_fts) as rank
    FROM components_fts
    JOIN components c ON components_fts.rowid = c.id
    WHERE components_fts MATCH ?
    ORDER BY rank
    LIMIT ?
    """

    cursor.execute(sql, (query, limit))

    results = []
    for row in cursor.fetchall():
        results.append({
            "fqn": row[0],
            "type": row[1],
            "name": row[2],
            "description": row[3],
            "plugin": row[4],
            "rank": row[5],
        })

    return results


def main():
    """Main entry point for standalone testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Build Ring component database')
    parser.add_argument('--db', type=Path, default=Path('ring-index.db'),
                        help='Output database path')
    parser.add_argument('--test-query', type=str, default=None,
                        help='Test FTS query after building')
    args = parser.parse_args()

    # Import scanner here to avoid circular import
    from scanner import scan_all_plugins

    # Find repo root (assume we're in tools/ring-cli/extractor)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent.parent

    if not (repo_root / '.claude-plugin').exists():
        print(f"Error: Could not find repo root from {script_dir}", file=sys.stderr)
        print("Please run from repository root or specify --repo", file=sys.stderr)
        sys.exit(1)

    # Scan components
    components = scan_all_plugins(repo_root)

    # Create database
    conn = create_database(args.db)

    # Insert components
    inserted = insert_components(conn, components)
    print(f"Inserted {inserted} components", file=sys.stderr)

    # Get stats
    stats = get_database_stats(conn)
    print(f"\nDatabase statistics:", file=sys.stderr)
    print(f"  Total: {stats['total']}", file=sys.stderr)
    print(f"  By type: {stats['by_type']}", file=sys.stderr)
    print(f"  By plugin: {stats['by_plugin']}", file=sys.stderr)

    # Test query if provided
    if args.test_query:
        print(f"\nTest query: {args.test_query}", file=sys.stderr)
        results = search_fts(conn, args.test_query)
        for r in results:
            desc = r['description'] or ''
            print(f"  {r['fqn']}: {desc[:50]}{'...' if len(desc) > 50 else ''} (rank: {r['rank']:.2f})")

    conn.close()
    print(f"\nDatabase saved to: {args.db}", file=sys.stderr)


if __name__ == '__main__':
    main()

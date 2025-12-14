#!/usr/bin/env python3
"""
Main entry point for building the Ring component index.

Usage:
    python build_index.py                    # Build from current directory
    python build_index.py --repo /path/to/ring  # Build from specified repo
    python build_index.py --output ring-index.db  # Specify output path
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from .scanner import scan_all_plugins
    from .database import create_database, insert_components, get_database_stats, rebuild_fts_index
except ImportError:
    from scanner import scan_all_plugins
    from database import create_database, insert_components, get_database_stats, rebuild_fts_index


def find_repo_root(start_path: Path) -> Path:
    """Find repository root by looking for .claude-plugin directory."""
    current = start_path.resolve()

    for _ in range(10):  # Limit search depth
        if (current / '.claude-plugin').exists():
            return current
        if current.parent == current:
            break
        current = current.parent

    raise FileNotFoundError(
        f"Could not find Ring repository root from {start_path}. "
        "Please specify --repo or run from within the repository."
    )


def main():
    parser = argparse.ArgumentParser(
        description='Build Ring component search index',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build_index.py
    python build_index.py --repo /path/to/ring
    python build_index.py --output /path/to/ring-index.db
    python build_index.py --json components.json
        """
    )
    parser.add_argument(
        '--repo', type=Path, default=None,
        help='Repository root directory (default: auto-detect)'
    )
    parser.add_argument(
        '--output', type=Path, default=None,
        help='Output database path (default: tools/ring-cli/ring-index.db)'
    )
    parser.add_argument(
        '--json', type=Path, default=None,
        help='Also output components as JSON file'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Find repo root
    try:
        if args.repo:
            repo_root = args.repo.resolve()
            if not (repo_root / '.claude-plugin').exists():
                print(f"Error: {repo_root} does not appear to be a Ring repository",
                      file=sys.stderr)
                sys.exit(1)
        else:
            repo_root = find_repo_root(Path.cwd())
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Repository root: {repo_root}", file=sys.stderr)

    # Determine output path
    if args.output:
        db_path = args.output.resolve()
    else:
        db_path = repo_root / 'tools' / 'ring-cli' / 'ring-index.db'

    # Ensure output directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Scan components
    print("\n=== Scanning plugins ===", file=sys.stderr)
    components = scan_all_plugins(repo_root)

    if not components:
        print("Error: No components found", file=sys.stderr)
        sys.exit(1)

    # Create database
    print("\n=== Building database ===", file=sys.stderr)
    conn = create_database(db_path)

    # Insert components
    inserted = insert_components(conn, components)

    # Rebuild FTS index for optimization
    rebuild_fts_index(conn)

    # Get and display stats
    stats = get_database_stats(conn)

    print("\n=== Build complete ===", file=sys.stderr)
    print(f"Components indexed: {stats['total']}", file=sys.stderr)
    print(f"  Skills:   {stats['by_type'].get('skill', 0)}", file=sys.stderr)
    print(f"  Agents:   {stats['by_type'].get('agent', 0)}", file=sys.stderr)
    print(f"  Commands: {stats['by_type'].get('command', 0)}", file=sys.stderr)
    print(f"\nDatabase: {db_path}", file=sys.stderr)

    # Output JSON if requested
    if args.json:
        json_output = json.dumps([c.to_dict() for c in components], indent=2)
        args.json.write_text(json_output)
        print(f"JSON: {args.json}", file=sys.stderr)

    conn.close()

    # Print success message
    print(f"\nSuccess! Index built with {stats['total']} components.", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Ring CLI - Component Discovery Tool

Discover Ring components (skills, agents, commands) through natural language queries.

## Quick Start

```bash
# Build the index and CLI
./build.sh

# Search for components
./cli/ring-cli "code review"
./cli/ring-cli --type agent "backend golang"
./cli/ring-cli --json "debugging"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  BUILD TIME (CI/maintainers)                                    │
├─────────────────────────────────────────────────────────────────┤
│  1. extractor/ parses all plugin *.md files                     │
│  2. Builds SQLite database with FTS5 index                      │
│  3. Commits ring-index.db to repository                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  RUNTIME (user)                                                 │
├─────────────────────────────────────────────────────────────────┤
│  $ ring-cli "preciso revisar código Go antes de PR"             │
│                              ↓                                  │
│  Phase 1: FTS5 pre-filter (fast, ~5-10 candidates)              │
│                              ↓                                  │
│  Output: Top N components with usage hints                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### extractor/ (Python)

Metadata extraction from plugin markdown files:

- `models.py` - Data structures for components
- `parser.py` - YAML frontmatter parsing
- `scanner.py` - Directory scanning
- `database.py` - SQLite/FTS5 database builder
- `build_index.py` - Main build script

### cli/ (Go)

Cross-platform CLI for querying the index:

- `main.go` - Entry point and flags
- `database.go` - SQLite operations
- `output.go` - Result formatting

### ring-index.db (SQLite)

Pre-built search index with:

- Components table (all metadata)
- FTS5 virtual table (full-text search)
- Automatic triggers for index sync

## Usage

```bash
# Basic search
ring-cli "how to debug"

# Filter by type
ring-cli --type skill "testing"
ring-cli --type agent "backend"
ring-cli --type command "review"

# JSON output (for scripting)
ring-cli --json "authentication" | jq '.[] | .fqn'

# Custom database path
ring-cli --db /path/to/ring-index.db "query"

# Limit results
ring-cli --limit 10 "documentation"
```

## Development

### Prerequisites

- Python 3.8+ with PyYAML
- Go 1.21+ with CGO enabled
- C compiler (gcc/clang) for sqlite3 CGO
- SQLite 3.9+ (for FTS5 support)

### Building

```bash
# Full build (requires CGO for FTS5)
./build.sh

# Just the index
cd extractor && python build_index.py

# Just the CLI (with FTS5 support)
cd cli && CGO_CFLAGS="-DSQLITE_ENABLE_FTS5" go build -tags "fts5" -o ring-cli .
```

### Testing

```bash
# Test index with query
python extractor/database.py --test-query "code review"

# Test CLI
./cli/ring-cli --version
./cli/ring-cli "test query"
```

## CI/CD

The index is automatically rebuilt when component files change:

- Trigger: Push to `main` with changes to `**/skills/*/SKILL.md`, `**/agents/*.md`, or `**/commands/*.md`
- Workflow: `.github/workflows/rebuild-index.yml`
- Result: Updated `ring-index.db` committed to repository

## SQLite Schema

```sql
CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    plugin TEXT NOT NULL,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    fqn TEXT NOT NULL UNIQUE,
    description TEXT,
    use_cases TEXT,      -- JSON array
    keywords TEXT,       -- JSON array
    file_path TEXT,
    full_content TEXT,
    model TEXT,
    trigger TEXT,
    skip_when TEXT,
    argument_hint TEXT
);

CREATE VIRTUAL TABLE components_fts USING fts5(
    name, description, use_cases, keywords, trigger,
    content='components', content_rowid='id'
);
```

## BM25 Ranking Weights

The search uses BM25 ranking with custom weights:

| Column | Weight | Rationale |
|--------|--------|-----------|
| name | 1.0 | Base weight |
| description | 2.0 | Most relevant for user queries |
| use_cases | 1.5 | Good context signals |
| keywords | 1.0 | Supporting terms |
| trigger | 1.5 | When-to-use context |

Lower BM25 scores = better matches (more negative is better).

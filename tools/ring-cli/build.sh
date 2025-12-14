#!/usr/bin/env bash
# Build script for ring-cli
# Builds both the index and the CLI binary

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Ring CLI Build Script ==="
echo "Repository: $REPO_ROOT"
echo ""

# Verify prerequisites
for cmd in python3 go; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Error: $cmd is required but not found" >&2
        exit 1
    fi
done

# Build index
echo "Building index..."
cd "$SCRIPT_DIR/extractor"
python3 build_index.py --repo "$REPO_ROOT" --output "$SCRIPT_DIR/ring-index.db"

# Build CLI with FTS5 support (requires CGO)
echo ""
echo "Building CLI..."
cd "$SCRIPT_DIR/cli"
CGO_ENABLED=1 CGO_CFLAGS="-DSQLITE_ENABLE_FTS5" go build -tags "fts5" -o ring-cli .

echo ""
echo "=== Build complete ==="
echo "Index: $SCRIPT_DIR/ring-index.db"
echo "CLI:   $SCRIPT_DIR/cli/ring-cli"
echo ""
echo "Test with:"
echo "  $SCRIPT_DIR/cli/ring-cli \"code review\""

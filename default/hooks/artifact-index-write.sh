#!/usr/bin/env bash
# PostToolUse hook: Index handoffs/plans immediately on Write
# Core two: Write tool
# Purpose: Immediate indexing for searchability

set -euo pipefail

# Read input from stdin
INPUT=$(cat)

# Determine project root early for path validation
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Extract file path from Write tool output
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

if [[ -z "$FILE_PATH" ]]; then
    # No file path in input, skip
    echo '{"result": "continue"}'
    exit 0
fi

# Path boundary validation: ensure FILE_PATH is within PROJECT_ROOT
# This prevents path traversal attacks (e.g., ../../etc/passwd)
validate_path_boundary() {
    local file_path="$1"
    local project_root="$2"

    # Resolve to absolute paths (handles ../ and symlinks)
    local resolved_file resolved_root

    # For file path, resolve the directory portion (file may not exist yet)
    local file_dir
    file_dir=$(dirname "$file_path")

    # If directory doesn't exist, walk up to find existing parent
    while [[ ! -d "$file_dir" ]] && [[ "$file_dir" != "/" ]]; do
        file_dir=$(dirname "$file_dir")
    done

    if [[ -d "$file_dir" ]]; then
        resolved_file="$(cd "$file_dir" && pwd)/$(basename "$file_path")"
    else
        # Cannot resolve, reject
        return 1
    fi

    resolved_root="$(cd "$project_root" && pwd)"

    # Check if resolved file path starts with resolved project root
    if [[ "$resolved_file" == "$resolved_root"/* ]]; then
        return 0
    else
        return 1
    fi
}

# Validate path is within project boundary
if ! validate_path_boundary "$FILE_PATH" "$PROJECT_ROOT"; then
    # Path outside project root, skip silently (security: don't reveal validation)
    echo '{"result": "continue"}'
    exit 0
fi

# Check if file is a handoff or plan
if [[ "$FILE_PATH" == *"/handoffs/"* ]] || [[ "$FILE_PATH" == *"/plans/"* ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
    PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

    # Path to artifact indexer (try plugin lib first, then project .ring)
    INDEXER="${PLUGIN_ROOT}/lib/artifact-index/artifact_index.py"

    if [[ ! -f "$INDEXER" ]]; then
        INDEXER="${PROJECT_ROOT}/.ring/lib/artifact-index/artifact_index.py"
    fi

    if [[ -f "$INDEXER" ]]; then
        # Index the single file (fast path)
        python3 "$INDEXER" --file "$FILE_PATH" --project "$PROJECT_ROOT" 2>/dev/null || true
    fi
fi

# Continue processing
cat <<'HOOKEOF'
{
  "result": "continue"
}
HOOKEOF

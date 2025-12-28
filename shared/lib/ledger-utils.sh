#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Shared ledger utilities for Ring hooks
# Usage: source this file, then call find_active_ledger "$ledger_dir"

# Find active ledger (most recently modified) - SAFE implementation
# Finds the newest CONTINUITY-*.md file in the specified directory
#
# Arguments:
#   $1 - ledger_dir: Path to the directory containing CONTINUITY-*.md files
#
# Returns:
#   Prints the path to the most recently modified ledger file, or empty string if none found
#
# Security:
#   - Rejects symlinks explicitly (prevents symlink attacks)
#   - Uses null-terminated paths (prevents injection via malicious filenames)
#   - Portable across macOS/Linux (handles stat differences)
find_active_ledger() {
    local ledger_dir="$1"

    # Return empty if directory doesn't exist
    [[ ! -d "$ledger_dir" ]] && echo "" && return 0

    local newest=""
    local newest_time=0

    # Safe iteration with null-terminated paths
    while IFS= read -r -d '' file; do
        # Security: Reject symlinks explicitly
        if [[ -L "$file" ]]; then
            echo "Warning: Skipping symlink: $file" >&2
            continue
        fi

        # Get modification time (portable across macOS/Linux)
        local mtime
        if [[ "$(uname)" == "Darwin" ]]; then
            mtime=$(stat -f %m "$file" 2>/dev/null || echo 0)
        else
            mtime=$(stat -c %Y "$file" 2>/dev/null || echo 0)
        fi

        if (( mtime > newest_time )); then
            newest_time=$mtime
            newest="$file"
        fi
    done < <(find "$ledger_dir" -maxdepth 1 -name "CONTINUITY-*.md" -type f -print0 2>/dev/null)

    echo "$newest"
}

# Export for subshells
export -f find_active_ledger 2>/dev/null || true

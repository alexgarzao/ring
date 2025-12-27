#!/usr/bin/env bash
# Ledger save hook - auto-saves active ledger before compaction or stop
# Triggered by: PreCompact, Stop events

set -euo pipefail

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER_DIR="${PROJECT_ROOT}/.ring/ledgers"

# Source shared JSON escaping utility
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"
if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/json-escape.sh"
else
    # Fallback: define json_escape locally
    json_escape() {
        local input="$1"
        if command -v jq &>/dev/null; then
            printf '%s' "$input" | jq -Rs . | sed 's/^"//;s/"$//'
        else
            printf '%s' "$input" | sed \
                -e 's/\\/\\\\/g' \
                -e 's/"/\\"/g' \
                -e 's/\t/\\t/g' \
                -e 's/\r/\\r/g' \
                -e ':a;N;$!ba;s/\n/\\n/g'
        fi
    }
fi

# Find active ledger (most recently modified) - SAFE implementation
# Fixes: GNU/Linux data leak, symlink following, command injection
find_active_ledger() {
    local ledger_dir="$LEDGER_DIR"

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

# Update ledger timestamp - SAFE implementation
# Fixes: Silent failure when Updated: line missing
update_ledger_timestamp() {
    local ledger_file="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    if grep -q "^Updated:" "$ledger_file" 2>/dev/null; then
        # Update existing timestamp
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' "s/^Updated:.*$/Updated: ${timestamp}/" "$ledger_file"
        else
            sed -i "s/^Updated:.*$/Updated: ${timestamp}/" "$ledger_file"
        fi
    else
        # Append if missing
        echo "Updated: ${timestamp}" >> "$ledger_file"
    fi

    # Always update filesystem mtime as fallback
    touch "$ledger_file"
}

# Main logic
main() {
    local active_ledger
    active_ledger=$(find_active_ledger)

    if [[ -z "$active_ledger" ]]; then
        # No active ledger - nothing to save
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "LedgerSave",
    "message": "No active ledger found. Nothing to save."
  }
}
EOF
        exit 0
    fi

    # Update timestamp
    update_ledger_timestamp "$active_ledger"

    local ledger_name
    ledger_name=$(basename "$active_ledger" .md)

    # Extract current phase for status message
    local current_phase=""
    current_phase=$(grep -E '\[->' "$active_ledger" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//' || echo "")

    local message="Ledger saved: ${ledger_name}.md"
    if [[ -n "$current_phase" ]]; then
        message="${message}\nCurrent phase: ${current_phase}"
    fi
    message="${message}\n\nAfter clear/compact, state will auto-restore on resume."

    local message_escaped
    message_escaped=$(json_escape "$message")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "LedgerSave",
    "additionalContext": "${message_escaped}"
  }
}
EOF
}

main "$@"

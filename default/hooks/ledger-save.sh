#!/usr/bin/env bash
# Ledger save hook - auto-saves active ledger before compaction or stop
# Triggered by: PreCompact, Stop events

set -euo pipefail

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER_DIR="${PROJECT_ROOT}/.ring/ledgers"

# Source shared utilities
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"

# Source JSON escaping utility
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

# Source ledger utilities
if [[ -f "${SHARED_LIB}/ledger-utils.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/ledger-utils.sh"
else
    # Fallback: define find_active_ledger locally if shared lib not found
    find_active_ledger() {
        local ledger_dir="$1"
        [[ ! -d "$ledger_dir" ]] && echo "" && return 0
        local newest="" newest_time=0
        while IFS= read -r -d '' file; do
            [[ -L "$file" ]] && continue
            local mtime
            if [[ "$(uname)" == "Darwin" ]]; then
                mtime=$(stat -f %m "$file" 2>/dev/null || echo 0)
            else
                mtime=$(stat -c %Y "$file" 2>/dev/null || echo 0)
            fi
            (( mtime > newest_time )) && newest_time=$mtime && newest="$file"
        done < <(find "$ledger_dir" -maxdepth 1 -name "CONTINUITY-*.md" -type f -print0 2>/dev/null)
        echo "$newest"
    }
fi

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
    active_ledger=$(find_active_ledger "$LEDGER_DIR")

    if [[ -z "$active_ledger" ]]; then
        # No active ledger - nothing to save
        cat <<'EOF'
{
  "result": "continue"
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
  "result": "continue",
  "message": "${message_escaped}"
}
EOF
}

main "$@"

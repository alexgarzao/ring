#!/usr/bin/env bash
# Stop hook: Prompt for session outcome
# Purpose: Capture user feedback on session success/failure
# Note: Non-blocking - user can skip

set -euo pipefail

# Read input from stdin (not used currently, but available)
INPUT=$(cat)

# Determine project root
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Load shared JSON escape utility
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"
if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=../../shared/lib/json-escape.sh
    source "${SHARED_LIB}/json-escape.sh"
else
    # Fallback if shared lib not found
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

# Check multiple handoff locations (matching artifact_index.py behavior)
HANDOFFS_DIRS=(
    "${PROJECT_ROOT}/docs/handoffs"
    "${PROJECT_ROOT}/.ring/handoffs"
)

RECENT_HANDOFF=""
for HANDOFFS_DIR in "${HANDOFFS_DIRS[@]}"; do
    if [[ ! -d "$HANDOFFS_DIR" ]]; then
        continue
    fi

    # Find most recent handoff in this directory (sorted by modification time)
    # Use -print0 and xargs -0 for safe handling of special characters
    FOUND=$(find "$HANDOFFS_DIR" -name "*.md" -mmin -60 -type f -print0 2>/dev/null | \
        xargs -0 ls -t 2>/dev/null | head -1)

    if [[ -n "$FOUND" ]]; then
        RECENT_HANDOFF="$FOUND"
        break  # Found one, use it
    fi
done

if [[ -z "$RECENT_HANDOFF" ]]; then
    # No recent handoff found in any location
    cat <<'HOOKEOF'
{
  "result": "continue"
}
HOOKEOF
    exit 0
fi

# Extract handoff filename for display
HANDOFF_NAME=$(basename "$RECENT_HANDOFF")

# Build message with proper escaping for JSON safety
MESSAGE="Session ending. Recent handoff found: ${HANDOFF_NAME}

When you mark the session outcome, use:
python3 default/lib/artifact-index/artifact_mark.py --file ${RECENT_HANDOFF} --outcome <SUCCEEDED|PARTIAL_PLUS|PARTIAL_MINUS|FAILED>

Or list recent handoffs: python3 default/lib/artifact-index/artifact_mark.py --list"

# Escape message for JSON (handles special chars, quotes, newlines)
MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

# Return message prompting for outcome
# Note: The actual prompt will be handled by the agent using AskUserQuestion
cat <<HOOKEOF
{
  "result": "continue",
  "message": "${MESSAGE_ESCAPED}"
}
HOOKEOF

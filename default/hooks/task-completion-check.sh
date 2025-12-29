#!/usr/bin/env bash
# Task Completion Check - PostToolUse hook for TodoWrite
# Detects when all todos are marked complete and triggers handoff creation
# Performance target: <50ms execution time

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MONOREPO_ROOT="$(cd "${PLUGIN_ROOT}/.." && pwd)"

# Read input from stdin
INPUT=$(cat)

# Source shared libraries
SHARED_LIB="${MONOREPO_ROOT}/shared/lib"
if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/json-escape.sh"
else
    # Fallback: minimal JSON escaping
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

# Parse TodoWrite tool output from input
# Expected input structure:
# {
#   "tool_name": "TodoWrite",
#   "tool_input": { "todos": [...] },
#   "tool_output": { ... }
# }

# Extract todos array using jq if available, otherwise skip
if ! command -v jq &>/dev/null; then
    # No jq - cannot parse todos, return minimal response
    cat <<'EOF'
{
  "result": "continue"
}
EOF
    exit 0
fi

# Parse the todos from tool_input
TODOS=$(echo "$INPUT" | jq -r '.tool_input.todos // []' 2>/dev/null)

# Persist todos state for outcome-inference.sh to read later
# This solves the data flow break where Stop hook doesn't have access to todos
if [[ -n "$TODOS" ]] && [[ "$TODOS" != "null" ]] && [[ "$TODOS" != "[]" ]]; then
    PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    STATE_DIR="${PROJECT_ROOT}/.ring/state"
    mkdir -p "$STATE_DIR"

    # Session ID isolation - use CLAUDE_SESSION_ID if available, fallback to PPID
    SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"
    # Sanitize session ID: keep only alphanumeric, hyphens, underscores
    SESSION_ID_SAFE=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
    [[ -z "$SESSION_ID_SAFE" ]] && SESSION_ID_SAFE="unknown"

    # Atomic write: temp file + mv
    TODOS_STATE_FILE="${STATE_DIR}/todos-state-${SESSION_ID_SAFE}.json"
    TEMP_TODOS_FILE="${TODOS_STATE_FILE}.tmp.$$"
    echo "$TODOS" > "$TEMP_TODOS_FILE"
    mv "$TEMP_TODOS_FILE" "$TODOS_STATE_FILE"
fi

if [[ -z "$TODOS" ]] || [[ "$TODOS" == "null" ]] || [[ "$TODOS" == "[]" ]]; then
    # No todos or empty - nothing to check
    cat <<'EOF'
{
  "result": "continue"
}
EOF
    exit 0
fi

# Count total and completed todos
TOTAL_COUNT=$(echo "$TODOS" | jq 'length')
COMPLETED_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "completed")] | length')
IN_PROGRESS_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "in_progress")] | length')
PENDING_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "pending")] | length')

# Check if all todos are complete
if [[ "$TOTAL_COUNT" -gt 0 ]] && [[ "$COMPLETED_COUNT" -eq "$TOTAL_COUNT" ]]; then
    # All todos complete - trigger handoff creation
    TASK_LIST=$(echo "$TODOS" | jq -r '.[] | "- " + .content')
    MESSAGE="<MANDATORY-USER-MESSAGE>
TASK COMPLETION DETECTED - HANDOFF RECOMMENDED

All ${TOTAL_COUNT} todos are marked complete.

**FIRST:** Run /context to check actual context usage.

**IF context is high (>70%):** Create handoff NOW:
1. Run /create-handoff to preserve this session's learnings
2. Document what worked and what failed in the handoff

**IF context is low (<70%):** Handoff is optional - you can continue with new tasks.

Completed tasks:
${TASK_LIST}
</MANDATORY-USER-MESSAGE>"

    MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${MESSAGE_ESCAPED}"
  }
}
EOF
else
    # Not all complete - return status summary
    if [[ "$COMPLETED_COUNT" -gt 0 ]]; then
        MESSAGE="Task progress: ${COMPLETED_COUNT}/${TOTAL_COUNT} complete, ${IN_PROGRESS_COUNT} in progress, ${PENDING_COUNT} pending."
        MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${MESSAGE_ESCAPED}"
  }
}
EOF
    else
        # No completed tasks - minimal response
        cat <<'EOF'
{
  "result": "continue"
}
EOF
    fi
fi

exit 0

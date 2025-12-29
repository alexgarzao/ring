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
TASK COMPLETION DETECTED - HANDOFF REQUIRED

All ${TOTAL_COUNT} todos are marked complete. You MUST create a handoff document NOW:

1. MANDATORY: Run /create-handoff to preserve this session's learnings
2. MANDATORY: Document what worked and what failed in the handoff
3. After handoff created, session can end or continue with new tasks

This handoff will be indexed for future sessions to learn from.

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

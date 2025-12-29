#!/usr/bin/env bash
# SessionStart hook: Prompt for previous session outcome grade
# Purpose: Capture user feedback on session success/failure AFTER /clear or /compact
# Event: SessionStart (matcher: clear|compact) - AI is active and can prompt user
#
# Why SessionStart instead of PreCompact?
# - PreCompact additionalContext is NOT visible to AI (architectural limitation)
# - SessionStart additionalContext IS visible to AI
# - State files (todos, ledger, handoffs) persist on disk after clear/compact

set -euo pipefail

# Read input from stdin (not used currently, but available)
INPUT=$(cat)

# Determine project root
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Session identification
SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"
SESSION_ID_SAFE=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
[[ -z "$SESSION_ID_SAFE" ]] && SESSION_ID_SAFE="unknown"

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

# Check if there's session work to grade
# Priority: 1) todos state, 2) active ledger, 3) recent handoff
HAS_SESSION_WORK=false
SESSION_CONTEXT=""

# Check for todos state (indicates TodoWrite was used this session)
TODOS_FILE="${PROJECT_ROOT}/.ring/state/todos-state-${SESSION_ID_SAFE}.json"
if [[ -f "$TODOS_FILE" ]]; then
    HAS_SESSION_WORK=true
    if command -v jq &>/dev/null; then
        TOTAL=$(jq 'length' "$TODOS_FILE" 2>/dev/null || echo 0)
        COMPLETED=$(jq '[.[] | select(.status == "completed")] | length' "$TODOS_FILE" 2>/dev/null || echo 0)
        SESSION_CONTEXT="Task progress: ${COMPLETED}/${TOTAL} completed"
    fi
fi

# Check for active ledger
LEDGER_DIR="${PROJECT_ROOT}/.ring/ledgers"
if [[ -d "$LEDGER_DIR" ]]; then
    ACTIVE_LEDGER=$(find "$LEDGER_DIR" -maxdepth 1 -name "CONTINUITY-*.md" -type f -mmin -120 2>/dev/null | head -1)
    if [[ -n "$ACTIVE_LEDGER" ]]; then
        HAS_SESSION_WORK=true
        LEDGER_NAME=$(basename "$ACTIVE_LEDGER" .md)
        if [[ -n "$SESSION_CONTEXT" ]]; then
            SESSION_CONTEXT="${SESSION_CONTEXT}, Ledger: ${LEDGER_NAME}"
        else
            SESSION_CONTEXT="Ledger: ${LEDGER_NAME}"
        fi
    fi
fi

# Check for recent handoffs (modified in last 2 hours)
# Store the path for later use with artifact_mark.py
HANDOFF_FILE_PATH=""
HANDOFFS_DIRS=("${PROJECT_ROOT}/docs/handoffs" "${PROJECT_ROOT}/.ring/handoffs")
for HANDOFFS_DIR in "${HANDOFFS_DIRS[@]}"; do
    if [[ -d "$HANDOFFS_DIR" ]]; then
        RECENT_HANDOFF=$(find "$HANDOFFS_DIR" -name "*.md" -mmin -120 -type f 2>/dev/null | head -1)
        if [[ -n "$RECENT_HANDOFF" ]]; then
            HAS_SESSION_WORK=true
            HANDOFF_FILE_PATH="$RECENT_HANDOFF"
            HANDOFF_NAME=$(basename "$RECENT_HANDOFF")
            if [[ -n "$SESSION_CONTEXT" ]]; then
                SESSION_CONTEXT="${SESSION_CONTEXT}, Handoff: ${HANDOFF_NAME}"
            else
                SESSION_CONTEXT="Handoff: ${HANDOFF_NAME}"
            fi
            break
        fi
    fi
done

# If no session work detected, skip prompting
if [[ "$HAS_SESSION_WORK" != "true" ]]; then
    cat <<'HOOKEOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart"
  }
}
HOOKEOF
    exit 0
fi

# Build artifact_mark instruction only if we have a handoff file to mark
ARTIFACT_MARK_INSTRUCTION=""
if [[ -n "$HANDOFF_FILE_PATH" ]]; then
    # Make path relative to project root for cleaner output
    RELATIVE_HANDOFF="${HANDOFF_FILE_PATH#"${PROJECT_ROOT}/"}"
    # Use absolute path to artifact_mark.py (SCRIPT_DIR points to hooks/, lib/ is sibling)
    ARTIFACT_MARK_SCRIPT="${SCRIPT_DIR}/../lib/artifact-index/artifact_mark.py"
    ARTIFACT_MARK_INSTRUCTION="

After user responds, save the grade using:
\`python3 ${ARTIFACT_MARK_SCRIPT} --file ${RELATIVE_HANDOFF} --outcome <GRADE>\`"
fi

# Build prompt message for the AI to ask user
MESSAGE="<MANDATORY-USER-MESSAGE>
PREVIOUS SESSION OUTCOME GRADE REQUESTED

You just cleared/compacted the previous session. Please ask the user to rate the PREVIOUS session's outcome.

**Previous Session Context:** ${SESSION_CONTEXT}

**MANDATORY ACTION:** Use AskUserQuestion to ask:
\"How would you rate the previous session's outcome?\"

Options:
- SUCCEEDED: All goals achieved, high quality output
- PARTIAL_PLUS: Most goals achieved (≥80%), minor issues
- PARTIAL_MINUS: Some progress (50-79%), significant gaps
- FAILED: Goals not achieved (<50%), major issues
${ARTIFACT_MARK_INSTRUCTION}

Then continue with the new session.
</MANDATORY-USER-MESSAGE>"

MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

# Return hook response with additionalContext (AI will process this)
cat <<HOOKEOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${MESSAGE_ESCAPED}"
  }
}
HOOKEOF

#!/usr/bin/env bash
# Outcome Inference Hook Wrapper
# Calls Python module to infer session outcome from state
# Triggered by: Stop event (runs before learning-extract.sh)

set -euo pipefail

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib/outcome-inference"

# Source shared JSON escaping library
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"
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

# Read input from stdin
INPUT=$(cat)

# Find Python interpreter
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    # Python not available - skip inference
    echo '{"result": "continue", "message": "Outcome inference skipped: Python not available"}'
    exit 0
fi

# Check if module exists
if [[ ! -f "${LIB_DIR}/outcome_inference.py" ]]; then
    echo '{"result": "continue", "message": "Outcome inference skipped: Module not found"}'
    exit 0
fi

# Session identification - use CLAUDE_SESSION_ID if available, fallback to PPID
SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"
# Sanitize session ID: keep only alphanumeric, hyphens, underscores
SESSION_ID_SAFE=$(echo "$SESSION_ID" | tr -cd 'a-zA-Z0-9_-')
[[ -z "$SESSION_ID_SAFE" ]] && SESSION_ID_SAFE="unknown"

# Read persisted todos from task-completion-check.sh
# This solves the data flow break where Stop hook doesn't have direct access to todos
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="${PROJECT_ROOT}/.ring/state"
TODOS_FILE="${STATE_DIR}/todos-state-${SESSION_ID_SAFE}.json"

INPUT_FOR_PYTHON='{"todos": []}'
if [[ -f "$TODOS_FILE" ]]; then
    TODOS_DATA=$(cat "$TODOS_FILE" 2>/dev/null || echo '[]')
    if command -v jq &>/dev/null; then
        # Wrap in expected format for Python: {"todos": [...]}
        INPUT_FOR_PYTHON=$(echo "$TODOS_DATA" | jq '{todos: .}' 2>/dev/null || echo '{"todos": []}')
    else
        # Fallback: simple string wrapping (assumes valid JSON array)
        INPUT_FOR_PYTHON="{\"todos\": ${TODOS_DATA}}"
    fi
fi

# Run inference with persisted todos piped
RESULT=$(echo "$INPUT_FOR_PYTHON" | "$PYTHON_CMD" "${LIB_DIR}/outcome_inference.py" 2>/dev/null || echo '{}')

# Extract outcome and reason using jq if available
if command -v jq &>/dev/null; then
    OUTCOME=$(echo "$RESULT" | jq -r '.outcome // "UNKNOWN"')
    REASON=$(echo "$RESULT" | jq -r '.reason // "Unable to determine"')
    CONFIDENCE=$(echo "$RESULT" | jq -r '.confidence // "low"')
else
    # Fallback: grep-based extraction
    OUTCOME=$(echo "$RESULT" | grep -o '"outcome": *"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")
    REASON=$(echo "$RESULT" | grep -o '"reason": *"[^"]*"' | cut -d'"' -f4 || echo "Unable to determine")
    CONFIDENCE=$(echo "$RESULT" | grep -o '"confidence": *"[^"]*"' | cut -d'"' -f4 || echo "low")
fi

# Save outcome to state file for learning-extract.py to pick up
# Note: PROJECT_ROOT, STATE_DIR, and SESSION_ID_SAFE already defined above
mkdir -p "$STATE_DIR"

# Escape variables for safe JSON output
OUTCOME_ESCAPED=$(json_escape "$OUTCOME")
REASON_ESCAPED=$(json_escape "$REASON")
CONFIDENCE_ESCAPED=$(json_escape "$CONFIDENCE")

# Write outcome state (session-isolated filename)
cat > "${STATE_DIR}/session-outcome-${SESSION_ID_SAFE}.json" << EOF
{
  "status": "${OUTCOME_ESCAPED}",
  "summary": "${REASON_ESCAPED}",
  "confidence": "${CONFIDENCE_ESCAPED}",
  "inferred_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "key_decisions": []
}
EOF

# Build message and escape for JSON
MESSAGE="Session outcome inferred: ${OUTCOME} (${CONFIDENCE} confidence) - ${REASON}"
MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

# Return hook response
cat << EOF
{
  "result": "continue",
  "message": "${MESSAGE_ESCAPED}"
}
EOF

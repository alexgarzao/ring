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

# Run inference with input piped
RESULT=$(echo "$INPUT" | "$PYTHON_CMD" "${LIB_DIR}/outcome_inference.py" 2>/dev/null || echo '{}')

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
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="${PROJECT_ROOT}/.ring/state"
mkdir -p "$STATE_DIR"

# Escape variables for safe JSON output
OUTCOME_ESCAPED=$(json_escape "$OUTCOME")
REASON_ESCAPED=$(json_escape "$REASON")
CONFIDENCE_ESCAPED=$(json_escape "$CONFIDENCE")

# Write outcome state
cat > "${STATE_DIR}/session-outcome.json" << EOF
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

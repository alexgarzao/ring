#!/usr/bin/env bash
# Learning extraction hook wrapper
# Calls Python script for SessionEnd learning extraction

set -euo pipefail

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find Python interpreter
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    # Python not available - output minimal JSON response
    echo '{"result": "continue", "error": "Python not available for learning extraction"}'
    exit 0
fi

# Construct input JSON for Stop event (framework doesn't provide stdin)
INPUT_JSON='{"type": "stop"}'

# Pass constructed input to Python script
echo "$INPUT_JSON" | "$PYTHON_CMD" "${SCRIPT_DIR}/learning-extract.py"

#!/usr/bin/env bash
# Integration tests for context-usage-check.sh
# Run: bash default/hooks/tests/test-context-usage.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
HOOK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOOK="${HOOK_DIR}/context-usage-check.sh"

# Resolve /tmp to canonical path (e.g., /private/tmp on macOS)
TMP_DIR="/tmp"
if [[ -L "$TMP_DIR" ]] && [[ -d "$TMP_DIR" ]]; then
    TMP_DIR="$(cd "$TMP_DIR" && pwd -P)"
fi

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test helper
run_test() {
    local name="$1"
    local expected="$2"
    local input="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    # Clean state for test
    rm -f "${TMP_DIR}/context-usage-test-"*.json

    # Run hook with test session ID
    export CLAUDE_SESSION_ID="test-$$"
    export CLAUDE_PROJECT_DIR="/tmp"

    local output
    output=$(echo "$input" | "$HOOK" 2>/dev/null || true)

    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}PASS${NC}: $name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}: $name"
        echo "  Expected to contain: $expected"
        echo "  Got: $output"
    fi

    # Clean up
    rm -f "${TMP_DIR}/context-usage-test-"*.json
}

echo "Running context-usage-check.sh tests..."
echo "========================================"

# Test 1: First prompt returns valid JSON
run_test "First prompt returns valid JSON" \
    "hookSpecificOutput" \
    '{"prompt": "test", "session_id": "test"}'

# Test 2: Hook is fast (<50ms)
echo -n "Testing performance... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-perf-"*.json
export CLAUDE_SESSION_ID="perf-$$"
export CLAUDE_PROJECT_DIR="/tmp"
start=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time() * 1e9))")
echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
end=$(date +%s%N 2>/dev/null || python3 -c "import time; print(int(time.time() * 1e9))")
duration=$(( (end - start) / 1000000 ))  # Convert to ms
if [[ $duration -lt 50 ]]; then
    echo -e "${GREEN}PASS${NC}: Hook executed in ${duration}ms (<50ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}: Hook took ${duration}ms (>50ms)"
fi
rm -f "${TMP_DIR}/context-usage-perf-"*.json

# Test 3: State file is created
echo -n "Testing state file creation... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-state-"*.json
rm -rf "${TMP_DIR}/.ring" 2>/dev/null || true
export CLAUDE_SESSION_ID="state-$$"
export CLAUDE_PROJECT_DIR="/tmp"
echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
# Hook uses TMP_DIR directly when .ring/state doesn't exist
if [[ -f "${TMP_DIR}/context-usage-state-$$.json" ]]; then
    echo -e "${GREEN}PASS${NC}: State file created"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}: State file not found at ${TMP_DIR}/context-usage-state-$$.json"
fi
rm -f "${TMP_DIR}/context-usage-state-"*.json

# Test 4: Turn count increments
echo -n "Testing turn count increment... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-count-"*.json
rm -rf "${TMP_DIR}/.ring" 2>/dev/null || true
export CLAUDE_SESSION_ID="count-$$"
export CLAUDE_PROJECT_DIR="/tmp"

# Run hook 3 times
for _ in {1..3}; do
    echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
done

# Check turn count (hook uses TMP_DIR when .ring/state doesn't exist)
STATE_FILE="${TMP_DIR}/context-usage-count-$$.json"
if [[ -f "$STATE_FILE" ]]; then
    if command -v jq &>/dev/null; then
        count=$(jq -r '.turn_count' "$STATE_FILE")
    else
        count=$(grep -o '"turn_count":[0-9]*' "$STATE_FILE" | grep -o '[0-9]*')
    fi
    if [[ "$count" == "3" ]]; then
        echo -e "${GREEN}PASS${NC}: Turn count is 3 after 3 prompts"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}: Turn count is $count, expected 3"
    fi
else
    echo -e "${RED}FAIL${NC}: State file not found"
fi
rm -f "${TMP_DIR}/context-usage-count-"*.json

# Test 5: Warning deduplication (info tier)
echo -n "Testing warning deduplication... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-dedup-"*.json
rm -rf "${TMP_DIR}/.ring" 2>/dev/null || true
export CLAUDE_SESSION_ID="dedup-$$"
export CLAUDE_PROJECT_DIR="/tmp"

# Create state file at 51% (just over info threshold)
# Note: without .ring/state, hook uses TMP_DIR directly
cat > "${TMP_DIR}/context-usage-dedup-$$.json" <<EOF
{
  "session_id": "dedup-$$",
  "turn_count": 22,
  "estimated_pct": 51,
  "current_tier": "info",
  "acknowledged_tier": "info",
  "updated_at": "2025-01-01T00:00:00Z"
}
EOF

# Run hook - should NOT show warning since info already acknowledged
output=$(echo '{"prompt": "test"}' | "$HOOK" 2>/dev/null || true)
if echo "$output" | grep -q "additionalContext"; then
    echo -e "${RED}FAIL${NC}: Warning shown when tier already acknowledged"
else
    echo -e "${GREEN}PASS${NC}: Warning not repeated for same tier"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
rm -f "${TMP_DIR}/context-usage-dedup-"*.json

# Test 6: Critical always shows
echo -n "Testing critical always shows... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-crit-"*.json
rm -rf "${TMP_DIR}/.ring" 2>/dev/null || true
export CLAUDE_SESSION_ID="crit-$$"
export CLAUDE_PROJECT_DIR="/tmp"

# Create state at high turn count (68 turns = ~85%) with critical already acknowledged
# The hook recalculates tier from turn_count, so we need enough turns to trigger critical
# Formula: pct = (45000 + turns*2500) * 100 / 200000
# For 85%: 170000 = 45000 + turns*2500 => turns = 50
# For 86%: 172000 = 45000 + turns*2500 => turns = 50.8 => 51
cat > "${TMP_DIR}/context-usage-crit-$$.json" <<EOF
{
  "session_id": "crit-$$",
  "turn_count": 50,
  "estimated_pct": 85,
  "current_tier": "critical",
  "acknowledged_tier": "critical",
  "updated_at": "2025-01-01T00:00:00Z"
}
EOF

# Run hook - SHOULD show warning even though critical acknowledged
# After this run, turn_count becomes 51, pct stays at 86% (critical)
output=$(echo '{"prompt": "test"}' | "$HOOK" 2>/dev/null || true)
if echo "$output" | grep -q "additionalContext"; then
    echo -e "${GREEN}PASS${NC}: Critical warning shown even when acknowledged"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}: Critical warning not shown"
fi
rm -f "${TMP_DIR}/context-usage-crit-"*.json

# Test 7: Reset via environment variable
echo -n "Testing reset via env var... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f "${TMP_DIR}/context-usage-reset-"*.json
rm -rf "${TMP_DIR}/.ring" 2>/dev/null || true
export CLAUDE_SESSION_ID="reset-$$"
export CLAUDE_PROJECT_DIR="/tmp"

# Create state file (without .ring/state, hook uses TMP_DIR directly)
cat > "${TMP_DIR}/context-usage-reset-$$.json" <<EOF
{
  "session_id": "reset-$$",
  "turn_count": 10,
  "estimated_pct": 30,
  "current_tier": "none",
  "acknowledged_tier": "info",
  "updated_at": "2025-01-01T00:00:00Z"
}
EOF

# Run with reset env var - this should delete the state file and start fresh
export RING_RESET_CONTEXT_WARNING=1
echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
unset RING_RESET_CONTEXT_WARNING

# Check state was reset (turn count should be 1 now)
STATE_FILE="${TMP_DIR}/context-usage-reset-$$.json"
if [[ -f "$STATE_FILE" ]]; then
    if command -v jq &>/dev/null; then
        count=$(jq -r '.turn_count' "$STATE_FILE")
    else
        count=$(grep -o '"turn_count":[0-9]*' "$STATE_FILE" | grep -o '[0-9]*')
    fi
    if [[ "$count" == "1" ]]; then
        echo -e "${GREEN}PASS${NC}: State reset, turn count is 1"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}FAIL${NC}: Turn count is $count, expected 1 after reset"
    fi
else
    echo -e "${RED}FAIL${NC}: State file not found"
fi
rm -f "${TMP_DIR}/context-usage-reset-"*.json

# Summary
echo "========================================"
echo "Tests: $TESTS_PASSED/$TESTS_RUN passed"

if [[ $TESTS_PASSED -eq $TESTS_RUN ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi

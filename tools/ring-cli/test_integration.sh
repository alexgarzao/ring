#!/usr/bin/env bash
# Integration tests for ring-cli
# Run: ./test_integration.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$SCRIPT_DIR/cli/ring-cli"
DB="$SCRIPT_DIR/ring-index.db"

PASSED=0
FAILED=0

# Test helper functions
pass() {
    echo "  ✓ $1"
    PASSED=$((PASSED + 1))
}

fail() {
    echo "  ✗ $1"
    FAILED=$((FAILED + 1))
}

test_output_contains() {
    local description="$1"
    local output="$2"
    local expected="$3"

    if echo "$output" | grep -q "$expected"; then
        pass "$description"
    else
        fail "$description (expected '$expected')"
    fi
}

test_output_not_contains() {
    local description="$1"
    local output="$2"
    local unexpected="$3"

    if echo "$output" | grep -q "$unexpected"; then
        fail "$description (unexpected '$unexpected')"
    else
        pass "$description"
    fi
}

echo "=== Ring CLI Integration Tests ==="
echo ""

# Verify prerequisites
echo "Prerequisites:"
if [ ! -f "$CLI" ]; then
    echo "  ✗ CLI binary not found. Run ./build.sh first."
    exit 1
fi
pass "CLI binary exists"

if [ ! -f "$DB" ]; then
    echo "  ✗ Database not found. Run ./build.sh first."
    exit 1
fi
pass "Database exists"

# Verify database has content
COUNT=$(sqlite3 "$DB" "SELECT COUNT(*) FROM components")
if [ "$COUNT" -ge 130 ]; then
    pass "Database has $COUNT components (≥130 minimum)"
else
    fail "Database has only $COUNT components (expected ≥130)"
fi

echo ""
echo "Basic Queries:"

# Test 1: Simple search
OUTPUT=$("$CLI" "code review" 2>&1)
test_output_contains "Simple search returns results" "$OUTPUT" "Found.*component"
test_output_contains "Search includes code-reviewer" "$OUTPUT" "code-reviewer"

# Test 2: Type filter - skill
OUTPUT=$("$CLI" --type skill "debugging" 2>&1)
test_output_contains "Skill filter returns results" "$OUTPUT" "SKILL"
test_output_not_contains "Skill filter excludes agents" "$OUTPUT" "\[AGENT\]"

# Test 3: Type filter - agent
OUTPUT=$("$CLI" --type agent "backend" 2>&1)
test_output_contains "Agent filter returns results" "$OUTPUT" "AGENT"
test_output_not_contains "Agent filter excludes skills" "$OUTPUT" "\[SKILL\]"

# Test 4: Type filter - command
OUTPUT=$("$CLI" --type command "review" 2>&1)
test_output_contains "Command filter returns results" "$OUTPUT" "CMD"

# Test 5: JSON output
OUTPUT=$("$CLI" --json "testing" 2>&1)
test_output_contains "JSON output is valid" "$OUTPUT" "\"fqn\""
test_output_contains "JSON has plugin field" "$OUTPUT" "\"plugin\""

# Test 6: Limit flag
OUTPUT=$("$CLI" --limit 2 "code" 2>&1)
RESULT_COUNT=$(echo "$OUTPUT" | grep -c "^\d\." || true)
if [ "$RESULT_COUNT" -le 2 ]; then
    pass "Limit flag restricts results"
else
    fail "Limit flag did not restrict results (got $RESULT_COUNT)"
fi

echo ""
echo "Edge Cases:"

# Test 7: Empty query
OUTPUT=$("$CLI" "" 2>&1 || true)
test_output_contains "Empty query shows tips" "$OUTPUT" "Tips"

# Test 8: Whitespace-only query
OUTPUT=$("$CLI" "   " 2>&1 || true)
test_output_contains "Whitespace query handled" "$OUTPUT" "No components found\|Tips"

# Test 9: FTS5 reserved keywords (OR)
OUTPUT=$("$CLI" 'test OR fail' 2>&1 || true)
test_output_not_contains "OR keyword doesn't cause error" "$OUTPUT" "syntax error"

# Test 10: FTS5 reserved keywords (NOT)
OUTPUT=$("$CLI" 'NOT debugging' 2>&1 || true)
test_output_not_contains "NOT keyword doesn't cause error" "$OUTPUT" "syntax error"
test_output_contains "NOT keyword stripped, 'debugging' searched" "$OUTPUT" "debugging"

# Test 11: Special characters
OUTPUT=$("$CLI" 'test!@#$%^&*()' 2>&1 || true)
test_output_not_contains "Special chars don't cause error" "$OUTPUT" "error"

# Test 12: Leading hyphen (FTS5 NOT injection)
OUTPUT=$("$CLI" '"-test"' 2>&1 || true)
test_output_not_contains "Leading hyphen sanitized" "$OUTPUT" "syntax error"

# Test 13: Very long query
LONG_QUERY=$(printf 'test%.0s ' {1..100})
OUTPUT=$("$CLI" "$LONG_QUERY" 2>&1 || true)
test_output_not_contains "Long query handled" "$OUTPUT" "error"

echo ""
echo "Version and Help:"

# Test 14: Version flag
OUTPUT=$("$CLI" --version 2>&1)
test_output_contains "Version flag works" "$OUTPUT" "ring-cli"

# Test 15: Help flag
OUTPUT=$("$CLI" --help 2>&1 || true)
test_output_contains "Help shows usage" "$OUTPUT" "Usage\|QUERY"

echo ""
echo "=== Results ==="
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

echo ""
echo "All tests passed!"

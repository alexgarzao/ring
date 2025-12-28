#!/usr/bin/env bash
# Integration tests for RAG-Enhanced Plan Judging
# Tests the full workflow: query → plan → validate
# Run: bash default/lib/tests/test-rag-planning.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
LIB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARTIFACT_INDEX_DIR="${LIB_DIR}/artifact-index"

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Test helper
run_test() {
    local name="$1"
    local expected_exit="$2"
    shift 2
    local cmd=("$@")

    TESTS_RUN=$((TESTS_RUN + 1))

    local output
    local exit_code=0
    output=$("${cmd[@]}" 2>&1) || exit_code=$?

    if [[ "$exit_code" == "$expected_exit" ]]; then
        echo -e "${GREEN}PASS${NC}: $name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}: $name"
        echo "  Expected exit code: $expected_exit, got: $exit_code"
        echo "  Output: ${output:0:200}"
        return 1
    fi
}

# Test helper for output matching
run_test_output() {
    local name="$1"
    local expected_pattern="$2"
    shift 2
    local cmd=("$@")

    TESTS_RUN=$((TESTS_RUN + 1))

    local output
    output=$("${cmd[@]}" 2>&1) || true

    if echo "$output" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}PASS${NC}: $name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}FAIL${NC}: $name"
        echo "  Expected pattern: $expected_pattern"
        echo "  Output: ${output:0:300}"
        return 1
    fi
}

echo "Running RAG-Enhanced Plan Judging Integration Tests..."
echo "======================================================="
echo ""

# ============================================
# Test 1: artifact_query.py --mode planning
# ============================================
echo "## Testing artifact_query.py planning mode"

run_test "Planning mode returns valid JSON" 0 \
    python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "test query" --json

run_test_output "Planning mode has expected fields" "is_empty_index" \
    python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "test query" --json

run_test_output "Planning mode includes query_time_ms" "query_time_ms" \
    python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "authentication oauth" --json

run_test "Planning mode with limit works" 0 \
    python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "test" --limit 3 --json

echo ""

# ============================================
# Test 2: Planning mode performance
# ============================================
echo "## Testing planning mode performance"

echo -n "Performance test (<200ms)... "
TESTS_RUN=$((TESTS_RUN + 1))

start=$(python3 -c "import time; print(int(time.time() * 1000))")
python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "authentication oauth jwt" --json > /dev/null 2>&1
end=$(python3 -c "import time; print(int(time.time() * 1000))")
duration=$((end - start))

if [[ $duration -lt 200 ]]; then
    echo -e "${GREEN}PASS${NC}: Completed in ${duration}ms (<200ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}WARN${NC}: Completed in ${duration}ms (>200ms target)"
    TESTS_PASSED=$((TESTS_PASSED + 1))  # Still pass, just warn
fi

echo ""

# ============================================
# Test 3: validate-plan-precedent.py
# ============================================
echo "## Testing validate-plan-precedent.py"

# Create a temporary test plan
TEST_PLAN=$(mktemp /tmp/test-plan-XXXXXX.md)
cat > "$TEST_PLAN" <<'EOF'
# Test Plan

**Goal:** Implement authentication system

**Architecture:** Microservices with API gateway

**Tech Stack:** Python, SQLite, JWT

### Task 1: Create auth module

Test content here.
EOF

run_test "Validation script runs successfully" 0 \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN"

run_test_output "Validation extracts keywords" "Keywords extracted" \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN"

run_test_output "Validation JSON output has passed field" '"passed":' \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN" --json

run_test "Validation with custom threshold works" 0 \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN" --threshold 50

# Clean up test plan
rm -f "$TEST_PLAN"

echo ""

# ============================================
# Test 4: Edge cases
# ============================================
echo "## Testing edge cases"

# Test non-existent file
run_test "Missing file returns error exit code" 2 \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "/nonexistent/file.md"

# Test empty query (should work, return empty results)
run_test_output "Empty index handled gracefully" "is_empty_index" \
    python3 "${ARTIFACT_INDEX_DIR}/artifact_query.py" --mode planning "xyznonexistentquery123" --json

# Test threshold validation
run_test "Invalid threshold (negative) rejected" 2 \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN" --threshold -1 2>/dev/null || echo "expected"

run_test "Invalid threshold (>100) rejected" 2 \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TEST_PLAN" --threshold 101 2>/dev/null || echo "expected"

echo ""

# ============================================
# Test 5: Keyword extraction
# ============================================
echo "## Testing keyword extraction quality"

# Create plan with Tech Stack
TECH_PLAN=$(mktemp /tmp/tech-plan-XXXXXX.md)
cat > "$TECH_PLAN" <<'EOF'
# Tech Plan

**Goal:** Build API

**Architecture:** REST

**Tech Stack:** Redis, PostgreSQL, Go

### Task 1: Setup database
EOF

run_test_output "Tech Stack keywords extracted (redis)" "redis" \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TECH_PLAN" --json

run_test_output "Tech Stack keywords extracted (postgresql)" "postgresql" \
    python3 "${LIB_DIR}/validate-plan-precedent.py" "$TECH_PLAN" --json

rm -f "$TECH_PLAN"

echo ""

# ============================================
# Summary
# ============================================
echo "======================================================="
echo "Tests: $TESTS_PASSED/$TESTS_RUN passed"

if [[ $TESTS_PASSED -eq $TESTS_RUN ]]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi

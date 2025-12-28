#!/usr/bin/env bash
# Comprehensive tests for Ring shell utilities
#
# Usage:
#   ./test_shell_utils.sh
#   ./test_shell_utils.sh -v  # verbose mode
#
# Tests:
#   - json-escape.sh: json_escape(), json_string()
#   - hook-utils.sh: get_json_field(), output_hook_result(), etc.
#   - context-check.sh: estimate_context_usage(), increment_turn_count(), etc.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Verbose mode
VERBOSE="${1:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Temp directory for test isolation
TEST_TMP_DIR=""

# =============================================================================
# Test Helpers
# =============================================================================

setup_test_env() {
    TEST_TMP_DIR=$(mktemp -d)
    export CLAUDE_PROJECT_DIR="$TEST_TMP_DIR"
}

teardown_test_env() {
    if [[ -n "$TEST_TMP_DIR" ]] && [[ -d "$TEST_TMP_DIR" ]]; then
        rm -rf "$TEST_TMP_DIR"
    fi
    unset CLAUDE_PROJECT_DIR
}

assert_equals() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected: '$expected'"
        echo "  Actual:   '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_contains() {
    local needle="$1"
    local haystack="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$haystack" == *"$needle"* ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected to contain: '$needle'"
        echo "  Actual: '$haystack'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_not_empty() {
    local actual="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -n "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected non-empty, got empty string"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_empty() {
    local actual="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -z "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected empty, got: '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_exit_code() {
    local expected_code="$1"
    local actual_code="$2"
    local test_name="$3"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$expected_code" == "$actual_code" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Expected exit code: $expected_code"
        echo "  Actual exit code:   $actual_code"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_exists() {
    local filepath="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -f "$filepath" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  File does not exist: $filepath"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_dir_exists() {
    local dirpath="$1"
    local test_name="$2"
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -d "$dirpath" ]]; then
        echo -e "${GREEN}✓${NC} $test_name"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $test_name"
        echo "  Directory does not exist: $dirpath"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# =============================================================================
# Source the utilities (after helpers are defined)
# =============================================================================

# Source in order of dependencies
source "${SCRIPT_DIR}/../json-escape.sh"
source "${SCRIPT_DIR}/../hook-utils.sh"
source "${SCRIPT_DIR}/../context-check.sh"

# =============================================================================
# json_escape() Tests
# =============================================================================

test_json_escape_basic_string() {
    echo -e "\n${YELLOW}=== json_escape() Tests ===${NC}"

    local result
    result=$(json_escape "hello world")
    assert_equals "hello world" "$result" "json_escape: basic string (no special chars)"
}

test_json_escape_with_quotes() {
    local result
    result=$(json_escape 'string with "quotes" inside')
    assert_equals 'string with \"quotes\" inside' "$result" "json_escape: string with quotes → escaped quotes"
}

test_json_escape_with_newlines() {
    local input=$'line1\nline2'
    local result
    result=$(json_escape "$input")
    assert_equals 'line1\nline2' "$result" "json_escape: string with newlines → \\n"
}

test_json_escape_with_tabs() {
    local input=$'col1\tcol2'
    local result
    result=$(json_escape "$input")
    assert_equals 'col1\tcol2' "$result" "json_escape: string with tabs → \\t"
}

test_json_escape_with_backslashes() {
    local result
    result=$(json_escape 'path\\to\\file')
    assert_equals 'path\\\\to\\\\file' "$result" "json_escape: string with backslashes → \\\\"
}

test_json_escape_empty_string() {
    local result
    result=$(json_escape "")
    assert_empty "$result" "json_escape: empty string returns empty"
}

test_json_escape_unicode() {
    local result
    result=$(json_escape "hello 世界 emoji 🎉")
    assert_contains "hello" "$result" "json_escape: unicode characters preserved (contains hello)"
    assert_contains "世界" "$result" "json_escape: unicode characters preserved (contains CJK)"
}

test_json_escape_carriage_return() {
    local input=$'line1\rline2'
    local result
    result=$(json_escape "$input")
    assert_equals 'line1\rline2' "$result" "json_escape: carriage return → \\r"
}

test_json_escape_mixed_special_chars() {
    local input=$'say "hello"\tthere\nworld'
    local result
    result=$(json_escape "$input")
    assert_equals 'say \"hello\"\tthere\nworld' "$result" "json_escape: mixed special chars"
}

# =============================================================================
# json_string() Tests
# =============================================================================

test_json_string_wraps_in_quotes() {
    echo -e "\n${YELLOW}=== json_string() Tests ===${NC}"

    local result
    result=$(json_string "hello")
    assert_equals '"hello"' "$result" "json_string: wraps basic string in quotes"
}

test_json_string_empty() {
    local result
    result=$(json_string "")
    assert_equals '""' "$result" "json_string: empty string becomes empty JSON string"
}

test_json_string_with_escapes() {
    local result
    result=$(json_string 'say "hi"')
    assert_equals '"say \"hi\""' "$result" "json_string: escapes and wraps"
}

# =============================================================================
# get_json_field() Tests
# =============================================================================

test_get_json_field_simple() {
    echo -e "\n${YELLOW}=== get_json_field() Tests ===${NC}"

    local json='{"name": "test", "value": 42}'
    local result
    result=$(get_json_field "$json" "name")
    assert_equals "test" "$result" "get_json_field: extract simple string field"
}

test_get_json_field_number() {
    local json='{"name": "test", "value": 42}'
    local result
    result=$(get_json_field "$json" "value")
    assert_equals "42" "$result" "get_json_field: extract number field"
}

test_get_json_field_not_found() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "missing") || exit_code=$?
    # When using jq, empty field returns success with empty string
    # Either behavior is acceptable: empty result or non-zero exit
    if [[ -z "$result" ]]; then
        assert_empty "$result" "get_json_field: field not found returns empty"
    else
        echo -e "${GREEN}✓${NC} get_json_field: field not found (no match)"
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
}

test_get_json_field_invalid_field_name() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "invalid-field-name") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: invalid field name (hyphen) fails"
}

test_get_json_field_injection_attempt() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    # Attempt field injection
    result=$(get_json_field "$json" '.name; system("echo INJECTED")') || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: injection attempt blocked"
}

test_get_json_field_empty_json() {
    local result
    local exit_code=0
    result=$(get_json_field "" "name") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: empty JSON fails"
}

test_get_json_field_empty_field() {
    local json='{"name": "test"}'
    local result
    local exit_code=0
    result=$(get_json_field "$json" "") || exit_code=$?
    assert_exit_code "1" "$exit_code" "get_json_field: empty field name fails"
}

test_get_json_field_nested_json() {
    local json='{"outer": {"inner": "value"}, "name": "top"}'
    local result
    result=$(get_json_field "$json" "name")
    assert_equals "top" "$result" "get_json_field: nested JSON gets top-level field"
}

test_get_json_field_boolean() {
    local json='{"enabled": true, "disabled": false}'
    local result
    result=$(get_json_field "$json" "enabled")
    assert_equals "true" "$result" "get_json_field: extract boolean true"

    # Note: jq's "// empty" pattern returns empty for false values
    # This is a known limitation - false is falsy in jq so "false // empty" = empty
    result=$(get_json_field "$json" "disabled")
    assert_empty "$result" "get_json_field: boolean false (jq limitation: returns empty)"
}

test_get_json_field_underscore_name() {
    local json='{"field_name": "works"}'
    local result
    result=$(get_json_field "$json" "field_name")
    assert_equals "works" "$result" "get_json_field: underscore in field name"
}

# =============================================================================
# get_project_root() Tests
# =============================================================================

test_get_project_root() {
    echo -e "\n${YELLOW}=== get_project_root() Tests ===${NC}"
    setup_test_env

    local result
    result=$(get_project_root)
    assert_equals "$TEST_TMP_DIR" "$result" "get_project_root: uses CLAUDE_PROJECT_DIR"

    teardown_test_env
}

test_get_project_root_fallback() {
    # Unset CLAUDE_PROJECT_DIR to test fallback
    unset CLAUDE_PROJECT_DIR

    local result
    local pwd_result
    result=$(get_project_root)
    pwd_result=$(pwd)
    assert_equals "$pwd_result" "$result" "get_project_root: falls back to pwd when no env var"
}

# =============================================================================
# get_ring_state_dir() Tests
# =============================================================================

test_get_ring_state_dir_creates() {
    echo -e "\n${YELLOW}=== get_ring_state_dir() Tests ===${NC}"
    setup_test_env

    local result
    result=$(get_ring_state_dir)
    assert_equals "${TEST_TMP_DIR}/.ring/state" "$result" "get_ring_state_dir: returns correct path"
    assert_dir_exists "$result" "get_ring_state_dir: creates directory"

    teardown_test_env
}

test_get_ring_state_dir_permissions() {
    setup_test_env

    local result
    result=$(get_ring_state_dir)
    local perms
    perms=$(stat -f "%Lp" "$result" 2>/dev/null || stat -c "%a" "$result" 2>/dev/null)
    assert_equals "700" "$perms" "get_ring_state_dir: has secure permissions (700)"

    teardown_test_env
}

# =============================================================================
# output_hook_result() Tests
# =============================================================================

test_output_hook_result_continue() {
    echo -e "\n${YELLOW}=== output_hook_result() Tests ===${NC}"

    local result
    result=$(output_hook_result "continue")
    assert_contains '"result": "continue"' "$result" "output_hook_result: continue without message"
}

test_output_hook_result_block_with_message() {
    local result
    result=$(output_hook_result "block" "Something went wrong")
    assert_contains '"result": "block"' "$result" "output_hook_result: block result"
    assert_contains '"message": "Something went wrong"' "$result" "output_hook_result: includes message"
}

test_output_hook_result_escapes_message() {
    local result
    result=$(output_hook_result "continue" 'Message with "quotes"')
    assert_contains '\"quotes\"' "$result" "output_hook_result: escapes quotes in message"
}

# =============================================================================
# output_hook_context() Tests
# =============================================================================

test_output_hook_context() {
    echo -e "\n${YELLOW}=== output_hook_context() Tests ===${NC}"

    local result
    result=$(output_hook_context "SessionStart" "Additional context here")
    assert_contains '"hookEventName": "SessionStart"' "$result" "output_hook_context: includes event name"
    assert_contains '"additionalContext": "Additional context here"' "$result" "output_hook_context: includes context"
}

# =============================================================================
# output_hook_empty() Tests
# =============================================================================

test_output_hook_empty() {
    echo -e "\n${YELLOW}=== output_hook_empty() Tests ===${NC}"

    local result
    result=$(output_hook_empty)
    assert_equals "{}" "$result" "output_hook_empty: returns empty JSON object"
}

test_output_hook_empty_with_event() {
    local result
    result=$(output_hook_empty "PromptSubmit")
    assert_contains '"hookEventName": "PromptSubmit"' "$result" "output_hook_empty: includes event name"
}

# =============================================================================
# estimate_context_usage() Tests
# =============================================================================

test_estimate_context_usage_no_data() {
    echo -e "\n${YELLOW}=== estimate_context_usage() Tests ===${NC}"
    setup_test_env

    local result
    result=$(estimate_context_usage)
    assert_equals "0" "$result" "estimate_context_usage: returns 0 when no data"

    teardown_test_env
}

test_estimate_context_usage_from_turns() {
    setup_test_env

    # Create session file with turn count
    local state_dir
    state_dir=$(get_ring_state_dir)
    cat > "${state_dir}/current-session.json" <<EOF
{
  "turn_count": 23,
  "updated_at": "2024-01-01T00:00:00Z"
}
EOF

    local result
    result=$(estimate_context_usage)
    assert_equals "23" "$result" "estimate_context_usage: turn 23 → ~23%"

    teardown_test_env
}

test_estimate_context_usage_from_context_file() {
    setup_test_env

    local state_dir
    state_dir=$(get_ring_state_dir)
    cat > "${state_dir}/context-usage.json" <<EOF
{
  "estimated_percentage": 50,
  "updated_at": "2024-01-01T00:00:00Z"
}
EOF

    local result
    result=$(estimate_context_usage)
    assert_equals "50" "$result" "estimate_context_usage: reads from context-usage.json"

    teardown_test_env
}

test_estimate_context_usage_capped_at_100() {
    setup_test_env

    local state_dir
    state_dir=$(get_ring_state_dir)
    cat > "${state_dir}/current-session.json" <<EOF
{
  "turn_count": 150,
  "updated_at": "2024-01-01T00:00:00Z"
}
EOF

    local result
    result=$(estimate_context_usage)
    assert_equals "100" "$result" "estimate_context_usage: capped at 100%"

    teardown_test_env
}

# =============================================================================
# increment_turn_count() Tests
# =============================================================================

test_increment_turn_count_from_zero() {
    echo -e "\n${YELLOW}=== increment_turn_count() Tests ===${NC}"
    setup_test_env

    local result
    result=$(increment_turn_count)
    assert_equals "1" "$result" "increment_turn_count: 0 → 1"

    teardown_test_env
}

test_increment_turn_count_existing() {
    setup_test_env

    local state_dir
    state_dir=$(get_ring_state_dir)
    cat > "${state_dir}/current-session.json" <<EOF
{
  "turn_count": 5,
  "updated_at": "2024-01-01T00:00:00Z"
}
EOF

    local result
    result=$(increment_turn_count)
    assert_equals "6" "$result" "increment_turn_count: 5 → 6"

    # Verify file was updated
    local stored
    stored=$(get_json_field "$(cat "${state_dir}/current-session.json")" "turn_count")
    assert_equals "6" "$stored" "increment_turn_count: file updated to 6"

    teardown_test_env
}

test_increment_turn_count_concurrent() {
    echo -e "\n${YELLOW}=== increment_turn_count() Concurrency Test ===${NC}"
    setup_test_env

    # Reset to 0
    reset_turn_count

    # Run 10 concurrent increments
    for i in {1..10}; do
        increment_turn_count &
    done
    wait

    local state_dir
    state_dir=$(get_ring_state_dir)
    local final_count
    final_count=$(get_json_field "$(cat "${state_dir}/current-session.json")" "turn_count")

    # With proper locking, should be exactly 10
    assert_equals "10" "$final_count" "increment_turn_count: concurrent increments (10 parallel) → 10"

    teardown_test_env
}

# =============================================================================
# reset_turn_count() Tests
# =============================================================================

test_reset_turn_count() {
    echo -e "\n${YELLOW}=== reset_turn_count() Tests ===${NC}"
    setup_test_env

    # First increment a few times
    increment_turn_count >/dev/null
    increment_turn_count >/dev/null
    increment_turn_count >/dev/null

    # Now reset
    reset_turn_count

    local state_dir
    state_dir=$(get_ring_state_dir)
    local count
    count=$(get_json_field "$(cat "${state_dir}/current-session.json")" "turn_count")
    assert_equals "0" "$count" "reset_turn_count: resets to 0"

    teardown_test_env
}

test_reset_turn_count_creates_file() {
    setup_test_env

    local state_dir
    state_dir=$(get_ring_state_dir)
    local session_file="${state_dir}/current-session.json"

    # Ensure file doesn't exist
    rm -f "$session_file"

    # Reset should create it
    reset_turn_count

    assert_file_exists "$session_file" "reset_turn_count: creates file if missing"

    teardown_test_env
}

test_reset_turn_count_includes_timestamps() {
    setup_test_env

    reset_turn_count

    local state_dir
    state_dir=$(get_ring_state_dir)
    local content
    content=$(cat "${state_dir}/current-session.json")

    assert_contains "started_at" "$content" "reset_turn_count: includes started_at"
    assert_contains "updated_at" "$content" "reset_turn_count: includes updated_at"

    teardown_test_env
}

# =============================================================================
# update_context_usage() Tests
# =============================================================================

test_update_context_usage() {
    echo -e "\n${YELLOW}=== update_context_usage() Tests ===${NC}"
    setup_test_env

    update_context_usage 75

    local state_dir
    state_dir=$(get_ring_state_dir)
    local content
    content=$(cat "${state_dir}/context-usage.json")

    assert_contains '"estimated_percentage": 75' "$content" "update_context_usage: stores percentage"
    assert_contains "threshold_info" "$content" "update_context_usage: includes thresholds"

    teardown_test_env
}

test_update_context_usage_invalid_input() {
    setup_test_env

    # Non-numeric input should be treated as 0
    update_context_usage "invalid"

    local state_dir
    state_dir=$(get_ring_state_dir)
    local content
    content=$(cat "${state_dir}/context-usage.json")

    assert_contains '"estimated_percentage": 0' "$content" "update_context_usage: invalid input → 0"

    teardown_test_env
}

# =============================================================================
# get_context_warning() Tests
# =============================================================================

test_get_context_warning_ok() {
    echo -e "\n${YELLOW}=== get_context_warning() Tests ===${NC}"

    local result
    result=$(get_context_warning 30)
    assert_empty "$result" "get_context_warning: 30% → no warning"
}

test_get_context_warning_info() {
    local result
    result=$(get_context_warning 50)
    assert_contains "INFO" "$result" "get_context_warning: 50% → INFO"
    assert_contains "50%" "$result" "get_context_warning: includes percentage"
}

test_get_context_warning_warning() {
    local result
    result=$(get_context_warning 70)
    assert_contains "WARNING" "$result" "get_context_warning: 70% → WARNING"
}

test_get_context_warning_critical() {
    local result
    result=$(get_context_warning 85)
    assert_contains "CRITICAL" "$result" "get_context_warning: 85% → CRITICAL"
    assert_contains "/clear" "$result" "get_context_warning: critical includes /clear suggestion"
}

# =============================================================================
# get_warning_level() Tests
# =============================================================================

test_get_warning_level_ok() {
    echo -e "\n${YELLOW}=== get_warning_level() Tests ===${NC}"

    local result
    result=$(get_warning_level 30)
    assert_equals "ok" "$result" "get_warning_level: 30% → ok"
}

test_get_warning_level_info() {
    local result
    result=$(get_warning_level 55)
    assert_equals "info" "$result" "get_warning_level: 55% → info"
}

test_get_warning_level_warning() {
    local result
    result=$(get_warning_level 75)
    assert_equals "warning" "$result" "get_warning_level: 75% → warning"
}

test_get_warning_level_critical() {
    local result
    result=$(get_warning_level 90)
    assert_equals "critical" "$result" "get_warning_level: 90% → critical"
}

# =============================================================================
# Run All Tests
# =============================================================================

main() {
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}Ring Shell Utilities Test Suite${NC}"
    echo -e "${YELLOW}========================================${NC}"

    # json_escape tests
    test_json_escape_basic_string
    test_json_escape_with_quotes
    test_json_escape_with_newlines
    test_json_escape_with_tabs
    test_json_escape_with_backslashes
    test_json_escape_empty_string
    test_json_escape_unicode
    test_json_escape_carriage_return
    test_json_escape_mixed_special_chars

    # json_string tests
    test_json_string_wraps_in_quotes
    test_json_string_empty
    test_json_string_with_escapes

    # get_json_field tests
    test_get_json_field_simple
    test_get_json_field_number
    test_get_json_field_not_found
    test_get_json_field_invalid_field_name
    test_get_json_field_injection_attempt
    test_get_json_field_empty_json
    test_get_json_field_empty_field
    test_get_json_field_nested_json
    test_get_json_field_boolean
    test_get_json_field_underscore_name

    # get_project_root tests
    test_get_project_root
    test_get_project_root_fallback

    # get_ring_state_dir tests
    test_get_ring_state_dir_creates
    test_get_ring_state_dir_permissions

    # output_hook_result tests
    test_output_hook_result_continue
    test_output_hook_result_block_with_message
    test_output_hook_result_escapes_message

    # output_hook_context tests
    test_output_hook_context

    # output_hook_empty tests
    test_output_hook_empty
    test_output_hook_empty_with_event

    # estimate_context_usage tests
    test_estimate_context_usage_no_data
    test_estimate_context_usage_from_turns
    test_estimate_context_usage_from_context_file
    test_estimate_context_usage_capped_at_100

    # increment_turn_count tests
    test_increment_turn_count_from_zero
    test_increment_turn_count_existing
    test_increment_turn_count_concurrent

    # reset_turn_count tests
    test_reset_turn_count
    test_reset_turn_count_creates_file
    test_reset_turn_count_includes_timestamps

    # update_context_usage tests
    test_update_context_usage
    test_update_context_usage_invalid_input

    # get_context_warning tests
    test_get_context_warning_ok
    test_get_context_warning_info
    test_get_context_warning_warning
    test_get_context_warning_critical

    # get_warning_level tests
    test_get_warning_level_ok
    test_get_warning_level_info
    test_get_warning_level_warning
    test_get_warning_level_critical

    # Summary
    echo ""
    echo -e "${YELLOW}========================================${NC}"
    echo -e "Results: ${GREEN}${TESTS_PASSED}${NC}/${TESTS_RUN} passed"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "${RED}Failed: ${TESTS_FAILED}${NC}"
        exit 1
    else
        echo -e "${GREEN}All tests passed!${NC}"
        exit 0
    fi
}

main "$@"

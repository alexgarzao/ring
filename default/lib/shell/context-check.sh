#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Context usage estimation utilities for Ring hooks
#
# Usage:
#   source /path/to/context-check.sh
#   percentage=$(estimate_context_usage)
#   warning=$(get_context_warning "$percentage")
#
# Context estimation approach:
#   - Claude Code's context window is ~200K tokens
#   - We estimate usage from session state files
#   - Conservative estimates to warn early

set -euo pipefail

# Determine script location and source dependencies
CONTEXT_CHECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source hook-utils if not already sourced
if ! declare -f get_ring_state_dir &>/dev/null; then
    # shellcheck source=hook-utils.sh
    source "${CONTEXT_CHECK_DIR}/hook-utils.sh"
fi

# Approximate context window size (tokens)
# Claude's actual limit is ~200K, we use conservative estimate
readonly CONTEXT_WINDOW_TOKENS=200000

# Warning thresholds
readonly THRESHOLD_INFO=50
readonly THRESHOLD_WARNING=70
readonly THRESHOLD_CRITICAL=85

# Estimate context usage percentage
# Returns: integer 0-100 representing estimated usage percentage
estimate_context_usage() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local usage_file="${state_dir}/context-usage.json"

    # Check if context-usage.json exists and has recent data
    if [[ -f "$usage_file" ]]; then
        local estimated
        estimated=$(get_json_field "$(cat "$usage_file")" "estimated_percentage" 2>/dev/null || echo "")
        if [[ -n "$estimated" ]] && [[ "$estimated" =~ ^[0-9]+$ ]]; then
            printf '%s' "$estimated"
            return 0
        fi
    fi

    # Fallback: estimate from conversation turn count in state file
    local session_file="${state_dir}/current-session.json"
    if [[ -f "$session_file" ]]; then
        local turns
        turns=$(get_json_field "$(cat "$session_file")" "turn_count" 2>/dev/null || echo "0")

        # Rough estimate: ~2000 tokens per turn average
        # 200K context / 2000 tokens = 100 turns for full context
        # So: percentage = turns (since 100 turns = 100%)
        if [[ "$turns" =~ ^[0-9]+$ ]]; then
            local percentage=$turns  # 1 turn = 1%, 100 turns = 100%
            if [[ $percentage -gt 100 ]]; then
                percentage=100
            fi
            printf '%s' "$percentage"
            return 0
        fi
    fi

    # No data available, return 0 (unknown)
    printf '0'
}

# Update context usage estimate
# Args: $1 - estimated percentage (0-100)
update_context_usage() {
    local percentage="${1:-0}"

    # Validate numeric input (security: prevent injection)
    if ! [[ "$percentage" =~ ^[0-9]+$ ]]; then
        percentage=0
    fi

    local state_dir
    state_dir=$(get_ring_state_dir)
    local usage_file="${state_dir}/context-usage.json"
    local temp_file="${usage_file}.tmp.$$"

    # Get current timestamp
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Atomic write: write to temp file then rename
    cat > "$temp_file" <<EOF
{
  "estimated_percentage": ${percentage},
  "updated_at": "${timestamp}",
  "threshold_info": ${THRESHOLD_INFO},
  "threshold_warning": ${THRESHOLD_WARNING},
  "threshold_critical": ${THRESHOLD_CRITICAL}
}
EOF
    mv "$temp_file" "$usage_file"
}

# Increment turn count in session state (with atomic write and file locking)
increment_turn_count() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local session_file="${state_dir}/current-session.json"
    local lock_file="${session_file}.lock"

    # Use flock for atomic read-modify-write
    (
        flock -x 200 || return 1

        local temp_file="${session_file}.tmp.$$"
        local turn_count=0
        if [[ -f "$session_file" ]]; then
            turn_count=$(get_json_field "$(cat "$session_file")" "turn_count" 2>/dev/null || echo "0")
            if ! [[ "$turn_count" =~ ^[0-9]+$ ]]; then
                turn_count=0
            fi
        fi

        turn_count=$((turn_count + 1))

        local timestamp
        timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # Atomic write: write to temp file then rename
        cat > "$temp_file" <<EOF
{
  "turn_count": ${turn_count},
  "updated_at": "${timestamp}"
}
EOF
        mv "$temp_file" "$session_file"

        printf '%s' "$turn_count"
    ) 200>"$lock_file"
}

# Reset turn count (call on session start, with atomic write)
reset_turn_count() {
    local state_dir
    state_dir=$(get_ring_state_dir)
    local session_file="${state_dir}/current-session.json"
    local temp_file="${session_file}.tmp.$$"

    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Atomic write: write to temp file then rename
    cat > "$temp_file" <<EOF
{
  "turn_count": 0,
  "started_at": "${timestamp}",
  "updated_at": "${timestamp}"
}
EOF
    mv "$temp_file" "$session_file"
}

# Get context warning message for a given percentage
# Args: $1 - percentage (0-100)
# Returns: warning message or empty string
get_context_warning() {
    local percentage="${1:-0}"

    if [[ $percentage -ge $THRESHOLD_CRITICAL ]]; then
        printf 'CRITICAL: Context at %d%%. MUST run /clear with ledger save NOW or risk losing work.' "$percentage"
    elif [[ $percentage -ge $THRESHOLD_WARNING ]]; then
        printf 'WARNING: Context at %d%%. Recommend running /clear with ledger save soon.' "$percentage"
    elif [[ $percentage -ge $THRESHOLD_INFO ]]; then
        printf 'INFO: Context at %d%%. Consider summarizing or preparing ledger.' "$percentage"
    else
        # No warning needed
        printf ''
    fi
}

# Get warning severity level
# Args: $1 - percentage (0-100)
# Returns: "critical", "warning", "info", or "ok"
get_warning_level() {
    local percentage="${1:-0}"

    if [[ $percentage -ge $THRESHOLD_CRITICAL ]]; then
        printf 'critical'
    elif [[ $percentage -ge $THRESHOLD_WARNING ]]; then
        printf 'warning'
    elif [[ $percentage -ge $THRESHOLD_INFO ]]; then
        printf 'info'
    else
        printf 'ok'
    fi
}

# Export functions for subshells
export -f estimate_context_usage 2>/dev/null || true
export -f update_context_usage 2>/dev/null || true
export -f increment_turn_count 2>/dev/null || true
export -f reset_turn_count 2>/dev/null || true
export -f get_context_warning 2>/dev/null || true
export -f get_warning_level 2>/dev/null || true

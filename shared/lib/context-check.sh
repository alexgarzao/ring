#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Shared context estimation utilities for Ring hooks
# Usage: source this file, then call estimate_context_pct

# Constants for estimation
# These are conservative estimates based on typical usage patterns
readonly TOKENS_PER_TURN=2500        # Average tokens per conversation turn
readonly BASE_SYSTEM_OVERHEAD=45000  # System prompt, tools, etc.
readonly DEFAULT_CONTEXT_SIZE=200000 # Claude's typical context window

# Estimate context usage percentage based on turn count
# Args: $1 = turn_count (required)
# Returns: Estimated percentage (0-100)
estimate_context_pct() {
    local turn_count="${1:-0}"
    local context_size="${2:-$DEFAULT_CONTEXT_SIZE}"

    # Estimate: system overhead + (turns * tokens_per_turn)
    local estimated_tokens=$((BASE_SYSTEM_OVERHEAD + (turn_count * TOKENS_PER_TURN)))

    # Calculate percentage (integer math)
    local pct=$((estimated_tokens * 100 / context_size))

    # Cap at 100%
    if [[ "$pct" -gt 100 ]]; then
        pct=100
    fi

    echo "$pct"
}

# Get warning tier based on percentage
# Args: $1 = percentage (required)
# Returns: "none", "info", "warning", or "critical"
get_warning_tier() {
    local pct="${1:-0}"

    if [[ "$pct" -ge 85 ]]; then
        echo "critical"
    elif [[ "$pct" -ge 70 ]]; then
        echo "warning"
    elif [[ "$pct" -ge 50 ]]; then
        echo "info"
    else
        echo "none"
    fi
}

# Get warning message for a tier
# Args: $1 = tier (required), $2 = percentage (required)
# Returns: Warning message string or empty
get_warning_message() {
    local tier="$1"
    local pct="$2"

    case "$tier" in
        critical)
            echo "CONTEXT CRITICAL: ${pct}% - MUST create handoff/ledger and /clear soon to avoid losing work!"
            ;;
        warning)
            echo "Context Warning: ${pct}% - Recommend creating a continuity ledger or handoff document soon."
            ;;
        info)
            echo "Context at ${pct}%. Consider summarizing progress when you reach a stopping point."
            ;;
        *)
            echo ""
            ;;
    esac
}

# Format a context warning block for injection
# Args: $1 = tier (required), $2 = percentage (required)
# Returns: Formatted warning block or empty
format_context_warning() {
    local tier="$1"
    local pct="$2"
    local message
    message=$(get_warning_message "$tier" "$pct")

    if [[ -z "$message" ]]; then
        echo ""
        return
    fi

    local icon
    case "$tier" in
        critical)
            icon="[!!!]"
            ;;
        warning)
            icon="[!!]"
            ;;
        info)
            icon="[i]"
            ;;
        *)
            icon=""
            ;;
    esac

    # Format based on severity
    if [[ "$tier" == "critical" ]]; then
        cat <<EOF
<context-warning severity="critical">
$icon $message

Recommended actions:
1. Run /create-handoff to save current progress
2. Run /clear to reset context
3. Session state will auto-restore from ledger

Current turn count indicates approaching context limit.
</context-warning>
EOF
    elif [[ "$tier" == "warning" ]]; then
        cat <<EOF
<context-warning severity="warning">
$icon $message

Suggested: /create-handoff to save state before clearing.
</context-warning>
EOF
    else
        cat <<EOF
<context-warning severity="info">
$icon $message
</context-warning>
EOF
    fi
}

# Export for subshells
export -f estimate_context_pct 2>/dev/null || true
export -f get_warning_tier 2>/dev/null || true
export -f get_warning_message 2>/dev/null || true
export -f format_context_warning 2>/dev/null || true

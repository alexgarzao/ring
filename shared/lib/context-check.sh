#!/usr/bin/env bash
# =============================================================================
# STATELESS Context Check Utilities
# =============================================================================
# PURPOSE: Pure functions for context estimation without file I/O
#
# USE THIS WHEN:
#   - You need quick context percentage calculations
#   - You need warning tier lookups without state
#   - You're building UI/display components
#
# DO NOT USE FOR:
#   - Tracking turn counts (use default/lib/shell/context-check.sh)
#   - Persisting state across invocations
#
# KEY FUNCTIONS:
#   - estimate_context_pct()    - Calculate % from turn count (pure function)
#   - get_warning_tier()        - Get tier name from percentage (pure function)
#   - format_context_warning()  - Format user-facing warning message
#
# FORMULA:
#   estimated_tokens = 45000 + (turn_count * 2500)
#   percentage = estimated_tokens * 100 / context_size
#
# TIERS (4 levels):
#   - none:     0-49%   (safe, no warning)
#   - info:     50-69%  (informational notice)
#   - warning:  70-84%  (recommend handoff/ledger)
#   - critical: 85%+    (mandatory action required)
# =============================================================================
# shellcheck disable=SC2034  # Unused variables OK for exported config

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

# Wrap message in MANDATORY-USER-MESSAGE tags for critical actions
# Args: $1 = message content (required)
# Returns: Message wrapped in mandatory tags
wrap_mandatory_message() {
    local message="$1"
    cat <<EOF
<MANDATORY-USER-MESSAGE>
$message
</MANDATORY-USER-MESSAGE>
EOF
}

# Format a context warning block for injection
# Args: $1 = tier (required), $2 = percentage (required)
# Returns: Formatted warning block or empty
# BEHAVIOR:
#   - critical (85%+): MANDATORY-USER-MESSAGE requiring STOP + ledger + handoff + /clear
#   - warning (70-84%): MANDATORY-USER-MESSAGE requiring ledger creation
#   - info (50-69%): Simple context-warning XML tag (no mandatory)
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

    # Format based on severity - MANDATORY tags at warning+ tiers
    if [[ "$tier" == "critical" ]]; then
        # Critical: MANDATORY message requiring immediate action
        local critical_content
        critical_content=$(cat <<INNER
$icon CONTEXT CRITICAL: ${pct}% usage (from session data).

**MANDATORY ACTIONS:**
1. STOP current task immediately
2. Run /create-handoff to save progress NOW
3. Create continuity-ledger with current state
4. Run /clear to reset context
5. Resume from handoff in new session

**Verify with /context if needed.**
INNER
)
        wrap_mandatory_message "$critical_content"
    elif [[ "$tier" == "warning" ]]; then
        # Warning: MANDATORY message requiring ledger creation
        local warning_content
        warning_content=$(cat <<INNER
$icon Context Warning: ${pct}% usage (from session data).

**RECOMMENDED ACTIONS:**
- Create a continuity-ledger to preserve session state
- Run: /create-handoff or manually create ledger

**Recommended:** Complete current task, then /clear before starting new work.
INNER
)
        wrap_mandatory_message "$warning_content"
    else
        # Info: Simple warning, no mandatory tags
        cat <<EOF
<context-warning severity="info">
$icon Context at ${pct}%.
</context-warning>
EOF
    fi
}

# Export for subshells
export -f estimate_context_pct 2>/dev/null || true
export -f get_warning_tier 2>/dev/null || true
export -f get_warning_message 2>/dev/null || true
export -f wrap_mandatory_message 2>/dev/null || true
export -f format_context_warning 2>/dev/null || true

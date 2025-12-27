# Context Usage Warnings Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Implement a UserPromptSubmit hook that monitors estimated context usage and injects tiered warnings to help users manage context proactively before hitting limits.

**Architecture:** A lightweight bash hook that estimates context usage from available signals (turn count, cumulative tool output), writes state to `.ring/state/context-usage.json`, and injects tiered warnings (50%/70%/85%) into the conversation via `additionalContext`.

**Tech Stack:**
- Bash shell script (hook implementation)
- JSON (state files, hook configuration)
- jq (JSON manipulation, optional but recommended)

**Global Prerequisites:**
- Environment: macOS/Linux, Bash 4.0+
- Tools: `bash --version` (4.0+), optionally `jq --version` (1.6+)
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
bash --version        # Expected: GNU bash, version 4.x+ or 5.x+
jq --version          # Expected: jq-1.6+ (optional but recommended)
git status            # Expected: clean working tree on main
ls -la default/hooks/ # Expected: hooks.json, session-start.sh, etc.
```

---

## Architecture Overview

```
UserPromptSubmit Hook Flow
==========================

User submits prompt
        |
        v
+------------------+
| context-usage-   |
| check.sh fires   |
+------------------+
        |
        v
+------------------+
| Read state from  |
| .ring/state/     |
| context-usage.   |
| json             |
+------------------+
        |
        v
+------------------+
| Increment turn   |
| count, estimate  |
| context %        |
+------------------+
        |
        v
+------------------+
| Write updated    |
| state back       |
+------------------+
        |
        v
+------------------+
| If % >= threshold|
| inject warning   |
| into response    |
+------------------+
        |
        v
Output JSON with additionalContext (if warning needed)
```

**Warning Tiers:**
| Threshold | Level | Message | Action |
|-----------|-------|---------|--------|
| 50% | Informational | Context at 50%, consider summarizing soon | User awareness |
| 70% | Warning | Context at 70%, recommend creating ledger | Prompt to prepare |
| 85% | Critical | Context at 85%, MUST clear soon | Urgent action |

---

## Task 1: Create .ring Directory Structure

**Files:**
- Create: `$PROJECT_ROOT/.ring/state/` (directory)

**Prerequisites:**
- None (first task)

**Step 1: Create the .ring directory structure**

Create the directory that will hold Ring state files. This is created in the project root, not in the plugin directory.

```bash
# Note: This script creates directories. Users run this in their project.
# The hook will also auto-create if missing.
mkdir -p .ring/state
```

**Expected output:**
```
(no output on success)
```

**Step 2: Verify the directory was created**

Run: `ls -la .ring/`

**Expected output:**
```
total 0
drwxr-xr-x  3 user  group  96 Dec 27 10:00 .
drwxr-xr-x 10 user  group 320 Dec 27 10:00 ..
drwxr-xr-x  2 user  group  64 Dec 27 10:00 state
```

**Step 3: Add .ring to .gitignore (if not already present)**

Check if `.ring/` is in the project's `.gitignore`. The `.ring/` directory contains session-specific state and should not be committed.

Run: `grep -q '\.ring/' .gitignore 2>/dev/null || echo '.ring/' >> .gitignore`

**Note:** This step applies to user projects, not to the Ring plugin itself. The hook documentation should mention this.

**If Task Fails:**

1. **Permission denied:**
   - Check: Do you have write access to project root?
   - Fix: Run with appropriate permissions
   - Rollback: N/A (no changes to undo)

2. **Directory already exists:**
   - This is fine - proceed to next task
   - The `-p` flag handles this case

---

## Task 2: Create Shared Context Check Library

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`

**Prerequisites:**
- None (standalone utility)

**Step 1: Write the context estimation library**

This shared library provides context estimation utilities that can be used by hooks.

```bash
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

Suggested: /continuity-ledger to save state before clearing.
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
```

**Step 2: Verify the file was created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`

**Expected output:**
```
-rw-r--r--  1 user  group  XXXX Dec 27 10:05 /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh
```

**Step 3: Make the file executable (for testing)**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`

**Step 4: Test the library functions**

Run:
```bash
source /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh
estimate_context_pct 10
get_warning_tier 75
```

**Expected output:**
```
35
warning
```

**Step 5: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh
git commit -m "feat(context-warnings): add shared context estimation library"
```

**If Task Fails:**

1. **Source command fails:**
   - Check: Bash version with `bash --version`
   - Fix: Ensure Bash 4.0+ is installed
   - Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`

2. **Math calculations wrong:**
   - Check: Test with known values
   - Fix: Verify integer arithmetic syntax
   - Rollback: `git checkout -- shared/lib/context-check.sh`

---

## Task 3: Create the Context Usage Check Hook

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Prerequisites:**
- Task 2 completed (context-check.sh library)
- Files must exist: `/Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`, `/Users/fredamaral/repos/lerianstudio/ring/shared/lib/json-escape.sh`

**Step 1: Write the UserPromptSubmit hook**

```bash
#!/usr/bin/env bash
# shellcheck disable=SC2034  # Unused variables OK for exported config
# Context Usage Check - UserPromptSubmit hook
# Estimates context usage and injects tiered warnings
# Performance target: <50ms execution time

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MONOREPO_ROOT="$(cd "${PLUGIN_ROOT}/.." && pwd)"

# Session identification
# CLAUDE_SESSION_ID is provided by Claude Code, fallback to PPID for session isolation
SESSION_ID="${CLAUDE_SESSION_ID:-$PPID}"

# State file location - use project's .ring/state/ if available, else /tmp
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
if [[ -d "${PROJECT_DIR}/.ring/state" ]]; then
    STATE_DIR="${PROJECT_DIR}/.ring/state"
else
    # Fallback to /tmp for projects without .ring/ initialized
    STATE_DIR="/tmp"
fi
STATE_FILE="${STATE_DIR}/context-usage-${SESSION_ID}.json"

# Source shared libraries
SHARED_LIB="${MONOREPO_ROOT}/shared/lib"
if [[ -f "${SHARED_LIB}/context-check.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/context-check.sh"
else
    # Fallback: inline minimal estimation
    estimate_context_pct() {
        local turn_count="${1:-0}"
        local pct=$((22 + (turn_count * 1)))  # Very rough estimate
        [[ "$pct" -gt 100 ]] && pct=100
        echo "$pct"
    }
    get_warning_tier() {
        local pct="${1:-0}"
        if [[ "$pct" -ge 85 ]]; then echo "critical"
        elif [[ "$pct" -ge 70 ]]; then echo "warning"
        elif [[ "$pct" -ge 50 ]]; then echo "info"
        else echo "none"
        fi
    }
    format_context_warning() {
        local tier="$1"
        local pct="$2"
        case "$tier" in
            critical) echo "[!!!] CONTEXT CRITICAL: ${pct}% - MUST /clear soon!" ;;
            warning) echo "[!!] Context Warning: ${pct}% - Consider creating ledger." ;;
            info) echo "[i] Context at ${pct}%." ;;
            *) echo "" ;;
        esac
    }
fi

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

# Read current state or initialize
if [[ -f "$STATE_FILE" ]]; then
    if command -v jq &>/dev/null; then
        turn_count=$(jq -r '.turn_count // 0' "$STATE_FILE" 2>/dev/null || echo 0)
        acknowledged_tier=$(jq -r '.acknowledged_tier // "none"' "$STATE_FILE" 2>/dev/null || echo "none")
    else
        # Fallback: grep-based parsing
        turn_count=$(grep -o '"turn_count":[0-9]*' "$STATE_FILE" 2>/dev/null | grep -o '[0-9]*' || echo 0)
        acknowledged_tier=$(grep -o '"acknowledged_tier":"[^"]*"' "$STATE_FILE" 2>/dev/null | sed 's/.*://;s/"//g' || echo "none")
    fi
else
    turn_count=0
    acknowledged_tier="none"
fi

# Increment turn count
turn_count=$((turn_count + 1))

# Estimate context percentage
estimated_pct=$(estimate_context_pct "$turn_count")

# Determine warning tier
current_tier=$(get_warning_tier "$estimated_pct")

# Write updated state
# Use atomic write pattern: write to temp, then mv
TEMP_STATE="${STATE_FILE}.tmp.$$"
mkdir -p "$(dirname "$STATE_FILE")"

cat > "$TEMP_STATE" <<EOF
{
  "session_id": "${SESSION_ID}",
  "turn_count": ${turn_count},
  "estimated_pct": ${estimated_pct},
  "current_tier": "${current_tier}",
  "acknowledged_tier": "${acknowledged_tier}",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
mv "$TEMP_STATE" "$STATE_FILE"

# Determine if we should show a warning
# Don't repeat same-tier warnings within session (user has seen it)
# But DO show if tier has escalated
show_warning=false
if [[ "$current_tier" != "none" ]]; then
    case "$current_tier" in
        critical)
            # Always show critical warnings
            show_warning=true
            ;;
        warning)
            # Show if not already acknowledged at warning or higher
            if [[ "$acknowledged_tier" != "warning" && "$acknowledged_tier" != "critical" ]]; then
                show_warning=true
            fi
            ;;
        info)
            # Show if not already acknowledged at any tier
            if [[ "$acknowledged_tier" == "none" ]]; then
                show_warning=true
            fi
            ;;
    esac
fi

# Update acknowledged tier if showing a warning
if [[ "$show_warning" == "true" ]]; then
    # Update state with acknowledged tier
    cat > "$TEMP_STATE" <<EOF
{
  "session_id": "${SESSION_ID}",
  "turn_count": ${turn_count},
  "estimated_pct": ${estimated_pct},
  "current_tier": "${current_tier}",
  "acknowledged_tier": "${current_tier}",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    mv "$TEMP_STATE" "$STATE_FILE"
fi

# Generate output
if [[ "$show_warning" == "true" ]]; then
    warning_content=$(format_context_warning "$current_tier" "$estimated_pct")
    warning_escaped=$(json_escape "$warning_content")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "${warning_escaped}"
  }
}
EOF
else
    # No warning needed, return minimal output
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
EOF
fi

exit 0
```

**Step 2: Make the hook executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Expected output:**
```
(no output on success)
```

**Step 3: Verify the hook was created and is executable**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Expected output:**
```
-rwxr-xr-x  1 user  group  XXXX Dec 27 10:15 /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh
```

**Step 4: Test the hook with mock input**

Run:
```bash
echo '{"prompt": "test prompt", "session_id": "test-123"}' | /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh
```

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
```

(First turn won't show warning since estimate is low)

**Step 5: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh
git commit -m "feat(context-warnings): add context usage check hook"
```

**If Task Fails:**

1. **Permission denied on chmod:**
   - Check: File ownership
   - Fix: Use sudo if needed, or check directory permissions
   - Rollback: `rm /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

2. **JSON output malformed:**
   - Check: Run with `bash -x` to see each command
   - Fix: Verify json_escape function works
   - Rollback: `git checkout -- default/hooks/context-usage-check.sh`

3. **State file not created:**
   - Check: `ls -la /tmp/context-usage-*.json`
   - Fix: Verify STATE_DIR permissions
   - Rollback: Clean state files: `rm /tmp/context-usage-*.json`

---

## Task 4: Register Hook in hooks.json

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 3 completed (context-usage-check.sh exists)

**Step 1: Read current hooks.json content**

The current hooks.json has UserPromptSubmit with claude-md-reminder.sh. We need to add context-usage-check.sh to the same array.

**Step 2: Update hooks.json to add the new hook**

The updated hooks.json should be:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      },
      {
        "matcher": "clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/context-usage-check.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 3: Verify the JSON is valid**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:**
The formatted JSON should be displayed without errors.

**Step 4: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json
git commit -m "feat(context-warnings): register context-usage-check hook"
```

**If Task Fails:**

1. **Invalid JSON:**
   - Check: `jq . default/hooks/hooks.json` to see parse error
   - Fix: Correct JSON syntax (missing comma, bracket, etc.)
   - Rollback: `git checkout -- default/hooks/hooks.json`

2. **Hook doesn't fire:**
   - Check: Verify hook is registered under correct event
   - Check: Verify `${CLAUDE_PLUGIN_ROOT}` resolves correctly
   - Fix: Check Claude Code logs for hook execution errors

---

## Task 5: Write Integration Test Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh`

**Prerequisites:**
- Task 3 completed (hook exists)
- Task 2 completed (shared library exists)

**Step 1: Create tests directory if needed**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests`

**Step 2: Write the test script**

```bash
#!/usr/bin/env bash
# Integration tests for context-usage-check.sh
# Run: bash default/hooks/tests/test-context-usage.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
HOOK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
HOOK="${HOOK_DIR}/context-usage-check.sh"

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
    rm -f /tmp/context-usage-test-*.json

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
    rm -f /tmp/context-usage-test-*.json
}

echo "Running context-usage-check.sh tests..."
echo "========================================"

# Test 1: First prompt returns valid JSON
run_test "First prompt returns valid JSON" \
    "hookSpecificOutput" \
    '{"prompt": "test", "session_id": "test"}'

# Test 2: Hook is fast (<100ms)
echo -n "Testing performance... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f /tmp/context-usage-perf-*.json
export CLAUDE_SESSION_ID="perf-$$"
start=$(date +%s%N)
echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
end=$(date +%s%N)
duration=$(( (end - start) / 1000000 ))  # Convert to ms
if [[ $duration -lt 100 ]]; then
    echo -e "${GREEN}PASS${NC}: Hook executed in ${duration}ms (<100ms)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}: Hook took ${duration}ms (>100ms)"
fi
rm -f /tmp/context-usage-perf-*.json

# Test 3: State file is created
echo -n "Testing state file creation... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f /tmp/context-usage-state-*.json
export CLAUDE_SESSION_ID="state-$$"
echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
if [[ -f "/tmp/context-usage-state-$$.json" ]]; then
    echo -e "${GREEN}PASS${NC}: State file created"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}FAIL${NC}: State file not found"
fi
rm -f /tmp/context-usage-state-*.json

# Test 4: Turn count increments
echo -n "Testing turn count increment... "
TESTS_RUN=$((TESTS_RUN + 1))
rm -f /tmp/context-usage-count-*.json
export CLAUDE_SESSION_ID="count-$$"
export CLAUDE_PROJECT_DIR="/tmp"

# Run hook 3 times
for _ in {1..3}; do
    echo '{"prompt": "test"}' | "$HOOK" > /dev/null 2>&1
done

# Check turn count
STATE_FILE="/tmp/context-usage-count-$$.json"
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
rm -f /tmp/context-usage-count-*.json

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
```

**Step 3: Make the test script executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh`

**Step 4: Run the tests**

Run: `bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh`

**Expected output:**
```
Running context-usage-check.sh tests...
========================================
PASS: First prompt returns valid JSON
Testing performance... PASS: Hook executed in XXms (<100ms)
Testing state file creation... PASS: State file created
Testing turn count increment... PASS: Turn count is 3 after 3 prompts
========================================
Tests: 4/4 passed
All tests passed!
```

**Step 5: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh
git commit -m "test(context-warnings): add integration tests for context usage hook"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Read test output for specific failure
   - Fix: Debug the hook with `bash -x`
   - Rollback: N/A (tests don't modify system)

2. **Permission denied:**
   - Check: Script is executable
   - Fix: `chmod +x` the test script
   - Rollback: N/A

---

## Task 6: Update Session Start to Reset Context State

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Prerequisites:**
- Task 3 completed (context-usage-check.sh exists)

**Step 1: Read current session-start.sh to understand structure**

The session-start.sh already handles SessionStart events. We need to add logic to reset the context usage state on session start (clear/compact) so estimates restart fresh.

**Step 2: Add context state reset logic**

Add the following near the top of the script, after the SCRIPT_DIR/PLUGIN_ROOT setup:

```bash
# Reset context usage state on session start
# This ensures fresh estimates after /clear or compact
reset_context_state() {
    local session_id="${CLAUDE_SESSION_ID:-$PPID}"
    local project_dir="${CLAUDE_PROJECT_DIR:-.}"

    # Clear state files for this session
    rm -f "${project_dir}/.ring/state/context-usage-${session_id}.json" 2>/dev/null || true
    rm -f "/tmp/context-usage-${session_id}.json" 2>/dev/null || true
}

# Always reset context state on SessionStart
# (whether startup, resume, clear, or compact)
reset_context_state
```

This code should be added after line 20 (after MONOREPO_ROOT is set) and before the PyYAML installation block.

**Step 3: Verify the modification**

Run: `grep -n "reset_context_state" /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Expected output:**
```
21:# Reset context usage state on session start
22:reset_context_state() {
32:reset_context_state
```
(Line numbers may vary slightly)

**Step 4: Test the session-start hook still works**

Run: `echo '{"type": "startup"}' | /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh | head -5`

**Expected output:**
Should start with `{` and contain valid JSON with `hookSpecificOutput`.

**Step 5: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh
git commit -m "feat(context-warnings): reset context state on session start"
```

**If Task Fails:**

1. **Session start hook broken:**
   - Check: Run hook manually and check output
   - Fix: Verify JSON output is valid
   - Rollback: `git checkout -- default/hooks/session-start.sh`

2. **State files not cleaned:**
   - Check: `ls /tmp/context-usage-*.json` before/after
   - Fix: Verify rm command syntax
   - Rollback: `git checkout -- default/hooks/session-start.sh`

---

## Task 7: Add User-Dismissible Warnings (State Tracking Enhancement)

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Prerequisites:**
- Task 3 completed (initial hook)

**Step 1: The hook already has acknowledgement tracking**

The hook implementation in Task 3 already includes `acknowledged_tier` tracking that prevents repeated warnings at the same level. This task verifies that behavior works correctly.

**Step 2: Add a reset capability via environment variable**

Add the following after the session identification section (around line 15):

```bash
# Allow users to reset warnings via environment variable
# Set RING_RESET_CONTEXT_WARNING=1 to re-enable warnings
if [[ "${RING_RESET_CONTEXT_WARNING:-}" == "1" ]]; then
    rm -f "$STATE_FILE" 2>/dev/null || true
fi
```

**Step 3: Document the dismissal behavior**

The warning system works as follows:
- **50% (info):** Shown once per session, not repeated
- **70% (warning):** Shown once per session unless reset
- **85% (critical):** Always shown (safety feature)

Users can reset warnings by:
1. Running `/clear` (session start resets state)
2. Setting `RING_RESET_CONTEXT_WARNING=1` before their next prompt

**Step 4: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh
git commit -m "feat(context-warnings): add warning reset capability"
```

**If Task Fails:**

1. **Environment variable not working:**
   - Check: Export variable before running hook
   - Fix: Verify bash reads the variable correctly
   - Rollback: `git checkout -- default/hooks/context-usage-check.sh`

---

## Task 8: Run Code Review

**Prerequisites:**
- Tasks 1-7 completed

**Step 1: Dispatch all 3 reviewers in parallel**

- REQUIRED SUB-SKILL: Use requesting-code-review
- All reviewers run simultaneously:
  - `ring-default:code-reviewer`
  - `ring-default:business-logic-reviewer`
  - `ring-default:security-reviewer`
- Wait for all to complete

**Step 2: Handle findings by severity (MANDATORY)**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments for these severities)
- Re-run all 3 reviewers in parallel after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments in code at the relevant location
- Format: `TODO(review): [Issue description] (reported by [reviewer] on [date], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments in code at the relevant location
- Format: `FIXME(nitpick): [Issue description] (reported by [reviewer] on [date], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have `TODO(review):` comments added
- All Cosmetic issues have `FIXME(nitpick):` comments added

---

## Task 9: Create User Documentation

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/docs/CONTEXT_WARNINGS.md`

**Prerequisites:**
- Tasks 1-8 completed

**Step 1: Create docs directory if needed**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/docs`

**Step 2: Write the documentation**

```markdown
# Context Usage Warnings

Ring monitors your estimated context usage and provides proactive warnings before you hit Claude's context limits.

## How It Works

A UserPromptSubmit hook estimates context usage based on:
- Turn count in current session
- Conservative token-per-turn estimates

Warnings are injected into the conversation at these thresholds:

| Threshold | Level | What Happens |
|-----------|-------|--------------|
| 50% | Info | Gentle reminder to consider summarizing |
| 70% | Warning | Recommend creating continuity ledger |
| 85% | Critical | Urgent - must clear context soon |

## Warning Behavior

- **50% and 70% warnings** are shown once per session
- **85% critical warnings** are always shown (safety feature)
- Warnings reset when you run `/clear` or start a new session

## Resetting Warnings

If you've dismissed a warning but want to see it again:

```bash
# Method 1: Clear context (recommended)
# Run /clear in Claude Code

# Method 2: Force reset via environment
export RING_RESET_CONTEXT_WARNING=1
# Then submit your next prompt
```

## Customization

### Adjusting Thresholds

Edit `shared/lib/context-check.sh` and modify the `get_warning_tier` function:

```bash
get_warning_tier() {
    local pct="${1:-0}"

    if [[ "$pct" -ge 85 ]]; then   # Adjust critical threshold
        echo "critical"
    elif [[ "$pct" -ge 70 ]]; then  # Adjust warning threshold
        echo "warning"
    elif [[ "$pct" -ge 50 ]]; then  # Adjust info threshold
        echo "info"
    else
        echo "none"
    fi
}
```

### Adjusting Estimation

The estimation uses conservative defaults. Adjust in `shared/lib/context-check.sh`:

```bash
readonly TOKENS_PER_TURN=2500        # Average tokens per turn
readonly BASE_SYSTEM_OVERHEAD=45000  # System prompt overhead
readonly DEFAULT_CONTEXT_SIZE=200000 # Total context window
```

### Disabling Warnings

To disable context warnings entirely, remove the hook from `default/hooks/hooks.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/claude-md-reminder.sh"
          }
          // Remove context-usage-check.sh entry
        ]
      }
    ]
  }
}
```

## State Files

Context state is stored in:
- `.ring/state/context-usage-{session_id}.json` (if `.ring/` exists)
- `/tmp/context-usage-{session_id}.json` (fallback)

State files are automatically cleaned up on session start.

## Performance

The hook is designed to execute in <50ms to avoid slowing down prompts. Performance is achieved by:
- Simple turn-count based estimation (no API calls)
- Atomic file operations
- Minimal JSON processing

## Troubleshooting

### Warnings not appearing

1. Check hook is registered:
   ```bash
   cat default/hooks/hooks.json | grep context-usage
   ```

2. Check hook is executable:
   ```bash
   ls -la default/hooks/context-usage-check.sh
   ```

3. Run hook manually:
   ```bash
   echo '{"prompt": "test"}' | default/hooks/context-usage-check.sh
   ```

### Warnings appearing too early/late

Adjust the `TOKENS_PER_TURN` constant in `shared/lib/context-check.sh`. Higher values = warnings appear earlier.

### State file issues

Clear state manually:
```bash
rm -f .ring/state/context-usage-*.json
rm -f /tmp/context-usage-*.json
```
```

**Step 3: Verify documentation**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/docs/CONTEXT_WARNINGS.md`

**Expected output:**
```
-rw-r--r--  1 user  group  XXXX Dec 27 11:00 /Users/fredamaral/repos/lerianstudio/ring/default/docs/CONTEXT_WARNINGS.md
```

**Step 4: Commit**

```bash
git add /Users/fredamaral/repos/lerianstudio/ring/default/docs/CONTEXT_WARNINGS.md
git commit -m "docs(context-warnings): add user documentation"
```

**If Task Fails:**

1. **Directory creation fails:**
   - Check: Permissions on default/ directory
   - Fix: Create manually with appropriate permissions
   - Rollback: N/A

---

## Task 10: Final Integration Verification

**Files:**
- None (verification only)

**Prerequisites:**
- All previous tasks completed

**Step 1: Verify all files exist**

Run:
```bash
ls -la /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/docs/CONTEXT_WARNINGS.md
```

**Expected output:**
All files exist with appropriate permissions (hooks should be executable).

**Step 2: Verify hooks.json is valid**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:**
Valid JSON with context-usage-check.sh in UserPromptSubmit hooks.

**Step 3: Run all tests**

Run: `bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/tests/test-context-usage.sh`

**Expected output:**
```
Tests: X/X passed
All tests passed!
```

**Step 4: Test end-to-end in a mock session**

Run:
```bash
# Simulate 30 turns to trigger 50% warning
export CLAUDE_SESSION_ID="e2e-test-$$"
export CLAUDE_PROJECT_DIR="/tmp"
mkdir -p /tmp/.ring/state

for i in {1..30}; do
    echo '{"prompt": "test '$i'"}' | /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh > /tmp/hook-output-$i.json
done

# Check that a warning appeared somewhere
grep -l "context" /tmp/hook-output-*.json | head -1 | xargs cat

# Cleanup
rm -rf /tmp/.ring /tmp/hook-output-*.json /tmp/context-usage-*.json
```

**Expected output:**
At least one output should contain a context warning message.

**Step 5: Final commit with all changes**

If any uncommitted changes remain:
```bash
git status
git add -A
git commit -m "feat(context-warnings): complete context usage warnings implementation"
```

**If Task Fails:**

1. **Tests fail:**
   - Check: Individual test output
   - Fix: Debug specific failing test
   - Rollback: Revert to last working commit

2. **End-to-end test fails:**
   - Check: State file contents
   - Check: Hook output at each turn
   - Fix: Adjust estimation constants if needed

---

## Success Criteria Checklist

- [ ] Hook executes in <50ms (performance requirement)
- [ ] State file created and updated correctly
- [ ] Turn count increments on each prompt
- [ ] 50% warning appears at appropriate turn count
- [ ] 70% warning appears at appropriate turn count
- [ ] 85% warning appears at appropriate turn count
- [ ] Warnings don't repeat (except critical)
- [ ] State resets on session start
- [ ] Reset via environment variable works
- [ ] All tests pass
- [ ] Documentation complete

---

## Rollback Procedure

If the feature needs to be rolled back:

```bash
# Remove hook registration
git checkout -- default/hooks/hooks.json

# Remove new files
rm -f default/hooks/context-usage-check.sh
rm -f default/hooks/tests/test-context-usage.sh
rm -f default/docs/CONTEXT_WARNINGS.md
rm -f shared/lib/context-check.sh

# Revert session-start.sh changes
git checkout -- default/hooks/session-start.sh

# Clean state files
rm -rf .ring/state/context-usage-*.json
rm -f /tmp/context-usage-*.json
```

---

**Plan complete and saved to `docs/plans/2025-12-27-context-usage-warnings.md`.**

# Automatic Context Management Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Transform Ring's context management from passive warnings to fully automated behavioral enforcement that triggers state preservation at context thresholds, auto-creates handoffs on task completion, and feeds the learning extraction pipeline.

**Architecture:** Three-phase approach:
1. Phase 1 injects MANDATORY behavioral triggers into existing context warnings
2. Phase 2 adds task completion detection via PostToolUse hook on TodoWrite
3. Phase 3 implements outcome inference from session state (todos, errors, test results)

**Tech Stack:**
- Bash (hooks)
- Python 3.8+ (outcome inference, artifact indexing)
- JSON (hook configuration, state files)
- SQLite (artifact index database)

**Global Prerequisites:**
- Environment: macOS or Linux with bash 4+
- Tools: Python 3.8+, jq (recommended), sqlite3
- Access: Write access to Ring repository
- State: Working from `main` branch

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version        # Expected: Python 3.8+
bash --version           # Expected: GNU bash 4.0+
jq --version             # Expected: jq-1.6+ (optional but recommended)
sqlite3 --version        # Expected: 3.x
git status               # Expected: clean working tree on main branch
ls default/hooks/        # Expected: context-usage-check.sh exists
```

---

## Historical Precedent

**Query:** "context management handoff continuity ledger"
**Index Status:** Empty (no prior handoffs in artifact index)

### Successful Patterns to Reference
- No historical data available (new feature)

### Failure Patterns to AVOID
- No historical data available (new feature)

### Related Past Plans
- No historical data available (new feature)

---

## Phase 1: Behavioral Injection (Quick Wins)

**Objective:** Transform passive context warnings into MANDATORY behavioral triggers that force state preservation.

---

### Task 1.1: Read Current Context Check Implementation

**Files:**
- Read: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Prerequisites:**
- None

**Step 1: Understand current warning format**

Read the file and identify these key sections:
- `format_context_warning()` function (line ~79-88 fallback)
- Warning tier logic (lines ~158-177)
- Output format (lines ~196-217)

The current output format is:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "[!!] Context Warning: 70% - Consider creating ledger."
  }
}
```

**Step 2: Identify modification points**

The current implementation uses PASSIVE language:
- "Consider creating ledger" (70%)
- "MUST /clear soon" (85%)

We need to inject `<MANDATORY-USER-MESSAGE>` tags at 70% and 85%.

**Expected understanding:**
- Current warnings are suggestions, not mandates
- Hook returns JSON with `additionalContext` field
- The `using-ring` skill checks for `<MANDATORY-USER-MESSAGE>` tags

---

### Task 1.2: Create Enhanced Warning Functions in Shared Library

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh:80-160`

**Prerequisites:**
- Task 1.1 completed

**Step 1: Backup current implementation**

Run: `cp /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh.bak`

**Expected output:**
```
(no output - file copied)
```

**Step 2: Add mandatory message wrapper function**

Add after line 98 (after `get_warning_message` function):

```bash
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
```

**Step 3: Update format_context_warning for behavioral injection**

Replace the `format_context_warning` function (lines 104-160) with:

```bash
# Format a context warning block for injection
# Args: $1 = tier (required), $2 = percentage (required)
# Returns: Formatted warning block or empty
# NOTE: At 70%+ returns MANDATORY-USER-MESSAGE for behavioral enforcement
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

    # BEHAVIORAL ENFORCEMENT: At 70%+ inject mandatory message
    if [[ "$tier" == "critical" ]]; then
        # 85%+ : STOP work and create handoff/ledger
        wrap_mandatory_message "CONTEXT CRITICAL (${pct}%) - MANDATORY ACTION REQUIRED

You MUST stop current work and preserve state NOW:

1. MANDATORY: Run the continuity-ledger skill to save current session state
2. MANDATORY: Create a handoff document with /create-handoff
3. MANDATORY: Run /clear to reset context

DO NOT proceed with any other work until these steps are complete.
Your work will be lost if you continue without preserving state.

After /clear, the session state will auto-restore from ledger."
    elif [[ "$tier" == "warning" ]]; then
        # 70-84%: Mandate ledger creation but allow continued work
        wrap_mandatory_message "CONTEXT WARNING (${pct}%) - ACTION REQUIRED

You MUST create a continuity ledger NOW:

1. MANDATORY: Run the continuity-ledger skill
2. RECOMMENDED: Consider /create-handoff if nearing task completion
3. After ledger created, you may continue work

Failure to create a ledger risks losing session state on next /clear.

Current work can continue after ledger is created."
    else
        # 50-69%: Info only, no mandatory action
        cat <<EOF
<context-warning severity="info">
$icon $message
</context-warning>
EOF
    fi
}
```

**Step 4: Add export for new function**

Add at end of file (after line 166):

```bash
export -f wrap_mandatory_message 2>/dev/null || true
```

**Step 5: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/shared/lib/context-check.sh`

**Expected output:**
```
(no output - syntax valid)
```

**If Task Fails:**

1. **Syntax error:**
   - Run: `bash -n /path/to/file.sh 2>&1` to see exact error
   - Fix: Check for unclosed quotes or heredocs
   - Rollback: `cp /path/to/file.sh.bak /path/to/file.sh`

2. **Function not exported:**
   - Check: `source shared/lib/context-check.sh && type wrap_mandatory_message`
   - Fix: Ensure export line is after function definition

---

### Task 1.3: Update Context Usage Check Hook

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh:78-88`

**Prerequisites:**
- Task 1.2 completed

**Step 1: Update fallback format_context_warning**

Replace the fallback `format_context_warning` function (lines 79-88) with:

```bash
    format_context_warning() {
        local tier="$1"
        local pct="$2"
        # Wrap in mandatory message for behavioral enforcement at 70%+
        if [[ "$tier" == "critical" ]]; then
            cat <<EOF
<MANDATORY-USER-MESSAGE>
CONTEXT CRITICAL (${pct}%) - STOP and preserve state NOW:
1. MANDATORY: Run continuity-ledger skill
2. MANDATORY: Run /create-handoff
3. MANDATORY: Run /clear
</MANDATORY-USER-MESSAGE>
EOF
        elif [[ "$tier" == "warning" ]]; then
            cat <<EOF
<MANDATORY-USER-MESSAGE>
CONTEXT WARNING (${pct}%) - Create ledger NOW:
1. MANDATORY: Run continuity-ledger skill
2. Continue work after ledger created
</MANDATORY-USER-MESSAGE>
EOF
        elif [[ "$tier" == "info" ]]; then
            echo "[i] Context at ${pct}%."
        else
            echo ""
        fi
    }
```

**Step 2: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Expected output:**
```
(no output - syntax valid)
```

**Step 3: Test hook execution**

Run: `CLAUDE_SESSION_ID=test-123 bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/context-usage-check.sh`

**Expected output (first run):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
```

**If Task Fails:**

1. **Hook crashes:**
   - Check: `bash -x /path/to/hook.sh` for debug output
   - Fix: Ensure heredocs use consistent indentation
   - Rollback: `git checkout default/hooks/context-usage-check.sh`

---

### Task 1.4: Add Context Management Rules to using-ring Skill

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/using-ring/SKILL.md:285-298`

**Prerequisites:**
- Task 1.3 completed

**Step 1: Enhance Context Management section**

Replace the "Context Management & Self-Improvement" section (lines 285-298) with:

```markdown
## Context Management & Self-Improvement

Ring includes skills for managing context and enabling self-improvement:

| Skill | Use When |
|-------|----------|
| `continuity-ledger` | Context at 70%+, before /clear, multi-phase work |
| `handoff-tracking` | Session ending, task completing, major milestone |
| `artifact-query` | Search past handoffs, plans, or outcomes by keywords |
| `compound-learnings` | Analyze learnings from multiple sessions, detect patterns |

### MANDATORY Context Preservation (NON-NEGOTIABLE)

**When you receive a `<MANDATORY-USER-MESSAGE>` about context:**

| Context Level | MANDATORY Action | Cannot Proceed Until |
|---------------|------------------|---------------------|
| 70-84% (Warning) | Create continuity ledger | Ledger file exists |
| 85%+ (Critical) | Create ledger AND handoff, then /clear | Both created, /clear executed |

**Anti-Rationalization for Context Management:**

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I'll create the ledger after finishing this task" | Context may exceed limit mid-task, losing work | **Create ledger NOW** |
| "The warning is just a suggestion" | MANDATORY-USER-MESSAGE is NON-NEGOTIABLE | **Execute required actions immediately** |
| "I'm almost done, I can skip the ledger" | "Almost done" tasks often reveal new complexity | **Create ledger NOW** |
| "The 70% threshold seems conservative" | Thresholds are calibrated from real failures | **Trust the threshold, create ledger** |
| "I'll remember the context after /clear" | Human memory is unreliable, ledgers are not | **Create ledger NOW** |
| "Creating a handoff seems excessive" | Handoffs feed learning system, always valuable | **Create handoff at 85%+** |

**Verification:** After completing mandatory context actions, confirm:
- [ ] Ledger file exists at `.ring/ledgers/CONTINUITY-*.md`
- [ ] Ledger contains current task state
- [ ] At 85%+: Handoff created in `docs/handoffs/`
- [ ] At 85%+: /clear executed

**Compound Learnings workflow:** Session ends -> Hook extracts learnings -> After 3+ sessions, patterns emerge -> User approves -> Permanent rules/skills created.
```

**Step 2: Verify markdown syntax**

Run: `head -350 /Users/fredamaral/repos/lerianstudio/ring/default/skills/using-ring/SKILL.md | tail -80`

**Expected output:** The new Context Management section is visible and properly formatted.

**If Task Fails:**

1. **Markdown table broken:**
   - Check: Pipe characters align in tables
   - Fix: Use consistent spacing within table cells
   - Rollback: `git checkout default/skills/using-ring/SKILL.md`

---

### Task 1.5: Test Phase 1 Integration

**Files:**
- Test: Integration of context-usage-check.sh with using-ring skill

**Prerequisites:**
- Tasks 1.1-1.4 completed

**Step 1: Create test state file to simulate high context**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/state
cat > /Users/fredamaral/repos/lerianstudio/ring/.ring/state/context-usage-test-phase1.json << 'EOF'
{
  "session_id": "test-phase1",
  "turn_count": 35,
  "estimated_pct": 66,
  "current_tier": "info",
  "acknowledged_tier": "none",
  "updated_at": "2025-12-29T00:00:00Z"
}
EOF
```

**Expected output:**
```
(no output - file created)
```

**Step 2: Test warning tier progression**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_SESSION_ID=test-phase1 \
CLAUDE_PROJECT_DIR=/Users/fredamaral/repos/lerianstudio/ring \
bash default/hooks/context-usage-check.sh
```

**Expected output (turn 36, ~67%):**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
```

**Step 3: Simulate 70% threshold**

Run:
```bash
cat > /Users/fredamaral/repos/lerianstudio/ring/.ring/state/context-usage-test-phase1.json << 'EOF'
{
  "session_id": "test-phase1",
  "turn_count": 37,
  "estimated_pct": 69,
  "current_tier": "info",
  "acknowledged_tier": "none",
  "updated_at": "2025-12-29T00:00:00Z"
}
EOF
CLAUDE_SESSION_ID=test-phase1 \
CLAUDE_PROJECT_DIR=/Users/fredamaral/repos/lerianstudio/ring \
bash default/hooks/context-usage-check.sh
```

**Expected output (turn 38, ~70%):**
Output should contain `<MANDATORY-USER-MESSAGE>` with "CONTEXT WARNING" and ledger instructions.

**Step 4: Cleanup test files**

Run:
```bash
rm -f /Users/fredamaral/repos/lerianstudio/ring/.ring/state/context-usage-test-phase1.json
```

**If Task Fails:**

1. **No mandatory message at 70%:**
   - Check: `get_warning_tier` returns "warning" at 70%
   - Check: `format_context_warning` wraps in MANDATORY tags
   - Debug: Add `set -x` to hook and rerun

2. **JSON parse error:**
   - Check: Special characters in message are escaped
   - Fix: Ensure `json_escape` handles newlines in heredocs

---

### Task 1.6: Commit Phase 1 Changes

**Files:**
- Commit: All Phase 1 changes

**Prerequisites:**
- Task 1.5 tests pass

**Step 1: Stage changes**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add shared/lib/context-check.sh \
        default/hooks/context-usage-check.sh \
        default/skills/using-ring/SKILL.md
```

**Step 2: Verify staged changes**

Run: `git diff --staged --stat`

**Expected output:**
```
 default/hooks/context-usage-check.sh  | XX +++++----
 default/skills/using-ring/SKILL.md    | XX +++++----
 shared/lib/context-check.sh           | XX +++++
 3 files changed, XX insertions(+), XX deletions(-)
```

**Step 3: Commit**

Run:
```bash
git commit -m "feat(context): add mandatory behavioral triggers at 70%/85% thresholds

- Inject MANDATORY-USER-MESSAGE at 70% requiring ledger creation
- Inject MANDATORY-USER-MESSAGE at 85% requiring handoff + /clear
- Add anti-rationalization table for context management in using-ring
- Transform passive warnings into enforced behavioral triggers" \
--trailer "Generated-by: Claude" \
--trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:**
```
[main xxxxxxx] feat(context): add mandatory behavioral triggers at 70%/85% thresholds
 3 files changed, XX insertions(+), XX deletions(-)
```

**If Task Fails:**

1. **Pre-commit hook fails:**
   - Check: Run linting manually
   - Fix: Address any style issues
   - Retry: Stage fixes and commit again (new commit, not amend)

---

### Task 1.7: Code Review Checkpoint - Phase 1

**Purpose:** Verify Phase 1 changes before proceeding to Phase 2.

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Dispatch:
- `ring-default:code-reviewer` - Check code quality, error handling
- `ring-default:business-logic-reviewer` - Check behavioral logic correctness
- `ring-default:security-reviewer` - Check for injection vulnerabilities in JSON/heredocs

**Step 2: Handle findings by severity**

| Severity | Action |
|----------|--------|
| Critical/High/Medium | Fix immediately, re-run all 3 reviewers |
| Low | Add `TODO(review):` comment at relevant location |
| Cosmetic | Add `FIXME(nitpick):` comment at relevant location |

**Step 3: Proceed only when**

- [ ] Zero Critical/High/Medium issues remain
- [ ] All Low issues have TODO(review): comments added
- [ ] All Cosmetic issues have FIXME(nitpick): comments added

---

## Phase 2: Task Completion Detection

**Objective:** Automatically detect when all TodoWrite tasks are complete and trigger handoff creation.

---

### Task 2.1: Create Task Completion Check Hook

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`

**Prerequisites:**
- Phase 1 completed

**Step 1: Create the hook file**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`:

```bash
#!/usr/bin/env bash
# Task Completion Check - PostToolUse hook for TodoWrite
# Detects when all todos are marked complete and triggers handoff creation
# Performance target: <50ms execution time

set -euo pipefail

# Determine plugin root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
MONOREPO_ROOT="$(cd "${PLUGIN_ROOT}/.." && pwd)"

# Read input from stdin
INPUT=$(cat)

# Source shared libraries
SHARED_LIB="${MONOREPO_ROOT}/shared/lib"
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

# Parse TodoWrite tool output from input
# Expected input structure:
# {
#   "tool_name": "TodoWrite",
#   "tool_input": { "todos": [...] },
#   "tool_output": { ... }
# }

# Extract todos array using jq if available, otherwise skip
if ! command -v jq &>/dev/null; then
    # No jq - cannot parse todos, return minimal response
    cat <<'EOF'
{
  "result": "continue"
}
EOF
    exit 0
fi

# Parse the todos from tool_input
TODOS=$(echo "$INPUT" | jq -r '.tool_input.todos // []' 2>/dev/null)

if [[ -z "$TODOS" ]] || [[ "$TODOS" == "null" ]] || [[ "$TODOS" == "[]" ]]; then
    # No todos or empty - nothing to check
    cat <<'EOF'
{
  "result": "continue"
}
EOF
    exit 0
fi

# Count total and completed todos
TOTAL_COUNT=$(echo "$TODOS" | jq 'length')
COMPLETED_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "completed")] | length')
IN_PROGRESS_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "in_progress")] | length')
PENDING_COUNT=$(echo "$TODOS" | jq '[.[] | select(.status == "pending")] | length')

# Check if all todos are complete
if [[ "$TOTAL_COUNT" -gt 0 ]] && [[ "$COMPLETED_COUNT" -eq "$TOTAL_COUNT" ]]; then
    # All todos complete - trigger handoff creation
    MESSAGE="<MANDATORY-USER-MESSAGE>
TASK COMPLETION DETECTED - HANDOFF REQUIRED

All ${TOTAL_COUNT} todos are marked complete. You MUST create a handoff document NOW:

1. MANDATORY: Run /create-handoff to preserve this session's learnings
2. MANDATORY: Document what worked and what failed in the handoff
3. After handoff created, session can end or continue with new tasks

This handoff will be indexed for future sessions to learn from.

Completed tasks:
$(echo "$TODOS" | jq -r '.[] | "- " + .content')
</MANDATORY-USER-MESSAGE>"

    MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${MESSAGE_ESCAPED}"
  }
}
EOF
else
    # Not all complete - return status summary
    if [[ "$COMPLETED_COUNT" -gt 0 ]]; then
        MESSAGE="Task progress: ${COMPLETED_COUNT}/${TOTAL_COUNT} complete, ${IN_PROGRESS_COUNT} in progress, ${PENDING_COUNT} pending."
        MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "${MESSAGE_ESCAPED}"
  }
}
EOF
    else
        # No completed tasks - minimal response
        cat <<'EOF'
{
  "result": "continue"
}
EOF
    fi
fi

exit 0
```

**Step 2: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`

**Expected output:**
```
(no output - permissions set)
```

**Step 3: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`

**Expected output:**
```
(no output - syntax valid)
```

**If Task Fails:**

1. **Syntax error:**
   - Check: Heredoc delimiters match (EOF vs 'EOF')
   - Fix: Ensure jq commands are properly quoted
   - Debug: `bash -x` for line-by-line execution

---

### Task 2.2: Test Task Completion Hook

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`

**Prerequisites:**
- Task 2.1 completed

**Step 1: Test with incomplete todos**

Run:
```bash
echo '{
  "tool_name": "TodoWrite",
  "tool_input": {
    "todos": [
      {"content": "Task 1", "status": "completed", "activeForm": "Doing task 1"},
      {"content": "Task 2", "status": "in_progress", "activeForm": "Doing task 2"},
      {"content": "Task 3", "status": "pending", "activeForm": "Doing task 3"}
    ]
  }
}' | bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh
```

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Task progress: 1/3 complete, 1 in progress, 1 pending."
  }
}
```

**Step 2: Test with all todos complete**

Run:
```bash
echo '{
  "tool_name": "TodoWrite",
  "tool_input": {
    "todos": [
      {"content": "Task 1", "status": "completed", "activeForm": "Doing task 1"},
      {"content": "Task 2", "status": "completed", "activeForm": "Doing task 2"}
    ]
  }
}' | bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh
```

**Expected output:**
Output should contain `<MANDATORY-USER-MESSAGE>` with "TASK COMPLETION DETECTED" and handoff instructions.

**Step 3: Test with empty todos**

Run:
```bash
echo '{
  "tool_name": "TodoWrite",
  "tool_input": {
    "todos": []
  }
}' | bash /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh
```

**Expected output:**
```json
{
  "result": "continue"
}
```

**If Task Fails:**

1. **jq errors:**
   - Check: `jq --version` returns valid version
   - Fix: Install jq or verify fallback path works

2. **Wrong count:**
   - Debug: Add `echo "DEBUG: TOTAL=$TOTAL_COUNT COMPLETED=$COMPLETED_COUNT" >&2` before conditional

---

### Task 2.3: Register Hook in hooks.json

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 2.2 tests pass

**Step 1: Add TodoWrite matcher to PostToolUse**

The current hooks.json has PostToolUse for Write. Add TodoWrite matcher.

Find this section:
```json
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/artifact-index-write.sh"
          }
        ]
      }
    ],
```

Add after the Write matcher block:
```json
      {
        "matcher": "TodoWrite",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/task-completion-check.sh"
          }
        ]
      }
```

**Step 2: Verify JSON syntax**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:**
Valid JSON with the new TodoWrite matcher visible in PostToolUse array.

**Step 3: Verify hook path**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/hooks/task-completion-check.sh`

**Expected output:**
```
-rwxr-xr-x  1 user  group  XXXX Dec 29 XX:XX task-completion-check.sh
```

**If Task Fails:**

1. **JSON invalid:**
   - Check: Missing commas between array elements
   - Fix: Ensure comma after first PostToolUse matcher block
   - Rollback: `git checkout default/hooks/hooks.json`

---

### Task 2.4: Commit Phase 2 Changes

**Files:**
- Commit: All Phase 2 changes

**Prerequisites:**
- Tasks 2.1-2.3 completed

**Step 1: Stage changes**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/hooks/task-completion-check.sh \
        default/hooks/hooks.json
```

**Step 2: Verify staged changes**

Run: `git diff --staged --stat`

**Expected output:**
```
 default/hooks/hooks.json               |  X ++++
 default/hooks/task-completion-check.sh | XX ++++++++++++++++
 2 files changed, XX insertions(+)
```

**Step 3: Commit**

Run:
```bash
git commit -m "feat(context): add task completion detection hook

- Create task-completion-check.sh for PostToolUse on TodoWrite
- Detect when all todos are marked complete
- Inject MANDATORY-USER-MESSAGE requiring handoff creation
- Register hook in hooks.json under PostToolUse matcher" \
--trailer "Generated-by: Claude" \
--trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:**
```
[main xxxxxxx] feat(context): add task completion detection hook
 2 files changed, XX insertions(+)
 create mode 100755 default/hooks/task-completion-check.sh
```

---

### Task 2.5: Code Review Checkpoint - Phase 2

**Purpose:** Verify Phase 2 changes before proceeding to Phase 3.

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Focus areas:
- `ring-default:code-reviewer` - jq usage, error handling, edge cases
- `ring-default:business-logic-reviewer` - Todo counting logic, completion detection
- `ring-default:security-reviewer` - Input parsing, injection prevention

**Step 2: Handle findings by severity**

(Same as Phase 1)

**Step 3: Proceed only when zero Critical/High/Medium issues remain**

---

## Phase 3: Outcome Inference

**Objective:** Automatically infer session outcomes from observable state (todos, errors, test results) and update handoff documents.

---

### Task 3.1: Create Outcome Inference Module

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py`

**Prerequisites:**
- Phase 2 completed

**Step 1: Create directory**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference`

**Expected output:**
```
(no output - directory created)
```

**Step 2: Create outcome inference module**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py`:

```python
#!/usr/bin/env python3
"""Outcome inference module for automatic handoff outcome detection.

This module analyzes session state to infer task outcomes:
- SUCCEEDED: All todos complete, no errors
- PARTIAL_PLUS: Most todos complete, minor issues
- PARTIAL_MINUS: Some progress, significant blockers
- FAILED: No meaningful progress or abandoned

Input sources:
1. TodoWrite state (from .ring/state/todos-*.json)
2. Recent errors (from conversation context)
3. Test results (if available)
4. Handoff status field

Usage:
    from outcome_inference import infer_outcome
    outcome = infer_outcome(project_root)
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Outcome definitions
OUTCOME_SUCCEEDED = "SUCCEEDED"
OUTCOME_PARTIAL_PLUS = "PARTIAL_PLUS"
OUTCOME_PARTIAL_MINUS = "PARTIAL_MINUS"
OUTCOME_FAILED = "FAILED"
OUTCOME_UNKNOWN = "UNKNOWN"


def get_project_root() -> Path:
    """Get the project root directory."""
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        return Path(os.environ["CLAUDE_PROJECT_DIR"])
    return Path.cwd()


def sanitize_session_id(session_id: str) -> str:
    """Sanitize session ID for safe use in filenames."""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', session_id)
    if not sanitized:
        return "unknown"
    return sanitized[:64]


def get_todo_state(project_root: Path) -> Optional[Dict]:
    """Read the most recent TodoWrite state file.

    Returns:
        Dict with 'todos' array or None if not found
    """
    state_dir = project_root / ".ring" / "state"
    if not state_dir.exists():
        return None

    # Find most recent todos file
    todo_files = list(state_dir.glob("todos-*.json"))
    if not todo_files:
        return None

    # Sort by modification time, newest first
    todo_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    try:
        with open(todo_files[0], encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def analyze_todos(todos: List[Dict]) -> Tuple[int, int, int, int]:
    """Analyze todo list and return counts.

    Returns:
        Tuple of (total, completed, in_progress, pending)
    """
    if not todos:
        return (0, 0, 0, 0)

    total = len(todos)
    completed = sum(1 for t in todos if t.get("status") == "completed")
    in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
    pending = sum(1 for t in todos if t.get("status") == "pending")

    return (total, completed, in_progress, pending)


def get_recent_handoff(project_root: Path) -> Optional[Path]:
    """Find the most recent handoff file.

    Searches both docs/handoffs/ and .ring/handoffs/

    Returns:
        Path to most recent handoff or None
    """
    handoff_dirs = [
        project_root / "docs" / "handoffs",
        project_root / ".ring" / "handoffs",
    ]

    most_recent = None
    most_recent_time = 0

    for handoff_dir in handoff_dirs:
        if not handoff_dir.exists():
            continue

        for handoff_file in handoff_dir.rglob("*.md"):
            mtime = handoff_file.stat().st_mtime
            if mtime > most_recent_time:
                most_recent_time = mtime
                most_recent = handoff_file

    return most_recent


def parse_handoff_status(handoff_path: Path) -> Optional[str]:
    """Parse the status field from a handoff file's frontmatter.

    Returns:
        Status string (complete, in_progress, blocked) or None
    """
    try:
        content = handoff_path.read_text(encoding='utf-8')
    except IOError:
        return None

    # Parse YAML frontmatter
    if not content.startswith("---"):
        return None

    end_marker = content.find("---", 3)
    if end_marker == -1:
        return None

    frontmatter = content[3:end_marker]

    # Find status field
    for line in frontmatter.split("\n"):
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()

    return None


def infer_outcome_from_todos(
    total: int,
    completed: int,
    in_progress: int,
    pending: int
) -> Tuple[str, str]:
    """Infer outcome from todo counts.

    Returns:
        Tuple of (outcome, reason)
    """
    if total == 0:
        return (OUTCOME_UNKNOWN, "No todos tracked")

    completion_ratio = completed / total

    if completed == total:
        return (OUTCOME_SUCCEEDED, f"All {total} tasks completed")

    if completion_ratio >= 0.8:
        remaining = total - completed
        return (OUTCOME_PARTIAL_PLUS, f"{completed}/{total} tasks done, {remaining} minor items remain")

    if completion_ratio >= 0.5:
        return (OUTCOME_PARTIAL_MINUS, f"{completed}/{total} tasks done, significant work remains")

    if completed > 0:
        return (OUTCOME_PARTIAL_MINUS, f"Only {completed}/{total} tasks completed")

    if in_progress > 0:
        return (OUTCOME_PARTIAL_MINUS, f"Work started but no tasks completed ({in_progress} in progress)")

    return (OUTCOME_FAILED, f"No progress made on {total} tasks")


def infer_outcome_from_handoff_status(status: Optional[str]) -> Optional[Tuple[str, str]]:
    """Infer outcome from handoff status field.

    Returns:
        Tuple of (outcome, reason) or None if status doesn't map clearly
    """
    if not status:
        return None

    status_lower = status.lower()

    if status_lower == "complete":
        return (OUTCOME_SUCCEEDED, "Handoff marked as complete")

    if status_lower == "blocked":
        return (OUTCOME_PARTIAL_MINUS, "Handoff marked as blocked")

    # in_progress doesn't map to a clear outcome
    return None


def infer_outcome(
    project_root: Optional[Path] = None,
    todos: Optional[List[Dict]] = None,
    handoff_status: Optional[str] = None,
) -> Dict:
    """Infer session outcome from available state.

    Priority order:
    1. Explicit handoff status (complete/blocked)
    2. Todo completion ratio
    3. Default to UNKNOWN

    Args:
        project_root: Project root directory (uses env var if not provided)
        todos: Optional pre-parsed todos list
        handoff_status: Optional pre-parsed handoff status

    Returns:
        Dict with 'outcome', 'reason', and 'confidence' keys
    """
    if project_root is None:
        project_root = get_project_root()

    result = {
        "outcome": OUTCOME_UNKNOWN,
        "reason": "Unable to determine outcome",
        "confidence": "low",
        "sources": [],
    }

    # Try handoff status first (explicit signal)
    if handoff_status is None:
        handoff_path = get_recent_handoff(project_root)
        if handoff_path:
            handoff_status = parse_handoff_status(handoff_path)
            if handoff_status:
                result["sources"].append(f"handoff:{handoff_path.name}")

    if handoff_status:
        handoff_inference = infer_outcome_from_handoff_status(handoff_status)
        if handoff_inference:
            result["outcome"], result["reason"] = handoff_inference
            result["confidence"] = "high"
            return result

    # Try todo state
    if todos is None:
        todo_state = get_todo_state(project_root)
        if todo_state:
            todos = todo_state.get("todos", [])
            result["sources"].append("todos")

    if todos:
        total, completed, in_progress, pending = analyze_todos(todos)
        if total > 0:
            result["outcome"], result["reason"] = infer_outcome_from_todos(
                total, completed, in_progress, pending
            )
            # Confidence based on completion clarity
            if completed == total or completed == 0:
                result["confidence"] = "high"
            elif completed / total >= 0.8 or completed / total <= 0.2:
                result["confidence"] = "medium"
            else:
                result["confidence"] = "low"
            return result

    return result


def main():
    """CLI entry point for testing."""
    import sys

    # Read optional todos from stdin
    todos = None
    if not sys.stdin.isatty():
        try:
            input_data = json.loads(sys.stdin.read())
            todos = input_data.get("todos")
        except json.JSONDecodeError:
            pass

    result = infer_outcome(todos=todos)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

**Step 3: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py`

**Step 4: Verify syntax**

Run: `python3 -m py_compile /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py`

**Expected output:**
```
(no output - syntax valid)
```

**If Task Fails:**

1. **Python syntax error:**
   - Check: Indentation (use 4 spaces consistently)
   - Fix: Use `python3 -c "import ast; ast.parse(open('file.py').read())"` for detailed error

---

### Task 3.2: Test Outcome Inference Module

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py`

**Prerequisites:**
- Task 3.1 completed

**Step 1: Test with all complete todos**

Run:
```bash
echo '{"todos": [
  {"status": "completed"},
  {"status": "completed"},
  {"status": "completed"}
]}' | python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py
```

**Expected output:**
```json
{
  "outcome": "SUCCEEDED",
  "reason": "All 3 tasks completed",
  "confidence": "high",
  "sources": []
}
```

**Step 2: Test with partial completion (80%+)**

Run:
```bash
echo '{"todos": [
  {"status": "completed"},
  {"status": "completed"},
  {"status": "completed"},
  {"status": "completed"},
  {"status": "pending"}
]}' | python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py
```

**Expected output:**
```json
{
  "outcome": "PARTIAL_PLUS",
  "reason": "4/5 tasks done, 1 minor items remain",
  "confidence": "medium",
  "sources": []
}
```

**Step 3: Test with low completion**

Run:
```bash
echo '{"todos": [
  {"status": "completed"},
  {"status": "pending"},
  {"status": "pending"},
  {"status": "pending"},
  {"status": "pending"}
]}' | python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py
```

**Expected output:**
```json
{
  "outcome": "PARTIAL_MINUS",
  "reason": "Only 1/5 tasks completed",
  "confidence": "low",
  "sources": []
}
```

**Step 4: Test with no progress**

Run:
```bash
echo '{"todos": [
  {"status": "pending"},
  {"status": "pending"}
]}' | python3 /Users/fredamaral/repos/lerianstudio/ring/default/lib/outcome-inference/outcome_inference.py
```

**Expected output:**
```json
{
  "outcome": "FAILED",
  "reason": "No progress made on 2 tasks",
  "confidence": "high",
  "sources": []
}
```

**If Task Fails:**

1. **Wrong outcome:**
   - Debug: Add print statements in `infer_outcome_from_todos`
   - Check: Completion ratio calculations

---

### Task 3.3: Create Outcome Inference Hook Wrapper

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/outcome-inference.sh`

**Prerequisites:**
- Task 3.2 tests pass

**Step 1: Create wrapper script**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/outcome-inference.sh`:

```bash
#!/usr/bin/env bash
# Outcome Inference Hook Wrapper
# Calls Python module to infer session outcome from state
# Triggered by: Stop event (runs before learning-extract.sh)

set -euo pipefail

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/../lib/outcome-inference"

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

# Extract outcome and reason
OUTCOME=$(echo "$RESULT" | jq -r '.outcome // "UNKNOWN"' 2>/dev/null || echo "UNKNOWN")
REASON=$(echo "$RESULT" | jq -r '.reason // "Unable to determine"' 2>/dev/null || echo "Unable to determine")
CONFIDENCE=$(echo "$RESULT" | jq -r '.confidence // "low"' 2>/dev/null || echo "low")

# Save outcome to state file for learning-extract.py to pick up
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
STATE_DIR="${PROJECT_ROOT}/.ring/state"
mkdir -p "$STATE_DIR"

# Write outcome state
cat > "${STATE_DIR}/session-outcome.json" << EOF
{
  "status": "${OUTCOME}",
  "summary": "${REASON}",
  "confidence": "${CONFIDENCE}",
  "inferred_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "key_decisions": []
}
EOF

# Source JSON escape utility
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"
if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/json-escape.sh"
else
    json_escape() {
        printf '%s' "$1" | jq -Rs . 2>/dev/null | sed 's/^"//;s/"$//' || printf '%s' "$1"
    }
fi

# Build message
MESSAGE="Session outcome inferred: ${OUTCOME} (${CONFIDENCE} confidence)
Reason: ${REASON}"
MESSAGE_ESCAPED=$(json_escape "$MESSAGE")

# Return hook response
cat << EOF
{
  "result": "continue",
  "message": "${MESSAGE_ESCAPED}"
}
EOF
```

**Step 2: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/outcome-inference.sh`

**Step 3: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/outcome-inference.sh`

**Expected output:**
```
(no output - syntax valid)
```

**If Task Fails:**

1. **Heredoc issues:**
   - Check: EOF delimiters are consistent
   - Fix: Ensure no spaces before EOF terminator

---

### Task 3.4: Register Outcome Inference in hooks.json

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 3.3 completed

**Step 1: Add outcome-inference to Stop hooks**

Find the Stop section:
```json
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ledger-save.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-outcome.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/learning-extract.sh"
          }
        ]
      }
    ]
```

Add outcome-inference BEFORE learning-extract (order matters - inference must run first):

```json
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ledger-save.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-outcome.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/outcome-inference.sh"
          },
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/learning-extract.sh"
          }
        ]
      }
    ]
```

**Step 2: Verify JSON syntax**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:**
Valid JSON with outcome-inference.sh in Stop hooks array.

**If Task Fails:**

1. **JSON invalid:**
   - Check: Commas between hook objects
   - Rollback: `git checkout default/hooks/hooks.json`

---

### Task 3.5: Update Learning Extract to Use Inferred Outcomes

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/learning-extract.py:132-176`

**Prerequisites:**
- Task 3.4 completed

**Step 1: Enhance extract_learnings_from_outcomes function**

The current function already reads from `.ring/state/session-outcome.json`. Verify it handles the new format with confidence field.

Read lines 132-176 and verify the function handles:
- `status` field (maps to outcome)
- `summary` field (maps to learnings)
- `key_decisions` field

The current implementation should already work with the new outcome-inference.sh output format. No changes needed if the structure matches.

**Step 2: Verify integration**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/state
cat > /Users/fredamaral/repos/lerianstudio/ring/.ring/state/session-outcome.json << 'EOF'
{
  "status": "SUCCEEDED",
  "summary": "All tasks completed successfully",
  "confidence": "high",
  "key_decisions": ["Used TDD approach", "Chose hooks over polling"]
}
EOF

echo '{"type": "stop", "session_id": "test-inference"}' | \
python3 /Users/fredamaral/repos/lerianstudio/ring/default/hooks/learning-extract.py
```

**Expected output:**
```json
{
  "result": "continue",
  "message": "Session learnings saved to .ring/cache/learnings/2025-12-29-test-inference.md"
}
```

**Step 3: Verify learnings file content**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings/2025-12-29-*.md`

**Expected output:**
Learnings file should contain "What Worked" section with "All tasks completed successfully".

**Step 4: Cleanup**

Run:
```bash
rm -f /Users/fredamaral/repos/lerianstudio/ring/.ring/state/session-outcome.json
rm -f /Users/fredamaral/repos/lerianstudio/ring/.ring/cache/learnings/2025-12-29-test-*.md
```

**If Task Fails:**

1. **Learnings not extracted:**
   - Debug: Check `extract_learnings_from_outcomes` return value
   - Check: File path matches expected pattern

---

### Task 3.6: Commit Phase 3 Changes

**Files:**
- Commit: All Phase 3 changes

**Prerequisites:**
- Tasks 3.1-3.5 completed

**Step 1: Stage changes**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/lib/outcome-inference/ \
        default/hooks/outcome-inference.sh \
        default/hooks/hooks.json
```

**Step 2: Verify staged changes**

Run: `git diff --staged --stat`

**Expected output:**
```
 default/hooks/hooks.json                              |  X ++++
 default/hooks/outcome-inference.sh                    | XX ++++++++++
 default/lib/outcome-inference/outcome_inference.py   | XX ++++++++++
 3 files changed, XX insertions(+)
```

**Step 3: Commit**

Run:
```bash
git commit -m "feat(context): add automatic outcome inference from session state

- Create outcome_inference.py module with todo/handoff analysis
- Create outcome-inference.sh hook wrapper
- Register hook in Stop event (before learning-extract)
- Infer SUCCEEDED/PARTIAL_PLUS/PARTIAL_MINUS/FAILED from:
  - Todo completion ratios
  - Handoff status fields
- Write inferred outcome to session-outcome.json for learning extraction" \
--trailer "Generated-by: Claude" \
--trailer "AI-Model: claude-opus-4-5-20251101"
```

**Expected output:**
```
[main xxxxxxx] feat(context): add automatic outcome inference from session state
 3 files changed, XX insertions(+)
 create mode 100755 default/hooks/outcome-inference.sh
 create mode 100755 default/lib/outcome-inference/outcome_inference.py
```

---

### Task 3.7: Code Review Checkpoint - Phase 3

**Purpose:** Final review before completion.

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Focus areas:
- `ring-default:code-reviewer` - Python module quality, error handling
- `ring-default:business-logic-reviewer` - Outcome inference logic correctness
- `ring-default:security-reviewer` - File path handling, input validation

**Step 2: Handle findings by severity**

(Same as Phase 1)

**Step 3: Proceed only when zero Critical/High/Medium issues remain**

---

## Final Integration Test

### Task 4.1: End-to-End Integration Test

**Files:**
- Test: Full pipeline integration

**Prerequisites:**
- All phases completed and reviewed

**Step 1: Simulate full session lifecycle**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring

# 1. Create test state directory
mkdir -p .ring/state .ring/cache/learnings

# 2. Simulate high context (70%)
cat > .ring/state/context-usage-e2e-test.json << 'EOF'
{
  "session_id": "e2e-test",
  "turn_count": 37,
  "estimated_pct": 69,
  "current_tier": "info",
  "acknowledged_tier": "none"
}
EOF

# 3. Run context check (should trigger warning at 70%)
echo "=== Context Check at 70% ==="
CLAUDE_SESSION_ID=e2e-test \
CLAUDE_PROJECT_DIR=/Users/fredamaral/repos/lerianstudio/ring \
bash default/hooks/context-usage-check.sh

# 4. Simulate task completion
echo ""
echo "=== Task Completion Check ==="
echo '{
  "tool_name": "TodoWrite",
  "tool_input": {
    "todos": [
      {"content": "Phase 1", "status": "completed", "activeForm": ""},
      {"content": "Phase 2", "status": "completed", "activeForm": ""},
      {"content": "Phase 3", "status": "completed", "activeForm": ""}
    ]
  }
}' | bash default/hooks/task-completion-check.sh

# 5. Run outcome inference
echo ""
echo "=== Outcome Inference ==="
echo '{"todos": [
  {"status": "completed"},
  {"status": "completed"},
  {"status": "completed"}
]}' | python3 default/lib/outcome-inference/outcome_inference.py

# 6. Cleanup
rm -rf .ring/state/context-usage-e2e-test.json .ring/state/session-outcome.json
```

**Expected output:**
1. Context check should output MANDATORY-USER-MESSAGE at 70%
2. Task completion should output MANDATORY-USER-MESSAGE for handoff
3. Outcome inference should return SUCCEEDED

**Step 2: Verify hooks.json registration**

Run: `jq '.hooks.PostToolUse | map(.matcher)' default/hooks/hooks.json`

**Expected output:**
```json
[
  "Write",
  "TodoWrite"
]
```

Run: `jq '.hooks.Stop[0].hooks | map(.command | split("/") | last)' default/hooks/hooks.json`

**Expected output:**
```json
[
  "ledger-save.sh",
  "session-outcome.sh",
  "outcome-inference.sh",
  "learning-extract.sh"
]
```

**If Task Fails:**

1. **Hook not triggered:**
   - Check: hooks.json syntax
   - Check: File permissions (must be executable)

2. **Wrong output format:**
   - Debug: Run individual hooks with `bash -x`

---

### Task 4.2: Final Commit with All Changes

**Files:**
- Verify: All changes committed

**Prerequisites:**
- Task 4.1 passes

**Step 1: Check git status**

Run: `git status`

**Expected output:**
```
On branch main
nothing to commit, working tree clean
```

If there are uncommitted changes, stage and commit them with an appropriate message.

**Step 2: Review commit history**

Run: `git log --oneline -5`

**Expected output:**
Should show 3 commits from this implementation:
- feat(context): add automatic outcome inference from session state
- feat(context): add task completion detection hook
- feat(context): add mandatory behavioral triggers at 70%/85% thresholds

---

## Summary

This plan implements Automatic Context Management in three phases:

| Phase | What It Does | Files Changed |
|-------|--------------|---------------|
| 1 | Behavioral injection at 70%/85% thresholds | context-check.sh, context-usage-check.sh, using-ring |
| 2 | Task completion detection on TodoWrite | task-completion-check.sh, hooks.json |
| 3 | Outcome inference from session state | outcome_inference.py, outcome-inference.sh, hooks.json |

**Key behaviors after implementation:**

1. **At 70% context:** MANDATORY-USER-MESSAGE forces ledger creation
2. **At 85% context:** MANDATORY-USER-MESSAGE forces handoff + /clear
3. **When all todos complete:** MANDATORY-USER-MESSAGE forces handoff creation
4. **On session end:** Outcome automatically inferred and saved for learning extraction

**Integration points:**
- `using-ring` skill enforces MANDATORY-USER-MESSAGE display
- Hooks feed into existing learning-extract.py pipeline
- Outcomes enable compound-learnings skill pattern detection

---

## Appendix: File Change Summary

| File | Action | Lines Changed |
|------|--------|---------------|
| `shared/lib/context-check.sh` | Modify | +50 (new functions) |
| `default/hooks/context-usage-check.sh` | Modify | +20 (fallback update) |
| `default/skills/using-ring/SKILL.md` | Modify | +40 (context rules) |
| `default/hooks/task-completion-check.sh` | Create | +100 |
| `default/hooks/outcome-inference.sh` | Create | +70 |
| `default/lib/outcome-inference/outcome_inference.py` | Create | +250 |
| `default/hooks/hooks.json` | Modify | +15 (new matchers) |

**Total: ~545 lines of new/modified code**

# Continuity Ledger Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create a session state persistence system that auto-saves ledger files before `/clear` and auto-loads them on session resume, enabling multi-phase implementations to survive context resets with full fidelity.

**Architecture:** A skill-based ledger system with hook integration. Users invoke the skill to create/update ledgers manually, while hooks automatically detect and load active ledgers on SessionStart. PreCompact/Stop hooks auto-save current state.

**Tech Stack:**
- Bash shell scripts (hooks)
- Markdown (ledger files, skill file)
- JSON (hook registration, state output)
- Ring's existing hook infrastructure (`default/hooks/`)

**Global Prerequisites:**
- Environment: macOS/Linux, Bash 4.0+
- Tools: `jq` (recommended for JSON escaping), `bash`, `date`
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
bash --version     # Expected: GNU bash, version 4.0+
jq --version       # Expected: jq-1.x (optional but recommended)
git status         # Expected: clean working tree
ls -la /Users/fredamaral/repos/lerianstudio/ring/default/hooks/  # Expected: session-start.sh exists
```

---

## Phase Overview

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | Tasks 1-3 | Directory structure and skill file |
| Phase 2 | Tasks 4-7 | Session-start hook integration |
| Phase 3 | Tasks 8-11 | Ledger save hook |
| Phase 4 | Tasks 12-14 | Template and documentation |
| Phase 5 | Tasks 15-17 | Integration testing |

---

## Task 1: Create Continuity Ledger Skill Directory

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/`

**Prerequisites:**
- Directory `default/skills/` must exist

**Step 1: Verify parent directory exists**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/skills/`

**Expected output:**
```
drwxr-xr-x  ... brainstorming
drwxr-xr-x  ... condition-based-waiting
... (other skill directories)
```

**Step 2: Create the skill directory**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger`

**Step 3: Verify directory was created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/skills/ | grep continuity`

**Expected output:**
```
drwxr-xr-x  ... continuity-ledger
```

**If Task Fails:**

1. **Permission denied:**
   - Check: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/`
   - Fix: `chmod u+w /Users/fredamaral/repos/lerianstudio/ring/default/skills/`
   - Rollback: N/A (directory creation is idempotent)

---

## Task 2: Create Continuity Ledger SKILL.md

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/SKILL.md`

**Prerequisites:**
- Task 1 completed (directory exists)

**Step 1: Write the skill file**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/SKILL.md` with content:

```markdown
---
name: continuity-ledger
description: |
  Create or update continuity ledger for state preservation across /clear operations.
  Ledgers maintain session state externally, surviving context resets with full fidelity.

trigger: |
  - Before running /clear
  - Context usage approaching 70%+
  - Multi-phase implementations (3+ phases)
  - Complex refactors spanning multiple sessions
  - Any session expected to hit 85%+ context

skip_when: |
  - Quick tasks (< 30 min estimated)
  - Simple single-file bug fixes
  - Already using handoffs for cross-session transfer
  - No multi-phase work in progress
---

# Continuity Ledger

Maintain a ledger file that survives `/clear` for long-running sessions. Unlike handoffs (cross-session), ledgers preserve state within a session.

**Why clear instead of compact?** Each compaction is lossy compression - after several compactions, you're working with degraded context. Clearing + loading the ledger gives you fresh context with full signal.

## When to Use

- Before running `/clear`
- Context usage approaching 70%+
- Multi-day implementations
- Complex refactors you pick up/put down
- Any session expected to hit 85%+ context

## When NOT to Use

- Quick tasks (< 30 min)
- Simple bug fixes
- Single-file changes
- Already using handoffs for cross-session transfer

## Ledger Location

Ledgers are stored in: `$PROJECT_ROOT/.ring/ledgers/`
Format: `CONTINUITY-<session-name>.md`

**Use kebab-case for session name** (e.g., `auth-refactor`, `api-migration`)

## Process

### 1. Determine Ledger File

Check if a ledger already exists:
```bash
ls "$PROJECT_ROOT/.ring/ledgers/CONTINUITY-"*.md 2>/dev/null
```

- **If exists**: Update the existing ledger
- **If not**: Create new file with the template below

### 2. Create/Update Ledger

**REQUIRED SECTIONS (all must be present):**

```markdown
# Session: <name>
Updated: <ISO timestamp>

## Goal
<Success criteria - what does "done" look like?>

## Constraints
<Tech requirements, patterns to follow, things to avoid>

## Key Decisions
<Choices made with brief rationale>
- Decision 1: Chose X over Y because...
- Decision 2: ...

## State
- Done:
  - [x] Phase 1: <completed phase>
  - [x] Phase 2: <completed phase>
- Now: [->] Phase 3: <current focus - ONE thing only>
- Next:
  - [ ] Phase 4: <queued item>
  - [ ] Phase 5: <queued item>

## Open Questions
- UNCONFIRMED: <things needing verification after clear>
- UNCONFIRMED: <assumptions that should be validated>

## Working Set
<Active files, branch, test commands>
- Branch: `feature/xyz`
- Key files: `src/auth/`, `tests/auth/`
- Test cmd: `npm test -- --grep auth`
- Build cmd: `npm run build`
```

### 3. Checkbox States

| Symbol | Meaning |
|--------|---------|
| `[x]` | Completed |
| `[->]` | In progress (current) |
| `[ ]` | Pending |

**Why checkboxes in files:** TodoWrite survives compaction, but the *understanding* around those todos degrades each time context is compressed. File-based checkboxes are never compressed - full fidelity preserved.

### 4. Update Guidelines

**When to update the ledger:**
- Session start: Read and refresh
- After major decisions
- Before `/clear`
- At natural breakpoints
- When context usage >70%

**What to update:**
- Move completed items from "Now" to "Done" (change `[->]` to `[x]`)
- Update "Now" with current focus
- Add new decisions as they're made
- Mark items as UNCONFIRMED if uncertain

### 5. After Clear Recovery

When resuming after `/clear`:

1. **Ledger loads automatically** (SessionStart hook)
2. **Find `[->]` marker** to see current phase
3. **Review UNCONFIRMED items**
4. **Ask 1-3 targeted questions** to validate assumptions
5. **Update ledger** with clarifications
6. **Continue work** with fresh context

## Template Response

After creating/updating the ledger, respond:

```
Continuity ledger updated: .ring/ledgers/CONTINUITY-<name>.md

Current state:
- Done: <summary of completed phases>
- Now: <current focus>
- Next: <upcoming phases>

Ready for /clear - ledger will reload on resume.
```

## UNCONFIRMED Prefix

Mark uncertain items explicitly:

```markdown
## Open Questions
- UNCONFIRMED: Does the auth middleware need updating?
- UNCONFIRMED: Are we using v2 or v3 of the API?
```

After `/clear`, these prompt you to verify before proceeding.

## Comparison with Other Tools

| Tool | Scope | Fidelity |
|------|-------|----------|
| CLAUDE.md | Project | Always fresh, stable patterns |
| TodoWrite | Turn | Survives compaction, but understanding degrades |
| CONTINUITY-*.md | Session | External file - never compressed, full fidelity |
| Handoffs | Cross-session | External file - detailed context for new session |

## Example

```markdown
# Session: auth-refactor
Updated: 2025-01-15T14:30:00Z

## Goal
Replace JWT auth with session-based auth. Done when all tests pass and no JWT imports remain.

## Constraints
- Must maintain backward compat for 2 weeks (migration period)
- Use existing Redis for session storage
- No new dependencies

## Key Decisions
- Session tokens: UUID v4 (simpler than signed tokens for our use case)
- Storage: Redis with 24h TTL (matches current JWT expiry)
- Migration: Dual-auth period, feature flag controlled

## State
- Done:
  - [x] Phase 1: Session model
  - [x] Phase 2: Redis integration
  - [x] Phase 3: Login endpoint
- Now: [->] Phase 4: Logout endpoint and session invalidation
- Next:
  - [ ] Phase 5: Middleware swap
  - [ ] Phase 6: Remove JWT
  - [ ] Phase 7: Update tests

## Open Questions
- UNCONFIRMED: Does rate limiter need session awareness?

## Working Set
- Branch: `feature/session-auth`
- Key files: `src/auth/session.ts`, `src/middleware/auth.ts`
- Test cmd: `npm test -- --grep session`
```

## Additional Notes

- **Keep it concise** - Brevity matters for context
- **One "Now" item** - Forces focus, prevents sprawl
- **UNCONFIRMED prefix** - Signals what to verify after clear
- **Update frequently** - Stale ledgers lose value quickly
- **Clear > compact** - Fresh context beats degraded context
```

**Step 2: Verify file was created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/`

**Expected output:**
```
-rw-r--r--  ... SKILL.md
```

**Step 3: Validate YAML frontmatter**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/SKILL.md`

**Expected output:**
```
---
name: continuity-ledger
description: |
  Create or update continuity ledger for state preservation across /clear operations.
...
```

**If Task Fails:**

1. **File not created:**
   - Check: Directory exists with `ls -la .../skills/continuity-ledger/`
   - Fix: Re-run directory creation from Task 1

2. **Invalid YAML:**
   - Check: Ensure `---` delimiters are present
   - Fix: Verify no tabs in YAML section (use spaces only)

---

## Task 3: Commit Skill File

**Files:**
- Modified: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/SKILL.md`

**Prerequisites:**
- Task 2 completed

**Step 1: Stage the new files**

Run: `cd /Users/fredamaral/repos/lerianstudio/ring && git add default/skills/continuity-ledger/`

**Step 2: Create commit**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git commit -m "$(cat <<'EOF'
feat(context): add continuity-ledger skill for session state persistence

Add new skill that enables users to create and maintain ledger files
that preserve session state across /clear operations. Ledgers track
multi-phase implementations with checkboxes and survive context resets.
EOF
)"
```

**Expected output:**
```
[main ...] feat(context): add continuity-ledger skill for session state persistence
 1 file changed, ... insertions(+)
 create mode 100644 default/skills/continuity-ledger/SKILL.md
```

**Step 3: Verify commit**

Run: `git log --oneline -1`

**Expected output:**
```
<hash> feat(context): add continuity-ledger skill for session state persistence
```

**If Task Fails:**

1. **Nothing to commit:**
   - Check: `git status` (files may already be staged)
   - Fix: Ensure files exist before staging

2. **Pre-commit hook fails:**
   - Check: Read hook output for specific error
   - Fix: Address issues, then `git add . && git commit -m "..."`

---

## Task 4: Create Ledger Detection Function

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Prerequisites:**
- Tasks 1-3 completed

**Step 1: Read current session-start.sh**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Expected:** File exists with current hook implementation (as read earlier)

**Step 2: Add ledger detection function after DOUBT_QUESTIONS variable**

Insert the following function after line 92 (after the `DOUBT_QUESTIONS` variable ends):

```bash
# Detect and load active continuity ledger
detect_active_ledger() {
    local project_root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    local ledger_dir="${project_root}/.ring/ledgers"
    local active_ledger=""
    local ledger_content=""

    # Check if ledger directory exists
    if [[ ! -d "$ledger_dir" ]]; then
        echo ""
        return 0
    fi

    # Find most recently modified ledger
    active_ledger=$(find "$ledger_dir" -name "CONTINUITY-*.md" -type f 2>/dev/null | \
        xargs ls -t 2>/dev/null | head -1)

    if [[ -z "$active_ledger" ]]; then
        echo ""
        return 0
    fi

    # Read ledger content
    ledger_content=$(cat "$active_ledger" 2>/dev/null || echo "")

    if [[ -z "$ledger_content" ]]; then
        echo ""
        return 0
    fi

    # Extract current phase (line with [->] marker)
    local current_phase=""
    current_phase=$(grep -E '\[->?\]' "$active_ledger" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//' || echo "")

    # Format output
    local ledger_name
    ledger_name=$(basename "$active_ledger" .md)

    cat <<LEDGER_EOF
## Active Continuity Ledger: ${ledger_name}

**Current Phase:** ${current_phase:-"No active phase marked"}

<continuity-ledger-content>
${ledger_content}
</continuity-ledger-content>

**Instructions:**
1. Review the State section - find [->] for current work
2. Check Open Questions for UNCONFIRMED items
3. Continue from where you left off
LEDGER_EOF
}
```

**Step 3: Verify function is syntactically correct**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Expected output:** (no output = syntax OK)

**If you see errors:** Check for missing quotes or unmatched brackets

**If Task Fails:**

1. **Syntax error:**
   - Check: Run `bash -n` to identify line number
   - Fix: Compare with template above
   - Rollback: `git checkout -- default/hooks/session-start.sh`

---

## Task 5: Integrate Ledger into Hook Output

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Prerequisites:**
- Task 4 completed

**Step 1: Add ledger detection call before JSON output**

Find the line (around line 131):
```bash
skills_overview=$(generate_skills_overview || echo "Error generating skills quick reference")
```

Add after it:
```bash
# Detect active ledger (if any)
ledger_context=$(detect_active_ledger)
```

**Step 2: Add ledger escaping**

Find the line (around line 159):
```bash
doubt_questions_escaped=$(json_escape "$DOUBT_QUESTIONS")
```

Add after it:
```bash
ledger_context_escaped=$(json_escape "$ledger_context")
```

**Step 3: Update JSON output to include ledger**

Find the JSON output section (around line 163-169) that looks like:
```bash
cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "<ring-critical-rules>\n${critical_rules_escaped}\n</ring-critical-rules>\n\n<ring-doubt-questions>\n${doubt_questions_escaped}\n</ring-doubt-questions>\n\n<ring-skills-system>\n${overview_escaped}\n</ring-skills-system>"
  }
}
EOF
```

Replace with:
```bash
# Build additionalContext with optional ledger section
additional_context="<ring-critical-rules>\n${critical_rules_escaped}\n</ring-critical-rules>\n\n<ring-doubt-questions>\n${doubt_questions_escaped}\n</ring-doubt-questions>\n\n<ring-skills-system>\n${overview_escaped}\n</ring-skills-system>"

# Append ledger context if present
if [[ -n "$ledger_context" ]]; then
    additional_context="${additional_context}\n\n<ring-continuity-ledger>\n${ledger_context_escaped}\n</ring-continuity-ledger>"
fi

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "${additional_context}"
  }
}
EOF
```

**Step 4: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Expected output:** (no output = syntax OK)

**If Task Fails:**

1. **JSON malformed:**
   - Check: Ensure no unescaped quotes in ledger content
   - Fix: The `json_escape` function should handle this
   - Rollback: `git checkout -- default/hooks/session-start.sh`

---

## Task 6: Test Ledger Detection Manually

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Prerequisites:**
- Task 5 completed

**Step 1: Create test ledger directory**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers
```

**Step 2: Create test ledger file**

Run:
```bash
cat > /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-test-session.md <<'EOF'
# Session: test-session
Updated: 2025-12-27T12:00:00Z

## Goal
Test that ledger detection works correctly.

## Constraints
- Must output JSON
- Must escape content properly

## Key Decisions
- Using bash for hook implementation

## State
- Done:
  - [x] Phase 1: Create test
- Now: [->] Phase 2: Verify detection
- Next:
  - [ ] Phase 3: Clean up

## Open Questions
- UNCONFIRMED: Does escaping work for special chars?

## Working Set
- Branch: `main`
- Key files: `default/hooks/session-start.sh`
EOF
```

**Step 3: Run hook and verify output**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_PROJECT_DIR="$(pwd)" echo '{"type": "startup"}' | default/hooks/session-start.sh | jq .
```

**Expected output:** Valid JSON with `additionalContext` containing:
- `<ring-continuity-ledger>` section
- Ledger content including "test-session"
- Current phase showing "Phase 2: Verify detection"

**Step 4: Verify ledger content is present**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_PROJECT_DIR="$(pwd)" echo '{"type": "startup"}' | default/hooks/session-start.sh | \
jq -r '.hookSpecificOutput.additionalContext' | grep -c "CONTINUITY-test-session"
```

**Expected output:**
```
1
```

**If Task Fails:**

1. **jq parse error:**
   - Check: Run without `| jq .` to see raw output
   - Fix: Check for unescaped characters in test ledger

2. **Ledger not found:**
   - Check: `ls -la .ring/ledgers/`
   - Fix: Ensure file was created with correct path

---

## Task 7: Commit Session-Start Hook Changes

**Files:**
- Modified: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`

**Prerequisites:**
- Task 6 completed (tests pass)

**Step 1: Stage changes**

Run: `cd /Users/fredamaral/repos/lerianstudio/ring && git add default/hooks/session-start.sh`

**Step 2: Commit**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git commit -m "$(cat <<'EOF'
feat(context): add ledger detection to session-start hook

SessionStart hook now detects active continuity ledgers in .ring/ledgers/
and loads their content into additionalContext. This enables automatic
state restoration after /clear operations.
EOF
)"
```

**Expected output:**
```
[main ...] feat(context): add ledger detection to session-start hook
 1 file changed, ... insertions(+), ... deletions(-)
```

**If Task Fails:**

1. **Pre-commit hook fails:**
   - Check: Review shellcheck warnings
   - Fix: Address any critical issues
   - Retry: `git commit -m "..."`

---

## Task 8: Create Ledger Save Hook Shell Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`

**Prerequisites:**
- Tasks 1-7 completed

**Step 1: Create the hook script**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`:

```bash
#!/usr/bin/env bash
# Ledger save hook - auto-saves active ledger before compaction or stop
# Triggered by: PreCompact, Stop events

set -euo pipefail

# Determine paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEDGER_DIR="${PROJECT_ROOT}/.ring/ledgers"

# Source shared JSON escaping utility
SHARED_LIB="${SCRIPT_DIR}/../../shared/lib"
if [[ -f "${SHARED_LIB}/json-escape.sh" ]]; then
    # shellcheck source=/dev/null
    source "${SHARED_LIB}/json-escape.sh"
else
    # Fallback: define json_escape locally
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

# Find active ledger (most recently modified)
find_active_ledger() {
    if [[ ! -d "$LEDGER_DIR" ]]; then
        echo ""
        return 0
    fi

    find "$LEDGER_DIR" -name "CONTINUITY-*.md" -type f 2>/dev/null | \
        xargs ls -t 2>/dev/null | head -1
}

# Update ledger timestamp
update_ledger_timestamp() {
    local ledger_file="$1"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Update the "Updated:" line if it exists
    if grep -q "^Updated:" "$ledger_file" 2>/dev/null; then
        if [[ "$(uname)" == "Darwin" ]]; then
            # macOS sed requires empty string for -i
            sed -i '' "s/^Updated:.*$/Updated: ${timestamp}/" "$ledger_file"
        else
            # GNU sed
            sed -i "s/^Updated:.*$/Updated: ${timestamp}/" "$ledger_file"
        fi
    fi
}

# Main logic
main() {
    local active_ledger
    active_ledger=$(find_active_ledger)

    if [[ -z "$active_ledger" ]]; then
        # No active ledger - nothing to save
        cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "LedgerSave",
    "message": "No active ledger found. Nothing to save."
  }
}
EOF
        exit 0
    fi

    # Update timestamp
    update_ledger_timestamp "$active_ledger"

    local ledger_name
    ledger_name=$(basename "$active_ledger" .md)

    # Extract current phase for status message
    local current_phase=""
    current_phase=$(grep -E '\[->?\]' "$active_ledger" 2>/dev/null | head -1 | sed 's/^[[:space:]]*//' || echo "")

    local message="Ledger saved: ${ledger_name}.md"
    if [[ -n "$current_phase" ]]; then
        message="${message}\nCurrent phase: ${current_phase}"
    fi
    message="${message}\n\nAfter clear/compact, state will auto-restore on resume."

    local message_escaped
    message_escaped=$(json_escape "$message")

    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "LedgerSave",
    "additionalContext": "${message_escaped}"
  }
}
EOF
}

main "$@"
```

**Step 2: Make script executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`

**Step 3: Verify syntax**

Run: `bash -n /Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`

**Expected output:** (no output = syntax OK)

**If Task Fails:**

1. **Syntax error:**
   - Check: Run `bash -n` to see line number
   - Fix: Compare with template above

---

## Task 9: Test Ledger Save Hook

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`

**Prerequisites:**
- Task 8 completed
- Test ledger from Task 6 still exists

**Step 1: Verify test ledger exists**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/`

**Expected output:**
```
-rw-r--r--  ... CONTINUITY-test-session.md
```

**Step 2: Run hook and verify output**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_PROJECT_DIR="$(pwd)" echo '{}' | default/hooks/ledger-save.sh | jq .
```

**Expected output:**
```json
{
  "hookSpecificOutput": {
    "hookEventName": "LedgerSave",
    "additionalContext": "Ledger saved: CONTINUITY-test-session.md\nCurrent phase: Now: [->] Phase 2: Verify detection\n\nAfter clear/compact, state will auto-restore on resume."
  }
}
```

**Step 3: Verify timestamp was updated**

Run: `grep "^Updated:" /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-test-session.md`

**Expected output:** Today's date in ISO format:
```
Updated: 2025-12-27T...Z
```

**If Task Fails:**

1. **jq parse error:**
   - Check: Run without `| jq .` to see raw output
   - Fix: Check json_escape function

2. **Timestamp not updated:**
   - Check: `cat .ring/ledgers/CONTINUITY-test-session.md`
   - Fix: Ensure "Updated:" line exists in test file

---

## Task 10: Register Ledger Save Hook in hooks.json

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 9 completed

**Step 1: Read current hooks.json**

Run: `cat /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected:** Current hook configuration

**Step 2: Update hooks.json to add PreCompact and Stop hooks**

Replace the entire file content with:

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
          }
        ]
      }
    ],
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ledger-save.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ledger-save.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 3: Validate JSON syntax**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:** Formatted JSON with no errors

**If Task Fails:**

1. **jq parse error:**
   - Check: Ensure no trailing commas, matching braces
   - Fix: Validate JSON at jsonlint.com if needed
   - Rollback: `git checkout -- default/hooks/hooks.json`

---

## Task 11: Commit Ledger Save Hook

**Files:**
- Created: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`
- Modified: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 10 completed

**Step 1: Stage changes**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/hooks/ledger-save.sh default/hooks/hooks.json
```

**Step 2: Commit**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git commit -m "$(cat <<'EOF'
feat(context): add ledger-save hook for PreCompact and Stop events

Add hook that auto-saves active continuity ledger before context
compaction or when agent stops. Updates ledger timestamp and notifies
user that state will auto-restore on resume.
EOF
)"
```

**Expected output:**
```
[main ...] feat(context): add ledger-save hook for PreCompact and Stop events
 2 files changed, ... insertions(+)
 create mode 100755 default/hooks/ledger-save.sh
```

**If Task Fails:**

1. **Shellcheck warnings:**
   - Check: Review warnings, address critical issues
   - Fix: Add shellcheck disable comments if needed

---

## Task 12: Create Ledger Template File

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-template.md`

**Prerequisites:**
- Tasks 1-11 completed

**Step 1: Create templates directory**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/templates`

**Step 2: Create the template file**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-template.md`:

```markdown
# Session: <session-name>
Updated: <YYYY-MM-DDTHH:MM:SSZ>

## Goal
<What does "done" look like? Include measurable success criteria.>

## Constraints
<Technical requirements, patterns to follow, things to avoid>
- Constraint 1: ...
- Constraint 2: ...

## Key Decisions
<Choices made with brief rationale>
- Decision 1: Chose X over Y because...
- Decision 2: ...

## State
- Done:
  - [x] Phase 1: <completed phase description>
- Now: [->] Phase 2: <current focus - ONE thing only>
- Next:
  - [ ] Phase 3: <queued item>
  - [ ] Phase 4: <queued item>

## Open Questions
- UNCONFIRMED: <things needing verification after clear>
- UNCONFIRMED: <assumptions that should be validated>

## Working Set
- Branch: `<branch-name>`
- Key files: `<primary file or directory>`
- Test cmd: `<command to run tests>`
- Build cmd: `<command to build>`

---

## Ledger Usage Notes

**Checkbox States:**
- `[x]` = Completed
- `[->]` = In progress (current)
- `[ ]` = Pending

**When to Update:**
- After completing a phase (change `[->]` to `[x]`, move `[->]` to next)
- Before running `/clear`
- When context usage > 70%

**After Clear:**
1. Ledger loads automatically
2. Find `[->]` for current phase
3. Verify UNCONFIRMED items
4. Continue work

**To create a new ledger:**
```bash
cp .ring/templates/CONTINUITY-template.md .ring/ledgers/CONTINUITY-<session-name>.md
```
```

**Step 3: Verify file created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/templates/`

**Expected output:**
```
-rw-r--r--  ... CONTINUITY-template.md
```

**If Task Fails:**

1. **Directory not created:**
   - Check: `ls -la default/`
   - Fix: Re-run mkdir command

---

## Task 13: Create Example Filled Ledger

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-example.md`

**Prerequisites:**
- Task 12 completed

**Step 1: Create example ledger**

Create file `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-example.md`:

```markdown
# Session: context-management-system
Updated: 2025-12-27T14:30:00Z

## Goal
Implement context management system for Ring plugin. Done when:
1. Continuity ledger skill exists and is functional
2. SessionStart hook loads ledgers automatically
3. PreCompact/Stop hooks save ledgers automatically
4. All tests pass

## Constraints
- Must integrate with existing Ring hook infrastructure
- Must use bash for hooks (matching existing patterns)
- Must not break existing session-start.sh functionality
- Ledgers stored in .ring/ledgers/ (not default/ plugin directory)

## Key Decisions
- Ledger location: .ring/ledgers/ (project-level, not plugin-level)
  - Rationale: Ledgers are project-specific state, not plugin artifacts
- Checkpoint marker: [->] for current phase
  - Rationale: Visually distinct from [x] and [ ], grep-friendly
- Hook trigger: PreCompact AND Stop
  - Rationale: Catch both automatic compaction and manual stop

## State
- Done:
  - [x] Phase 1: Create continuity-ledger skill directory
  - [x] Phase 2: Write SKILL.md with full documentation
  - [x] Phase 3: Add ledger detection to session-start.sh
  - [x] Phase 4: Create ledger-save.sh hook
  - [x] Phase 5: Register hooks in hooks.json
- Now: [->] Phase 6: Create templates and documentation
- Next:
  - [ ] Phase 7: Integration testing
  - [ ] Phase 8: Clean up test artifacts

## Open Questions
- UNCONFIRMED: Does Claude Code support PreCompact hook? (need to verify)
- UNCONFIRMED: Should ledger-save.sh also index to artifact database?

## Working Set
- Branch: `main`
- Key files:
  - `default/skills/continuity-ledger/SKILL.md`
  - `default/hooks/session-start.sh`
  - `default/hooks/ledger-save.sh`
- Test cmd: `echo '{}' | default/hooks/ledger-save.sh | jq .`
- Build cmd: N/A (bash scripts)
```

**Step 2: Verify file created**

Run: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/templates/`

**Expected output:**
```
-rw-r--r--  ... CONTINUITY-example.md
-rw-r--r--  ... CONTINUITY-template.md
```

**If Task Fails:**

1. **File not created:**
   - Check: Verify templates directory exists
   - Fix: Re-run mkdir from Task 12

---

## Task 14: Commit Templates

**Files:**
- Created: `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-template.md`
- Created: `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-example.md`

**Prerequisites:**
- Task 13 completed

**Step 1: Stage changes**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/templates/
```

**Step 2: Commit**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && git commit -m "$(cat <<'EOF'
docs(context): add continuity ledger templates

Add template and example files for continuity ledgers:
- CONTINUITY-template.md: Blank template with all required sections
- CONTINUITY-example.md: Filled example showing real usage
EOF
)"
```

**Expected output:**
```
[main ...] docs(context): add continuity ledger templates
 2 files changed, ... insertions(+)
 create mode 100644 default/templates/CONTINUITY-example.md
 create mode 100644 default/templates/CONTINUITY-template.md
```

**If Task Fails:**

1. **Nothing to commit:**
   - Check: `git status` to see what's staged
   - Fix: Ensure files exist before staging

---

## Task 15: Run Code Review

**Prerequisites:**
- Tasks 1-14 completed

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

Dispatch:
- `ring-default:code-reviewer`
- `ring-default:business-logic-reviewer`
- `ring-default:security-reviewer`

All reviewers run simultaneously. Wait for all to complete.

**Step 2: Handle findings by severity**

**Critical/High/Medium Issues:**
- Fix immediately (do NOT add TODO comments)
- Re-run all 3 reviewers after fixes
- Repeat until zero Critical/High/Medium issues remain

**Low Issues:**
- Add `TODO(review):` comments at relevant location
- Format: `TODO(review): [Issue] (reported by [reviewer], severity: Low)`

**Cosmetic/Nitpick Issues:**
- Add `FIXME(nitpick):` comments at relevant location
- Format: `FIXME(nitpick): [Issue] (reported by [reviewer], severity: Cosmetic)`

**Step 3: Proceed only when:**
- Zero Critical/High/Medium issues remain
- All Low issues have TODO(review): comments
- All Cosmetic issues have FIXME(nitpick): comments

**If Task Fails:**

1. **Critical issues found:**
   - Fix: Address each issue per reviewer feedback
   - Re-run: All 3 reviewers again

---

## Task 16: Integration Test - Full Lifecycle

**Files:**
- Test: All created files

**Prerequisites:**
- Task 15 completed (code review passed)

**Step 1: Clean up test artifacts from earlier tasks**

Run:
```bash
rm -rf /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-test-session.md
```

**Step 2: Create fresh test ledger using template**

Run:
```bash
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers && \
cp /Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-template.md \
   /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-integration-test.md
```

**Step 3: Edit test ledger with test values**

Run:
```bash
cat > /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-integration-test.md <<'EOF'
# Session: integration-test
Updated: 2025-12-27T00:00:00Z

## Goal
Verify full ledger lifecycle works correctly.

## Constraints
- Must load on SessionStart
- Must save on PreCompact/Stop

## Key Decisions
- Using integration test to verify

## State
- Done:
  - [x] Phase 1: Create test ledger
- Now: [->] Phase 2: Verify SessionStart loads it
- Next:
  - [ ] Phase 3: Verify Stop saves it

## Open Questions
- UNCONFIRMED: Will timestamp update correctly?

## Working Set
- Branch: `main`
- Key files: `.ring/ledgers/`
- Test cmd: `echo '{"type":"startup"}' | default/hooks/session-start.sh`
EOF
```

**Step 4: Test SessionStart loads ledger**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_PROJECT_DIR="$(pwd)" echo '{"type": "startup"}' | default/hooks/session-start.sh | \
jq -r '.hookSpecificOutput.additionalContext' | grep -c "integration-test"
```

**Expected output:**
```
1
```

**Step 5: Test Stop saves ledger**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
CLAUDE_PROJECT_DIR="$(pwd)" echo '{}' | default/hooks/ledger-save.sh | jq .
```

**Expected output:** JSON with `additionalContext` mentioning "integration-test"

**Step 6: Verify timestamp was updated**

Run:
```bash
grep "^Updated:" /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-integration-test.md
```

**Expected output:** Today's timestamp (not 2025-12-27T00:00:00Z)

**If Task Fails:**

1. **Ledger not detected:**
   - Check: `ls -la .ring/ledgers/`
   - Fix: Ensure file exists with correct naming

2. **Timestamp not updated:**
   - Check: `cat .ring/ledgers/CONTINUITY-integration-test.md`
   - Fix: Verify sed command in ledger-save.sh

---

## Task 17: Clean Up and Final Commit

**Files:**
- Clean: `/Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-integration-test.md`

**Prerequisites:**
- Task 16 completed (all tests pass)

**Step 1: Remove test ledger**

Run:
```bash
rm -f /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers/CONTINUITY-integration-test.md
rmdir /Users/fredamaral/repos/lerianstudio/ring/.ring/ledgers 2>/dev/null || true
rmdir /Users/fredamaral/repos/lerianstudio/ring/.ring 2>/dev/null || true
```

**Step 2: Add .ring to .gitignore if not already**

Run:
```bash
grep -q "^\.ring/$" /Users/fredamaral/repos/lerianstudio/ring/.gitignore || \
echo ".ring/" >> /Users/fredamaral/repos/lerianstudio/ring/.gitignore
```

**Step 3: Verify .gitignore updated**

Run:
```bash
grep "\.ring" /Users/fredamaral/repos/lerianstudio/ring/.gitignore
```

**Expected output:**
```
.ring/
```

**Step 4: Stage and commit .gitignore if changed**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git diff --name-only | grep -q ".gitignore" && \
git add .gitignore && \
git commit -m "chore: add .ring/ to gitignore for ledger storage" || \
echo "No .gitignore changes needed"
```

**Step 5: Final verification**

Run:
```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git log --oneline -5
```

**Expected output:** Recent commits showing:
- feat(context): add continuity-ledger skill
- feat(context): add ledger detection to session-start hook
- feat(context): add ledger-save hook
- docs(context): add continuity ledger templates
- (optional) chore: add .ring/ to gitignore

---

## Summary

**Files Created:**
- `/Users/fredamaral/repos/lerianstudio/ring/default/skills/continuity-ledger/SKILL.md`
- `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/ledger-save.sh`
- `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-template.md`
- `/Users/fredamaral/repos/lerianstudio/ring/default/templates/CONTINUITY-example.md`

**Files Modified:**
- `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-start.sh`
- `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`
- `/Users/fredamaral/repos/lerianstudio/ring/.gitignore`

**Usage:**

1. **Create a ledger:**
   ```bash
   mkdir -p .ring/ledgers
   cp default/templates/CONTINUITY-template.md .ring/ledgers/CONTINUITY-my-feature.md
   # Edit the ledger with your session details
   ```

2. **Use the skill:** Invoke `ring-default:continuity-ledger` to create/update ledgers

3. **Automatic behavior:**
   - On `/clear` or session resume: Ledger content loads into context
   - On PreCompact or Stop: Ledger timestamp is updated

**Verification:**
```bash
# Test ledger detection
mkdir -p .ring/ledgers
echo "# Session: test" > .ring/ledgers/CONTINUITY-test.md
CLAUDE_PROJECT_DIR="$(pwd)" echo '{"type":"startup"}' | default/hooks/session-start.sh | jq .
```

---

**Plan complete and saved to `docs/plans/2025-12-27-context-continuity-ledger.md`.**

Two execution options:

**1. Subagent-Driven (this session)** - Dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?

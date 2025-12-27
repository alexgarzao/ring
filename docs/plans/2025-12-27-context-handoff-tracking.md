# Handoff/Outcome Tracking Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Create a handoff document system that captures session work at transition points, tracks outcomes via user feedback, and integrates with the artifact index for searchable history.

**Architecture:** Session-aware handoff creation skill generates structured markdown documents with YAML frontmatter. A PostToolUse hook indexes handoffs immediately on Write. Stop hook prompts user for outcome (non-blocking skip allowed). Handoffs integrate with Ring's existing execution report format and link to session traces when available.

**Tech Stack:**
- Python 3.8+ (artifact_index.py adaptation, artifact_mark.py)
- Bash (hook wrapper scripts)
- JSON (hook configuration in hooks.json)
- SQLite3 with FTS5 (artifact index database)

**Global Prerequisites:**
- Environment: macOS/Linux, Python 3.8+
- Tools: `python3 --version` (3.8+), `sqlite3 --version` (3.x)
- Access: Write access to `default/` plugin directory
- State: On `main` branch, clean working tree
- Dependency: Artifact Index (Phase 1) MUST be complete

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
python3 --version  # Expected: Python 3.8+
sqlite3 --version  # Expected: 3.x
git status         # Expected: clean working tree on main
ls default/lib/artifact-index/  # Expected: artifact_index.py, artifact_schema.sql exist (Phase 1 complete)
```

---

## Implementation Overview

This plan creates Phase 2 of the Context Management System:

```
Phase 2: Data Capture
├── Task 1-3: Handoff Tracking Skill
├── Task 4-5: Create Handoff Command
├── Task 6-7: Resume Handoff Command
├── Task 8-10: PostToolUse Hook (artifact-index-write.sh)
├── Task 11-13: Stop Hook (session-outcome.sh)
├── Task 14-15: Outcome Marking Script
├── Task 16: Update hooks.json
├── Task 17: Code Review Checkpoint
└── Task 18: Final Verification
```

**Dependency Chain:**
- Artifact Index (Phase 1) -> Handoff Tracking -> Outcome Marking
- Hooks depend on lib scripts being in place

---

## Task 1: Create Handoff Tracking Skill Directory

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Prerequisites:**
- Directory `default/skills/` must exist
- Phase 1 (Artifact Index) complete

**Step 1: Create skill directory**

Run: `mkdir -p /Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking`

**Expected output:**
```
(no output on success)
```

**Step 2: Verify directory creation**

Run: `ls -d /Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking`

**Expected output:**
```
/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking
```

**If Task Fails:**
1. Check parent directory exists: `ls /Users/fredamaral/repos/lerianstudio/ring/default/skills/`
2. Check permissions: `ls -la /Users/fredamaral/repos/lerianstudio/ring/default/`

---

## Task 2: Write Handoff Tracking Skill

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Prerequisites:**
- Task 1 complete (directory exists)

**Step 1: Create SKILL.md**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`:

```markdown
---
name: handoff-tracking
description: |
  Create detailed handoff documents for session transitions. Captures task status,
  learnings, decisions, and next steps in a structured format that gets indexed
  for future retrieval.

trigger: |
  - Session ending or transitioning
  - User runs /create-handoff command
  - Context pressure requiring /clear
  - Completing a major milestone

skip_when: |
  - Quick Q&A session with no implementation
  - No meaningful work to document
  - Session was exploratory with no decisions

related:
  before: [executing-plans, subagent-driven-development]
  after: [artifact-query]
---

# Handoff Tracking

## Overview

Create structured handoff documents that preserve session context for future sessions. Handoffs capture what was done, what worked, what failed, key decisions, and next steps.

**Core principle:** Handoffs are indexed immediately on creation, making them searchable before the session ends.

**Announce at start:** "I'm creating a handoff document to preserve this session's context."

## When to Create Handoffs

| Situation | Action |
|-----------|--------|
| Session ending | ALWAYS create handoff |
| Running /clear | Create handoff BEFORE clear |
| Major milestone complete | Create handoff to checkpoint progress |
| Context at 70%+ | Create handoff, then /clear |
| Blocked and need help | Create handoff with blockers documented |

## Handoff File Location

**Path:** `docs/handoffs/{session-name}/YYYY-MM-DD_HH-MM-SS_{description}.md`

Where:
- `{session-name}` - From active work context (e.g., `context-management`, `auth-feature`)
- `YYYY-MM-DD_HH-MM-SS` - Current timestamp in 24-hour format
- `{description}` - Brief kebab-case description of work done

**Example:** `docs/handoffs/context-management/2025-12-27_14-30-00_handoff-tracking-skill.md`

If no clear session context, use `general/` as the folder name.

## Handoff Document Template

Use this exact structure for all handoff documents:

~~~markdown
---
date: {ISO timestamp with timezone}
session_name: {session-name}
git_commit: {current commit hash}
branch: {current branch}
repository: {repository name}
topic: "{Feature/Task} Implementation"
tags: [implementation, {relevant-tags}]
status: {complete|in_progress|blocked}
outcome: UNKNOWN
root_span_id: {trace ID if available, empty otherwise}
turn_span_id: {turn span ID if available, empty otherwise}
---

# Handoff: {concise description}

## Task Summary
{Description of task(s) worked on and their status: completed, in_progress, blocked.
If following a plan, reference the plan document and current phase.}

## Critical References
{2-3 most important file paths that must be read to continue this work.
Leave blank if none.}
- `path/to/critical/file.md`

## Recent Changes
{Files modified in this session with line references}
- `src/path/to/file.py:45-67` - Added validation logic
- `tests/path/to/test.py:10-30` - New test cases

## Learnings

### What Worked
{Specific approaches that succeeded - these get indexed for future sessions}
- Approach: {description} - worked because {reason}
- Pattern: {pattern name} was effective for {use case}

### What Failed
{Attempted approaches that didn't work - helps future sessions avoid same mistakes}
- Tried: {approach} -> Failed because: {reason}
- Error: {error type} when {action} -> Fixed by: {solution}

### Key Decisions
{Important choices made and WHY - future sessions reference these}
- Decision: {choice made}
  - Alternatives: {other options considered}
  - Reason: {why this choice}

## Files Modified
{Exhaustive list of files created or modified}
- `path/to/new/file.py` - NEW: Description
- `path/to/existing/file.py:100-150` - MODIFIED: Description

## Action Items & Next Steps
{Prioritized list for the next session}
1. {Most important next action}
2. {Second priority}
3. {Additional items}

## Other Notes
{Anything else relevant: codebase locations, useful commands, gotchas}
~~~

## The Process

### Step 1: Gather Session Metadata

```bash
# Get current git state
git rev-parse HEAD        # Commit hash
git branch --show-current # Branch name
git remote get-url origin # Repository

# Get timestamp
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

### Step 2: Determine Session Name

Check for active work context:
1. Recent plan files in `docs/plans/` - extract feature name
2. Recent branch name - use as session context
3. If unclear, use `general`

### Step 3: Write Handoff Document

1. Create handoff directory if needed: `mkdir -p docs/handoffs/{session-name}/`
2. Write handoff file with template structure
3. Fill in all sections with session details
4. Be thorough in learnings - these feed compound learning

### Step 4: Verify Indexing

After writing the handoff, verify it was indexed:

```bash
# Check artifact index updated (if database exists)
sqlite3 .ring/cache/artifact-index/context.db \
  "SELECT id, session_name FROM handoffs ORDER BY indexed_at DESC LIMIT 1"
```

The PostToolUse hook automatically indexes handoffs on Write.

## Integration with Ring

### Execution Reports
When working within dev-team cycles, the handoff's "Recent Changes" and "Files Modified" sections should mirror the execution report format:

| Metric | Include |
|--------|---------|
| Duration | Time spent on session |
| Tasks Completed | X/Y from plan |
| Files Created | N |
| Files Modified | N |
| Tests Added | N |

### Session Traces
If session tracing is enabled (Braintrust, etc.), include:
- `root_span_id` - Main trace ID
- `turn_span_id` - Current turn span

These enable correlation between handoffs and detailed session logs.

## Outcome Tracking

Outcomes are marked AFTER the handoff is created, either:
1. User responds to Stop hook prompt
2. User runs outcome marking command later

**Valid outcomes:**
| Outcome | Meaning |
|---------|---------|
| SUCCEEDED | Task completed successfully |
| PARTIAL_PLUS | Mostly done, minor issues remain |
| PARTIAL_MINUS | Some progress, major issues remain |
| FAILED | Task abandoned or blocked |

Handoffs start with `outcome: UNKNOWN` and get updated when marked.

## Remember

- **Be thorough in Learnings** - These feed the compound learning system
- **Include file:line references** - Makes resumption faster
- **Document WHY not just WHAT** - Decisions without rationale are useless
- **Index happens automatically** - PostToolUse hook handles it
- **Outcome is separate** - Don't try to guess outcome, leave as UNKNOWN
```

**Step 2: Verify file was created**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Expected output:**
```
~190 lines
```

**If Task Fails:**
1. Check directory exists: `ls -d default/skills/handoff-tracking/`
2. Check write permissions

---

## Task 3: Commit Handoff Tracking Skill

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/skills/handoff-tracking/SKILL.md`

**Prerequisites:**
- Task 2 complete

**Step 1: Stage and commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/skills/handoff-tracking/SKILL.md && \
git commit -m "feat(skills): add handoff-tracking skill for session transitions" --trailer "X-Lerian-Ref: 0x1"
```

**Expected output:**
```
[main ...] feat(skills): add handoff-tracking skill for session transitions
 1 file changed, ~190 insertions(+)
 create mode 100644 default/skills/handoff-tracking/SKILL.md
```

---

## Task 4: Create Create-Handoff Command

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`

**Prerequisites:**
- Task 3 complete

**Step 1: Write create-handoff command**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`:

```markdown
---
name: create-handoff
description: Create a handoff document capturing current session state for future resumption
argument-hint: "[session-name] [description]"
---

Create a detailed handoff document that preserves the current session's context, learnings, and next steps for future sessions.

## Usage

```
/create-handoff [session-name] [description]
```

**Arguments:**
- `session-name` (optional): Work stream name (e.g., `auth-feature`, `context-management`)
- `description` (optional): Brief description of the handoff

If arguments not provided, infer from:
1. Recent plan files in `docs/plans/`
2. Current git branch name
3. Ask user if unclear

## Process

### Step 1: Determine Handoff Location

```bash
# Get session context
SESSION_NAME="${1:-$(git branch --show-current | sed 's/^feature\///')}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DESC="${2:-session-handoff}"

# Create directory
mkdir -p "docs/handoffs/${SESSION_NAME}"

# File path
echo "docs/handoffs/${SESSION_NAME}/${TIMESTAMP}_${DESC}.md"
```

### Step 2: Gather Metadata

Run these commands to gather required metadata:

```bash
# Git state
git rev-parse HEAD
git branch --show-current
git remote get-url origin 2>/dev/null || echo "local"

# Timestamp
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

### Step 3: Write Handoff Document

Use the handoff-tracking skill template. Fill in:

1. **Task Summary**: What were you working on? What's the status?
2. **Critical References**: What files MUST be read to continue?
3. **Recent Changes**: What files did you modify (with line numbers)?
4. **Learnings**: What worked? What failed? What decisions were made?
5. **Action Items**: What's next?

### Step 4: Confirm Creation

After writing the handoff, respond:

```
Handoff created: docs/handoffs/{session-name}/{timestamp}_{desc}.md

The handoff has been automatically indexed and will be searchable.

Resume in a new session with:
/resume-handoff docs/handoffs/{session-name}/{timestamp}_{desc}.md
```

## Example

```
User: /create-handoff context-management artifact-index-complete
Assistant: Creating handoff for context-management session...

[Gathers metadata, writes handoff document]

Handoff created: docs/handoffs/context-management/2025-12-27_15-45-00_artifact-index-complete.md

Resume in a new session with:
/resume-handoff docs/handoffs/context-management/2025-12-27_15-45-00_artifact-index-complete.md
```
```

**Step 2: Verify command file**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`

**Expected output:**
First 20 lines showing frontmatter and usage section.

---

## Task 5: Commit Create-Handoff Command

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/create-handoff.md`

**Prerequisites:**
- Task 4 complete

**Step 1: Stage and commit**

```bash
\
git add default/commands/create-handoff.md && \
git commit -m "feat(commands): add create-handoff command" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 6: Create Resume-Handoff Command

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`

**Prerequisites:**
- Task 5 complete

**Step 1: Write resume-handoff command**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`:

```markdown
---
name: resume-handoff
description: Resume work from a handoff document with context analysis and validation
argument-hint: "<path-to-handoff.md>"
---

Resume work from a handoff document through an interactive process. Handoffs contain critical context, learnings, and next steps from previous sessions.

## Usage

```
/resume-handoff <path-to-handoff.md>
/resume-handoff <session-name>
```

**Arguments:**
- `path-to-handoff.md`: Direct path to handoff file
- `session-name`: Session folder name (will find most recent handoff)

## Process

### Step 1: Locate Handoff

**If path provided:** Read the handoff file directly.

**If session-name provided:**
```bash
# Find most recent handoff for session
ls -t docs/handoffs/{session-name}/*.md | head -1
```

**If nothing provided:** List available handoffs:
```bash
find docs/handoffs -name "*.md" -type f | head -10
```

### Step 2: Read and Analyze Handoff

1. Read handoff document completely
2. Extract key sections:
   - Task(s) and their statuses
   - Recent changes
   - Learnings (what worked, what failed)
   - Critical references
   - Action items and next steps

### Step 3: Verify Current State

Check if changes from handoff still exist:

```bash
# Check files mentioned in handoff exist
ls -la {files-from-handoff}

# Check git state
git log --oneline -5
git status
```

### Step 4: Present Analysis

Present to user:
```
I have analyzed the handoff from {date}.

**Original Tasks:**
- [Task 1]: {Status from handoff} -> {Current verification}

**Key Learnings:**
- {Learning} - {Still valid / Changed}

**Recommended Next Actions:**
1. {Most logical next step}
2. {Second priority}

Shall I proceed with {recommended action}?
```

### Step 5: Create Action Plan

Use TodoWrite to create task list from action items.

### Step 6: Begin Implementation

Start with first approved task, referencing learnings from handoff.

## Guidelines

1. **Read entire handoff first** - Do not start work until fully analyzed
2. **Verify current state** - Handoff state may not match current state
3. **Apply learnings** - Use documented patterns and avoid documented failures
4. **Be interactive** - Get user buy-in before starting work

## Common Scenarios

| Scenario | Action |
|----------|--------|
| All changes present | Proceed with next steps |
| Some changes missing | Reconcile differences first |
| Tasks in_progress | Complete unfinished work first |
| Stale handoff | Re-evaluate strategy with user |
```

**Step 2: Verify command file**

Run: `wc -l /Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`

**Expected output:**
```
~100 lines
```

---

## Task 7: Commit Resume-Handoff Command

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/commands/resume-handoff.md`

**Prerequisites:**
- Task 6 complete

**Step 1: Stage and commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/commands/resume-handoff.md && \
git commit -m "feat(commands): add resume-handoff command" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 8: Create PostToolUse Hook Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`

**Prerequisites:**
- Task 7 complete
- Phase 1 artifact_index.py exists

**Step 1: Write artifact-index-write.sh**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`:

```bash
#!/usr/bin/env bash
# PostToolUse hook: Index handoffs/plans immediately on Write
# Core two: Write tool
# Purpose: Immediate indexing for searchability

set -euo pipefail

# Read input from stdin
INPUT=$(cat)

# Extract file path from Write tool output
FILE_PATH=$(echo "$INPUT" | jq -r .tool_input.file_path
//
empty)

if [[ -z "$FILE_PATH" ]]; then
    # No file path in input, skip
    echo {\result\: \continue\}
    exit 0
fi

# Check if file is a handoff or plan
if [[ "$FILE_PATH" == *"/handoffs/"* ]] || [[ "$FILE_PATH" == *"/plans/"* ]]; then
    # Determine project root
    PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
    
    # Path to artifact indexer
    INDEXER="${PROJECT_ROOT}/.ring/lib/artifact-index/artifact_index.py"
    
    # Alternative: plugin lib location
    if [[ ! -f "$INDEXER" ]]; then
        INDEXER="${CLAUDE_PLUGIN_ROOT:-}/lib/artifact-index/artifact_index.py"
    fi
    
    if [[ -f "$INDEXER" ]]; then
        # Index the single file (fast path)
        python3 "$INDEXER" --file "$FILE_PATH" 2>/dev/null || true
    fi
fi

# Continue processing
cat << HOOKEOF
{
  "result": "continue"
}
HOOKEOF
```

**Step 2: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`

**Step 3: Verify script**

Run: `head -20 /Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`

---

## Task 9: Test PostToolUse Hook

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`

**Prerequisites:**
- Task 8 complete

**Step 1: Test with mock input**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
echo {\tool_input\: {\file_path\: \docs/handoffs/test/test.md\}} | \
./default/hooks/artifact-index-write.sh
```

**Expected output:**
```json
{
  "result": "continue"
}
```

**Step 2: Verify no errors**

Run: `echo $?`

**Expected output:**
```
0
```

---

## Task 10: Commit PostToolUse Hook

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/artifact-index-write.sh`

**Prerequisites:**
- Task 9 complete

**Step 1: Stage and commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/hooks/artifact-index-write.sh && \
git commit -m "feat(hooks): add PostToolUse hook for artifact indexing on Write" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 11: Create Stop Hook Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh`

**Prerequisites:**
- Task 10 complete

**Step 1: Write session-outcome.sh**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh`:

```bash
#!/usr/bin/env bash
# Stop hook: Prompt for session outcome
# Purpose: Capture user feedback on session success/failure
# Note: Non-blocking - user can skip

set -euo pipefail

# Read input from stdin
INPUT=$(cat)

# Determine project root
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Check if any handoffs exist from this session
HANDOFFS_DIR="${PROJECT_ROOT}/docs/handoffs"
if [[ ! -d "$HANDOFFS_DIR" ]]; then
    # No handoffs directory, skip outcome prompt
    cat << HOOKEOF
{
  "result": "continue"
}
HOOKEOF
    exit 0
fi

# Find most recent handoff (created in last hour)
RECENT_HANDOFF=$(find "$HANDOFFS_DIR" -name "*.md" -mmin -60 -type f 2>/dev/null | head -1)

if [[ -z "$RECENT_HANDOFF" ]]; then
    # No recent handoff, skip outcome prompt
    cat << HOOKEOF
{
  "result": "continue"
}
HOOKEOF
    exit 0
fi

# Extract handoff filename for display
HANDOFF_NAME=$(basename "$RECENT_HANDOFF")

# Return message prompting for outcome
# Note: The actual prompt will be handled by the agent using AskUserQuestion
cat << HOOKEOF
{
  "result": "continue",
  "message": "Session ending. Recent handoff found: ${HANDOFF_NAME}\\n\\nWhen you mark the session outcome, use:\\npython3 .ring/lib/artifact-index/artifact_mark.py --handoff <id> --outcome <SUCCEEDED|PARTIAL_PLUS|PARTIAL_MINUS|FAILED>\\n\\nTo find handoff ID: sqlite3 .ring/cache/artifact-index/context.db \\\"SELECT id, session_name FROM handoffs ORDER BY indexed_at DESC LIMIT 5\\\""
}
HOOKEOF
```

**Step 2: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh`

---

## Task 12: Test Stop Hook

**Files:**
- Test: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh`

**Prerequisites:**
- Task 11 complete

**Step 1: Test with empty project**

```bash
cd /tmp && \
echo {}} | /Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh
```

**Expected output:**
```json
{
  "result": "continue"
}
```

(Should continue without message since no handoffs exist in /tmp)

---

## Task 13: Commit Stop Hook

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/session-outcome.sh`

**Prerequisites:**
- Task 12 complete

**Step 1: Stage and commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/hooks/session-outcome.sh && \
git commit -m "feat(hooks): add Stop hook for session outcome prompting" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 14: Create Outcome Marking Script

**Files:**
- Create: `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py`

**Prerequisites:**
- Task 13 complete
- Phase 1 artifact_index.py exists

**Step 1: Write artifact_mark.py**

Write this content to `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py`:

```python
#!/usr/bin/env python3
"""
USAGE: artifact_mark.py --handoff ID --outcome OUTCOME [--notes NOTES] [--db PATH]

Mark a handoff with user outcome in the artifact index database.

This updates the handoff outcome and sets confidence to HIGH to indicate
user verification. Used for improving future session recommendations.

Examples:
    # Mark a handoff as succeeded
    python3 artifact_mark.py --handoff abc123 --outcome SUCCEEDED

    # Mark with additional notes
    python3 artifact_mark.py --handoff abc123 --outcome PARTIAL_PLUS --notes "Almost done"

    # List handoffs to find IDs
    sqlite3 .ring/cache/artifact-index/context.db \
        "SELECT id, session_name, task_summary FROM handoffs ORDER BY indexed_at DESC LIMIT 10"
"""

import argparse
import sqlite3
from pathlib import Path
from typing import Optional


def get_db_path(custom_path: Optional[str] = None) -> Path:
    """Get database path."""
    if custom_path:
        return Path(custom_path)
    return Path(".ring/cache/artifact-index/context.db")


def main():
    parser = argparse.ArgumentParser(
        description="Mark handoff outcome in artifact index",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --handoff abc123 --outcome SUCCEEDED
  %(prog)s --handoff abc123 --outcome PARTIAL_PLUS --notes "One test failing"
"""
    )
    parser.add_argument("--handoff", required=True, help="Handoff ID to mark")
    parser.add_argument(
        "--outcome",
        required=True,
        choices=["SUCCEEDED", "PARTIAL_PLUS", "PARTIAL_MINUS", "FAILED"],
        help="Outcome of the handoff"
    )
    parser.add_argument("--notes", default="", help="Optional notes about outcome")
    parser.add_argument("--db", type=str, help="Custom database path")

    args = parser.parse_args()

    db_path = get_db_path(args.db)

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        print("Run artifact_index.py --all to create the database first.")
        return 1

    conn = sqlite3.connect(db_path)

    # Check if handoff exists
    cursor = conn.execute(
        "SELECT id, session_name, task_summary FROM handoffs WHERE id = ?",
        (args.handoff,)
    )
    handoff = cursor.fetchone()

    if not handoff:
        print(f"Error: Handoff not found: {args.handoff}")
        print("\\nAvailable handoffs:")
        cursor = conn.execute(
            "SELECT id, session_name, task_summary FROM handoffs ORDER BY indexed_at DESC LIMIT 10"
        )
        for row in cursor.fetchall():
            summary = row[2][:60] + "..." if row[2] and len(row[2]) > 60 else row[2]
            print(f"  {row[0]}: {row[1]} - {summary}")
        conn.close()
        return 1

    # Update the handoff
    cursor = conn.execute(
        "UPDATE handoffs SET outcome = ?, outcome_notes = ?, confidence = HIGH WHERE id = ?",
        (args.outcome, args.notes, args.handoff)
    )

    if cursor.rowcount == 0:
        print(f"Error: Failed to update handoff: {args.handoff}")
        conn.close()
        return 1

    conn.commit()

    # Show confirmation
    print(f"Marked handoff {args.handoff} as {args.outcome}")
    print(f"  Session: {handoff[1]}")
    if handoff[2]:
        summary = handoff[2][:80] + "..." if len(handoff[2]) > 80 else handoff[2]
        print(f"  Summary: {summary}")
    if args.notes:
        print(f"  Notes: {args.notes}")
    print(f"  Confidence: HIGH (user-verified)")

    conn.close()
    return 0


if __name__ == "__main__":
    exit(main())
```

**Step 2: Make executable**

Run: `chmod +x /Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py`

---

## Task 15: Commit Outcome Marking Script

**Files:**
- Stage: `/Users/fredamaral/repos/lerianstudio/ring/default/lib/artifact-index/artifact_mark.py`

**Prerequisites:**
- Task 14 complete

**Step 1: Stage and commit**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/lib/artifact-index/artifact_mark.py && \
git commit -m "feat(lib): add artifact_mark.py for outcome tracking" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 16: Update hooks.json

**Files:**
- Modify: `/Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Prerequisites:**
- Task 15 complete

**Step 1: Update hooks.json to register new hooks**

Add the PostToolUse and Stop hooks to the existing hooks.json:

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
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-outcome.sh"
          }
        ]
      }
    ]
  }
}
```

**Step 2: Verify JSON is valid**

Run: `jq . /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json`

**Expected output:**
Valid JSON with new hooks sections.

**Step 3: Commit hooks.json**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
git add default/hooks/hooks.json && \
git commit -m "feat(hooks): register PostToolUse and Stop hooks for handoff tracking" --trailer "X-Lerian-Ref: 0x1"
```

---

## Task 17: Code Review Checkpoint

**Prerequisites:**
- Tasks 1-16 complete

**Step 1: Dispatch all 3 reviewers in parallel**

REQUIRED SUB-SKILL: Use requesting-code-review

All reviewers run simultaneously:
- code-reviewer
- business-logic-reviewer  
- security-reviewer

**Step 2: Handle findings by severity**

| Severity | Action |
|----------|--------|
| Critical/High/Medium | Fix immediately, re-run all reviewers |
| Low | Add `TODO(review):` comment |
| Cosmetic | Add `FIXME(nitpick):` comment |

**Step 3: Proceed when**

- Zero Critical/High/Medium issues remain
- All Low issues have TODO comments
- All Cosmetic issues have FIXME comments

---

## Task 18: Final Verification

**Prerequisites:**
- Task 17 complete (code review passed)

**Step 1: Verify all files exist**

```bash
cd /Users/fredamaral/repos/lerianstudio/ring && \
ls -la default/skills/handoff-tracking/SKILL.md && \
ls -la default/commands/create-handoff.md && \
ls -la default/commands/resume-handoff.md && \
ls -la default/hooks/artifact-index-write.sh && \
ls -la default/hooks/session-outcome.sh && \
ls -la default/lib/artifact-index/artifact_mark.py
```

**Expected output:**
All files listed with appropriate permissions.

**Step 2: Verify hooks.json updated**

```bash
jq ".hooks.PostToolUse, .hooks.Stop" /Users/fredamaral/repos/lerianstudio/ring/default/hooks/hooks.json
```

**Expected output:**
PostToolUse and Stop hook configurations.

**Step 3: Test end-to-end flow**

```bash
# Create test handoff directory
mkdir -p /Users/fredamaral/repos/lerianstudio/ring/docs/handoffs/test

# The Write tool will trigger artifact-index-write.sh hook
# The Stop event will trigger session-outcome.sh hook
```

---

## If Task Fails

**General recovery steps:**

1. **File creation failed:**
   - Check parent directory exists
   - Check write permissions
   - Rollback: `git checkout -- <file>`

2. **Hook not triggering:**
   - Verify hooks.json is valid JSON: `jq . default/hooks/hooks.json`
   - Check hook script is executable: `chmod +x default/hooks/<script>.sh`
   - Check CLAUDE_PLUGIN_ROOT is set

3. **Database not found:**
   - Phase 1 may not be complete
   - Run: `python3 default/lib/artifact-index/artifact_index.py --all`

4. **Cannot recover:**
   - Document what failed and why
   - Return to human partner
   - Do not guess

---

## Success Criteria

| Criteria | Verification |
|----------|--------------|
| Handoff skill exists | `ls default/skills/handoff-tracking/SKILL.md` |
| Commands exist | `ls default/commands/*-handoff.md` |
| Hooks registered | `jq ".hooks.PostToolUse, .hooks.Stop" default/hooks/hooks.json` |
| Hooks executable | `ls -la default/hooks/*.sh \| grep x` |
| Outcome marking works | `python3 default/lib/artifact-index/artifact_mark.py --help` |
| Code review passed | Zero Critical/High/Medium issues |

---

## Plan Complete

**Files created:**
- `default/skills/handoff-tracking/SKILL.md` - Handoff creation skill
- `default/commands/create-handoff.md` - /create-handoff command
- `default/commands/resume-handoff.md` - /resume-handoff command
- `default/hooks/artifact-index-write.sh` - PostToolUse hook for indexing
- `default/hooks/session-outcome.sh` - Stop hook for outcome prompting
- `default/lib/artifact-index/artifact_mark.py` - Outcome marking script

**Files modified:**
- `default/hooks/hooks.json` - Added PostToolUse and Stop hook registrations

**Next Phase:** Context Usage Warnings (Phase 3) or Compound Learnings (Phase 4)


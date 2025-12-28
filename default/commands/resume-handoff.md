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

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: handoff-tracking
```

The skill contains the complete workflow with:
- Handoff location and reading process
- State verification procedures
- Action plan creation
- Learnings application
- Interactive resumption guidelines

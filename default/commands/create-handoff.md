---
name: ring:create-handoff
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

---

## MANDATORY: Load Full Skill

**This command MUST load the skill for complete workflow execution.**

```
Use Skill tool: handoff-tracking
```

The skill contains the complete workflow with:
- Handoff document template
- Metadata gathering process
- Automatic indexing integration
- Outcome tracking
- Session trace correlation

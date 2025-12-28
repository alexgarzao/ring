---
name: compound-learnings
description: |
  Use when asked to "analyze learnings", "find patterns", "what should become rules",
  "compound my learnings", or after accumulating 5+ session learnings. Analyzes
  session learnings to detect recurring patterns (3+ occurrences), categorizes them
  as rule/skill/hook candidates, and generates proposals for user approval.

trigger: |
  - "What patterns should become permanent?"
  - "Analyze my learnings"
  - "Compound learnings"
  - "Turn learnings into rules"
  - After completing a feature with multiple sessions

skip_when: |
  - Fewer than 3 learning files exist
  - Just completed first session (no patterns to detect yet)
  - Looking for specific past learning (use artifact search instead)

related:
  complementary: [handoff-tracking, artifact-query]
---

# Compound Learnings

Transform ephemeral session learnings into permanent, compounding capabilities.

## Overview

This skill analyzes accumulated learnings from past sessions, detects recurring patterns (appearing in 3+ sessions), and generates proposals for new rules, skills, or hooks. User approval is REQUIRED before creating any permanent artifacts.

**Core Principle:** The system improves itself over time by learning from successes and failures.

## When to Use

- "What should I learn from recent sessions?"
- "Improve my setup based on recent work"
- "Turn learnings into skills/rules"
- "What patterns should become permanent?"
- "Compound my learnings"
- After completing a multi-session feature

## When NOT to Use

- Fewer than 3 learning files exist (insufficient data)
- Looking for a specific past learning (use artifact search)
- First session on a new project (no history yet)

## Process

### Step 1: Gather Learnings

```bash
# List learnings (most recent first)
ls -t $PROJECT_ROOT/.ring/cache/learnings/*.md 2>/dev/null | head -20

# Count total learnings
ls $PROJECT_ROOT/.ring/cache/learnings/*.md 2>/dev/null | wc -l
```

**If fewer than 3 files:** STOP. Insufficient data for pattern detection.

Read the most recent 5-10 files for analysis.

### Step 2: Extract and Consolidate Patterns

For each learnings file, extract entries from:

| Section Header | What to Extract |
|----------------|-----------------|
| `## What Worked` | Success patterns |
| `## What Failed` | Anti-patterns (invert to rules) |
| `## Key Decisions` | Design principles |
| `## Patterns` | Direct pattern candidates |

**Consolidate similar patterns before counting:**

| Raw Patterns | Consolidated To |
|--------------|-----------------|
| "Check artifacts before editing", "Verify outputs first", "Look before editing" | "Observe outputs before editing code" |
| "TDD approach", "Test-driven development", "Write tests first" | "Use TDD workflow" |

Use the most general formulation.

### Step 3: Detect Recurring Patterns

**Signal thresholds:**

| Occurrences | Action |
|-------------|--------|
| 1 | Skip (insufficient signal) |
| 2 | Consider - present to user for information only |
| 3+ | Strong signal - recommend creating permanent artifact |
| 4+ | Definitely create |

**Only patterns appearing in 3+ DIFFERENT sessions qualify for proposals.**

### Step 4: Categorize Patterns

For each qualifying pattern, determine artifact type:

```
Is it a sequence of commands/steps?
  → YES → SKILL (executable process)
  → NO ↓

Should it run automatically on an event?
  → YES → HOOK (SessionEnd, PostToolUse, etc.)
  → NO ↓

Is it "when X, do Y" or "never do X"?
  → YES → RULE (behavioral heuristic)
  → NO → Skip (not worth capturing)
```

**Examples:**

| Pattern | Type | Why |
|---------|------|-----|
| "Run tests before committing" | Hook (PreCommit) | Automatic gate |
| "Step-by-step debugging process" | Skill | Manual sequence |
| "Always use explicit file paths" | Rule | Behavioral heuristic |

### Step 5: Generate Proposals

Present each proposal in this format:

```markdown
---
## Pattern: [Generalized Name]

**Signal:** [N] sessions ([list session IDs])

**Category:** [rule / skill / hook]

**Rationale:** [Why this artifact type, why worth creating]

**Draft Content:**
[Preview of what would be created]

**Target Location:** `.ring/generated/rules/[name].md` or `.ring/generated/skills/[name]/SKILL.md`

**Your Action:** [APPROVE] / [REJECT] / [MODIFY]

---
```

### Step 6: WAIT FOR USER APPROVAL

**CRITICAL: DO NOT create any files without explicit user approval.**

User must explicitly say:
- "Approve" or "Create it" → Proceed to create
- "Reject" or "Skip" → Mark as rejected, do not create
- "Modify" → User provides changes, then re-propose

**NEVER assume approval. NEVER create without explicit consent.**

### Step 7: Create Approved Artifacts

#### Before Creating Any Artifact:
Ensure the target directories exist:
```bash
mkdir -p $PROJECT_ROOT/.ring/generated/rules
mkdir -p $PROJECT_ROOT/.ring/generated/skills
mkdir -p $PROJECT_ROOT/.ring/generated/hooks
```

#### For Rules:

Create file at `.ring/generated/rules/<slug>.md` with:
- Rule name and context
- Pattern description
- DO / DON'T sections
- Source sessions

#### For Skills:

Create directory `.ring/generated/skills/<slug>/` with `SKILL.md` containing:
- YAML frontmatter (name, description)
- Overview (what it does)
- When to Use (triggers)
- When NOT to Use
- Step-by-step process
- Source sessions

**Note:** Generated skills are project-local. To make them discoverable, add to your project's `CLAUDE.md`:
```markdown
## Project-Specific Skills
See `.ring/generated/skills/` for learnings-based skills.
```

#### For Hooks:

Create in `.ring/generated/hooks/<name>.sh` following Ring's hook patterns.
Register in project's `.claude/hooks.json` (not plugin's hooks.json).

### Step 8: Archive Processed Learnings

After creating artifacts, move processed learnings:

```bash
# Create archive directory
mkdir -p $PROJECT_ROOT/.ring/cache/learnings/archived

# Move processed files (preserving them for reference)
mv $PROJECT_ROOT/.ring/cache/learnings/2025-*.md $PROJECT_ROOT/.ring/cache/learnings/archived/
```

### Step 9: Summary Report

```markdown
## Compounding Complete

**Learnings Analyzed:** [N] sessions
**Patterns Found:** [M]
**Artifacts Created:** [K]

### Created:
- Rule: `explicit-paths.md` - Always use explicit file paths
- Skill: `systematic-debugging` - Step-by-step debugging workflow

### Skipped (insufficient signal):
- "Pattern X" (2 occurrences - below threshold)

### Rejected by User:
- "Pattern Y" - User chose not to create

**Your setup is now permanently improved.**
```

## Quality Checks

Before creating any artifact:

1. **Is it general enough?** Would it apply in other projects?
2. **Is it specific enough?** Does it give concrete guidance?
3. **Does it already exist?** Check `.ring/generated/rules/` and `.ring/generated/skills/` first
4. **Is it the right type?** Sequences → skills, heuristics → rules

## Common Mistakes

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| Creating without approval | Violates user consent | ALWAYS wait for explicit approval |
| Low-signal patterns | 1-2 occurrences is noise | Require 3+ session occurrences |
| Too specific | Won't apply elsewhere | Generalize to broader principle |
| Too vague | No actionable guidance | Include concrete DO/DON'T |
| Duplicate artifacts | Wastes space, confuses | Check existing rules/skills first |

## Files Reference

**Project-local data (per-project):**
- Learnings input: `.ring/cache/learnings/*.md`
- Proposals: `.ring/cache/proposals/pending.json`
- History: `.ring/cache/proposals/history.json`
- Generated rules: `.ring/generated/rules/<name>.md`
- Generated skills: `.ring/generated/skills/<name>/SKILL.md`
- Generated hooks: `.ring/generated/hooks/<name>.sh`

**Plugin code (shared, read-only):**
- Library: `default/lib/compound_learnings/`
- Skill: `default/skills/compound-learnings/SKILL.md`
- Command: `default/commands/compound-learnings.md`

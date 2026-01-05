# Ring to OpenCode Native Conversion Implementation Plan

> **For Agents:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Convert Ring (Claude Code plugin) to a native OpenCode distribution in a new `opencode/` directory

**Architecture:** Create a separate, maintained OpenCode-native version using OpenCode's singular directory naming conventions (`.opencode/skill/`, `.opencode/agent/`, `.opencode/command/`, `.opencode/plugin/`) with TypeScript plugins replacing bash hooks

**Tech Stack:** Markdown files with YAML frontmatter, TypeScript for plugins, JSON for configuration

**Global Prerequisites:**
- Environment: macOS/Linux, Node.js 18+, TypeScript 5+
- Tools:
  - `node --version` - Expected: v18.0.0+
  - `git --version` - Expected: 2.0+
  - Text editor with YAML support
- Access: Read access to `.references/opencode/` documentation
- State: Working on `main` branch, clean working tree

**Verification before starting:**
```bash
# Run ALL these commands and verify output:
node --version    # Expected: v18.0.0+
git status        # Expected: clean working tree
ls -la .references/opencode/  # Expected: INDEX.md and documentation files
```

## Historical Precedent

**Query:** "opencode conversion migration plugin"
**Index Status:** Populated

### Successful Patterns to Reference
- **ring-multiplatform-adaptation**: Successfully crawled OpenCode documentation (33 pages to .references/opencode/)
  - Documentation structure is well-organized in INDEX.md
  - Reference files available for skills.md, agents.md, commands.md, plugins.md

### Failure Patterns to AVOID
- No failed handoffs found for this topic

### Related Past Plans
- **automatic-context-management.md**: Context injection patterns (may inform plugin design)
- **context-usage-warnings.md**: State management patterns
- **context-handoff-tracking.md**: Session continuity patterns

---

## Conversion Rules Reference

### Skills Transformation

> **IMPORTANT: Metadata Limitation**
> OpenCode's `metadata` field is a **string-to-string map only**. Complex Ring fields (arrays, objects)
> CANNOT be stored directly. Strategy: **Serialize simple values to strings, move complex structures to markdown body.**

| Claude Code Field | OpenCode Field | Action |
|-------------------|----------------|--------|
| `name` | `name` | Keep (must match directory name) |
| `description` | `description` | Keep (max 1024 chars) |
| `trigger` | `metadata.trigger` | Move to metadata (string value only) |
| `skip_when` | `metadata.skip_when` | Move to metadata (string value only) |
| `related` | Body `## Related Skills` | Move to markdown body (object structure) |
| `compliance_rules` | Body `## Compliance Rules` | Move to markdown body (array of objects) |
| `prerequisites` | Body `## Prerequisites` | Move to markdown body (array of objects) |
| `composition` | Body `## Composition` | Move to markdown body (object structure) |
| `sequence` | `metadata.sequence_after`, `metadata.sequence_before` | Flatten to simple strings |
| `input_schema` | Body `## Inputs` | Move to markdown body as documentation |
| `output_schema` | Body `## Expected Output` | Move to markdown body as documentation |
| `examples` | Body `## Examples` | Move to markdown body |
| N/A | `license` | Add: MIT |
| N/A | `compatibility` | Add: opencode |
| N/A | `metadata.source` | Add: ring-default (or appropriate plugin) |

### Agents Transformation
| Claude Code Field | OpenCode Field | Action |
|-------------------|----------------|--------|
| `name` | (filename) | Agent name from filename |
| `description` | `description` | Keep (REQUIRED) |
| `type: reviewer` | `mode: subagent` | Convert type to mode |
| `model: opus` | `model: anthropic/claude-opus-4-5` | Convert shorthand |
| `model: sonnet` | `model: anthropic/claude-sonnet-4` | Convert shorthand |
| N/A | `tools` | Add tool restrictions |
| N/A | `temperature` | Add: 0.1 for reviewers |
| N/A | `permission` | Add if needed |
| **Model Requirement section** | N/A | **STRIP entirely** (handled by frontmatter) |

### Commands Transformation
| Claude Code Field | OpenCode Field | Action |
|-------------------|----------------|--------|
| `name` | (filename) | Command name from filename |
| `description` | `description` | Keep (REQUIRED) |
| `argument-hint` | Document in body | Remove from frontmatter, document usage |
| N/A | `agent` | Add target agent |
| N/A | `model` | Add model if specific needed |
| N/A | `subtask` | Add: true for complex commands |
| Body content | `template` body | EMBED skill logic, use $ARGUMENTS |

### Hooks to Plugins Transformation
| Claude Code Hook | OpenCode Plugin Event | Action |
|------------------|----------------------|--------|
| `session-start.sh` | `session.created` | Convert bash to TypeScript |
| `ledger-save.sh` | `experimental.session.compacting` | Convert context injection |
| `context-usage-check.sh` | `session.idle` | Convert monitoring |
| `artifact-index-write.sh` | `session.updated` | Convert indexing |
| Other hooks | N/A | Skip non-portable features |

---

## Phase 1: Directory Structure Setup

### Task 1.1: Create OpenCode Directory Structure

**Files:**
- Create: `opencode/.opencode/skill/.gitkeep`
- Create: `opencode/.opencode/agent/.gitkeep`
- Create: `opencode/.opencode/command/.gitkeep`
- Create: `opencode/.opencode/plugin/.gitkeep`

**Prerequisites:**
- Git repository is clean
- Working directory is repository root

**Step 1: Create the opencode directory with OpenCode structure**

```bash
mkdir -p opencode/.opencode/skill
mkdir -p opencode/.opencode/agent
mkdir -p opencode/.opencode/command
mkdir -p opencode/.opencode/plugin
```

**Step 2: Verify directory structure**

Run: `tree opencode/`

**Expected output:**
```
opencode/
└── .opencode/
    ├── skill/
    ├── agent/
    ├── command/
    └── plugin/
```

**Step 3: Create .gitkeep files**

```bash
touch opencode/.opencode/skill/.gitkeep
touch opencode/.opencode/agent/.gitkeep
touch opencode/.opencode/command/.gitkeep
touch opencode/.opencode/plugin/.gitkeep
```

**If Task Fails:**
1. Check permissions: `ls -la opencode/`
2. Rollback: `rm -rf opencode/`

---

### Task 1.2: Create OpenCode Configuration File

**Files:**
- Create: `opencode/opencode.json`

**Prerequisites:**
- Task 1.1 completed

**Step 1: Create opencode.json configuration**

> **SECURITY NOTE:** Permissions use restrictive defaults with explicit whitelists.
> Never use `"bash": "allow"` globally - it permits arbitrary command execution.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "version": "1.0.0",
  "name": "ring-opencode",
  "description": "Ring skills library for OpenCode - enforces proven software engineering practices",
  "permission": {
    "skill": {
      "*": "allow"
    },
    "edit": "ask",
    "bash": {
      "git *": "allow",
      "ls *": "allow",
      "pwd": "allow",
      "tree *": "allow",
      "head *": "allow",
      "tail *": "allow",
      "wc *": "allow",
      "find * -name *": "allow",
      "mkdir *": "ask",
      "rm *": "ask",
      "mv *": "ask",
      "cp *": "ask",
      "curl *": "deny",
      "wget *": "deny",
      "*": "ask"
    },
    "webfetch": "ask",
    "external_directory": "ask",
    "doom_loop": "ask"
  },
  "agent": {
    "build": {
      "mode": "primary",
      "model": "anthropic/claude-sonnet-4-20250514"
    },
    "plan": {
      "mode": "primary",
      "model": "anthropic/claude-opus-4-5-20251101",
      "permission": {
        "edit": "ask",
        "bash": "ask"
      }
    }
  }
}
```

**Step 2: Verify JSON is valid**

Run: `cat opencode/opencode.json | python3 -m json.tool`

**Expected output:** Formatted JSON without errors

**If Task Fails:**
1. Check JSON syntax errors
2. Rollback: `rm opencode/opencode.json`

---

### Task 1.3: Create AGENTS.md for OpenCode

**Files:**
- Create: `opencode/AGENTS.md`

**Prerequisites:**
- Task 1.1 completed

**Step 1: Create AGENTS.md**

```markdown
# AGENTS.md - Ring for OpenCode

This file provides guidance to OpenCode when working with code in this repository.

---

## Overview

Ring is a comprehensive skills library that enforces proven software engineering practices through mandatory workflows, parallel code review, and systematic development.

## Available Skills

Skills are loaded on-demand via the native `skill` tool. See `.opencode/skill/` for available skills.

### Core Skills
- `test-driven-development` - RED-GREEN-REFACTOR methodology
- `brainstorming` - Socratic design refinement
- `requesting-code-review` - Parallel 3-reviewer code review
- `systematic-debugging` - 4-phase debugging methodology
- `executing-plans` - Batch task execution with checkpoints

### Development Workflow
1. Use `brainstorming` to refine ideas into designs
2. Use `test-driven-development` for implementation
3. Use `requesting-code-review` before merging
4. Use `systematic-debugging` when issues arise

## Available Agents

Agents are invoked via @ mention or automatically by primary agents.

### Reviewers (subagents)
- `@code-reviewer` - Code quality, architecture, design patterns
- `@security-reviewer` - Security vulnerabilities, data protection
- `@business-logic-reviewer` - Business rules, domain correctness

### Specialist Agents (subagents)
- `@codebase-explorer` - Codebase exploration and analysis
- `@write-plan` - Implementation planning

## Available Commands

Commands are invoked via `/command-name`.

- `/commit` - Atomic commits with intelligent grouping
- `/codereview` - Dispatch all 3 reviewers in parallel
- `/brainstorm` - Start design refinement session

## Compliance Rules

- TDD: Test must fail before implementation
- Review: All 3 reviewers must pass
- Commits: Use conventional commit format

## Key Principles

1. **DRY** - Don't Repeat Yourself
2. **YAGNI** - You Aren't Gonna Need It
3. **TDD** - Test-Driven Development
4. **Frequent commits** - Small, atomic changes
```

**Step 2: Verify file created**

Run: `head -20 opencode/AGENTS.md`

**Expected output:** First 20 lines of the markdown file

---

## Phase 2: Core Skills Conversion (ring-default)

### Task 2.0: Copy shared-patterns Directory

**Files:**
- Source: `default/skills/shared-patterns/*.md`
- Create: `opencode/.opencode/skill/shared-patterns/*.md`

**Prerequisites:**
- Phase 1 completed

**Step 1: Create shared-patterns directory**

```bash
mkdir -p opencode/.opencode/skill/shared-patterns
```

**Step 2: Copy all shared pattern files**

```bash
cp default/skills/shared-patterns/*.md opencode/.opencode/skill/shared-patterns/
```

**Step 3: Verify files copied**

Run: `ls opencode/.opencode/skill/shared-patterns/`

**Expected output:**
```
ai-slop-detection.md
doubt-triggered-questions.md
exit-criteria.md
failure-recovery.md
reviewer-orchestrator-boundary.md
state-tracking.md
todowrite-integration.md
```

**Step 4: Count files**

Run: `ls opencode/.opencode/skill/shared-patterns/*.md | wc -l`

**Expected output:** `7`

**If Task Fails:**
1. Check source directory exists: `ls default/skills/shared-patterns/`
2. Rollback: `rm -rf opencode/.opencode/skill/shared-patterns`

---

### Task 2.1: Convert test-driven-development Skill

**Files:**
- Source: `default/skills/test-driven-development/SKILL.md`
- Create: `opencode/.opencode/skill/test-driven-development/SKILL.md`

**Prerequisites:**
- Phase 1 completed
- Source file exists

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/test-driven-development
```

**Step 2: Create converted SKILL.md**

The converted file MUST have ONLY these frontmatter fields:
- `name` (required)
- `description` (required)
- `license` (optional)
- `compatibility` (optional)
- `metadata` (optional - holds Ring-specific fields)

```yaml
---
name: test-driven-development
description: |
  RED-GREEN-REFACTOR implementation methodology - write failing test first,
  minimal implementation to pass, then refactor. Ensures tests verify behavior.
license: MIT
compatibility: opencode
metadata:
  trigger: |
    - Starting implementation of new feature
    - Starting implementation of bugfix
    - Writing new production code
  skip_when: |
    - Reviewing/modifying existing tests
    - Code already exists without tests
    - Exploratory/spike work
  source: ring-default
---

# Test-Driven Development (TDD)

[... REST OF BODY CONTENT FROM SOURCE - COPY VERBATIM ...]
```

**Step 3: Copy body content from source**

Copy ALL content after the `---` closing frontmatter from the source file.
Do NOT modify the body content.

**Step 4: Verify skill**

Run: `head -30 opencode/.opencode/skill/test-driven-development/SKILL.md`

**Expected output:** YAML frontmatter with only allowed fields, then markdown body

**If Task Fails:**
1. Check frontmatter syntax
2. Verify name matches directory name
3. Rollback: `rm -rf opencode/.opencode/skill/test-driven-development`

---

### Task 2.2: Convert brainstorming Skill

**Files:**
- Source: `default/skills/brainstorming/SKILL.md`
- Create: `opencode/.opencode/skill/brainstorming/SKILL.md`

**Prerequisites:**
- Task 2.1 completed

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/brainstorming
```

**Step 2: Create converted SKILL.md**

```yaml
---
name: brainstorming
description: |
  Socratic design refinement - transforms rough ideas into validated designs through
  structured questioning, alternative exploration, and incremental validation.
license: MIT
compatibility: opencode
metadata:
  trigger: |
    - New feature or product idea (requirements unclear)
    - User says "plan", "design", or "architect" something
    - Multiple approaches seem possible
  skip_when: |
    - Design already complete and validated
    - Have detailed plan ready to execute
    - Just need task breakdown from existing design
  sequence:
    before:
      - writing-plans
      - using-git-worktrees
  source: ring-default
---

# Brainstorming Ideas Into Designs

[... REST OF BODY CONTENT FROM SOURCE - COPY VERBATIM ...]
```

**Step 3: Copy body content from source**

**Step 4: Verify skill**

Run: `head -30 opencode/.opencode/skill/brainstorming/SKILL.md`

---

### Task 2.3: Convert requesting-code-review Skill

**Files:**
- Source: `default/skills/requesting-code-review/SKILL.md`
- Create: `opencode/.opencode/skill/requesting-code-review/SKILL.md`

**Prerequisites:**
- Task 2.2 completed

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/requesting-code-review
```

**Step 2: Read source and create converted SKILL.md**

Transform frontmatter, keeping only allowed fields. Move Ring-specific fields to `metadata:`.

**Step 3: Verify skill**

Run: `head -30 opencode/.opencode/skill/requesting-code-review/SKILL.md`

---

### Task 2.4: Convert systematic-debugging Skill

**Files:**
- Source: `default/skills/systematic-debugging/SKILL.md`
- Create: `opencode/.opencode/skill/systematic-debugging/SKILL.md`

**Prerequisites:**
- Task 2.3 completed

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/systematic-debugging
```

**Step 2: Create converted SKILL.md with transformed frontmatter**

**Step 3: Verify skill**

---

### Task 2.5: Convert executing-plans Skill

**Files:**
- Source: `default/skills/executing-plans/SKILL.md`
- Create: `opencode/.opencode/skill/executing-plans/SKILL.md`

**Prerequisites:**
- Task 2.4 completed

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/executing-plans
```

**Step 2: Create converted SKILL.md**

**Step 3: Verify skill**

---

### Task 2.6: Convert writing-plans Skill

**Files:**
- Source: `default/skills/writing-plans/SKILL.md`
- Create: `opencode/.opencode/skill/writing-plans/SKILL.md`

**Prerequisites:**
- Task 2.5 completed

**Step 1: Create skill directory and converted file**

**Step 2: Verify skill**

---

### Task 2.7: Convert using-ring Skill (rename to using-ring-opencode)

**Files:**
- Source: `default/skills/using-ring/SKILL.md`
- Create: `opencode/.opencode/skill/using-ring-opencode/SKILL.md`

**Prerequisites:**
- Task 2.6 completed

**Step 1: Create skill directory**

```bash
mkdir -p opencode/.opencode/skill/using-ring-opencode
```

**Step 2: Create converted SKILL.md**

NOTE: Rename skill to `using-ring-opencode` to distinguish from Claude Code version.
Update body content to reference OpenCode conventions instead of Claude Code.

**Step 3: Verify skill**

---

### Task 2.8: Convert Skills Batch A (Code Quality)

**Files:**
- Source: `default/skills/{name}/SKILL.md`
- Create: `opencode/.opencode/skill/{name}/SKILL.md`

**Prerequisites:**
- Task 2.7 completed

**Skills in this batch (6):**
1. `exploring-codebase`
2. `verification-before-completion`
3. `receiving-code-review`
4. `dispatching-parallel-agents`
5. `subagent-driven-development`
6. `defense-in-depth`

**For each skill:**
1. Create directory: `mkdir -p opencode/.opencode/skill/{name}`
2. Transform frontmatter (only allowed fields: name, description, license, compatibility, metadata)
3. Move complex fields (compliance_rules, prerequisites, related) to markdown body sections
4. Copy remaining body content verbatim
5. Verify name matches directory name

**Verification:**

Run: `ls opencode/.opencode/skill/ | wc -l`

**Expected output:** `14` (7 from Tasks 2.1-2.7 + 1 shared-patterns + 6 from this batch)

**If Task Fails:**
1. Check frontmatter syntax for each skill
2. Verify no unsupported fields remain in frontmatter
3. Rollback individual skill: `rm -rf opencode/.opencode/skill/{name}`

---

### Task 2.9: Convert Skills Batch B (Development Workflow)

**Files:**
- Source: `default/skills/{name}/SKILL.md`
- Create: `opencode/.opencode/skill/{name}/SKILL.md`

**Prerequisites:**
- Task 2.8 completed

**Skills in this batch (5):**
1. `linting-codebase`
2. `finishing-a-development-branch`
3. `testing-anti-patterns`
4. `root-cause-tracing`
5. `using-git-worktrees`

**For each skill:**
1. Create directory: `mkdir -p opencode/.opencode/skill/{name}`
2. Transform frontmatter (only allowed fields + metadata)
3. Move complex fields to markdown body sections
4. Copy remaining body content verbatim

**Verification:**

Run: `ls opencode/.opencode/skill/ | wc -l`

**Expected output:** `19` (14 from previous + 5 from this batch)

---

### Task 2.10: Convert Skills Batch C (State & Continuity)

**Files:**
- Source: `default/skills/{name}/SKILL.md`
- Create: `opencode/.opencode/skill/{name}/SKILL.md`

**Prerequisites:**
- Task 2.9 completed

**Skills in this batch (5):**
1. `condition-based-waiting`
2. `handoff-tracking`
3. `artifact-query`
4. `compound-learnings`
5. `continuity-ledger`

**For each skill:**
1. Create directory: `mkdir -p opencode/.opencode/skill/{name}`
2. Transform frontmatter (only allowed fields + metadata)
3. Move complex fields to markdown body sections
4. Copy remaining body content verbatim

**Verification:**

Run: `ls opencode/.opencode/skill/ | wc -l`

**Expected output:** `24` (19 from previous + 5 from this batch)

---

### Task 2.11: Convert Skills Batch D (Meta Skills)

**Files:**
- Source: `default/skills/{name}/SKILL.md`
- Create: `opencode/.opencode/skill/{name}/SKILL.md`

**Prerequisites:**
- Task 2.10 completed

**Skills in this batch (5):**
1. `interviewing-user`
2. `writing-skills`
3. `testing-agents-with-subagents`
4. `testing-skills-with-subagents`
5. `release-guide-info`

**For each skill:**
1. Create directory: `mkdir -p opencode/.opencode/skill/{name}`
2. Transform frontmatter (only allowed fields + metadata)
3. Move complex fields to markdown body sections
4. Copy remaining body content verbatim

**Final Phase 2 Verification:**

Run: `ls opencode/.opencode/skill/ | wc -l`

**Expected output:** `29` (28 skills + 1 shared-patterns directory)

Run: `ls opencode/.opencode/skill/*/SKILL.md | wc -l`

**Expected output:** `28` (all skills have SKILL.md)

---

### Task 2.12: Update Internal Path References

**Files:**
- All files in `opencode/.opencode/skill/*/SKILL.md`

**Prerequisites:**
- Task 2.11 completed

**Step 1: Find Ring-specific path references**

```bash
# Find references to old Ring paths
grep -r "default/skills" opencode/.opencode/skill/ || echo "None found"
grep -r "dev-team/skills" opencode/.opencode/skill/ || echo "None found"
grep -r "skills/shared-patterns" opencode/.opencode/skill/ || echo "None found"
```

**Step 2: Update shared-patterns references**

If any references found, update paths:
- Old: `skills/shared-patterns/X.md` or `default/skills/shared-patterns/X.md`
- New: `shared-patterns/X.md` (relative to skill directory)

```bash
# Example fix using sd (if needed)
# sd 'skills/shared-patterns/' 'shared-patterns/' opencode/.opencode/skill/*/SKILL.md
```

**Step 3: Update cross-skill references**

- Old: `default/skills/brainstorming/SKILL.md`
- New: `../brainstorming/SKILL.md` (relative) or just `brainstorming` (skill name)

**Step 4: Verify no Ring-specific paths remain**

Run: `grep -r "default/skills\|dev-team/skills" opencode/.opencode/skill/ | wc -l`

**Expected output:** `0`

**If Task Fails:**
1. Manually inspect files with old paths
2. Use find/replace to update remaining references

---

## Code Review Checkpoint 1

### Task CR1: Run Code Review on Phase 2

**Prerequisites:**
- All Phase 2 tasks completed

**Step 1: Dispatch code review**

REQUIRED SUB-SKILL: Use requesting-code-review

Run all 3 reviewers in parallel:
- code-reviewer
- security-reviewer
- business-logic-reviewer

Focus on:
- Frontmatter field compliance (only allowed fields)
- Name/directory consistency
- Body content preservation

**Step 2: Handle findings by severity**

- **Critical/High/Medium:** Fix immediately, re-run reviewers
- **Low:** Add TODO(review) comments
- **Cosmetic:** Add FIXME(nitpick) comments

**Step 3: Proceed only when zero Critical/High/Medium issues remain**

---

## Phase 3: Core Agents Conversion

### Task 3.1: Convert code-reviewer Agent

**Files:**
- Source: `default/agents/code-reviewer.md`
- Create: `opencode/.opencode/agent/code-reviewer.md`

**Prerequisites:**
- Phase 2 completed

**Step 1: Create converted agent file**

Key transformations:
- `type: reviewer` → `mode: subagent`
- `model: opus` → `model: anthropic/claude-opus-4-5-20251101`
- **STRIP entire "Model Requirement" section** (handled by frontmatter)
- Keep body content (review instructions)

```yaml
---
description: "Foundation Review: Reviews code quality, architecture, design patterns, algorithmic flow, and maintainability. Runs in parallel with business-logic-reviewer and security-reviewer for fast feedback."
mode: subagent
model: anthropic/claude-opus-4-5-20251101
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
permission:
  edit: deny
  bash:
    "git diff": allow
    "git log*": allow
    "git status": allow
    "*": deny
---

# Code Reviewer (Foundation)

You are a Senior Code Reviewer conducting **Foundation** review.

[... REST OF BODY CONTENT - STRIP "Model Requirement" SECTION ...]
```

**Step 2: Strip Model Requirement section from body**

Remove this entire section:
```
## ⚠️ Model Requirement: Claude Opus 4.5+
[... all content until next ## heading ...]
```

**Step 3: Verify agent**

Run: `head -30 opencode/.opencode/agent/code-reviewer.md`

**Expected output:** YAML frontmatter with OpenCode fields, no Model Requirement section

**If Task Fails:**
1. Check frontmatter syntax
2. Verify model format is `provider/model-id`
3. Rollback: `rm opencode/.opencode/agent/code-reviewer.md`

---

### Task 3.2: Convert security-reviewer Agent

**Files:**
- Source: `default/agents/security-reviewer.md`
- Create: `opencode/.opencode/agent/security-reviewer.md`

**Prerequisites:**
- Task 3.1 completed

**Step 1: Create converted agent file**

Apply same transformations as Task 3.1:
- Convert type → mode
- Convert model shorthand → full format
- Strip Model Requirement section
- Add tool restrictions

**Step 2: Verify agent**

---

### Task 3.3: Convert business-logic-reviewer Agent

**Files:**
- Source: `default/agents/business-logic-reviewer.md`
- Create: `opencode/.opencode/agent/business-logic-reviewer.md`

**Prerequisites:**
- Task 3.2 completed

**Step 1: Create converted agent file**

**Step 2: Verify agent**

---

### Task 3.4: Convert codebase-explorer Agent

**Files:**
- Source: `default/agents/codebase-explorer.md`
- Create: `opencode/.opencode/agent/codebase-explorer.md`

**Prerequisites:**
- Task 3.3 completed

**Step 1: Create converted agent file**

> **SECURITY:** Exploration agent needs bash for read-only commands. Use whitelist to prevent arbitrary execution.

```yaml
---
description: "Deep codebase exploration agent for architecture understanding, pattern discovery, and comprehensive code analysis. Uses Opus for thorough analysis."
mode: subagent
model: anthropic/claude-opus-4-5-20251101
temperature: 0.3
tools:
  write: false
  edit: false
  bash: true
permission:
  edit: deny
  write: deny
  bash:
    "ls *": allow
    "tree *": allow
    "head *": allow
    "tail *": allow
    "cat *": allow
    "find * -name *": allow
    "find * -type *": allow
    "wc *": allow
    "git log*": allow
    "git show*": allow
    "git diff*": allow
    "git status": allow
    "grep *": allow
    "*": deny
---

# Codebase Explorer

[... REST OF BODY FROM SOURCE, STRIP Model Requirement section ...]
```

**Step 2: Verify agent has bash whitelist**

Run: `grep -A 15 "permission:" opencode/.opencode/agent/codebase-explorer.md`

**Expected output:** Permission block with bash command whitelist ending in `"*": deny`

**Step 3: Verify Model Requirement section removed**

Run: `grep -c "Model Requirement" opencode/.opencode/agent/codebase-explorer.md`

**Expected output:** `0`

**If Task Fails:**
1. Check YAML syntax in frontmatter
2. Verify permission block is inside frontmatter (before `---`)
3. Rollback: `rm opencode/.opencode/agent/codebase-explorer.md`

---

### Task 3.5: Convert write-plan Agent

**Files:**
- Source: `default/agents/write-plan.md`
- Create: `opencode/.opencode/agent/write-plan.md`

**Prerequisites:**
- Task 3.4 completed

**Step 1: Create converted agent file**

Note: Planning agent needs restricted write access:
```yaml
tools:
  write: true  # Needs to write plan files
  edit: true
  bash: true
permission:
  edit: ask
```

**Step 2: Verify agent**

---

## Phase 4: Core Commands Conversion

### Task 4.1: Convert commit Command

**Files:**
- Source: `default/commands/commit.md`
- Create: `opencode/.opencode/command/commit.md`

**Prerequisites:**
- Phase 3 completed

**Step 1: Create converted command file**

Commands in OpenCode have different structure:
- Body becomes the template (prompt sent to LLM)
- Use `$ARGUMENTS` for user arguments
- Specify which agent handles the command

```yaml
---
description: Organize and create atomic git commits with intelligent change grouping
agent: build
subtask: false
---

Analyze changes, group them into coherent atomic commits, and create signed commits following repository conventions.

$ARGUMENTS

## Smart Commit Organization

This command does MORE than just commit. It analyzes your changes and organizes them intelligently.

### Process Overview
1. Run `git status` and `git diff` to understand all changes
2. Cluster related changes into logical commits
3. Determine optimal commit sequence
4. Present grouping plan for approval
5. Create signed commits in sequence

[... REST OF INSTRUCTIONS FROM SOURCE ...]
```

**Step 2: Verify command**

Run: `head -30 opencode/.opencode/command/commit.md`

**Expected output:** YAML frontmatter with description/agent/subtask, template body

---

### Task 4.2: Convert codereview Command

**Files:**
- Source: `default/commands/codereview.md`
- Create: `opencode/.opencode/command/codereview.md`

**Prerequisites:**
- Task 4.1 completed

**Step 1: Create converted command file**

```yaml
---
description: Run comprehensive parallel code review with all 3 specialized reviewers
agent: build
subtask: true
---

Dispatch all 3 code reviewers in parallel for comprehensive feedback:
- @code-reviewer - Foundation review (quality, architecture, patterns)
- @security-reviewer - Security analysis (vulnerabilities, data protection)
- @business-logic-reviewer - Business logic verification

$ARGUMENTS

Wait for all reviewers to complete, then aggregate findings by severity.
```

**Step 2: Verify command**

---

### Task 4.3: Convert brainstorm Command

**Files:**
- Source: `default/commands/brainstorm.md`
- Create: `opencode/.opencode/command/brainstorm.md`

**Prerequisites:**
- Task 4.2 completed

**Step 1: Create converted command file**

```yaml
---
description: Interactive design refinement using Socratic method
agent: plan
subtask: false
---

Load the brainstorming skill and begin design refinement for:

$ARGUMENTS

Follow the brainstorming skill phases:
1. Autonomous Recon - Inspect repo/docs/commits
2. Understanding - Ask targeted questions
3. Exploration - Propose 2-3 approaches
4. Design Presentation - Present in sections
5. Documentation - Write to docs/plans/
```

**Step 2: Verify command**

---

### Task 4.4: Convert write-plan Command

**Files:**
- Source: `default/commands/write-plan.md`
- Create: `opencode/.opencode/command/write-plan.md`

**Prerequisites:**
- Task 4.3 completed

**Step 1: Create converted command file**

**Step 2: Verify command**

---

### Task 4.5: Convert execute-plan Command

**Files:**
- Source: `default/commands/execute-plan.md`
- Create: `opencode/.opencode/command/execute-plan.md`

**Prerequisites:**
- Task 4.4 completed

**Step 1: Create converted command file**

**Step 2: Verify command**

---

### Task 4.6: Convert Remaining Core Commands (Batch)

**Files:**
- Source: `default/commands/*.md` (remaining)
- Create: `opencode/.opencode/command/*.md`

**Prerequisites:**
- Task 4.5 completed

**Remaining commands:**
1. `explore-codebase`
2. `worktree`
3. `lint`
4. `interview-me`
5. `create-handoff`
6. `resume-handoff`
7. `query-artifacts`
8. `compound-learnings`
9. `release-guide`

**For each command:**
1. Transform frontmatter (description, agent, subtask)
2. Convert body to template format
3. Use $ARGUMENTS for user input

**Step: Batch verification**

Run: `ls opencode/.opencode/command/ | wc -l`

**Expected output:** 14 (total commands)

---

## Code Review Checkpoint 2

### Task CR2: Run Code Review on Phases 3-4

**Prerequisites:**
- All Phase 3 and 4 tasks completed

**Step 1: Dispatch code review**

Focus on:
- Agent model format correctness
- Tool/permission configuration
- Command template structure
- Model Requirement sections stripped

**Step 2: Fix findings by severity**

**Step 3: Proceed when clean**

---

## Phase 5: TypeScript Plugins (Portable Hooks)

### Task 5.1: Create session-start Plugin

**Files:**
- Source: `default/hooks/session-start.sh`
- Create: `opencode/.opencode/plugin/session-start.ts`

**Prerequisites:**
- Phase 4 completed

**Step 1: Create TypeScript plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Session Start Plugin
 *
 * Injects Ring skills context and critical rules at session start.
 * Converted from: default/hooks/session-start.sh
 */
export const RingSessionStart: Plugin = async ({ project, $, directory, worktree }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        // Log Ring initialization
        console.log("[Ring] Session started - Ring skills system active")

        // Note: OpenCode handles skill discovery automatically
        // Skills in .opencode/skill/ are available via skill() tool
      }
    }
  }
}
```

**Step 2: Verify plugin**

Run: `cat opencode/.opencode/plugin/session-start.ts`

**Expected output:** Valid TypeScript with Plugin type

---

### Task 5.2: Create context-injection Plugin

**Files:**
- Source: `default/hooks/ledger-save.sh`
- Create: `opencode/.opencode/plugin/context-injection.ts`

**Prerequisites:**
- Task 5.1 completed

**Step 1: Create TypeScript plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Context Injection Plugin
 *
 * Injects Ring-specific context during session compaction.
 * Converted from: default/hooks/ledger-save.sh
 */
export const RingContextInjection: Plugin = async (ctx) => {
  return {
    "experimental.session.compacting": async (input, output) => {
      // Inject Ring critical rules into compaction context
      output.context.push(`
## Ring Skills System

Ring skills are available via the skill() tool. Key skills:
- test-driven-development: TDD methodology
- requesting-code-review: Parallel code review
- systematic-debugging: 4-phase debugging

## Ring Critical Rules

- 3-FILE RULE: Do not edit >3 files directly, dispatch agent instead
- TDD: Test must fail before implementation
- REVIEW: All 3 reviewers must pass
`)
    }
  }
}
```

**Step 2: Verify plugin**

---

### Task 5.3: Create notification Plugin (Optional)

**Files:**
- Create: `opencode/.opencode/plugin/notification.ts`

**Prerequisites:**
- Task 5.2 completed

**Step 1: Create TypeScript plugin**

```typescript
import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Notification Plugin
 *
 * Sends desktop notifications when Ring sessions complete.
 */
export const RingNotification: Plugin = async ({ $ }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.idle") {
        // macOS notification
        try {
          await $`osascript -e 'display notification "Ring session completed!" with title "Ring"'`
        } catch {
          // Notification not critical, ignore failures
        }
      }
    }
  }
}
```

**Step 2: Verify plugin**

---

### Task 5.4: Create package.json for Plugin Dependencies

**Files:**
- Create: `opencode/.opencode/package.json`

**Prerequisites:**
- Task 5.3 completed

**Step 1: Create package.json**

```json
{
  "name": "ring-opencode-plugins",
  "version": "1.0.0",
  "description": "Ring plugins for OpenCode",
  "dependencies": {
    "@opencode-ai/plugin": "^1.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/node": "^20.0.0"
  }
}
```

**Step 2: Verify JSON**

Run: `cat opencode/.opencode/package.json | python3 -m json.tool`

---

### Task 5.5: Create env-protection Plugin (SECURITY)

**Files:**
- Create: `opencode/.opencode/plugin/env-protection.ts`

**Prerequisites:**
- Task 5.4 completed

**Step 1: Create TypeScript plugin**

> **SECURITY:** This plugin prevents the LLM from reading sensitive files (.env, credentials, keys)

```typescript
import type { Plugin } from "@opencode-ai/plugin"

/**
 * Ring Environment Protection Plugin
 *
 * Prevents LLM from reading sensitive files (.env, credentials, secrets)
 * to avoid exposing API keys and passwords in conversation context.
 */
export const RingEnvProtection: Plugin = async (ctx) => {
  // SECURITY: Only use hardcoded patterns - never interpolate user input
  const PROTECTED_PATTERNS = [
    '.env',
    '.env.local',
    '.env.production',
    '.env.development',
    'credentials',
    'secrets',
    '.pem',
    '.key',
    'id_rsa',
    'id_ed25519',
    '.p12',
    '.pfx'
  ]

  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "read") {
        const filePath = (output.args?.filePath || '').toLowerCase()
        for (const pattern of PROTECTED_PATTERNS) {
          if (filePath.includes(pattern)) {
            throw new Error(`Security: Cannot read protected file type (${pattern}). ` +
              `This file may contain secrets or credentials.`)
          }
        }
      }
    }
  }
}
```

**Step 2: Verify plugin syntax**

Run: `head -30 opencode/.opencode/plugin/env-protection.ts`

**Expected output:** TypeScript with Plugin type and tool.execute.before handler

**Step 3: Test protection patterns**

Verify these patterns are in the PROTECTED_PATTERNS array:
- `.env` (environment files)
- `.pem`, `.key` (certificates)
- `id_rsa`, `id_ed25519` (SSH keys)

**If Task Fails:**
1. Check TypeScript syntax
2. Verify Plugin type import
3. Rollback: `rm opencode/.opencode/plugin/env-protection.ts`

---

## Phase 6: Dev-Team Skills Conversion

### Task 6.1: Convert using-dev-team Skill

**Files:**
- Source: `dev-team/skills/using-dev-team/SKILL.md`
- Create: `opencode/.opencode/skill/using-dev-team/SKILL.md`

**Prerequisites:**
- Phase 5 completed

**Step 1: Create skill directory and converted file**

**Step 2: Verify skill**

---

### Task 6.2: Convert dev-cycle Skill

**Files:**
- Source: `dev-team/skills/dev-cycle/SKILL.md`
- Create: `opencode/.opencode/skill/dev-cycle/SKILL.md`

**Prerequisites:**
- Task 6.1 completed

---

### Task 6.3: Convert Remaining Dev-Team Skills (Batch)

**Files:**
- Source: `dev-team/skills/*/SKILL.md`
- Create: `opencode/.opencode/skill/*/SKILL.md`

**Remaining skills:**
1. `dev-devops`
2. `dev-feedback-loop`
3. `dev-implementation`
4. `dev-refactor`
5. `dev-sre`
6. `dev-testing`
7. `dev-validation`

---

### Task 6.4a: Convert Dev-Team Backend Agents

**Files:**
- Source: `dev-team/agents/{name}.md`
- Create: `opencode/.opencode/agent/{name}.md`

**Prerequisites:**
- Task 6.3 completed

**Agents in this batch (2):**
1. `backend-engineer-golang`
2. `backend-engineer-typescript`

**For each agent:**
1. Convert `model: opus` → `model: anthropic/claude-opus-4-5-20251101`
2. Convert `type: specialist` → `mode: subagent`
3. **STRIP** the `## ⚠️ Model Requirement` section entirely
4. Add `temperature: 0.3` (implementation agents)
5. Add appropriate tool permissions
6. Keep all body content (Blocker Criteria, Anti-Rationalization, etc.)

**Example frontmatter for backend-engineer-golang:**
```yaml
---
description: "Backend engineer specializing in Go development following Lerian/Ring standards"
mode: subagent
model: anthropic/claude-opus-4-5-20251101
temperature: 0.3
tools:
  write: true
  edit: true
  bash: true
permission:
  edit: allow
  bash: allow
---
```

**Verification:**

Run: `grep -c "Model Requirement" opencode/.opencode/agent/backend-engineer-*.md`

**Expected output:** `0` (both files should have no Model Requirement section)

---

### Task 6.4b: Convert Dev-Team Frontend Agents

**Files:**
- Source: `dev-team/agents/{name}.md`
- Create: `opencode/.opencode/agent/{name}.md`

**Prerequisites:**
- Task 6.4a completed

**Agents in this batch (3):**
1. `frontend-engineer`
2. `frontend-designer`
3. `frontend-bff-engineer-typescript`

**For each agent:**
1. Convert model shorthand to full format
2. Convert type to mode
3. Strip Model Requirement sections
4. Add temperature and tool permissions

**Verification:**

Run: `ls opencode/.opencode/agent/frontend-*.md | wc -l`

**Expected output:** `3`

---

### Task 6.4c: Convert Dev-Team Infrastructure Agents

**Files:**
- Source: `dev-team/agents/{name}.md`
- Create: `opencode/.opencode/agent/{name}.md`

**Prerequisites:**
- Task 6.4b completed

**Agents in this batch (2):**
1. `devops-engineer`
2. `sre`

**For each agent:**
1. Convert model shorthand to full format
2. Convert type to mode
3. Strip Model Requirement sections
4. Add temperature and tool permissions

**Verification:**

Run: `ls opencode/.opencode/agent/{devops-engineer,sre}.md 2>/dev/null | wc -l`

**Expected output:** `2`

---

### Task 6.4d: Convert Dev-Team Quality Agents

**Files:**
- Source: `dev-team/agents/{name}.md`
- Create: `opencode/.opencode/agent/{name}.md`

**Prerequisites:**
- Task 6.4c completed

**Agents in this batch (2):**
1. `qa-analyst`
2. `prompt-quality-reviewer`

**For each agent:**
1. Convert model shorthand to full format
2. Convert type to mode
3. Strip Model Requirement sections
4. Add temperature: 0.1 (quality/review agents need consistency)
5. Add tool permissions

**Final Phase 6 Agents Verification:**

Run: `ls opencode/.opencode/agent/*.md | wc -l`

**Expected output:** `14` (5 from Phase 3 + 9 from Phase 6)

---

### Task 6.5: Convert Dev-Team Commands (Batch)

**Files:**
- Source: `dev-team/commands/*.md`
- Create: `opencode/.opencode/command/*.md`

**Commands:**
1. `dev-cycle`
2. `dev-refactor`
3. `dev-status`
4. `dev-cancel`
5. `dev-report`

---

## Code Review Checkpoint 3

### Task CR3: Run Code Review on Phases 5-6

**Prerequisites:**
- All Phase 5 and 6 tasks completed

**Step 1: Dispatch code review**

Focus on:
- TypeScript plugin syntax
- Dev-team skill/agent conversions
- Cross-references between skills

**Step 2: Fix findings by severity**

---

## Phase 7: Additional Plugins Conversion (Optional)

### Task 7.1: Convert PM-Team Skills (Optional)

**Files:**
- Source: `pm-team/skills/*/SKILL.md`
- Create: `opencode/.opencode/skill/*/SKILL.md`

**Skills:** 10 pre-development planning skills

---

### Task 7.2: Convert TW-Team Skills (Optional)

**Files:**
- Source: `tw-team/skills/*/SKILL.md`
- Create: `opencode/.opencode/skill/*/SKILL.md`

**Skills:** 7 technical writing skills

---

## Phase 8: Final Verification

### Task 8.1: Verify Complete Directory Structure

**Prerequisites:**
- All previous phases completed

**Step 1: Count all components**

```bash
echo "Skills: $(ls opencode/.opencode/skill/ | wc -l)"
echo "Agents: $(ls opencode/.opencode/agent/*.md 2>/dev/null | wc -l)"
echo "Commands: $(ls opencode/.opencode/command/*.md 2>/dev/null | wc -l)"
echo "Plugins: $(ls opencode/.opencode/plugin/*.ts 2>/dev/null | wc -l)"
```

**Expected output:**
```
Skills: 36+ (28 core + 9 dev-team minimum)
Agents: 14+ (5 core + 9 dev-team)
Commands: 19+ (14 core + 5 dev-team)
Plugins: 3-4
```

---

### Task 8.2: Verify Frontmatter Compliance

**Prerequisites:**
- Task 8.1 completed

**Step 1: Check for invalid frontmatter fields**

```bash
# Check skills for invalid fields (should only have: name, description, license, compatibility, metadata)
grep -r "^trigger:" opencode/.opencode/skill/*/SKILL.md && echo "ERROR: Found bare trigger field"
grep -r "^skip_when:" opencode/.opencode/skill/*/SKILL.md && echo "ERROR: Found bare skip_when field"
grep -r "^related:" opencode/.opencode/skill/*/SKILL.md && echo "ERROR: Found bare related field"
```

**Expected output:** No output (no invalid fields found)

---

### Task 8.3: Create README for OpenCode Distribution

**Files:**
- Create: `opencode/README.md`

**Prerequisites:**
- Task 8.2 completed

**Step 1: Create README**

```markdown
# Ring for OpenCode

Ring skills library converted for native OpenCode use.

## Installation

1. Copy the `.opencode/` directory to your project root:
   ```bash
   cp -r opencode/.opencode /path/to/your/project/
   ```

2. Copy `opencode.json` to your project root (optional, for customization):
   ```bash
   cp opencode/opencode.json /path/to/your/project/
   ```

3. Copy `AGENTS.md` to your project root:
   ```bash
   cp opencode/AGENTS.md /path/to/your/project/
   ```

## Usage

### Skills
Skills are automatically discovered. Use via the skill tool:
```
skill({ name: "test-driven-development" })
```

### Agents
Agents can be @ mentioned:
```
@code-reviewer review this code
```

### Commands
Commands are invoked with `/`:
```
/commit
/codereview
/brainstorm
```

## Components

- **Skills:** 36+ development workflow skills
- **Agents:** 14+ specialized AI agents
- **Commands:** 19+ utility commands
- **Plugins:** Session management and context injection

## Source

Converted from [Ring](https://github.com/LerianStudio/ring) Claude Code plugin.

## License

MIT
```

---

### Task 8.4: Final Commit

**Prerequisites:**
- All tasks completed
- All code reviews passed

**Step 1: Stage all OpenCode files**

```bash
git add opencode/
```

**Step 2: Create commit**

```bash
git commit -m "feat(opencode): add native OpenCode distribution" \
  -m "Convert Ring skills library for OpenCode compatibility:
- 36+ skills converted with OpenCode-compliant frontmatter
- 14+ agents converted with mode/model transformations
- 19+ commands converted with template format
- TypeScript plugins for session management
- Configuration and documentation" \
  --trailer "X-Lerian-Ref: 0x1"
```

**Step 3: Verify commit**

Run: `git log -1 --stat`

**Expected output:** Commit with opencode/ directory changes

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 3 | Directory structure setup (1.1-1.3) |
| 2 | 13 | Core skills conversion (2.0-2.12) |
| CR1 | 1 | Code review checkpoint |
| 3 | 5 | Core agents conversion (3.1-3.5) |
| 4 | 6 | Core commands conversion (4.1-4.6) |
| CR2 | 1 | Code review checkpoint |
| 5 | 5 | TypeScript plugins (5.1-5.5, includes security) |
| 6 | 8 | Dev-team conversion (6.1-6.5, with agent batches) |
| CR3 | 1 | Code review checkpoint |
| 7 | 2 | Optional: PM/TW teams |
| 8 | 4 | Final verification |
| **Total** | **49** | Complete conversion |

**Estimated time:** 5-7 hours for full conversion

**Security features added:**
- Restrictive bash permissions with whitelist
- .env file protection plugin
- Agent-specific permission controls

**Non-portable features (skipped):**
- Artifact indexing (requires Python backend)
- Token tracking (Claude Code specific)
- Complex bash hooks (simplified to TypeScript)

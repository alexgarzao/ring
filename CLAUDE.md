# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⛔ CRITICAL RULES (READ FIRST)

**These rules are NON-NEGOTIABLE. They MUST be followed for every task.**

### 1. Agent Modification = Mandatory Verification
When creating or modifying any agent in `*/agents/*.md`:
- **MUST** verify agent has all required sections (see "Agent Modification Verification")
- **MUST** use STRONG language (MUST, REQUIRED, CANNOT, FORBIDDEN)
- **MUST** include anti-rationalization tables
- If any section is missing → Agent is INCOMPLETE

### 2. Agents are EXECUTORS, Not DECISION-MAKERS
- Agents **VERIFY**, they DO NOT **ASSUME**
- Agents **REPORT** blockers, they DO NOT **SOLVE** ambiguity autonomously
- Agents **FOLLOW** gates, they DO NOT **SKIP** gates
- Agents **ASK** when uncertain, they DO NOT **GUESS**

### 3. Anti-Patterns (never Do These)
1. **never skip using-ring** - It's mandatory, not optional
2. **never run reviewers sequentially** - Always dispatch in parallel
3. **never skip TDD's RED phase** - Test must fail before implementation
4. **never ignore skill when applicable** - "Simple task" is not an excuse
5. **never use panic() in Go** - Error handling required
6. **never commit manually** - Always use `/commit` command
7. **never assume compliance** - VERIFY with evidence

### 4. Fully Qualified Names (always)
- ✅ `ring-default:code-reviewer`
- ✅ `ring-dev-team:backend-engineer-golang`
- ❌ `code-reviewer` (missing plugin prefix)
- ❌ `ring:code-reviewer` (ambiguous shorthand)

### 5. Standards-Agent Synchronization (always CHECK)
When modifying standards files (`dev-team/docs/standards/*.md`):

**⛔ FOUR-FILE UPDATE RULE:**
1. Edit `dev-team/docs/standards/{file}.md` - Add your `## Section Name`
2. **Update TOC** - Add section to the `## Table of Contents` at the top of the same file
3. Edit `dev-team/skills/shared-patterns/standards-coverage-table.md` - Add section to agent's index table
4. Edit `dev-team/agents/{agent}.md` - Verify agent references coverage table (not inline categories)
5. **All files in same commit** - Never update one without the others

**⛔ TOC MAINTENANCE RULE:**
Every standards file has a `## Table of Contents` section that MUST stay in sync:
- **Format:** `| # | [Section Name](#anchor-link) | Description |`
- **Meta-sections** (Checklist, Standards Compliance) are listed separately below the table
- **Anchor links** use lowercase with hyphens (e.g., `#error-handling-mandatory`)
- **Section count in TOC** MUST match section count in `standards-coverage-table.md`

**⛔ CHECKLIST: Adding/Removing a Section in Standards Files**
```
Before committing changes to dev-team/docs/standards/*.md:

[ ] 1. Did you add/remove a `## Section` in the standards file?
[ ] 2. Did you update the `## Table of Contents` in the SAME file?
    - Add/remove row: `| N | [Section Name](#anchor) | Description |`
    - Update numbering if needed
[ ] 3. Did you update `dev-team/skills/shared-patterns/standards-coverage-table.md`?
    - Find the agent's section index (e.g., "backend-engineer-golang → golang.md")
    - Add/remove the section row
[ ] 4. Do the section counts match?
    - Count `## ` headers in standards file (excluding meta-sections)
    - Count rows in TOC
    - Count rows in standards-coverage-table.md for that agent
    - all THREE must be equal

If any checkbox is no → Fix before committing.
```

**⛔ AGENT INLINE CATEGORIES ARE FORBIDDEN:**
- ✅ Agent has "Sections to Check" referencing `standards-coverage-table.md`
- ❌ Agent has inline "Comparison Categories" table (FORBIDDEN - causes drift)

**Meta-sections (excluded from agent checks):**
- `## Checklist` - Self-verification section in standards files
- `## Standards Compliance` - Output format examples
- `## Standards Compliance Output Format` - Output templates

| Standards File | Agents That Use It |
|----------------|-------------------|
| `golang.md` | `backend-engineer-golang`, `qa-analyst` |
| `typescript.md` | `backend-engineer-typescript`, `frontend-bff-engineer-typescript`, `qa-analyst` |
| `frontend.md` | `frontend-engineer`, `frontend-designer` |
| `devops.md` | `devops-engineer` |
| `sre.md` | `sre` |

**Section Index Location:** `dev-team/skills/shared-patterns/standards-coverage-table.md` → "Agent → Standards Section Index"

**Quick Reference - Section Counts (MUST match standards-coverage-table.md):**

| Agent | Standards File | Section Count |
|-------|----------------|---------------|
| `backend-engineer-golang` | golang.md | See coverage table |
| `backend-engineer-typescript` | typescript.md | See coverage table |
| `frontend-bff-engineer-typescript` | typescript.md | See coverage table |
| `frontend-engineer` | frontend.md | See coverage table |
| `frontend-designer` | frontend.md | See coverage table |
| `devops-engineer` | devops.md | See coverage table |
| `sre` | sre.md | See coverage table |
| `qa-analyst` | golang.md or typescript.md | See coverage table |

**⛔ If section counts in skills don't match this table → Update the skill.**

### 6. Agent Model Requirements (always RESPECT)
When invoking agents via Task tool:
- **MUST** check agent's `model:` field in YAML frontmatter
- **MUST** pass matching `model` parameter to Task tool
- Agents with `model: opus` → **MUST** call with `model="opus"`
- Agents with `model: sonnet` → **MUST** call with `model="sonnet"`
- **never** omit model parameter for specialized agents
- **never** let system auto-select model for agents with model requirements

**Examples:**
- ✅ `Task(subagent_type="code-reviewer", model="opus", ...)`
- ✅ `Task(subagent_type="backend-engineer-golang", model="opus", ...)`
- ❌ `Task(subagent_type="code-reviewer", ...)` - Missing model parameter
- ❌ `Task(subagent_type="code-reviewer", model="sonnet", ...)` - Wrong model

**Agent Self-Verification:**
All agents with `model:` field in frontmatter MUST include "Model Requirements" section that verifies they are running on the correct model and STOPS if not.

### 8. CLAUDE.md ↔ AGENTS.md Synchronization (AUTOMATIC via Symlink)

**⛔ AGENTS.md IS A SYMLINK TO CLAUDE.md - DO not BREAK:**
- `CLAUDE.md` - Primary project instructions (source of truth)
- `AGENTS.md` - Symlink to CLAUDE.md (automatically synchronized)

**Current Setup:** `AGENTS.md -> CLAUDE.md` (symlink)

**Why:** Both files serve as entry points for AI agents. CLAUDE.md is read by Claude Code, AGENTS.md is read by other AI systems. The symlink ensures they always contain identical information.

**Rules:**
- **never delete the AGENTS.md symlink**
- **never replace AGENTS.md with a regular file**
- **always edit CLAUDE.md** - changes automatically appear in AGENTS.md
- If symlink is broken → Restore with: `ln -sf CLAUDE.md AGENTS.md`

---

### 7. Content Duplication Prevention (always CHECK)
Before adding any content to prompts, skills, agents, or documentation:
1. **SEARCH FIRST**: `grep -r "keyword" --include="*.md"` - Check if content already exists
2. **If content exists** → **REFERENCE it**, DO NOT duplicate. Use: `See [file](path) for details`
3. **If adding new content** → Add to the canonical source per table below
4. **never copy** content between files - always link to the single source of truth

| Information Type | Canonical Source (Single Source of Truth) |
|-----------------|-------------------------------------------|
| Critical rules | CLAUDE.md |
| Language patterns | docs/PROMPT_ENGINEERING.md |
| Agent schemas | docs/AGENT_DESIGN.md |
| Workflows | docs/WORKFLOWS.md |
| Plugin overview | README.md |
| Agent requirements | CLAUDE.md (Agent Modification section) |
| Shared skill patterns | `{plugin}/skills/shared-patterns/*.md` |

**Shared Patterns Rule (MANDATORY):**
When content is reused across multiple skills within a plugin:
1. **Extract to shared-patterns**: Create `{plugin}/skills/shared-patterns/{pattern-name}.md`
2. **Reference from skills**: Use `See [shared-patterns/{name}.md](../shared-patterns/{name}.md)`
3. **never duplicate**: If the same table/section appears in 2+ skills → extract to shared-patterns

| Shared Pattern Type | Location |
|--------------------|----------|
| Pressure resistance scenarios | `{plugin}/skills/shared-patterns/pressure-resistance.md` |
| Anti-rationalization tables | `{plugin}/skills/shared-patterns/anti-rationalization.md` |
| Execution report format | `{plugin}/skills/shared-patterns/execution-report.md` |
| Standards coverage table | `{plugin}/skills/shared-patterns/standards-coverage-table.md` |

**Reference Pattern:**
- ✅ `See [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for language patterns`
- ✅ `See [shared-patterns/pressure-resistance.md](../shared-patterns/pressure-resistance.md) for universal pressures`
- ❌ Copying the language patterns table into another file
- ❌ Duplicating pressure resistance tables across multiple skills

---

## Quick Navigation

| Section | Content |
|---------|---------|
| [CRITICAL RULES](#-critical-rules-read-first) | Non-negotiable requirements |
| [CLAUDE.md ↔ AGENTS.md Sync](#8-claudemd--agentsmd-synchronization-automatic-via-symlink) | Symlink ensures sync |
| [Content Duplication Prevention](#7-content-duplication-prevention-always-check) | Canonical sources + reference pattern |
| [Anti-Rationalization Tables](#anti-rationalization-tables-mandatory-for-all-agents) | Prevent AI from assuming/skipping |
| [Lexical Salience Guidelines](#lexical-salience-guidelines-mandatory) | Selective emphasis for effective prompts |
| [Agent Modification Verification](#agent-modification-verification-mandatory) | Checklist for agent changes |
| [Repository Overview](#repository-overview) | What Ring is |
| [Architecture](#architecture) | Plugin summary |
| [Key Workflows](#key-workflows) | Quick reference + [full docs](docs/WORKFLOWS.md) |
| [Agent Output Schemas](#agent-output-schema-archetypes) | Schema summary + [full docs](docs/AGENT_DESIGN.md) |
| [Compliance Rules](#compliance-rules) | TDD, Review, Commit rules |
| [Standards-Agent Synchronization](#standards-agent-synchronization) | Standards ↔ Agent mapping |
| [Documentation Sync](#documentation-sync-checklist) | Files to update |

---

## Anti-Rationalization Tables (MANDATORY for All Agents)

**MANDATORY: Every agent must include an anti-rationalization table.** This is a HARD GATE for agent design.

**Why This Is Mandatory:**
AI models naturally attempt to be "helpful" by making autonomous decisions. This is dangerous in structured workflows. Agents MUST NOT rationalize skipping gates, assuming compliance, or making decisions that belong to users or orchestrators.

**Anti-rationalization tables use selective emphasis.** Place enforcement words (MUST, STOP, FORBIDDEN) at the beginning of instructions for maximum impact. See [Lexical Salience Guidelines](#lexical-salience-guidelines-mandatory).

**Required Table Structure:**
```markdown
| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "[Common excuse AI might generate]" | [Why this thinking is incorrect] | **[MANDATORY action in bold]** |
```

**Example from backend-engineer-golang.md:**
```markdown
| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Codebase already uses lib-commons" | Partial usage ≠ full compliance. Check everything. | **Verify all categories** |
| "Already follows Lerian standards" | Assumption ≠ verification. Prove it with evidence. | **Verify all categories** |
| "Only checking what seems relevant" | You don't decide relevance. The checklist does. | **Verify all categories** |
| "Code looks correct, skip verification" | Looking correct ≠ being correct. Verify. | **Verify all categories** |
| "Previous refactor already checked this" | Each refactor is independent. Check again. | **Verify all categories** |
| "Small codebase, not all applies" | Size is irrelevant. Standards apply uniformly. | **Verify all categories** |
```

**Mandatory Sections Every Agent MUST Have:**

| Section | Purpose | Language Requirements |
|---------|---------|----------------------|
| **Blocker Criteria** | Define when to STOP and report | Use "STOP", "CANNOT proceed", "HARD BLOCK" |
| **Cannot Be Overridden** | List non-negotiable requirements | Use "CANNOT be waived", "NON-NEGOTIABLE" |
| **Severity Calibration** | Define issue severity levels | Use "CRITICAL", "MUST be fixed" |
| **Pressure Resistance** | Handle user pressure to skip | Use "Cannot proceed", "I'll implement correctly" |
| **Anti-Rationalization Table** | Prevent AI from assuming/skipping | Use "Why It's WRONG", "REQUIRED action" |

**Language Guidelines for Agent Prompts:**

| Weak (AVOID) | Strong (Correct) |
|--------------|------------------|
| "You should check..." | "MUST check..." |
| "It's recommended to..." | "REQUIRED: ..." |
| "Consider verifying..." | "MANDATORY: Verify..." |
| "You can skip if..." | "CANNOT skip. No exceptions." |
| "Optionally include..." | "MANDATORY: Include..." |
| "Try to follow..." | "HARD GATE: Follow..." |

**Note:** Place enforcement word at the BEGINNING, not embedded in the sentence.

**HARD GATE: If an agent lacks anti-rationalization tables, it is incomplete and must be updated.**

---

## Lexical Salience Guidelines (MANDATORY)

**Effective prompts use selective emphasis.** When too many words are in CAPS, none stand out - the AI treats all as equal priority.

### Principle: Less is More

| Approach | Effectiveness | Why |
|----------|---------------|-----|
| Few CAPS words | HIGH | AI attention focuses on truly critical instructions |
| Many CAPS words | LOW | Salience dilution - everything emphasized = nothing emphasized |

### Words to Keep in Lowercase (Context Words)

These words provide context but DO NOT need emphasis:

| Word | Use Instead |
|------|-------------|
| ~~all~~ | all |
| ~~any~~ | any |
| ~~only~~ | only |
| ~~each~~ | each |
| ~~every~~ | every |
| ~~not~~ | not (except in "MUST not") |
| ~~no~~ | no |
| ~~and~~ | and |
| ~~or~~ | or |
| ~~if~~ | if |
| ~~else~~ | else |
| ~~never~~ | "MUST NOT" |
| ~~always~~ | "must" |

### Words to Keep in CAPS (Enforcement Words)

Use these sparingly and only at the **beginning** of instructions:

| Word | Purpose | Correct Position |
|------|---------|------------------|
| MUST | Primary requirement | "MUST verify before proceeding" |
| STOP | Immediate action | "STOP and report blocker" |
| HARD GATE | Critical checkpoint | "HARD GATE: Cannot proceed without..." |
| FAIL/PASS | Verdict states | "FAIL: Gate 4 incomplete" |
| MANDATORY | Section marker | "MANDATORY: Initialize first" |
| CRITICAL | Severity level | "CRITICAL: Security issue" |
| FORBIDDEN | Strong prohibition | "FORBIDDEN: Direct code editing" |
| REQUIRED | Alternative to MUST | "REQUIRED: Load standards first" |
| CANNOT | Prohibition | "CANNOT skip this gate" |

### Positioning Rule: Beginning of Instructions

**Enforcement words MUST appear at the BEGINNING of instructions, not in the middle or end.**

| Position | Effectiveness | Example |
|----------|---------------|---------|
| **Beginning** | HIGH | "MUST verify all sections before proceeding" |
| Middle | LOW | "You should verify all sections, this is MUST" |
| End | LOW | "Verify all sections before proceeding, MUST" |

### Transformation Examples

| Before (Diluted) | After (Focused) |
|------------------|-----------------|
| "You MUST check all sections" | "MUST check all sections" |
| "never skip any gate" | "MUST not skip any gate" |
| "This is MANDATORY for every task" | "MANDATORY: This applies to every task" |
| "always verify BEFORE proceeding" | "MUST verify before proceeding" |
| "Check if this CONDITION is met" | "MUST check if this condition is met" |

### Sentence Structure Pattern

```
[ENFORCEMENT WORD]: [Action/Instruction] [Context]

Examples:
- MUST dispatch agent before proceeding to next gate
- STOP and report if PROJECT_RULES.md is missing
- HARD GATE: All 3 reviewers must pass before Gate 5
- FORBIDDEN: Reading source code directly as orchestrator
```

### Strategic Spacing (Attention Reset)

**Spacing matters for AI attention.** When multiple critical rules appear in sequence, add blank lines between sections to allow "attention reset" - each section gets its own salient word.

| Pattern | Effectiveness | Why |
|---------|---------------|-----|
| Blank line between rule groups | HIGH | Attention "resets" between sections |
| Dense continuous text | LOW | Critical words blur together |

**Example - Strategic Spacing:**

```markdown
## Authentication

Handle auth tokens according to existing patterns.
Validate JWT signatures on every request.
NEVER log sensitive credentials.

## Data Access

Use repository pattern for all queries.
Implement pagination for list endpoints.
CRITICAL: All mutations must be idempotent.

## Error Handling

Wrap errors with context.
Map internal errors to HTTP codes.
NEVER expose stack traces to clients.
```

**Why this works:**
- Each section has ONE salient word (NEVER, CRITICAL, NEVER)
- Blank lines create visual and semantic boundaries
- AI attention focuses on one rule group at a time
- The enforcement word in each section stands out

**Anti-Pattern - Dense Text:**

```markdown
## Rules
Handle auth tokens. Validate JWT. NEVER log credentials. Use repository pattern. CRITICAL: mutations idempotent. Wrap errors. NEVER expose stacks.
```

**Why this fails:** Three CAPS words in one dense block - none stands out.

**Rule:** When writing multiple critical rules, space them into logical groups with blank lines between.

### Semantic Block Tags (Recognition Patterns)

**Use XML-like tags to create recognizable blocks for critical instructions.** Tags create semantic boundaries that AI models recognize as structured blocks requiring special attention.

| Tag | Purpose | AI Behavior |
|-----|---------|-------------|
| `<fetch_required>` | URLs to load before task | WebFetch all URLs first |
| `<block_condition>` | Blocker triggers | STOP if any condition true |
| `<forbidden>` | Prohibited actions | Reject if detected |
| `<dispatch_required>` | Single agent invocation | Use Task tool with specified agent |
| `<parallel_dispatch>` | Multiple agents in parallel | Dispatch all listed agents simultaneously |
| `<verify_before_proceed>` | Pre-conditions | Check all before continuing |
| `<output_required>` | Mandatory output sections | Include in response |
| `<cannot_skip>` | Non-negotiable steps | No exceptions allowed |
| `<user_decision>` | Requires user input | Wait for explicit response |

**Example Usage:**

```markdown
## Required Resources

<fetch_required>
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md
https://raw.githubusercontent.com/LerianStudio/ring/main/CLAUDE.md
</fetch_required>

Fetch all URLs above before starting the task.

---

<block_condition>
- PROJECT_RULES.md not found
- Coverage below 85%
- Any reviewer returns FAIL
</block_condition>

If any condition is true, STOP immediately and report blocker.

---

<forbidden>
- fmt.Println() in Go code
- console.log() in TypeScript
- Direct source code editing by orchestrator
</forbidden>

Any occurrence = IMMEDIATE REJECTION.

---

<dispatch_required agent="backend-engineer-golang" model="opus">
Implement user authentication endpoint with JWT validation.
</dispatch_required>

MUST use Task tool with specified agent and model.

---

<parallel_dispatch agents="backend-engineer-golang, qa-analyst, devops-engineer, sre" model="opus">
Analyze codebase against Ring standards. All agents receive same context:
- Codebase Report: docs/refactor/{timestamp}/codebase-report.md
- Project Rules: docs/PROJECT_RULES.md
</parallel_dispatch>

MUST dispatch all listed agents simultaneously in one message.
```

**Why Tags Work:**
- **Clear boundaries** - AI recognizes start/end of critical blocks
- **Semantic meaning** - Tag name conveys intent
- **Parseable** - Can be programmatically validated
- **Consistent pattern** - Same tag = same behavior across all prompts

See [docs/PROMPT_ENGINEERING.md](docs/PROMPT_ENGINEERING.md) for complete patterns and the [lexical salience refactoring plan](docs/plans/lexical-salience-refactor.md) for implementation details.

---

## Agent Modification Verification (MANDATORY)

**HARD GATE: Before creating or modifying any agent file, Claude Code MUST verify compliance with this checklist.**

When you receive instructions to create or modify an agent in `*/agents/*.md`:

**Step 1: Read This Section**
Before any agent work, re-read this CLAUDE.md section to understand current requirements.

**Step 2: Verify Agent Has all Required Sections**

| Required Section | Pattern to Check | If Missing |
|------------------|------------------|------------|
| **Standards Loading (MANDATORY)** | `## Standards Loading` | MUST add with WebFetch instructions |
| **Blocker Criteria - STOP and Report** | `## Blocker Criteria` | MUST add with decision type table |
| **Cannot Be Overridden** | `### Cannot Be Overridden` | MUST add with non-negotiable requirements |
| **Severity Calibration** | `## Severity Calibration` | MUST add with CRITICAL/HIGH/MEDIUM/LOW table |
| **Pressure Resistance** | `## Pressure Resistance` | MUST add with "User Says / Your Response" table |
| **Anti-Rationalization Table** | `Rationalization.*Why It's WRONG` | MUST add in Standards Compliance section |
| **When Implementation is Not Needed** | `## When.*Not Needed` | MUST add with compliance signs |
| **Standards Compliance Report** | `## Standards Compliance Report` | MUST add for dev-team agents |

**Step 3: Verify Language Strength**

Check agent uses STRONG language, not weak:

```text
SCAN for weak phrases → REPLACE with strong:
- "should" → "MUST"
- "recommended" → "REQUIRED"
- "consider" → "MANDATORY"
- "can skip" → "CANNOT skip"
- "optional" → "NON-NEGOTIABLE"
- "try to" → "HARD GATE:"
```

**Step 4: Before Completing Agent Modification**

```text
CHECKLIST (all must be YES):
[ ] Does agent have Standards Loading section?
[ ] Does agent have Blocker Criteria table?
[ ] Does agent have Cannot Be Overridden table?
[ ] Does agent have Severity Calibration table?
[ ] Does agent have Pressure Resistance table?
[ ] Does agent have Anti-Rationalization table?
[ ] Does agent have When Not Needed section?
[ ] Does agent use STRONG language (MUST, REQUIRED, CANNOT)?
[ ] Does agent define when to STOP and report?
[ ] Does agent define non-negotiable requirements?
[ ] If agent has model: field in frontmatter, does it have Model Requirements section?

If any checkbox is no → Agent is INCOMPLETE. Add missing sections.
```

**This verification is not optional. This is a HARD GATE for all agent modifications.**

---

## Repository Overview

Ring is a comprehensive skills library and workflow system for AI agents that enforces proven software engineering practices through mandatory workflows, parallel code review, and systematic pre-development planning. Currently implemented as a Claude Code plugin marketplace with **9 active plugins**, the skills are agent-agnostic and reusable across different AI systems.

**Active Plugins:**
- **ring-default**: 27 core skills, 13 slash commands, 5 specialized agents
- **ring-dev-team**: 9 development skills, 5 slash commands, 9 developer agents (Backend Go, Backend TypeScript, DevOps, Frontend TypeScript, Frontend Designer, QA, SRE)
- **ring-pm-team**: 10 product planning skills, 3 research agents, 2 slash commands
- **ring-finops-team**: 6 regulatory skills, 2 FinOps agents
- **ring-finance-team**: 8 financial operations skills, 6 finance agents, 3 slash commands (Financial Analyst, Budget Planner, Financial Modeler, Treasury Specialist, Accounting Specialist, Metrics Analyst)
- **ring-ops-team**: 8 operations skills, 5 ops agents, 4 slash commands (Platform Engineer, Incident Responder, Cloud Cost Optimizer, Infrastructure Architect, Security Operations)
- **ring-pmm-team**: 8 product marketing skills, 6 PMM agents, 3 slash commands (Market Researcher, Positioning Strategist, Messaging Specialist, GTM Planner, Launch Coordinator, Pricing Analyst)
- **ring-pmo-team**: 8 PMO skills, 5 PMO agents, 3 slash commands (Portfolio Manager, Resource Planner, Governance Specialist, Risk Analyst, Executive Reporter)
- **ring-tw-team**: 7 technical writing skills, 3 slash commands, 3 documentation agents (Functional Writer, API Writer, Docs Reviewer)

**Note:** Plugin versions are managed in `.claude-plugin/marketplace.json`

**Total: 91 skills (27 + 9 + 10 + 6 + 8 + 8 + 8 + 8 + 7) across 9 plugins**
**Total: 44 agents (5 + 9 + 3 + 2 + 6 + 5 + 6 + 5 + 3) across 9 plugins**
**Total: 36 commands (13 + 5 + 2 + 0 + 3 + 4 + 3 + 3 + 3) across 9 plugins**

The architecture uses markdown-based skill definitions with YAML frontmatter, auto-discovered at session start via hooks, and executed through Claude Code's native Skill/Task tools.

---

## Installation

See [README.md](README.md#installation) or [docs/platforms/](docs/platforms/) for detailed installation instructions.

**Quick install:** `curl -fsSL https://raw.githubusercontent.com/lerianstudio/ring/main/install-ring.sh | bash`

---

## Architecture

**Monorepo Structure** - 9 plugin collections:

| Plugin | Path | Contents |
|--------|------|----------|
| ring-default | `default/` | 27 skills, 5 agents, 13 commands |
| ring-dev-team | `dev-team/` | 9 skills, 9 agents, 5 commands |
| ring-pm-team | `pm-team/` | 10 skills, 3 agents, 2 commands |
| ring-finops-team | `finops-team/` | 6 skills, 2 agents |
| ring-finance-team | `finance-team/` | 8 skills, 6 agents, 3 commands |
| ring-ops-team | `ops-team/` | 8 skills, 5 agents, 4 commands |
| ring-pmm-team | `pmm-team/` | 8 skills, 6 agents, 3 commands |
| ring-pmo-team | `pmo-team/` | 8 skills, 5 agents, 3 commands |
| ring-tw-team | `tw-team/` | 7 skills, 3 agents, 3 commands |

Each plugin contains: `skills/`, `agents/`, `commands/`, `hooks/`

See [README.md](README.md#architecture) for full directory structure.

---

## Common Commands

```bash
# Git operations (no build system - this is a plugin)
git status                          # Check current branch (main)
git log --oneline -20              # Recent commits show hook development
git worktree list                  # Check isolated development branches

# Skill invocation (via Claude Code)
Skill tool: "test-driven-development"  # Enforce TDD workflow
Skill tool: "systematic-debugging"     # Debug with 4-phase analysis
Skill tool: "using-ring"               # Load mandatory workflows

# Slash commands
/codereview          # Dispatch 3 parallel reviewers
/brainstorm          # Socratic design refinement
/pre-dev-feature     # <2 day features (4 gates)
/pre-dev-full        # ≥2 day features (9 gates)
/execute-plan        # Batch execution with checkpoints
/worktree            # Create isolated development branch

# Hook validation (from default plugin)
bash default/hooks/session-start.sh      # Test skill loading
python default/hooks/generate-skills-ref.py # Generate skill overview
```

---

## Key Workflows

| Workflow | Quick Reference |
|----------|-----------------|
| Add skill | `mkdir default/skills/name/` → create `SKILL.md` with frontmatter |
| Add agent | Create `*/agents/name.md` → verify required sections per [Agent Design](docs/AGENT_DESIGN.md) |
| Modify hooks | Edit `*/hooks/hooks.json` → test with `bash */hooks/session-start.sh` |
| Code review | `/codereview` dispatches 3 parallel reviewers |
| Pre-dev (small) | `/pre-dev-feature` → 4-gate workflow |
| Pre-dev (large) | `/pre-dev-full` → 9-gate workflow |

See [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for detailed instructions.

---

## Important Patterns

### Code Organization
- **Skill Structure**: `default/skills/{name}/SKILL.md` with YAML frontmatter
- **Agent Output**: Required markdown sections per `default/agents/*.md:output_schema`
- **Hook Scripts**: Must output JSON with success/error fields
- **Shared Patterns**: Reference via `default/skills/shared-patterns/*.md`
- **Documentation**: Artifacts in `docs/pre-dev/{feature}/*.md`
- **Monorepo Layout**: Each plugin (`default/`, `team-*/`, `dev-team/`) is self-contained

### Naming Conventions
- Skills: `kebab-case` matching directory name
- Agents: `{domain}-reviewer.md` format
- Commands: `/ring-{plugin}:{action}` format (e.g., `/brainstorm`, `/pre-dev-feature`)
- Hooks: `{event}-{purpose}.sh` format

#### Agent/Skill/Command Invocation
- **always use fully qualified names**: `ring-{plugin}:{component}`
- **Examples:**
  - ✅ Correct: `ring-default:code-reviewer`
  - ✅ Correct: `ring-dev-team:backend-engineer-golang`
  - ❌ Wrong: `code-reviewer` (missing plugin prefix)
  - ❌ Wrong: `ring:code-reviewer` (ambiguous shorthand)
- **Rationale:** Prevents ambiguity in multi-plugin environments

---

## Agent Output Schema Archetypes

| Schema Type | Used By | Key Sections |
|-------------|---------|--------------|
| Implementation | * engineers | Summary, Implementation, Files Changed, Testing |
| Analysis | frontend-designer, finops-analyzer | Analysis, Findings, Recommendations |
| Reviewer | *-reviewer | VERDICT, Issues Found, What Was Done Well |
| Exploration | codebase-explorer | Exploration Summary, Key Findings, Architecture |
| Planning | write-plan | Goal, Architecture, Tech Stack, Tasks |

See [docs/AGENT_DESIGN.md](docs/AGENT_DESIGN.md) for complete schema definitions and Standards Compliance requirements.

---

## Compliance Rules

```bash
# TDD compliance (default/skills/test-driven-development/SKILL.md)
- Test file must exist before implementation
- Test must produce failure output (RED)
- Only then write implementation (GREEN)

# Review compliance (default/skills/requesting-code-review/SKILL.md)
- All 3 reviewers must pass
- Critical findings = immediate fix required
- Re-run all reviewers after fixes

# Skill compliance (default/skills/using-ring/SKILL.md)
- Check for applicable skills before any task
- If skill exists for task → MUST use it
- Announce non-obvious skill usage

# Commit compliance (default/commands/commit.md)
- always use /commit for all commits
- Never write git commit commands manually
- Command enforces: conventional commits, trailers, no emoji signatures
- MUST use --trailer parameter for AI identification (not in message body)
- Format: git commit -m "msg" --trailer "Generated-by: Claude" --trailer "AI-Model: <model>"
- never use HEREDOC to include trailers in message body
```

---

## Session Context

The system loads at SessionStart (from `default/` plugin):
1. `default/hooks/session-start.sh` - Loads skill quick reference via `generate-skills-ref.py`
2. `using-ring` skill - Injected as mandatory workflow
3. `default/hooks/claude-md-reminder.sh` - Reminds about CLAUDE.md on prompt submit

**Monorepo Context:**
- Repository: Monorepo marketplace with multiple plugin collections
- Active plugins: 9 (`ring-default`, `ring-dev-team`, `ring-pm-team`, `ring-finops-team`, `ring-finance-team`, `ring-ops-team`, `ring-pmm-team`, `ring-pmo-team`, `ring-tw-team`)
- Plugin versions: See `.claude-plugin/marketplace.json`
- Core plugin: `default/` (27 skills, 5 agents, 13 commands)
- Developer agents: `dev-team/` (9 skills, 9 agents, 5 commands)
- Product planning: `pm-team/` (10 skills, 3 agents, 2 commands)
- FinOps regulatory: `finops-team/` (6 skills, 2 agents)
- Finance operations: `finance-team/` (8 skills, 6 agents, 3 commands)
- Production operations: `ops-team/` (8 skills, 5 agents, 4 commands)
- Product marketing: `pmm-team/` (8 skills, 6 agents, 3 commands)
- Portfolio management: `pmo-team/` (8 skills, 5 agents, 3 commands)
- Technical writing: `tw-team/` (7 skills, 3 agents, 3 commands)
- Current git branch: `main`
- Remote: `github.com/LerianStudio/ring`

---

## Documentation Sync Checklist

**IMPORTANT:** When modifying agents, skills, commands, or hooks, check all these files for consistency:

```
Root Documentation:
├── CLAUDE.md              # Project instructions (this file)
├── MANUAL.md              # Team quick reference guide
├── README.md              # Public documentation
└── ARCHITECTURE.md        # Architecture diagrams

Reference Documentation:
├── docs/PROMPT_ENGINEERING.md  # Assertive language patterns
├── docs/AGENT_DESIGN.md        # Output schemas, standards compliance
└── docs/WORKFLOWS.md           # Detailed workflow instructions

Plugin Hooks (inject context at session start):
├── default/hooks/session-start.sh        # Skills reference
├── dev-team/hooks/session-start.sh       # Developer agents
├── pm-team/hooks/session-start.sh        # Pre-dev skills
├── finops-team/hooks/session-start.sh    # FinOps regulatory agents
├── finance-team/hooks/session-start.sh   # Finance operations agents
├── ops-team/hooks/session-start.sh       # Production operations agents
├── pmm-team/hooks/session-start.sh       # Product marketing agents
├── pmo-team/hooks/session-start.sh       # PMO agents
└── tw-team/hooks/session-start.sh        # Technical writing agents

Using-* Skills (plugin introductions):
├── default/skills/using-ring/SKILL.md             # Core workflow + agent list
├── dev-team/skills/using-dev-team/SKILL.md        # Developer agents guide
├── pm-team/skills/using-pm-team/SKILL.md          # Pre-dev workflow
├── finops-team/skills/using-finops-team/SKILL.md  # FinOps regulatory guide
├── finance-team/skills/using-finance-team/SKILL.md # Finance operations guide
├── ops-team/skills/using-ops-team/SKILL.md        # Production operations guide
├── pmm-team/skills/using-pmm-team/SKILL.md        # Product marketing guide
├── pmo-team/skills/using-pmo-team/SKILL.md        # PMO governance guide
└── tw-team/skills/using-tw-team/SKILL.md          # Technical writing guide
```

**Checklist when adding/modifying:**
- [ ] CLAUDE.md updated? → AGENTS.md auto-updates (it's a symlink)
- [ ] AGENTS.md symlink broken? → Restore with `ln -sf CLAUDE.md AGENTS.md`
- [ ] Agent added? Update hooks, using-* skills, MANUAL.md, README.md
- [ ] Skill added? Update CLAUDE.md architecture, hooks if plugin-specific
- [ ] Command added? Update MANUAL.md, README.md
- [ ] Plugin added? Create hooks/, using-* skill, update marketplace.json
- [ ] Names changed? Search repo for old names: `grep -r "old-name" --include="*.md" --include="*.sh"`

**Naming Convention Enforcement:**
- [ ] All agent invocations use `ring-{plugin}:agent-name` format
- [ ] All skill invocations use `ring-{plugin}:skill-name` format
- [ ] All command invocations use `/ring-{plugin}:command-name` format
- [ ] No `ring:` shorthand used (except in historical examples with context)
- [ ] No bare agent/skill names in invocation contexts

**Always use fully qualified names:** `ring-{plugin}:{component}` (e.g., `code-reviewer`)

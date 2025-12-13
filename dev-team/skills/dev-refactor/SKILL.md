---
name: dev-refactor
description: Analyzes codebase against standards and generates refactoring tasks for dev-cycle.
trigger: |
  - User wants to refactor existing project to follow standards
  - Legacy codebase needs modernization
  - Project audit requested

skip_when: |
  - Greenfield project → Use /ring-pm-team:pre-dev-* instead
  - Single file fix → Use ring-dev-team:dev-cycle directly
---

# Dev Refactor Skill

Analyzes existing codebase against Ring/Lerian standards and generates refactoring tasks compatible with dev-cycle.

## ⛔ CRITICAL: Specialized Agents Perform All Tasks

See [shared-patterns/orchestrator-principle.md](../shared-patterns/orchestrator-principle.md) for full ORCHESTRATOR principle, role separation, forbidden/required actions, step-to-agent mapping, and anti-rationalization table.

**Summary:** You orchestrate. Agents execute. If using Bash/Grep/Read to analyze code → STOP. Dispatch agent.

---

## Step 0: Validate PROJECT_RULES.md

**Check:** Does `docs/PROJECT_RULES.md` exist?

- **YES** → Continue to Step 1
- **NO** → Output blocker and TERMINATE:

```markdown
## BLOCKED: PROJECT_RULES.md Not Found

Cannot proceed without project standards baseline.

**Required Action:** Create `docs/PROJECT_RULES.md` with:
- Architecture patterns
- Code conventions
- Testing requirements
- Technology stack decisions

Re-run after file exists.
```

---

## Step 1: Detect Project Language

Check for manifest files:

| File | Language | Agent |
|------|----------|-------|
| `go.mod` | Go | ring-dev-team:backend-engineer-golang |
| `package.json` | TypeScript | ring-dev-team:backend-engineer-typescript |

If multiple languages detected, dispatch agents for ALL.

---

## Step 2: Read PROJECT_RULES.md

```
Read tool: docs/PROJECT_RULES.md
```

Extract project-specific conventions for agent context.

---

## Step 3: Generate Codebase Report

### ⛔ MANDATORY: Use Task Tool with ring-default:codebase-explorer

**YOU MUST USE THIS EXACT TOOL CALL:**

```yaml
Task:
  subagent_type: "ring-default:codebase-explorer"  # ← EXACT STRING, NOT "Explore"
  model: "opus"
  description: "Generate codebase architecture report"
  prompt: |
    Generate a comprehensive codebase report describing WHAT EXISTS.

    Include:
    - Project structure and directory layout
    - Architecture pattern (hexagonal, clean, etc.)
    - Technology stack from manifests
    - Code patterns: config, database, handlers, errors, telemetry, testing
    - Key files inventory with file:line references
    - Code snippets showing current implementation patterns

    Output format: EXPLORATION SUMMARY, KEY FINDINGS, ARCHITECTURE INSIGHTS, RELEVANT FILES
```

### Anti-Rationalization Table for Step 3

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "I'll use Bash find/ls to quickly explore" | Bash cannot analyze patterns, just lists files. codebase-explorer provides architectural analysis. | **Use Task with subagent_type="ring-default:codebase-explorer"** |
| "The Explore agent is faster" | "Explore" subagent_type ≠ "ring-default:codebase-explorer". Different agents. | **Use exact string: "ring-default:codebase-explorer"** |
| "I already know the structure from find output" | Knowing file paths ≠ understanding architecture. Agent provides analysis. | **Use Task with subagent_type="ring-default:codebase-explorer"** |
| "This is a small codebase, Bash is enough" | Size is irrelevant. The agent provides standardized output format required by Step 4. | **Use Task with subagent_type="ring-default:codebase-explorer"** |
| "I'll explore manually then dispatch agents" | Manual exploration skips the codebase-report.md artifact required for Step 4 gate. | **Use Task with subagent_type="ring-default:codebase-explorer"** |

### FORBIDDEN Actions for Step 3

```
❌ Bash(command="find ... -name '*.go'")     → SKILL FAILURE
❌ Bash(command="ls -la ...")                → SKILL FAILURE
❌ Bash(command="tree ...")                  → SKILL FAILURE
❌ Task(subagent_type="Explore", ...)        → SKILL FAILURE
❌ Task(subagent_type="general-purpose", ...)→ SKILL FAILURE
❌ Task(subagent_type="Plan", ...)           → SKILL FAILURE
```

### REQUIRED Action for Step 3

```
✅ Task(subagent_type="ring-default:codebase-explorer", model="opus", ...)
```

**After Task completes, save with Write tool:**

```
Write tool:
  file_path: "docs/refactor/{timestamp}/codebase-report.md"
  content: [Task output]
```

---

## Step 4: Dispatch Specialist Agents

### ⛔ HARD GATE: Verify codebase-report.md Exists

**BEFORE dispatching ANY specialist agent, verify:**

```
Check 1: Does docs/refactor/{timestamp}/codebase-report.md exist?
  - YES → Continue to dispatch agents
  - NO  → STOP. Go back to Step 3.

Check 2: Was codebase-report.md created by ring-default:codebase-explorer?
  - YES → Continue
  - NO (created by Bash output) → DELETE IT. Go back to Step 3. Use correct agent.
```

**If you skipped Step 3 or used Bash instead of Task tool → You MUST go back and redo Step 3 correctly.**

**Dispatch ALL applicable agents in ONE message (parallel):**

### For Go projects:

```yaml
Task 1:
  subagent_type: "ring-dev-team:backend-engineer-golang"
  model: "opus"
  description: "Go standards analysis"
  prompt: |
    **MODE: ANALYSIS ONLY**

    Compare codebase with Ring Go standards.

    Input:
    - Ring Standards: Load via WebFetch (golang.md)
    - Codebase Report: docs/refactor/{timestamp}/codebase-report.md
    - Project Rules: docs/PROJECT_RULES.md

    Output for each non-compliant pattern:
    - ISSUE-XXX: Pattern name, Severity, Location (file:line)
    - Current Code (snippet)
    - Expected Code (Ring standard)
    - Standard Reference (file:section:lines)

Task 2:
  subagent_type: "ring-dev-team:qa-analyst"
  model: "opus"
  description: "Test coverage analysis"
  prompt: |
    **MODE: ANALYSIS ONLY**
    Compare test patterns with Ring standards.
    Input: codebase-report.md, PROJECT_RULES.md
    Output: Coverage gaps, pattern violations with file:line

Task 3:
  subagent_type: "ring-dev-team:devops-engineer"
  model: "opus"
  description: "DevOps analysis"
  prompt: |
    **MODE: ANALYSIS ONLY**
    Compare DevOps setup with Ring standards.
    Input: codebase-report.md, PROJECT_RULES.md
    Output: Dockerfile, docker-compose, CI/CD gaps

Task 4:
  subagent_type: "ring-dev-team:sre"
  model: "opus"
  description: "Observability analysis"
  prompt: |
    **MODE: ANALYSIS ONLY**
    Compare observability with Ring standards.
    Input: codebase-report.md, PROJECT_RULES.md
    Output: Logging, tracing, health check gaps
```

### For TypeScript projects:

Replace Task 1 with `ring-dev-team:backend-engineer-typescript`.

---

## Step 4.1: Agent Report → Findings Mapping (HARD GATE)

**⛔ MANDATORY: ALL agent-reported issues MUST become findings.**

| Agent Report | Action |
|--------------|--------|
| Any difference between current code and Ring standard | → Create FINDING-XXX |
| Any missing pattern from Ring standards | → Create FINDING-XXX |
| Any deprecated pattern usage | → Create FINDING-XXX |
| Any observability gap | → Create FINDING-XXX |

**FORBIDDEN:**
- ❌ Ignoring agent-reported issues because they seem "minor"
- ❌ Filtering out issues based on personal judgment
- ❌ Summarizing multiple issues into one finding (each issue = one finding)

**REQUIRED:**
- ✅ Every line item from agent reports becomes a FINDING-XXX entry
- ✅ Preserve agent's severity assessment
- ✅ Include exact file:line references from agent report

---

## Step 5: Generate findings.md

**Use Write tool to create findings.md:**

**⛔ CRITICAL: Every issue reported by agents in Step 4 MUST appear here as a FINDING-XXX entry.**

```markdown
# Findings: {project-name}

**Generated:** {timestamp}
**Total Findings:** {count}

## FINDING-001: {Pattern Name}

**Severity:** Critical | High | Medium | Low
**Category:** {lib-commons | architecture | testing | devops}
**Agent:** {ring-dev-team:agent-name}
**Standard:** {file}.md:{section}

### Current Code
```{lang}
// file: {path}:{lines}
{actual code}
```

### Ring Standard Reference
**Standard:** {standards-file}.md → Section: {section-name}
**Pattern:** {pattern-name}
**URL:** https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/{file}.md

### Required Changes
1. {action item 1 - what to change}
2. {action item 2 - what to add/remove}
3. {action item 3 - pattern to follow}

### Why This Matters
- **Problem:** {what is wrong with current code}
- **Standard Violated:** {specific section from Ring standards}
- **Impact:** {business/technical impact if not fixed}

---

## FINDING-002: ...
```

---

## Step 6: Group Findings into Tasks

**⛔ HARD GATE: Every FINDING-XXX MUST appear in at least one REFACTOR-XXX task.**

Group related findings by:
1. Module/bounded context (same file/package = same task)
2. Dependency order (foundational changes first)
3. Severity (critical first)

**Mapping Verification:**
```
Before proceeding to Step 7, verify:
- Total findings in findings.md: X
- Total findings referenced in tasks: X (MUST MATCH)
- Orphan findings (not in any task): 0 (MUST BE ZERO)
```

**If ANY finding is not mapped to a task → STOP. Add missing findings to tasks.**

---

## Step 7: Generate tasks.md

**Use Write tool to create tasks.md:**

```markdown
# Refactoring Tasks: {project-name}

**Source:** findings.md
**Total Tasks:** {count}

## REFACTOR-001: {Task Name}

**Priority:** Critical | High | Medium
**Effort:** {hours}h
**Dependencies:** {other tasks or none}

### Findings Addressed
| Finding | Pattern | Severity | File:Line |
|---------|---------|----------|-----------|
| FINDING-001 | {name} | Critical | src/handler.go:45 |
| FINDING-003 | {name} | High | src/service.go:112 |

### Ring Standards to Follow
| Standard File | Section | URL |
|---------------|---------|-----|
| golang.md | Error Handling | [Link](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md) |
| sre.md | Structured Logging | [Link](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/sre.md) |

### Required Actions
1. [ ] {action from FINDING-001 - specific change to make}
2. [ ] {action from FINDING-001 - pattern to implement}
3. [ ] {action from FINDING-003 - specific change to make}

### Acceptance Criteria
- [ ] Code follows {standard}.md → {section} pattern
- [ ] No {anti-pattern} usage remains
- [ ] Tests pass after refactoring
- [ ] {additional criteria from findings}
```

---

## Step 8: User Approval

```yaml
AskUserQuestion:
  questions:
    - question: "Review refactoring plan. How to proceed?"
      header: "Approval"
      options:
        - label: "Approve all"
          description: "Proceed to dev-cycle execution"
        - label: "Critical only"
          description: "Execute only Critical/High tasks"
        - label: "Cancel"
          description: "Keep analysis, skip execution"
```

---

## Step 9: Save Artifacts

```
docs/refactor/{timestamp}/
├── codebase-report.md  (Step 3)
├── findings.md         (Step 5)
└── tasks.md           (Step 7)
```

---

## Step 10: Handoff to dev-cycle

**If user approved, use SlashCommand tool with tasks path:**

```yaml
SlashCommand:
  command: "/ring-dev-team:dev-cycle docs/refactor/{timestamp}/tasks.md"
```

Where `{timestamp}` is the same timestamp used in Step 9 artifacts.

dev-cycle executes each REFACTOR-XXX task through 6-gate process.

---

## Output Schema

```yaml
artifacts:
  - codebase-report.md (Step 3)
  - findings.md (Step 5)
  - tasks.md (Step 7)

traceability:
  Ring Standard → FINDING-XXX → REFACTOR-XXX → Implementation
```

---

## ⛔ Critical Rules Summary (READ THIS)

### Rule 1: Codebase Exploration MUST Use Specific Agent

```
✅ CORRECT: Task(subagent_type="ring-default:codebase-explorer", model="opus")
❌ WRONG:   Bash(find/ls/tree)
❌ WRONG:   Task(subagent_type="Explore")
❌ WRONG:   Task(subagent_type="general-purpose")
```

### Rule 2: Todo Items MUST Be Exact

Create these EXACT todo items (copy/paste):
1. `Validate PROJECT_RULES.md exists`
2. `Detect project language (go.mod or package.json)`
3. `Use Task tool: subagent_type=ring-default:codebase-explorer`
4. `Save codebase-report.md (GATE: blocks step 5)`
5. `Dispatch specialist agents in parallel`
6. `Generate findings.md`
7. `Generate tasks.md`
8. `User approval`
9. `Handoff to dev-cycle`

### Rule 3: Step 3 Blocks Step 5

```
Step 3 (codebase-explorer) → Creates codebase-report.md
                                    ↓
Step 4 (GATE) → Verifies file exists
                                    ↓
Step 5 (specialist agents) → ONLY runs if gate passes
```

### Why These Rules Exist

| Tool | What It Does | Why Wrong for Step 3 |
|------|--------------|---------------------|
| `Bash find/ls` | Lists file paths | No architectural analysis, no pattern detection |
| `Task(Explore)` | Fast codebase search | Different agent, lacks Ring standards context |
| `Task(general-purpose)` | Generic tasks | No specialized codebase analysis output format |
| `ring-default:codebase-explorer` | Deep architecture analysis | ✅ Correct - provides structured report for Step 5 |

### If You Violated These Rules

1. STOP current execution
2. DELETE any codebase-report.md created by wrong method
3. Go back to Step 3
4. Use correct Task tool call with `subagent_type="ring-default:codebase-explorer"`
5. Save output as codebase-report.md
6. Continue from Step 4

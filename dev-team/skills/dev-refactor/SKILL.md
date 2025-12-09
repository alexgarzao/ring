---
name: dev-refactor
description: |
  Analyzes existing codebase against standards to identify gaps in architecture, code quality,
  testing, and DevOps. Auto-detects project language and uses appropriate agent standards
  (Go, TypeScript, Frontend, DevOps, SRE). Generates refactoring tasks.md compatible with dev-cycle.

trigger: |
  - User wants to refactor existing project to follow standards
  - User runs /ring-dev-team:dev-refactor command
  - Legacy codebase needs modernization
  - Project audit requested

skip_when: |
  - Greenfield project → Use /ring-pm-team:pre-dev-* instead
  - Single file fix → Use ring-dev-team:dev-cycle directly
  - Unknown language (no go.mod, package.json, etc.) → Specify language manually

sequence:
  before: [ring-dev-team:dev-cycle]

related:
  similar: [ring-pm-team:pre-dev-research]
  complementary: [ring-dev-team:dev-cycle, ring-dev-team:dev-implementation]
---

# Dev Refactor Skill

This skill analyzes an existing codebase to identify gaps between current implementation and project standards, then generates a structured refactoring plan compatible with the dev-cycle workflow.

## What This Skill Does

1. **Detects project language** (Go, TypeScript, Python) from manifest files
2. **Reads PROJECT_RULES.md** (project-specific standards - MANDATORY)
3. **Dispatches specialized agents** that load their own Ring standards via WebFetch
4. **Compiles agent findings** into structured analysis report
5. **Generates tasks.md** in the same format as PM Team output
6. **User approves** the plan before execution via dev-cycle

## Foundational Principle

**REFACTORING ANALYSIS IS NOT OPTIONAL FOR CODEBASES WITH TECHNICAL DEBT**

When user requests refactoring or improvement:
1. **NEVER** skip analysis because "code works"
2. **ALWAYS** analyze all 4 dimensions
3. **DOCUMENT** all findings, not just critical
4. **PRESERVE** full analysis even if user filters later

**Cost comparison:**
- Cost of refactoring now: Known, bounded
- Cost of compounding debt: Unknown, unbounded

**Analysis now saves 10x effort later.**

## Pressure Resistance

**Codebase analysis is MANDATORY when requested. Pressure scenarios and required responses:**

| Pressure Type | Request | Agent Response |
|---------------|---------|----------------|
| **Works Fine** | "Code works, skip analysis" | "Working ≠ maintainable. Analysis reveals hidden technical debt." |
| **Time** | "No time for full analysis" | "Partial analysis = partial picture. Technical debt compounds daily." |
| **Legacy** | "Standards don't apply to legacy" | "Legacy code needs analysis MOST. Document gaps for improvement." |
| **Critical Only** | "Only fix critical issues" | "Medium issues become critical. Document all, prioritize later." |

**Non-negotiable principle:** If user requests refactoring analysis, complete ALL 4 dimensions (Architecture, Code, Testing, DevOps).

## Common Rationalizations - REJECTED

| Excuse | Reality |
|--------|---------|
| "Code works fine" | Working ≠ maintainable. Analysis finds hidden debt. |
| "Too time-consuming" | Cost of analysis < cost of compounding debt. |
| "Standards don't fit us" | Then document YOUR standards. Analysis still reveals gaps. |
| "Only critical matters" | Today's medium = tomorrow's critical. Document all. |
| "Legacy gets a pass" | Legacy sets precedent. Analysis shows what to improve. |
| "Team has their own way" | Document "their way" as standards. Analyze against it. |
| "ROI of refactoring is low" | ROI calculation requires analysis. You can't calculate without data. |
| "Partial analysis is enough" | Partial analysis = partial picture. Hidden debt in skipped areas. |
| "3 years without bugs = stable" | No bugs ≠ no debt. Time doesn't validate architecture. |
| "Analysis is overkill" | Analysis is the MINIMUM. Refactoring without analysis is guessing. |
| "Code smells ≠ problems" | Code smells ARE problems. They slow development and cause bugs. |
| "No specific problem motivating" | Technical debt IS the problem. Analysis quantifies it. |
| "Analysis complete, user can decide" | Analysis without action guidance is incomplete. Provide tasks.md. |
| "Findings documented, my job done" | Findings → Tasks → Execution. Documentation alone changes nothing. |

## Red Flags - STOP

If you catch yourself thinking ANY of these, STOP immediately:

- "Code works, no need to analyze"
- "This is too time-consuming"
- "Standards don't apply here"
- "Only critical issues matter"
- "Legacy code is exempt"
- "That's just how we do it here"
- "ROI doesn't justify full analysis"
- "Partial analysis is sufficient"
- "3+ years stable = no debt"
- "Analysis is overkill"
- "Code smells aren't real problems"
- "No specific problem to solve"
- "Analysis is done, user decides next"
- "Documented findings, job complete"

**All of these indicate analysis violation. Complete full 4-dimension analysis.**

## Analysis-to-Action Pipeline - MANDATORY

**Analysis without action guidance is incomplete:**

| Deliverable | Required? | Purpose |
|-------------|----------|---------|
| analysis-report.md | ✅ YES | Document findings |
| tasks.md | ✅ YES | Convert findings to actionable tasks |
| User approval prompt | ✅ YES | Get explicit decision on execution |

**Analysis completion checklist:**
- [ ] All 4 dimensions analyzed
- [ ] Findings categorized by severity
- [ ] Findings converted to REFACTOR-XXX tasks
- [ ] tasks.md generated in PM Team format
- [ ] User presented with approval options

**"Analysis complete" means tasks.md exists and user has been asked to approve.**

**If analysis ends without tasks.md:**
1. Analysis is NOT complete
2. Step 6 (Generate tasks.md) was skipped
3. Return to Step 6 before declaring completion

## Analysis Dimensions - ALL REQUIRED

**Every analysis MUST cover all 4 dimensions:**

| Dimension | What It Checks | Skip Allowed? |
|-----------|---------------|---------------|
| Architecture | Patterns, structure, dependencies | ❌ NO |
| Code Quality | Standards compliance, complexity, naming | ❌ NO |
| Testing | Coverage, test quality, TDD compliance | ❌ NO |
| DevOps | Containerization, CI/CD, infrastructure | ❌ NO |

**If user says "only check X":**
- Check X thoroughly
- Check other dimensions briefly
- Report: "Full analysis recommended for dimensions: [Y, Z]"

**NEVER produce partial analysis without noting gaps.**

## Cancellation Documentation - MANDATORY

**If user cancels analysis at approval step:**

1. **ASK:** "Why is analysis being cancelled?"
2. **DOCUMENT:** Save reason to `docs/refactor/{timestamp}/cancelled-reason.md`
3. **PRESERVE:** Keep partial analysis artifacts
4. **NOTE:** "Analysis cancelled by user: [reason]. Partial findings preserved."

**Cancellation without documentation is NOT allowed.**

## Prerequisites

Before starting analysis:

1. **Project root identified**: Know where the codebase lives
2. **Language detectable**: Project has go.mod, package.json, or similar manifest
3. **Scope defined**: Full project or specific directories
4. **PROJECT_RULES.md exists**: MANDATORY - analysis cannot proceed without it

### PROJECT_RULES.md is MANDATORY

**HARD GATE. Do NOT proceed without PROJECT_RULES.md.**

**Check:** (1) docs/PROJECT_RULES.md (2) docs/STANDARDS.md (legacy) → Found: Proceed | NOT Found: STOP with blocker

**Rationalizations REJECTED:** "Defaults are fine" → Generic, not YOUR conventions | "Add later" → Wrong standards = rework | "Small project" → Standards still needed | "Best practices" → "Best" varies, YOUR rules define YOUR best

**Note:** After check passes, agents load their own Ring standards via WebFetch. dev-refactor only reads PROJECT_RULES.md locally.

## Analysis Dimensions

| Dimension | Category | Checks |
|-----------|----------|--------|
| **Architecture** | DDD | Entities (identity), Value Objects (immutable), Aggregates (invariants), Repositories (interfaces), Domain events |
| | Clean/Hexagonal | Dependency direction (inward), Domain isolation, Ports as interfaces, Adapters implement ports |
| | Structure | Matches PROJECT_RULES.md, Separation of concerns, No circular deps |
| **Code Quality** | Naming | Files (snake/kebab), Functions (convention), Constants (UPPER_SNAKE) |
| | Errors | No ignored errors, Wrapped with context, No panic() in business, Custom domain errors |
| | Forbidden | No global state, No magic numbers, No commented code, No TODO without issue, No `any` (TS) |
| | Security | Input validation, Parameterized queries, No sensitive logging, No hardcoded secrets |
| **Testing** | Coverage | Current %, Gap to 80% minimum, Critical paths |
| | Patterns | Table-driven (Go), AAA structure, Proper mocks, No test pollution |
| | Types | Unit tests, Integration tests, Fixtures/factories |
| **DevOps** | Container | Dockerfile exists, Multi-stage, Non-root user, Health check |
| | Local Dev | docker-compose.yml, All services, Hot reload volumes |
| | Environment | .env.example, All vars documented, No secrets in repo |
| | CI/CD | Pipeline exists, Tests in CI, Linting enforced |

## Step 0: Verify PROJECT_RULES.md Exists (HARD GATE)

**NON-NEGOTIABLE. Analysis CANNOT proceed without project standards.**

**Check:** (1) docs/PROJECT_RULES.md (2) docs/STANDARDS.md (legacy) (3) --standards arg → Found: Proceed | NOT Found: STOP with blocker `missing_prerequisite`

**Pressure Resistance:** "Use defaults" → Generic, YOUR project needs YOUR rules | "We don't have standards" → Perfect time to define them | "Skip, analyze anyway" → Analysis without target = meaningless findings

---

## Step 1: Detect Project Language

| Manifest | Project Type | Agent |
|----------|--------------|-------|
| `go.mod` | Go | `backend-engineer-golang` |
| `package.json` + react/next | Frontend TS | `frontend-bff-engineer-typescript` |
| `package.json` + express/fastify/nestjs | Backend TS | `backend-engineer-typescript` |
| `Dockerfile` | DevOps | `devops-engineer` |
| Multiple | Mixed | Dispatch all applicable agents |

**Output:** Primary language, Project type, Agent standards list

## Step 2: Read PROJECT_RULES.md

**Action:** Read tool to load `docs/PROJECT_RULES.md` (project-specific conventions, stack decisions, architecture patterns)

**Responsibilities:** dev-refactor reads PROJECT_RULES.md locally, dispatches agents | Agents load Ring standards via WebFetch, analyze, return findings

## Step 3: Scan Codebase

**IMPORTANT:** Dispatch 4 agents in SINGLE message (parallel). All prompts start with `**MODE: ANALYSIS ONLY**`.

| Task | Agent | Focus Areas |
|------|-------|-------------|
| **Code** | Based on language: `ring-dev-team:backend-engineer-golang` / `ring-dev-team:backend-engineer-typescript` / `ring-dev-team:frontend-bff-engineer-typescript` | Structure, Architecture (DDD/Clean), Error handling, Naming, Security |
| **Testing** | `ring-dev-team:qa-analyst` | Coverage ≥80%, Test patterns, TDD compliance, Mock usage |
| **DevOps** | `ring-dev-team:devops-engineer` | Dockerfile (multi-stage, non-root, health), docker-compose, .env.example |
| **SRE** | `ring-dev-team:sre` | Health endpoints, Structured JSON logging, Tracing |

**Prompt template:** `**MODE: ANALYSIS ONLY** - Analyze for refactoring. Return findings with: severity, location (file:line), issue, recommendation.`

**Output:** Dimension-specific findings with severities for Step 4.

## Step 4: Compile Findings

**Process:** (1) Collect agent outputs (2) Parse findings (severity, location, issue, recommendation) (3) Deduplicate (4) Categorize by dimension (5) Sort by severity (Critical → High → Medium → Low)

**Output:** `analysis-report.md` with Summary table (Dimension | Issues | Critical | High | Medium | Low) + sections for each severity level with format: `### {ID}: {title}` + Location, Issue, Standard, Fix

## Step 5: Prioritize and Group

**Strategy:** (1) By bounded context/module (2) By dependency order (fix deps first) (3) By risk (critical security first)

**Output:** Grouped tasks: `REFACTOR-001: Fix domain layer isolation` (ARCH-001, 003, 005) → `REFACTOR-002: Error handling` (CODE-002, 007, 012) → `REFACTOR-003: Test coverage` (TEST-001-003) → `REFACTOR-004: Containerization` (DEVOPS-001-002)

## Step 6: Generate tasks.md

**Format:** Same as PM Team output. Each task has:

| Section | Content |
|---------|---------|
| **Header** | `## REFACTOR-XXX: {title}` |
| **Metadata** | Type, Effort, Priority, Dependencies |
| **Description** | What to fix and why |
| **Acceptance Criteria** | `- [ ] AC-X:` checklist items |
| **Technical Notes** | Files to modify, Patterns, Related issues |
| **Issues Addressed** | Table: ID \| Description \| Location |

**File:** `docs/refactor/{timestamp}/tasks.md`

## Step 7: User Approval

**AskUserQuestion:** "Review the refactoring plan. How do you want to proceed?"

| Option | Action |
|--------|--------|
| **Approve all** | Save tasks.md, proceed to dev-cycle execution |
| **Approve with changes** | Let user edit tasks.md first, then proceed |
| **Critical only** | Filter to only Critical/High priority tasks |
| **Cancel** | Abort execution, keep analysis report only |

## Step 8: Save Artifacts

**Location:** `docs/refactor/{timestamp}/` → `analysis-report.md` (findings) + `tasks.md` (approved tasks) + `project-rules-used.md` (snapshot of PROJECT_RULES.md)

**Note:** Ring standards are not saved (loaded dynamically by agents via WebFetch). Only project-specific rules preserved.

## Step 9: Handoff to dev-cycle

**If approved:** `/ring-dev-team:dev-cycle docs/refactor/{timestamp}/tasks.md`

Executes each task through 6 gates: Implementation (TDD) → DevOps → SRE → Testing → Review (3 parallel) → Validation

## Output Schema

**Format:** markdown | **Artifacts:** `analysis-report.md`, `tasks.md` (both in `docs/refactor/{timestamp}/`)

**Required sections:** `## Summary`, `## Critical Issues`, `## REFACTOR-XXX` (task entries)

## Example Usage

| Command | Purpose |
|---------|---------|
| `/ring-dev-team:dev-refactor` | Full project analysis |
| `/ring-dev-team:dev-refactor src/domain` | Analyze specific directory |
| `/ring-dev-team:dev-refactor --standards path/to/PROJECT_RULES.md` | Custom standards file |
| `/ring-dev-team:dev-refactor --analyze-only` | Analysis only (no execution) |

## Related Skills

| Skill | Purpose |
|-------|---------|
| `ring-dev-team:dev-cycle` | Executes refactoring tasks through 6 gates (after approval) |

## Key Principles

1. **Same workflow**: Refactoring uses the same dev-cycle as new features
2. **Separation of concerns**: dev-refactor reads PROJECT_RULES.md locally; agents load Ring standards via WebFetch
3. **Standards-driven**: Analysis combines project-specific rules (PROJECT_RULES.md) + Ring standards (loaded by agents)
4. **Traceable**: Every task links back to specific issues found
5. **Incremental**: Can approve subset of tasks (critical only, etc.)
6. **Reversible**: Original analysis preserved for reference

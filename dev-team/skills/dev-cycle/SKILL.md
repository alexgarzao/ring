---
name: dev-cycle
description: |
  Main orchestrator for the 6-gate development cycle system. Loads tasks/subtasks
  from PM team output and executes through implementation, devops, SRE, testing, review,
  and validation gates with state persistence and metrics collection.

trigger: |
  - Starting a new development cycle with a task file
  - Resuming an interrupted development cycle (--resume flag)
  - Need structured, gate-based task execution with quality checkpoints

skip_when: |
  - Already in a specific gate skill -> let that gate complete
  - Need to plan tasks first -> use ring-default:writing-plans or ring-pm-team:pre-dev-full
  - Human explicitly requests manual implementation (non-AI workflow)

NOT_skip_when: |
  - "Task is simple" → Simple ≠ risk-free. Execute gates.
  - "Tests already pass" → Tests ≠ review. Different concerns.
  - "Time pressure" → Pressure ≠ permission. Document and proceed.
  - "Already did N gates" → Sunk cost is irrelevant. Complete all gates.

sequence:
  before: [ring-dev-team:dev-feedback-loop]

related:
  complementary: [ring-dev-team:dev-implementation, ring-dev-team:dev-devops, ring-dev-team:dev-sre, ring-dev-team:dev-testing, ring-dev-team:dev-review, ring-dev-team:dev-validation, ring-dev-team:dev-feedback-loop]

verification:
  automated:
    - command: "test -f .ring/dev-team/current-cycle.json"
      description: "State file exists"
      success_pattern: "exit 0"
    - command: "cat .ring/dev-team/current-cycle.json | jq '.current_gate'"
      description: "Current gate is valid"
      success_pattern: "[0-5]"
  manual:
    - "All gates for current task show PASS in state file"
    - "No tasks have status 'blocked' for more than 3 iterations"

examples:
  - name: "New feature from PM workflow"
    invocation: "/ring-dev-team:dev-cycle docs/pre-dev/auth/tasks.md"
    expected_flow: |
      1. Load tasks with subtasks from tasks.md
      2. Ask user for checkpoint mode (per-task/per-gate/continuous)
      3. Execute Gate 0-5 for each task sequentially
      4. Generate feedback report after completion
  - name: "Resume interrupted cycle"
    invocation: "/ring-dev-team:dev-cycle --resume"
    expected_state: "Continues from last saved gate in current-cycle.json"
  - name: "Execute with per-gate checkpoints"
    invocation: "/ring-dev-team:dev-cycle tasks.md --checkpoint per-gate"
    expected_flow: |
      1. Execute Gate 0, pause for approval
      2. User approves, execute Gate 1, pause
      3. Continue until all gates complete
---

# Development Cycle Orchestrator

## Overview

The development cycle orchestrator loads tasks/subtasks from PM team output (or manual task files) and executes through 6 quality gates. Tasks are loaded at initialization - no separate import gate.

**Announce at start:** "I'm using the dev-cycle skill to orchestrate task execution through 6 gates."

## Pressure Resistance

**This skill enforces MANDATORY gates. Pressure scenarios and required responses:**

| Pressure Type | Request | Agent Response |
|---------------|---------|----------------|
| **Time** | "Production down, skip gates" | "Gates prevent production issues. Automatic mode = 20 min. Skipping gates increases risk." |
| **Sunk Cost** | "Already did 4 gates, skip review" | "Each gate catches different issues. Prior gates don't reduce review value. Review = 10 min." |
| **Authority** | "Director override, ship now" | "Cannot skip GATES based on authority. Can skip CHECKPOINTS (automatic mode). Gates are non-negotiable." |
| **Simplicity** | "Simple fix, skip gates" | "Simple tasks have complex impacts. AI doesn't negotiate. ALL tasks require ALL gates. No exceptions." |

**Non-negotiable principle:** Execution mode selection affects CHECKPOINTS (user approval pauses), not GATES (quality checks). ALL gates execute regardless of mode.

## Common Rationalizations - REJECTED

| Excuse | Reality |
|--------|---------|
| "Task is simple, skip gates" | Simple tasks have complex impacts. Gates catch what you don't see. |
| "Already passed N gates" | Each gate catches different issues. Sunk cost is irrelevant. |
| "Manager approved skipping" | Authority cannot override quality gates. Document the pressure. |
| "Tests pass, skip review" | Tests verify code works. Review verifies code is correct, secure, maintainable. |
| "Automatic mode means faster" | Automatic mode skips CHECKPOINTS, not GATES. Same quality, less interruption. |
| "Automatic mode will skip review" | Automatic mode affects user approval pauses, NOT quality gates. ALL gates execute regardless. |
| "We'll fix issues post-merge" | Post-merge fixes are 10x more expensive. Gates exist to prevent this. |
| "Defense in depth exists (frontend validates)" | Frontend can be bypassed. Backend is the last line. Fix at source. |
| "Backlog the Medium issue, it's documented" | Documented risk ≠ mitigated risk. Medium in Gate 4 = fix NOW, not later. |
| "Risk-based prioritization allows deferral" | Gates ARE the risk-based system. Reviewers define severity, not you. |
| "Business context justifies exception" | Business context informed gate design. Gates already account for it. |
| "Demo tomorrow, we'll fix after" | Demo with untested code = demo that crashes. Gates BEFORE demo. |
| "Just this one gate, then catch up" | One skipped gate = precedent. Next gate also "just one". No incremental compromise. |
| "90% done, finish without remaining gates" | 90% done with 0% gates = 0% verified. Gates verify the 90%. |
| "Ship now, gates as fast-follow" | Fast-follow = never-follow. Gates now or not at all. |

## Red Flags - STOP

If you catch yourself thinking ANY of these, STOP immediately:

- "This task is too simple for gates"
- "We already passed most gates"
- "Manager/Director said to skip"
- "Tests pass, review is redundant"
- "We can fix issues later"
- "Automatic mode will handle it"
- "Automatic mode will skip review"
- "Just this once won't hurt"
- "Frontend already validates this"
- "I'll document it in backlog/TODO"
- "Medium severity can wait"
- "Business context is different here"
- "Risk-based approach says defer"
- "Demo tomorrow, fix after"
- "Just this one gate"
- "90% done, almost there"
- "Ship now, gates as fast-follow"

**All of these indicate you're about to violate mandatory workflow. Return to gate execution.**

## Incremental Compromise Prevention

**The "just this once" pattern leads to complete gate erosion:**

```text
Day 1: "Skip review just this once" → Approved (precedent set)
Day 2: "Skip testing, we did it last time" → Approved (precedent extended)
Day 3: "Skip implementation checks, pattern established" → Approved (gates meaningless)
Day 4: Production incident from Day 1 code
```

**Prevention rules:**
1. **No incremental exceptions** - Each exception becomes the new baseline
2. **Document every pressure** - Log who requested, why, outcome
3. **Escalate patterns** - If same pressure repeats, escalate to team lead
4. **Gates are binary** - Complete or incomplete. No "mostly done".

## The 6 Gates

| Gate | Skill | Purpose | Agent |
|------|-------|---------|-------|
| 0 | dev-implementation | Write code following TDD | Based on task language/domain |
| 1 | dev-devops | Infrastructure and deployment | ring-dev-team:devops-engineer |
| 2 | dev-sre | Observability (metrics, health, logging) | ring-dev-team:sre |
| 3 | dev-testing | Unit tests for acceptance criteria | ring-dev-team:qa-analyst |
| 4 | dev-review | Parallel code review | ring-default:code-reviewer, ring-default:business-logic-reviewer, ring-default:security-reviewer (3x parallel) |
| 5 | dev-validation | Final acceptance validation | N/A (verification) |

## Integrated PM → Dev Workflow

**PM Team Output** → **Dev Team Execution** (`/ring-dev-team:dev-cycle`)

| Input Type | Path | Structure |
|------------|------|-----------|
| **Tasks only** | `docs/pre-dev/{feature}/tasks.md` | T-001, T-002, T-003 with requirements + acceptance criteria |
| **Tasks + Subtasks** | `docs/pre-dev/{feature}/` | tasks.md + `subtasks/{task-id}/ST-XXX-01.md, ST-XXX-02.md...` |

## Execution Order

**Core Principle:** Each execution unit (task OR subtask) passes through **all 6 gates** before the next unit.

**Flow:** Unit → Gate 0-5 → 🔒 Unit Checkpoint (Step 7.1) → 🔒 Task Checkpoint (Step 7.2) → Next Unit

| Scenario | Execution Unit | Gates Per Unit |
|----------|----------------|----------------|
| Task without subtasks | Task itself | 6 gates |
| Task with subtasks | Each subtask | 6 gates per subtask |

**Execution Modes:**

| Mode | Step 7.1 (unit) | Step 7.2 (task) |
|------|-----------------|-----------------|
| `manual_per_subtask` | ✓ Every unit | ✓ Every task |
| `manual_per_task` | ✗ Skip | ✓ Every task |
| `automatic` | ✗ Skip | ✗ Skip |

**Checkpoint Options:** Continue / Test First / Stop (7.1) | Continue / Integration Test / Stop (7.2)

## State Management

State persisted to `.ring/dev-team/current-cycle.json`:

| Field | Type | Values |
|-------|------|--------|
| `execution_mode` | string | `manual_per_subtask` \| `manual_per_task` \| `automatic` |
| `status` | string | `in_progress` \| `completed` \| `failed` \| `paused` \| `paused_for_approval` \| `paused_for_testing` \| `paused_for_task_approval` \| `paused_for_integration_testing` |
| `current_task_index` | int | Current task position |
| `current_gate` | int | 0-5 |
| `tasks[].status` | string | `pending` \| `in_progress` \| `completed` \| `failed` \| `blocked` |
| `tasks[].gate_progress` | object | Status per gate (implementation, devops, sre, testing, review, validation) |
| `metrics` | object | `total_duration_ms`, `gate_durations`, `review_iterations` |

## Step 0: Verify PROJECT_RULES.md Exists (HARD GATE)

**NON-NEGOTIABLE. Cycle CANNOT proceed without project standards.**

**Check:** (1) docs/PROJECT_RULES.md (2) docs/STANDARDS.md (legacy) (3) --resume state file → Found: Proceed | NOT Found: STOP with blocker `missing_prerequisite`

**Pressure Resistance:** "Standards slow us down" → No target = guessing = rework | "Use defaults" → Defaults are generic, YOUR project has specific conventions | "Create later" → Later = refactoring

---

## Step 1: Initialize or Resume

### New Cycle (with task file path)

**Input:** `path/to/tasks.md` OR `path/to/pre-dev/{feature}/`

1. **Detect input:** File → Load directly | Directory → Load tasks.md + discover subtasks/
2. **Build order:** Read tasks, check for subtasks (ST-XXX-01, 02...) or TDD autonomous mode
3. **Initialize state:** Generate cycle_id, create `.ring/dev-team/current-cycle.json`, set indices to 0
4. **Display plan:** "Loaded X tasks with Y subtasks"
5. **ASK EXECUTION MODE (MANDATORY - AskUserQuestion):**
   - Options: (a) Manual per subtask (b) Manual per task (c) Automatic
   - **Do NOT skip:** User hints ≠ mode selection. Only explicit a/b/c is valid.
6. **Start:** Display mode, proceed to Gate 0

### Resume Cycle (--resume flag)

1. Load `.ring/dev-team/current-cycle.json`, validate
2. Display: cycle started, tasks completed/total, current task/subtask/gate, paused reason
3. **Handle paused states:**

| Status | Action |
|--------|--------|
| `paused_for_approval` | Re-present Step 7.1 checkpoint |
| `paused_for_testing` | Ask if testing complete → continue or keep paused |
| `paused_for_task_approval` | Re-present Step 7.2 checkpoint |
| `paused_for_integration_testing` | Ask if integration testing complete |
| `paused` (generic) | Ask user to confirm resume |
| `in_progress` | Resume from current gate |

## Input Validation

Task files are generated by `/ring-pm-team:pre-dev-*` or `/ring-dev-team:dev-refactor`, which handle content validation. The dev-cycle performs basic format checks:

### Format Checks

| Check | Validation | Action |
|-------|------------|--------|
| File exists | Task file path is readable | Error: abort |
| Task headers | At least one `## Task:` found | Error: abort |
| Task ID format | `## Task: {ID} - {Title}` | Warning: use line number as ID |
| Acceptance criteria | At least one `- [ ]` per task | Warning: task may fail validation gate |

## Step 2: Gate 0 - Implementation (Per Execution Unit)

**REQUIRED SUB-SKILL:** Use ring-dev-team:dev-implementation

**Execution Unit:** Task (if no subtasks) OR Subtask (if task has subtasks)

1. Record gate start timestamp
2. **Select agent:** Go → `backend-engineer-golang` | TS backend → `backend-engineer-typescript` | React/Frontend → `frontend-engineer-typescript` | Infra → `devops-engineer`
3. **Dispatch:** Task tool with unit requirements, acceptance criteria, TDD methodology (RED→GREEN→REFACTOR)
4. **Receive:** Implementation report (files changed, tests written, results)
5. **Update state:** `gate_progress.implementation.status = "completed"`, artifacts
6. Proceed to Gate 1

## Step 3: Gate 1 - DevOps (Per Execution Unit)

**REQUIRED SUB-SKILL:** Use ring-dev-team:dev-devops

1. Record timestamp, check if DevOps needed (infra changes, new deployment, CI/CD updates)
2. **If needed:** Dispatch `ring-dev-team:devops-engineer` - check Dockerfile, K8s, CI/CD, env vars
3. **If not needed:** Mark "skipped" with reason
4. Update state, proceed to Gate 2

## Step 4: Gate 2 - SRE (Per Execution Unit)

**REQUIRED SUB-SKILL:** Use ring-dev-team:dev-sre

1. Record timestamp, check if SRE needed (new service/API, external deps, performance-critical)
2. **If needed:** Dispatch `ring-dev-team:sre` - Prometheus /metrics, health endpoints, JSON logging, tracing
3. **If not needed:** Mark "skipped" with reason
4. Update state, proceed to Gate 3

## Step 5: Gate 3 - Testing (Per Execution Unit)

**REQUIRED SUB-SKILL:** Use ring-dev-team:dev-testing

1. Record timestamp, dispatch `ring-dev-team:qa-analyst` with acceptance criteria
2. **Requirements:** Unit tests (≥80% coverage), integration tests, E2E (if applicable)
3. **If tests fail:** Loop back to Gate 0 with failure details, increment review_iterations
4. **If tests pass:** Update state, proceed to Gate 4

## Step 6: Gate 4 - Review (Per Execution Unit)

**REQUIRED SUB-SKILL:** Use ring-default:requesting-code-review

1. Record timestamp
2. **Dispatch 3 reviewers in parallel (single message, 3 Task calls, model: opus):** `code-reviewer`, `business-logic-reviewer`, `security-reviewer`
3. **Aggregate by severity:** Critical/High/Medium → Must fix | Low → TODO(review) | Cosmetic → FIXME(nitpick)
4. **If issues found:** Fix → re-run all 3 → repeat until clean (max 3 iterations)
5. When resolved, proceed to Gate 5

## Step 7: Gate 5 - Validation (Per Execution Unit)

1. Record timestamp
2. **Verify:** Each acceptance criterion implemented + tested → PASS/FAIL
3. **Final check:** All tests pass? No Critical/High/Medium issues? All criteria met?
4. **If fails:** Log reasons, loop back to appropriate gate
5. **If passes:** Set unit status = "completed", proceed to Step 7.1

## Step 7.1: Execution Unit Approval (Conditional)

**Checkpoint depends on `execution_mode`:** `manual_per_subtask` → Execute | `manual_per_task` / `automatic` → Skip

1. Set `status = "paused_for_approval"`, save state
2. Present summary: Unit ID, Parent Task, Gates 0-5 status, Criteria X/X, Duration, Files Changed
3. **AskUserQuestion:** "Ready to proceed?" Options: (a) Continue (b) Test First (c) Stop Here
4. **Handle response:**

| Response | Action |
|----------|--------|
| Continue | Set in_progress, move to next unit (or Step 7.2 if last) |
| Test First | Set `paused_for_testing`, STOP, output resume command |
| Stop Here | Set `paused`, STOP, output resume command |

## Step 7.2: Task Approval Checkpoint (Conditional)

**Checkpoint depends on `execution_mode`:** `manual_per_subtask` / `manual_per_task` → Execute | `automatic` → Skip

1. Set task `status = "completed"`, cycle `status = "paused_for_task_approval"`, save state
2. Present summary: Task ID, Subtasks X/X, Total Duration, Review Iterations, Files Changed
3. **AskUserQuestion:** "Task complete. Ready for next?" Options: (a) Continue (b) Integration Test (c) Stop Here
4. **Handle response:**

| Response | Action |
|----------|--------|
| Continue | Set in_progress, increment task_index, reset to Gate 0 |
| Integration Test | Set `paused_for_integration_testing`, STOP |
| Stop Here | Set `paused`, STOP |

**Note:** Tasks without subtasks execute both 7.1 and 7.2 in sequence.

## Step 8: Cycle Completion

1. **Calculate metrics:** total_duration_ms, average gate durations, review iterations, pass/fail ratio
2. **Update state:** `status = "completed"`, `completed_at = timestamp`
3. **Generate report:** Task | Subtasks | Duration | Review Iterations | Status
4. **REQUIRED:** Invoke `ring-dev-team:dev-feedback-loop` for metrics tracking
5. **Report:** "Cycle completed. Tasks X/X, Subtasks Y, Time Xh Xm, Review iterations X"

## Quick Commands

```bash
# Full PM workflow then dev execution
/ring-pm-team:pre-dev-full my-feature
/ring-dev-team:dev-cycle docs/pre-dev/my-feature/

# Simple PM workflow then dev execution
/ring-pm-team:pre-dev-feature my-feature
/ring-dev-team:dev-cycle docs/pre-dev/my-feature/tasks.md

# Manual task file
/ring-dev-team:dev-cycle docs/tasks/sprint-001.md

# Resume interrupted cycle
/ring-dev-team:dev-cycle --resume
```

## Error Recovery

| Type | Condition | Action |
|------|-----------|--------|
| **Recoverable** | Network timeout | Retry with exponential backoff |
| **Recoverable** | Agent failure | Retry once, then pause for user |
| **Recoverable** | Test flakiness | Re-run tests up to 2 times |
| **Non-Recoverable** | Missing required files | Stop and report |
| **Non-Recoverable** | Invalid state file | Must restart (cannot resume) |
| **Non-Recoverable** | Max review iterations | Pause for user |

**On any error:** Update state → Set status (failed/paused) → Save immediately → Report (what failed, why, how to recover, resume command)

## Execution Report

| Metric | Value |
|--------|-------|
| Duration | Xh Xm Ys |
| Tasks Processed | N/M |
| Current Gate | Gate X - [name] |
| Review Iterations | N |
| Result | PASS/FAIL/IN_PROGRESS |

### Gate Timings
| Gate | Duration | Status |
|------|----------|--------|
| Implementation | Xm Ys | in_progress |
| DevOps | - | pending |
| SRE | - | pending |
| Testing | - | pending |
| Review | - | pending |
| Validation | - | pending |

### State File Location
`.ring/dev-team/current-cycle.json`

---
name: ring:dev-cycle-frontend
description: |
  Frontend development cycle orchestrator with 9 gates. Loads tasks from PM team output
  or backend handoff and executes through implementation → devops → accessibility →
  unit testing → visual testing → E2E testing → performance testing → review → validation.

trigger: |
  - Starting a new frontend development cycle with a task file
  - Resuming an interrupted frontend development cycle (--resume flag)
  - After backend dev cycle completes (consuming handoff)

skip_when: |
  - No tasks file exists
  - Task is documentation-only or planning-only
  - Backend project — use ring:dev-cycle instead

sequence:
  before: [ring:dev-report]
---

# Frontend Development Cycle Orchestrator

You orchestrate. Agents execute. NEVER read/write/edit source files (*.ts, *.tsx, *.jsx, *.css) directly.
All code changes go through `Task(subagent_type=...)`. Announce at start: "Using ring:dev-cycle-frontend through 9 gates (Gate 0-8)."

## Step 0: Pre-Execution Setup (MANDATORY)

```
1. Detect UI library: Read package.json
   - "@lerianstudio/sindarian-ui" present → ui_library_mode = "sindarian-ui"
   - Otherwise → ui_library_mode = "fallback-only"
   Store in state.

2. Pre-cache standards (once):
   WebFetch → https://raw.githubusercontent.com/LerianStudio/ring/main/CLAUDE.md
   WebFetch → https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/frontend.md
   WebFetch → testing-accessibility.md, testing-visual.md, testing-e2e.md, testing-performance.md, devops.md, sre.md
   Store in state.cached_standards.

3. Load backend handoff if available: docs/ring:dev-cycle/handoff-frontend.json

4. Verify PROJECT_RULES.md exists → STOP if missing.

5. Ask execution mode: automatic | manual_per_task | manual_per_subtask
```

## Gate Map

| Gate | Cadence | Skill | Agent | Purpose |
|------|---------|-------|-------|---------|
| 0 | subtask | ring:dev-implementation | ring:frontend-engineer / ring:ui-engineer / ring:frontend-bff-engineer-typescript | TDD implementation |
| 1 | task | ring:dev-devops | ring:devops-engineer | Docker/compose/Nginx |
| 2 | task | ring:dev-frontend-accessibility | ring:qa-analyst-frontend (accessibility) | WCAG 2.1 AA |
| 3 | subtask | ring:dev-unit-testing | ring:qa-analyst-frontend (unit) | 85%+ coverage |
| 4 | task | ring:dev-frontend-visual | ring:qa-analyst-frontend (visual) | Snapshot tests |
| 5 | task | ring:dev-frontend-e2e | ring:qa-analyst-frontend (e2e) | Playwright E2E |
| 6 | task | ring:dev-frontend-performance | ring:qa-analyst-frontend (performance) | Core Web Vitals + Lighthouse ≥ 90 |
| 7 | task | ring:codereview | 5 parallel reviewers | Code review |
| 8 | subtask | ring:dev-validation | User | Acceptance sign-off |

All 9 gates are MANDATORY. No exceptions.

## Gate Agent Selection (Gate 0)

| Condition | Agent |
|-----------|-------|
| React/Next.js component | ring:frontend-engineer |
| Design system / Sindarian UI | ring:ui-engineer |
| BFF / API aggregation | ring:frontend-bff-engineer-typescript |
| Mixed | frontend-engineer first, then frontend-bff-engineer-typescript |

Pass `ui_library_mode` to every Gate 0 agent.

## Frontend TDD Policy

| Component Layer | TDD Required? | When |
|-----------------|---------------|------|
| Custom hooks | YES — RED→GREEN | Gate 0 |
| Form validation | YES — RED→GREEN | Gate 0 |
| State management | YES — RED→GREEN | Gate 0 |
| Conditional rendering | YES — RED→GREEN | Gate 0 |
| API integration | YES — RED→GREEN | Gate 0 |
| Layout / styling | NO — test-after | Gate 4 (visual) |
| Animations | NO — test-after | Gate 4 (visual) |
| Static presentational | NO — test-after | Gate 4 (visual) |

## Execution Order

```yaml
for each task:
  for each subtask:
    Gate 0 → Gate 3 → Gate 8   # subtask-level
    [checkpoint if manual_per_subtask]
  
  # task-level (after all subtasks)
  Gate 1 → Gate 2 → Gate 4 → Gate 5 → Gate 6 → Gate 7
```

## Gate Execution Workflow (MANDATORY for every gate)

```
1. Skill("[sub-skill-name]")
2. Follow sub-skill dispatch rules
3. Task(subagent_type=...)
4. Validate output
5. Write state
6. Next gate
```

Sub-skill MUST be loaded before dispatching the agent.

## Gate 7: Reviewers

Dispatch all 5 in parallel (single message):
1. ring:code-reviewer — quality, patterns, React best practices
2. ring:business-logic-reviewer — business logic, AC
3. ring:security-reviewer — XSS, CSRF, auth, CSP
4. ring:test-reviewer — test quality, coverage gaps
5. ring:frontend-engineer (review mode) — accessibility compliance, frontend standards

ALL 5 must pass. 4/5 = FAIL → re-run all 5.

## Gate Completion Criteria

| Gate | Required for COMPLETE |
|------|-----------------------|
| 0 | TDD RED captured (behavioral) + GREEN passes; visual: implementation complete |
| 1 | Dockerfile + docker-compose + .env.example |
| 2 | 0 WCAG AA violations + keyboard + screen reader |
| 3 | Coverage ≥ 85% + all AC tested |
| 4 | All snapshots pass + responsive breakpoints |
| 5 | All user flows + cross-browser (Chromium/Firefox/WebKit) + 3x stable |
| 6 | LCP < 2.5s, CLS < 0.1, INP < 200ms, Lighthouse ≥ 90 |
| 7 | All 5 reviewers PASS |
| 8 | Explicit "APPROVED" from user |

## State Management

State: `docs/ring:dev-cycle-frontend/current-cycle.json`

Write after EVERY gate. If write fails → STOP.

```json
{
  "ui_library_mode": "",
  "tasks_file": "",
  "execution_mode": "",
  "current_gate": 0,
  "current_task": "",
  "current_subtask": "",
  "gates_completed": {},
  "cached_standards": {}
}
```

## Blocker Handling

| Blocker | Action |
|---------|--------|
| Gate failure | STOP. Fix before proceeding. |
| Missing PROJECT_RULES.md | STOP. Create using template. |
| Standards WebFetch fails | STOP. Report. |
| Architectural decision needed | STOP. Present options to user. |

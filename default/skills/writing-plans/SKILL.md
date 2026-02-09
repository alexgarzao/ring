---
name: ring:writing-plans
description: |
  Creates comprehensive implementation plans with exact file paths, complete code
  examples, and verification steps for engineers with zero codebase context.

trigger: |
  - Design phase complete (brainstorming/PRD/TRD validated)
  - Need to create executable task breakdown
  - Creating work for other engineers or AI agents

skip_when: |
  - Design not validated → use brainstorming first
  - Requirements still unclear → use ring:pre-dev-prd-creation first
  - Already have a plan → use ring:executing-plans

sequence:
  after: [brainstorming, ring:pre-dev-trd-creation]
  before: [ring:executing-plans, ring:subagent-driven-development]

related:
  similar: [brainstorming]
---

# Writing Plans

## Overview

This skill dispatches a specialized agent to write comprehensive implementation plans for engineers with zero codebase context.

**Announce at start:** "I'm using the ring:writing-plans skill to create the implementation plan."

**Context:** This should be run in a dedicated worktree (created by ring:brainstorming skill).

## The Process

**Step 1: Dispatch Write-Plan Agent**

Dispatch via `Task(subagent_type: "ring:write-plan", model: "opus")` with:
- Instructions to create bite-sized tasks (2-5 min each)
- Include exact file paths, complete code, verification steps
- Save to `docs/plans/YYYY-MM-DD-<feature-name>.md`

**Step 2: Validate Plan**

After the plan is saved, validate it:

```bash
python3 default/lib/validate-plan-precedent.py docs/plans/YYYY-MM-DD-<feature>.md
```

**Interpretation:**
- `PASS` → Plan is safe to execute
- `WARNING` → Plan has issues to address
  - Review the warnings in the output
  - Update plan to address the issues
  - Re-run validation until PASS

**Step 3: Ask User About Execution**

Ask via `AskUserQuestion`: "Execute now?" Options:
1. Execute now → `ring:subagent-driven-development`
2. Parallel session → user opens new session with `ring:executing-plans`
3. Save for later → report location and end

## Why Use an Agent?

**Context preservation** (reading many files keeps supervisor clean) | **Model power** (Opus for comprehensive planning) | **Separation of concerns** (supervisor orchestrates, agent plans)

## What the Agent Does

Explore codebase → identify files → break into bite-sized tasks (2-5 min) → write complete code → include exact commands → add review checkpoints → verify Zero-Context Test → save to `docs/plans/YYYY-MM-DD-<feature>.md` → report back

## Requirements for Plans

Every plan: Header (goal, architecture, tech stack) | Verification commands with expected output | Exact file paths (never "somewhere in src") | Complete code (never "add validation here") | Bite-sized steps with verification | Failure recovery | Review checkpoints | Zero-Context Test | **Recommended agents per task**

## Agent Selection

| Task Type | Agent |
|-----------|-------|
| Backend API/services | `backend-engineer-{golang,typescript}` |
| Frontend/BFF | `frontend-bff-engineer-typescript` |
| Infra/CI/CD | `ring:devops-engineer` |
| Testing | `ring:qa-analyst` |
| Reliability | `ring:sre` |
| Fallback | `general-purpose` (built-in, no prefix) |

## Execution Options Reference

| Option | Description |
|--------|-------------|
| **Execute now** | Fresh subagent per task, code review between tasks → `ring:subagent-driven-development` |
| **Parallel session** | User opens new session, batch execution with human review → `ring:executing-plans` |
| **Save for later** | Plan at `docs/plans/YYYY-MM-DD-<feature>.md`, manual review before execution |

## Required Patterns

This skill uses these universal patterns:
- **State Tracking:** See `skills/shared-patterns/state-tracking.md`
- **Failure Recovery:** See `skills/shared-patterns/failure-recovery.md`
- **Exit Criteria:** See `skills/shared-patterns/exit-criteria.md`
- **TodoWrite:** See `skills/shared-patterns/todowrite-integration.md`

Apply ALL patterns when using this skill.

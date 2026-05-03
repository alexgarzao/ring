---
name: ring:execute-plan
description: |
  Controlled plan execution with human review checkpoints - loads plan, executes
  in batches, pauses for feedback. Supports one-go (autonomous) or batch modes.

trigger: |
  - Have a plan file ready to execute
  - Want human review between task batches
  - Need structured checkpoints during implementation

skip_when: |
  - Same session with independent tasks → use ring:subagent-driven-development
  - No plan exists → use ring:write-plan first

sequence:
  after: [ring:write-plan, ring:pre-dev-task-breakdown]
---

# Executing Plans

Load plan, review critically, choose execution mode, execute tasks with code review.

**Announce at start:** "Using ring:execute-plan skill to implement this plan."

## Process

### Step 1: Load and Review Plan

Read plan file. Raise concerns before starting. If no concerns: create TodoWrite and proceed.

### Step 2: Choose Execution Mode (MANDATORY — AskUserQuestion)

**This step is non-negotiable.** Use AskUserQuestion:

Options:
1. **One-go (autonomous)** — all batches with code review, report only at completion
2. **Batch (with review)** — pause for human feedback after each batch

"User intent is clear" / "user said just execute" do NOT skip this step. AskUserQuestion selects the mode (one-go or batch) — once selected, one-go proceeds autonomously without further checkpoints until completion.

### Step 2.5: Context Switching (Multi-Module Plans)

If plan has tasks with `target:` and `working_directory:` fields: before each module switch, ask user to confirm. Load module-specific `PROJECT_RULES.md` if present. Pass `working_directory` to agent.

**Optimization:** Batch tasks by module when no inter-module dependencies.

### Step 3: Execute Batch (default: first 3 tasks)

Agent selection: Go → `ring:backend-engineer-golang` | TS → `ring:backend-engineer-typescript` | Frontend → `ring:frontend-engineer` or `ring:frontend-bff-engineer-typescript` | Infra → `ring:devops-engineer` | Testing → `ring:qa-analyst` | SRE → `ring:sre`

Per task: check context switch → mark in_progress → dispatch to agent with working_directory → run verifications → mark completed.

### Step 4: Run Code Review (REQUIRED after each batch)

Use ring:codereview — all 10 reviewers in parallel.

Handle by severity:
- **Critical/High/Medium:** Fix immediately (no TODO) → re-run all 10 reviewers → repeat until resolved
- **Low:** `TODO(review): [Issue] ([reviewer], [date], Low)`
- **Cosmetic:** `FIXME(nitpick): [Issue] ([reviewer], [date], Cosmetic)`

Proceed only when: zero Critical/High/Medium remain + all Low/Cosmetic have comments.

### Step 5: Report and Continue

**One-go:** log internally → next batch → report at completion.  
**Batch:** show results → "Ready for feedback." → wait → apply changes → proceed.

### Step 6: Complete Development

Use ring:finishing-a-development-branch: verify tests, present options, execute choice.

## Stop Conditions

Stop immediately and ask (never guess): blocker mid-batch, critical gaps, unclear instruction, verification fails repeatedly.

## Quick Reference

- AskUserQuestion for execution mode: MANDATORY, no exceptions
- Use specialist agents over `ring:general-purpose` when available
- Code review: all 10 reviewers in parallel after each batch
- Severity handling: see Step 4 above

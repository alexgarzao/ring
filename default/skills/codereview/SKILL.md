---
name: ring:codereview
description: |
  Gate 8 of development cycle - dispatches 13 specialized reviewers (code, business-logic,
  security, test, nil-safety, consequences, dead-code, performance, multi-tenant, lib-commons,
  lib-observability, lib-systemplane, lib-streaming) in parallel and reports all findings by severity.
  Runs at TASK cadence — reviewers see cumulative diff, not per-subtask fragments. Report-only: no automatic remediation.
---

# Code Review (Gate 8)

## When to use
- Gate 8 of development cycle
- After completing major feature implementation
- Before merge to main branch
- After completing complex bug work

## Skip when
- Task is purely conversational or informational with no code changes
- Changes are limited to documentation or comments with zero logic modifications
- Code has not been modified since the last completed review cycle

## Sequence
**Runs after:** ring:dev-implementation
**Runs before:** ring:dev-validation

## Related
**Complementary:** ring:dev-cycle, ring:dev-implementation

Dispatch all 13 reviewer subagents in **parallel** for fast, comprehensive feedback.

**Announce at start:** "Using ring:codereview to dispatch 13 reviewers in parallel."

**Report-only boundary:** This skill does not remediate findings, dispatch implementation work, write comments into source files, generate external artifacts, invoke secondary review tools, or re-run reviewers automatically. It only dispatches the 13 reviewers once and reports their findings in the current session.

## Reviewers

| # | Agent | Focus |
|---|-------|-------|
| 1 | `ring:code-reviewer` | Architecture, design patterns, code quality |
| 2 | `ring:business-logic-reviewer` | Domain correctness, business rules, edge cases |
| 3 | `ring:security-reviewer` | Vulnerabilities, authentication, OWASP risks |
| 4 | `ring:test-reviewer` | Test quality, coverage, edge cases, anti-patterns |
| 5 | `ring:nil-safety-reviewer` | Nil/null pointer safety for Go and TypeScript |
| 6 | `ring:consequences-reviewer` | Ripple effects, caller chain impact, downstream consequences |
| 7 | `ring:dead-code-reviewer` | Orphaned code detection, reachability analysis |
| 8 | `ring:performance-reviewer` | Performance hotspots, allocations, goroutine leaks, N+1 |
| 9 | `ring:multi-tenant-reviewer` | Multi-tenant patterns, tenantId propagation, DB isolation |
| 10 | `ring:lib-commons-reviewer` | lib-commons non-observability package usage and reinvented-wheel opportunities |
| 11 | `ring:lib-observability-reviewer` | lib-observability adoption: tracing, metrics, log, zap, runtime, assert, redaction, constants |
| 12 | `ring:lib-systemplane-reviewer` | lib-systemplane adoption: hot-reloadable config, tenant-scoped knobs, admin authorizer, v4 residue |
| 13 | `ring:lib-streaming-reviewer` | lib-streaming adoption: event publishers, outbox writer, CloudEvents, manifest |

**Core principle:** All 13 reviewers run simultaneously in a single turn with 13 Task calls.

## Role Clarification

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Dispatch reviewers once, aggregate findings, report all severities in-session |
| **Reviewer Agents** | Analyze code, report issues with severity |

## Step 1: Gather Context (Auto-Detect if Not Provided)

Auto-detect: `unit_id` (generate if missing), `base_sha` (git merge-base HEAD main), `head_sha` (git rev-parse HEAD), `implementation_files` (git diff --name-only), `implementation_summary` (git log --oneline).

Display context banner before dispatching.

## Step 2: Initialize Review State

Track: unit_id, base/head SHA, reviewer verdicts for all 13 reviewers, and aggregated issues by severity: Critical, High, Medium, Low.

## Step 3: Dispatch All 13 Reviewers in Parallel

### ⛔ STOP-CHECK BEFORE DISPATCH

Before emitting any Task call, count the reviewers you intend to launch in this turn.
- Count MUST equal 13.
- If count < 13 → STOP. Do not partial-dispatch. Reconcile against the 13 reviewers listed in the Reviewers table above and try again.
- The 13 reviewers are the canonical pool. No substitutions, no omissions.

### ⛔ MUST NOT trickle-dispatch

All 13 reviewers leave in the SAME TURN, before reading any reviewer output.

Forbidden sequences:
- Dispatch reviewer 1 → read result → dispatch reviewer 2
- Dispatch a subset → wait → dispatch the rest
- Dispatch follow-up reviewers conditioned on partial output
- Loop sequentially over the reviewer list

If you find yourself about to dispatch a reviewer in a turn AFTER any reviewer has already returned a result → STOP. You violated parallel dispatch. Report the violation to the user and mark the gate INCOMPLETE rather than completing the trickle.

### Self-verify after dispatch

After the dispatch turn, verify all 13 Task calls were emitted in that single turn. If fewer than 13 went out, the gate did NOT execute correctly. Mark the run INCOMPLETE and surface the dispatch failure — do NOT silently continue with a partial pool.

### Parallel dispatch — atomic batch

Emit all 13 Task calls in a SINGLE TURN, as one atomic batch.

**If your runtime exposes a `multi_tool_use.parallel` wrapper**, use it to dispatch the complete pool in one wrapped invocation. This is the canonical fan-out mechanism on OpenAI-style tool envelopes and on certain Anthropic SDK consumers — naming it explicitly activates parallel emission on runtimes where trickle-dispatch is the default behavior.

**If your runtime emits parallel tool_use blocks natively** (Claude Code with Claude models), `multi_tool_use.parallel` may not be needed — but naming it is harmless and serves as an enforcement anchor.

The STOP-CHECK, anti-trickle, and self-verify guards above remain binding regardless of which mechanism your runtime uses.

**⛔ ALL 13 dispatched in a SINGLE turn with 13 Task calls.**

Read `reviewers/dispatch-prompts.md` for the full prompt templates for each reviewer. Inject:
- Task-level scope header (when `scope=task`)
- `base_sha` / `head_sha` from cumulative_diff_range when task-level
- Ring standards slice (cache-first per `shared-patterns/standards-cache-protocol.md`)
- Explicit instruction that reviewers must report findings only and must not modify files

## Step 4: Wait and Parse Output

Parse `VERDICT` and Issues for all 13 reviewers. Normalize every issue into one of four severity buckets: Critical, High, Medium, Low.

For each issue, preserve:
- Severity
- Title or short description
- File:line when provided
- Reviewer
- Evidence or reasoning
- Recommendation

If a reviewer returns `COSMETIC`, map it to Low.

## Step 5: Report Results In Session

Produce a detailed Markdown report in the current session. The report must include all Critical, High, Medium, and Low issues.

**⛔ Do not dispatch any follow-up agent to remediate findings. Do not edit files. Do not create reports on disk. Do not open a browser. Report back only.**

## Completion Rules

- Complete after all 13 reviewer outputs are collected and summarized.
- `PASS` means all 13 reviewers completed and reported zero issues.
- `ISSUES_FOUND` means at least one Critical, High, Medium, or Low issue was reported.
- `INCOMPLETE` means one or more reviewers did not return a parseable result.
- Low issues are still reported; never omit them from the session report.
- No automatic remediation, source-file changes, reviewer reruns, external artifacts, or secondary validation tools are part of this skill.

## Red Flags — STOP

- You are about to dispatch any non-reviewer agent.
- You are about to edit source files.
- You are about to create or open a separate report artifact.
- You are about to invoke a secondary review or validation tool.
- You are about to re-run reviewers without an explicit new user request.

All of these mean: stop and produce the session report instead.

## Output Format

```markdown
## Review Summary
**Status:** [PASS|ISSUES_FOUND|INCOMPLETE]
**Unit ID:** [unit_id]
**Base:** [base_sha]
**Head:** [head_sha]
**Scope:** [task|branch|provided]

## Issues by Severity
| Severity | Count |
|----------|-------|
| Critical | N |
| High     | N |
| Medium   | N |
| Low      | N |

## Critical Issues

[List every Critical issue. If none: None.]

| Issue | File:Line | Reviewer | Evidence | Recommendation |
|-------|-----------|----------|----------|----------------|
| [actual issue description] | [file:line] | [ring:xxx-reviewer] | [why it matters] | [recommended action] |

## High Issues

[List every High issue. If none: None.]

| Issue | File:Line | Reviewer | Evidence | Recommendation |
|-------|-----------|----------|----------|----------------|
| [actual issue description] | [file:line] | [ring:xxx-reviewer] | [why it matters] | [recommended action] |

## Medium Issues

[List every Medium issue. If none: None.]

| Issue | File:Line | Reviewer | Evidence | Recommendation |
|-------|-----------|----------|----------|----------------|
| [actual issue description] | [file:line] | [ring:xxx-reviewer] | [why it matters] | [recommended action] |

## Low Issues

[List every Low issue. If none: None.]

| Issue | File:Line | Reviewer | Evidence | Recommendation |
|-------|-----------|----------|----------|----------------|
| [actual issue description] | [file:line] | [ring:xxx-reviewer] | [why it matters] | [recommended action] |

## Reviewer Verdicts
| Reviewer | Verdict | Issues |
|----------|---------|--------|
| ring:code-reviewer | PASS/FAIL/INCOMPLETE | N |
[...13 rows]

## Report Boundary
No files were changed. No remediation agents were dispatched. No external report artifacts were generated.

_If all reviewers passed with zero issues: "No issues found across all 13 reviewers."_
```

---
name: ring:codereview
description: |
  Gate 4 of development cycle - dispatches 10 specialized reviewers (code, business-logic,
  security, test, nil-safety, consequences, dead-code, performance, multi-tenant, lib-commons) in parallel for comprehensive code review feedback.
  Runs at TASK cadence — reviewers see cumulative diff, not per-subtask fragments.

trigger: |
  - Gate 4 of development cycle
  - After completing major feature implementation
  - Before merge to main branch
  - After fixing complex bug

skip_when: |
  - Task is purely conversational or informational with no code changes
  - Changes are limited to documentation or comments with zero logic modifications
  - Code has not been modified since the last completed review cycle

sequence:
  after: [ring:dev-testing]
  before: [ring:dev-validation]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:dev-testing]
---

# Code Review (Gate 4)

Dispatch all 10 reviewer subagents in **parallel** for fast, comprehensive feedback.

**Announce at start:** "Using ring:codereview to dispatch 10 reviewers in parallel."

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
| 10 | `ring:lib-commons-reviewer` | lib-commons package usage and reinvented-wheel opportunities |

**Core principle:** All 10 reviewers run simultaneously in a single message with 10 Task calls.

## Role Clarification

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Dispatch reviewers, aggregate findings, track iterations |
| **Reviewer Agents** | Analyze code, report issues with severity |
| **Implementation Agent** | Fix issues found by reviewers |

## Step 1: Gather Context (Auto-Detect if Not Provided)

Auto-detect: `unit_id` (generate if missing), `base_sha` (git merge-base HEAD main), `head_sha` (git rev-parse HEAD), `implementation_files` (git diff --name-only), `implementation_summary` (git log --oneline).

Display context banner before dispatching.

## Step 2: Initialize Review State

Track: unit_id, base/head SHA, reviewer verdicts (10 reviewers), aggregated issues by severity, iterations (max 3).

## Step 2.5: Pre-Analysis Pipeline (MANDATORY)

Install and run `mithril --base=$BASE_SHA --head=$HEAD_SHA --output=docs/codereview`. On failure, continue in DEGRADED MODE.

Read context files from `docs/codereview/context-{reviewer-name}.md` for each of the 10 reviewers. Pass context to reviewers at dispatch time.

## Step 2.7: Review Slicing

See `../shared-patterns/reviewer-slicing-strategy.md` for full rationale.

1. Collect FILE_LIST, DIFF_STATS, PACKAGE_MAP, IMPORT_HINTS, CHANGE_SUMMARY
2. Dispatch `ring:review-slicer` agent with collected inputs
3. Parse response: `shouldSlice` bool, `slices[]`, `reasoning`
4. If `shouldSlice=true`: run all 10 reviewers per slice, then merge+dedup results

**Sliced merge rules:** Exact match dedup by (reviewer+file+line). Fuzzy dedup at >80% similarity (keep more detailed, note cross-detection). Co-located but orthogonal findings = NOT duplicates. Cross-cutting concerns (found in 2+ slices) = surface prominently.

## Step 3: Dispatch All 10 Reviewers in Parallel

**⛔ ALL 10 dispatched in a SINGLE message with 10 Task calls.**

Read `reviewers/dispatch-prompts.md` for the full prompt templates for each reviewer. Inject:
- Task-level scope header (when `scope=task`)
- `base_sha` / `head_sha` from cumulative_diff_range when task-level
- Pre-analysis context per reviewer
- Ring standards slice (cache-first per `shared-patterns/standards-cache-protocol.md`)

## Step 4: Wait and Parse Output

Parse VERDICT and Issues for all 10 reviewers. Aggregate by severity. If sliced, merge results from Step 3-S-Merge.

## Step 5: Handle Results

```
blocking = critical + high + medium
IF blocking == 0 → Step 8 (Success)
IF blocking > 0  → iterations++; IF iterations >= 3 → Step 9 (Escalate); ELSE Step 6 (Fix)
```

## Step 6: Dispatch Fixes

**⛔ NEVER edit source files directly. ALWAYS dispatch implementation agent.**

Send ALL Critical, High, Medium issues to implementation agent in one Task call. Include file:line and recommendations. After fixes committed → Step 7.

## Step 7: Re-Run All Reviewers After Fixes

**⛔ Always re-run ALL 10. Never cherry-pick reviewers.**

## Step 7.5: CodeRabbit CLI Validation

- Installed + authenticated → **MANDATORY**, no prompt, cannot skip
- Not installed → MUST ask user (install or skip — both valid choices)
- On issues found: CRITICAL/HIGH → dispatch fix + re-run Ring reviewers; MEDIUM/LOW → add TODO(coderabbit) comments

## Step 8: Visual Report + Success Output

Generate HTML report via `Skill("ring:visualize")`. Save to `docs/codereview/review-report-{unit_id}.html`. Open in browser.

Output: Review Summary (PASS), Issues by Severity count table, **Aggregate Issues section with full per-issue details** (severity, description, file:line, reviewer, recommendation), Reviewer Verdicts table (10 rows), CodeRabbit status, Handoff to Gate 5.

**⛔ The Aggregate Issues section MUST be populated with actual findings from reviewer output — not just counts. Collect all issues from `review_state.aggregated_issues` and emit one row per issue. If all reviewers passed with zero issues, emit: "No issues found across all 10 reviewers."**

## Step 9: Escalate — Max Iterations Reached

Generate FAIL visual report. Output: unresolved issues (list ALL Critical/High/Medium with file:line, reviewer, and recommendation), reviewer verdicts, `Ready for Gate 5: NO`, action required from user.

## Completion Rules

- Gate 4 complete ONLY when ALL 10 reviewers PASS
- 9/10 = FAIL → re-run all 10
- Critical/High/Medium MUST be fixed before proceeding
- Low/Cosmetic → add `// TODO(review):` / `// FIXME(nitpick):` comments
- CodeRabbit: MUST run if installed; MUST ask if not

## Output Format

```markdown
## Review Summary
**Status:** [PASS|FAIL|NEEDS_FIXES]
**Unit ID:** [unit_id]
**Iterations:** [N]

## Issues by Severity
| Severity | Count |
|----------|-------|
| Critical | N |
| High     | N |
| Medium   | N |
| Low      | N |

## Aggregate Issues

**⛔ MANDATORY: List every issue found across ALL reviewers with actual content. Never emit this section as empty or counts-only when issues exist.**

| Severity | Description | File:Line | Reviewer | Recommendation |
|----------|-------------|-----------|----------|----------------|
| [CRITICAL/HIGH/MEDIUM/LOW] | [actual issue description] | [file:line] | [ring:xxx-reviewer] | [fix] |

_If all reviewers PASSed with zero issues: "No issues found across all 10 reviewers."_

## Reviewer Verdicts
| Reviewer | Verdict | Issues |
|----------|---------|--------|
| ring:code-reviewer | ✅/❌ | N |
[...10 rows]

## CodeRabbit External Review
**Status:** [PASS|ISSUES_FOUND|SKIPPED|NOT_INSTALLED]
**Units Validated:** N | **Issues Found:** N | **Issues Resolved:** N/N

## Handoff to Next Gate
- Review status: [COMPLETE|FAILED]
- Blocking issues: [resolved|N remaining]
- Ready for Gate 5: [YES|NO]
```

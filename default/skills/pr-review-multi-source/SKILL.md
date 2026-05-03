---
name: ring:pr-review-multi-source
description: |
  PR-aware code review orchestrator that fetches PR metadata AND existing review
  comments from ALL sources (CodeRabbit, human reviewers, CI), dispatches Ring's
  10 specialized reviewer agents to evaluate BOTH code AND existing comments, and
  presents consolidated findings with source attribution. Batch applies approved
  fixes at the end and responds to PR comment threads with resolution status.

  Adapted from alexgarzao/optimus (optimus-pr-review).

trigger: |
  - When user provides a PR URL for review
  - When user asks to review a pull request with multi-source comment analysis
  - When user wants to evaluate existing CodeRabbit or human review comments alongside fresh agent review

skip_when: |
  - No PR URL provided and user wants a generic code review (use ring:codereview)
  - PR is already merged or closed
  - User wants a code review without PR context
---

# PR Review Multi-Source

PR-aware code review orchestrator. Fetches PR metadata, collects existing review comments from all sources (CodeRabbit, human reviewers, CI), dispatches Ring's 10 reviewer agents to evaluate both code and existing comments, and presents findings with source attribution.

> Adapted from [alexgarzao/optimus](https://github.com/alexgarzao/optimus).

## Phase 0: Fetch PR Context

### Step 0.1: Obtain PR URL
If no URL provided, try `gh pr view --json url`. If no PR found, ask user for URL.

### Step 0.2: Fetch PR Metadata
```bash
gh pr view <PR_NUMBER_OR_URL> --json title,body,state,headRefName,baseRefName,changedFiles,additions,deletions,labels,milestone,assignees,reviewRequests,comments,url,number
```
Guard: if state is `MERGED` or `CLOSED` → STOP. Store: title, description, head/base branches, changed files, labels, linked issues.

### Step 0.3: Collect Existing PR Comments
```bash
gh pr view <PR_NUMBER_OR_URL> --comments
gh api --paginate repos/{owner}/{repo}/pulls/{number}/reviews
gh api --paginate repos/{owner}/{repo}/pulls/{number}/comments
```
For each comment: source (CodeRabbit/human/CI), type, file:line, content, status, `comment_id`, `node_id`. Parse "Duplicated Comments" sections — treat as regular review comments. Group by source.

### Step 0.4: Checkout PR Branch
```bash
gh pr checkout <PR_NUMBER_OR_URL>
```

### Step 0.5: Fetch Changed Files
```bash
gh pr diff <PR_NUMBER_OR_URL> --name-only
```

---

## Phase 1: Present PR Summary

```markdown
## PR Review: #<number> — <title>
**Branch:** <head> → <base> | **Changed files:** X (+Y, -Z)
### PR Description | ### Existing Review Comments | ### Changed Files
```

---

## Phase 2: Determine Review Type

Ask user:
- **Initial** (5 agents) — correctness and critical gaps: code, business-logic, security, test, nil-safety
- **Final** (10 agents) — full coverage: adds consequences, dead-code, performance, multi-tenant, lib-commons

---

## Phase 3: Parallel Agent Dispatch

### Step 3.1: Discover Project Context
Detect stack, lint commands, unit/integration/E2E test commands, coding standards (PROJECT_RULES.md), reference docs. Store as LINT_CMD, TEST_UNIT_CMD, etc.

### Step 3.2: Dispatch Agents (Single Message, Parallel)

Each agent receives: all changed file contents, PR context (description, linked issues), ALL existing PR comments, coding standards.

**Agent prompt includes:**
```
PR Context: PR #N, purpose, linked issues, base branch.
Existing PR Comments (evaluate each — validate or contest):
  [all comments grouped by source, including from "Duplicated Comments" sections]
Review scope: Only files changed in this PR.
Your job:
  1. Review CODE for issues in your domain
  2. For each existing comment in your domain: AGREE / CONTEST / ALREADY FIXED + justification
  3. Report NEW findings not covered by existing comments
Output: Follow the shared reviewer output contract defined in
  shared-patterns/reviewer-output-schema-core.md.
  Additional required section: ## Comment Evaluation
    For each existing PR comment in your domain:
    - AGREE: valid concern, describe why
    - CONTEST: invalid/outdated, explain reasoning
    - ALREADY FIXED: identify the commit/change that resolved it
```

| Review Type | Agents |
|-------------|--------|
| Initial (5) | ring:code-reviewer, ring:business-logic-reviewer, ring:security-reviewer, ring:test-reviewer, ring:nil-safety-reviewer |
| Final (10) | + ring:consequences-reviewer, ring:dead-code-reviewer, ring:performance-reviewer, ring:multi-tenant-reviewer, ring:lib-commons-reviewer |

---

## Phase 4: Consolidation

Merge all findings. Deduplicate (keep one, note agreeing agents). Cross-reference comment evaluations. Sort: CRITICAL > HIGH > MEDIUM > LOW. Assign IDs: F1, F2, F3...

**Source Attribution:**
| Source | Label |
|--------|-------|
| New agent finding | `[Agent: <name>]` |
| Existing CodeRabbit + validated | `[CodeRabbit + Agent: <name>]` |
| Existing human + validated | `[Reviewer: <username> + Agent: <name>]` |
| Contested | `[Contested: <source> vs Agent: <name>]` |

---

## Phase 5: Present Overview

```markdown
## PR Review: #<number> — X findings
### New Findings | ### Validated Existing Comments | ### Contested Comments | ### Summary
```

---

## Phase 6: Interactive Resolution (Collect Decisions Only)

Process ONE finding at a time, severity order. For each: finding header, problem description (with code snippet), proposed solutions with tradeoffs, recommendation, user decision.

**BLOCKING:** Wait for user decision before advancing.

User options: approve option, request more context, discard, defer. Record all decisions. **Do NOT apply any fix yet.**

---

## Phase 7: Batch Apply All Approved Fixes

### Step 7.1: Pre-Apply Summary
Show table of all fixes to apply (finding, source, decision, files) + skipped + deferred list. Wait for confirmation.

### Step 7.2: Apply All Fixes
Group by file. Apply all changes. Run lint (fix format issues). Run unit tests (max 3 attempts per failure; if still failing, revert that fix and ask user).

### Step 7.3: Verification Gate
Run discovered project commands. Required: lint + unit tests always. Backend changes: + integration tests. Frontend changes: + E2E tests. All MUST pass.

---

## Phase 8: Final Summary

```markdown
## PR Review Summary: #<number>
### Sources Analyzed | ### Fixed | ### Skipped | ### Deferred | ### Verification | ### PR Readiness
**Verdict:** READY FOR MERGE / NEEDS CHANGES
```
Do NOT commit automatically. Ask user before committing.

---

## Phase 9: Respond to PR Comments

After user commits, reply to every evaluated PR comment thread.

### Step 9.1: Determine Responses
| Decision | Response |
|----------|----------|
| Fixed | Reply with commit SHA |
| Skipped | Reply with reason |
| Deferred | Reply with destination |
| Contested | Reply with agent's reasoning |
| Already fixed | Reply noting prior fix |

### Step 9.2: Post Replies + Resolve Threads
Inline review comments:
```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --method POST -f body="<reply>" -F in_reply_to=<comment_id>
```
Resolve threads via GraphQL:
```bash
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "<thread_node_id>"}) { thread { isResolved } } }'
```
Get thread node IDs by paginating `reviewThreads` (first: 100, loop until `hasNextPage=false`). Match REST `node_id` to GraphQL `comments.nodes[*].id`.

### Step 9.3: Reply Summary
Table: thread file:line, source, reply text, resolved status.

---

## Rules

- MUST fetch PR metadata AND existing comments before starting
- Agents MUST evaluate existing comments (validate/contest/already-fixed)
- Every finding MUST include source attribution
- Only review files changed in the PR
- One finding at a time, severity order
- No changes without user approval — fixes collected in Phase 6, applied in Phase 7
- Never merge the PR; never commit without explicit approval
- After commit, reply to every existing PR comment thread

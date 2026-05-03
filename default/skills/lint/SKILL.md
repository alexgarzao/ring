---
name: ring:lint
description: |
  Parallel lint fixing pattern - runs lint checks, groups issues into independent
  streams, and dispatches AI agents to fix all issues until the codebase is clean.

trigger: |
  - User runs /ring:lint command
  - Codebase has lint issues that need fixing
  - Multiple lint errors across different files/components

skip_when: |
  - Single lint error → fix directly without agent dispatch
  - Lint already passes → nothing to do
  - User only wants to see lint output, not fix
---

# Linting Codebase

Run lint checks, group issues into independent streams, dispatch parallel agents, iterate until clean.

## ⛔ Critical Constraints (communicate to ALL dispatched agents)

- DO NOT create automated scripts to fix lint issues
- DO NOT create documentation or README files
- DO NOT add comments explaining the fixes
- Fix each issue directly by editing source code
- Minimal changes — only what's needed for lint

## Phase 1: Run Lint

**Detect command:** `make lint` → `npm run lint` → `yarn lint` → `pnpm lint` → `golangci-lint run` → `cargo clippy` → `ruff check .` → `eslint .`

```bash
<lint_command> 2>&1 | tee /tmp/lint-output.txt; echo "EXIT_CODE: ${PIPESTATUS[0]}"
```

If `EXIT_CODE` is non-zero, lint failed. Report failure clearly before proceeding to grouping.

Parse: file path, line:column, error code/rule, message, severity.

## Phase 2: Group into Streams

| Issue Count | Grouping Strategy |
|-------------|-------------------|
| < 10 | By file |
| 10-50 | By directory |
| 50-100 | By error type/rule |
| > 100 | By component/module |

A stream is independent if: files don't import each other, fixes won't conflict, agents can work without knowledge of other streams.

## Phase 3: Parallel Agent Dispatch

**Single message with multiple Task calls** — one `ring:general-purpose` agent per stream.

Each agent receives: scope (files/dirs), issues (file:line:col + message), constraints (from above).

Dispatch when: 3+ files have issues, issues are in independent areas, fixes are mechanical.

Skip dispatch when: single file → fix directly, issues require architectural decisions, fixes would break things.

## Phase 4: Verification Loop (max 5 iterations)

Re-run lint after all agents complete:

| Result | Action |
|--------|--------|
| Lint passes | ✅ Done |
| Same issues remain | ⚠️ Investigate why fixes failed |
| New issues appeared | 🔄 Analyze + dispatch new agents |
| Fewer issues remain | 🔄 New streams, repeat |

After 5 iterations: report remaining issues and ask user.

## Output

**Success:** Initial issues, streams processed, agents dispatched, iterations, all pass, changes by stream.

**Partial:** Remaining issues with reasons (e.g., requires external types, intentional usage), recommended actions.

## Agent Selection

| Issue Type | Agent |
|------------|-------|
| TypeScript/JavaScript | `ring:general-purpose` |
| Go | `ring:backend-engineer-golang` |
| Security lints | `ring:security-reviewer` for report/analysis only — security findings are **not auto-fixed**; escalate to human review |
| Style/formatting | `ring:general-purpose` |

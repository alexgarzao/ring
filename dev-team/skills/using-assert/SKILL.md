---
name: ring:using-assert
description: |
  Dual-mode skill for github.com/LerianStudio/lib-commons/v5/commons/assert — Lerian's
  production-grade runtime assertion package.

  Sweep Mode (primary): Dispatches 6 parallel explorer subagents to sweep any Lerian Go
  codebase for DIY invariant checks, zero-panic policy violations, hand-rolled domain
  predicates, missing metric initialization, and unstructured error-boundary logging.
  Generates tasks compatible with ring:dev-cycle for batched fixes.

  Reference Mode: Full API surface of commons/assert — asserter lifecycle, instance method
  semantics, complete domain predicate catalog (numeric, financial, transaction state
  machine, network, time), observability trident, AssertionError unwrapping, decision tree
  for panic-vs-assert-vs-error, testing patterns.

trigger: |
  Sweep mode:
  - "Sweep the codebase for commons/assert opportunities"
  - "Audit this service for zero-panic policy compliance"
  - "Find panic()/log.Fatal violations"
  - "Replace DIY invariant checks with commons/assert"

  Reference mode:
  - "What's the signature for assert.DebitsEqualCredits?"
  - "How do I initialize assertion metrics?"
  - "Should I panic, assert, or return an error here?"
  - "How do I unwrap AssertionError in a Fiber error handler?"

skip_when: |
  - Working on non-Go services
  - Working on frontend code
  - Target codebase is Ring itself

related:
  similar: [ring:using-lib-commons, ring:using-runtime]
---

# ring:using-assert

## Mode Selection

| Request Shape | Mode |
|---|---|
| "Sweep / audit for assert opportunities" | **Sweep** |
| "Find panic()/log.Fatal() violations" | **Sweep** |
| "What's the signature for X?" | **Reference** |
| "Should I panic, assert, or return error?" | **Reference** |

---

# SWEEP MODE

4-phase sweep. Each phase has a hard gate — do not proceed until the current phase produces its artifact.

```
Phase 1: Version Reconnaissance   → assert-version-report.json
Phase 2: CHANGELOG Delta Analysis → assert-delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 6 × assert-sweep-{N}-{angle}.json
Phase 4: Consolidated Report      → assert-sweep-report.md + assert-sweep-tasks.json
```

## Phase 1: Version Reconnaissance

1. Read `go.mod` — extract pinned version of `github.com/LerianStudio/lib-commons/vN`
2. WebFetch `https://api.github.com/repos/LerianStudio/lib-commons/releases/latest` — extract `tag_name`
3. Classify drift: up-to-date / minor-drift / moderate-drift / major-upgrade / module-mismatch
4. Emit `/tmp/assert-version-report.json`: `{pinned_version, latest_version, drift_classification, major_upgrade_required, module_path}`

## Phase 2: CHANGELOG Delta Analysis

1. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-commons/main/CHANGELOG.md`
2. Filter entries between pinned_version and latest_version that affect `commons/assert`
3. Classify: `new-predicate` / `new-method` / `breaking-change` / `security-fix` / `bugfix`
4. Emit `/tmp/assert-delta-report.json`

## Phase 3: Multi-Angle DIY Sweep

Dispatch all 6 explorer angles in **one parallel batch**. Wait for all before Phase 4.

**Per-explorer dispatch** (`subagent_type: ring:codebase-explorer`):

```
## Target: <absolute path>
## Your Angle: <angle number + name>
## Severity Calibration / DIY Patterns / Replacement / Migration Complexity / Version Context
<verbatim from sub-files/sweep-angles.md for this angle>

## Output
Write to: /tmp/assert-sweep-{N}-{angle-slug}.json
Schema: { angle_number, angle_name, severity, migration_complexity,
  findings: [{file, line, diy_pattern, replacement, evidence_snippet, notes}],
  summary, requires_major_upgrade }
If no findings: write file with empty findings array.
```

Full angle specifications: `sub-files/sweep-angles.md`

The 6 angles cover:
1. `panic()` in non-test code (CRITICAL)
2. Defensive nil/empty checks without metric emission (HIGH)
3. Hand-rolled domain predicates duplicating `assert.*` (HIGH)
4. Missing `InitAssertionMetrics` at startup (HIGH)
5. Financial invariants in tests only, not production (CRITICAL)
6. `AssertionError` not unwrapped in error boundaries (MEDIUM)

## Phase 4: Consolidated Report

Dispatch synthesizer to read all 6 explorer files and emit:
1. `/tmp/assert-sweep-report.md` — aggregate findings by severity
2. `/tmp/assert-sweep-tasks.json` — one task per DIY pattern cluster

Surface report path + task count; offer handoff to `ring:dev-cycle`.

---

# REFERENCE MODE

Full API reference in `sub-files/reference.md`. Load sections relevant to your task.

## Quick Navigation

| # | Section | What you'll find |
|---|---|---|
| 1 | API Surface | Exported symbols, signatures |
| 2 | Asserter Lifecycle | Scoping, naming, anti-patterns |
| 3 | Instance Methods | That / NotNil / NotEmpty / NoError / Never / Halt |
| 4 | Domain Predicate Catalog | Numeric / financial / state-machine / network / time |
| 5 | Composition Pattern | Pure predicates + observable asserter |
| 6 | Observability Trident | Log + span event + metric on every failure |
| 7 | AssertionError Unwrapping | Error boundary patterns |
| 8 | Decision Tree | panic vs assert vs error |
| 9 | Testing Patterns | Proving assertions fire |
| 10 | Anti-Pattern Catalog | Six anti-patterns |
| 11 | Bootstrap Order | InitAssertionMetrics placement |
| 12–14 | Cross-references, Patterns, Breaking Changes | v4→v5 delta |

Read `sub-files/reference.md` for full API detail.

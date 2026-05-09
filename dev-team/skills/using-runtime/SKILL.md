---
name: ring:using-runtime
description: Dual-mode skill for lib-commons/v5/commons/runtime — the panic observability trident that turns silent goroutine deaths into production signal. Sweep Mode dispatches 6 parallel explorers to find naked goroutines, unobservable defer recover(), and missing panic-metric init. Reference Mode catalogs the API (SafeGo, RecoverWithPolicy, InitPanicMetrics) and framework integrations (Fiber, gRPC, RabbitMQ). Skip for non-Go or frontend code.
---

# ring:using-runtime

## When to use
Sweep mode:
- "Sweep / audit panic handling"
- "Find naked goroutines"
- "Migrate this service to commons/runtime"
- "Are our defer recover() calls observable?"

Reference mode:
- "Which SafeGo variant do I use for X?"
- "How does the observability trident fire on panic?"
- "Show me the policy decision tree"
- "How do I wire runtime into Fiber / gRPC / RabbitMQ?"

## Skip when
- Working on non-Go services
- Working on frontend code

## Related
**Similar:** ring:using-lib-commons, ring:using-assert


Extends `ring:using-lib-commons` Angle 15 (Panic handling DIY) into 6 focused sub-angles
with deeper detection patterns, full API reference, policy decision tree, and framework integrations.
Use when panic handling is the primary concern or when Angle 15 surfaced significant findings.

## Mode Selection

| Request Shape | Mode |
|---|---|
| "Sweep / audit panic handling / find naked goroutines" | **Sweep** |
| "Which SafeGo variant do I use?" | **Reference** |
| "Policy decision tree" | **Reference** |
| "Framework integration (Fiber/gRPC/RabbitMQ)" | **Reference** |

---

# SWEEP MODE

4-phase sweep. Each phase has a hard gate.

```
Phase 1: Version Reconnaissance   → runtime-version-report.json
Phase 2: CHANGELOG Delta Analysis → runtime-delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 6 × runtime-sweep-{N}-{angle}.json
Phase 4: Consolidated Report      → runtime-sweep-report.md + runtime-sweep-tasks.json
```

## Phase 1: Version Reconnaissance

1. Read `go.mod` — extract pinned version of `github.com/LerianStudio/lib-commons/vN`
2. WebFetch `https://api.github.com/repos/LerianStudio/lib-commons/releases/latest` — extract `tag_name`
3. Classify drift; emit `/tmp/runtime-version-report.json`

## Phase 2: CHANGELOG Delta Analysis

1. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-commons/main/CHANGELOG.md`
2. Filter entries affecting `commons/runtime`
3. Emit `/tmp/runtime-delta-report.json`

## Phase 3: Multi-Angle DIY Sweep

Dispatch all 6 explorer angles in **one parallel batch**. Wait for all before Phase 4.

**Per-explorer dispatch** (`subagent_type: ring:codebase-explorer`):

```
## Target: <absolute path>
## Your Angle: <angle number + name>
## Severity / DIY Patterns / Replacement / Migration Complexity / Version Context
<verbatim from sub-files/sweep-angles.md for this angle>

## Output
Write to: /tmp/runtime-sweep-{N}-{angle-slug}.json
Schema: { angle_number, angle_name, severity, migration_complexity,
  findings: [{file, line, diy_pattern, replacement, evidence_snippet, notes}],
  summary, requires_major_upgrade }
If no findings: write file with empty findings array.
```

Full angle specifications: `sub-files/sweep-angles.md`

The 6 angles cover:
1. Naked goroutine launches (CRITICAL)
2. Unobservable `defer recover()` (CRITICAL)
3. Missing `InitPanicMetrics` at startup (HIGH)
4. Missing `SetProductionMode(true)` in production (HIGH)
5. Framework panic handlers bypassing `HandlePanicValue` (HIGH)
6. Policy mismatch — KeepRunning vs CrashProcess (MEDIUM)

## Phase 4: Consolidated Report

Dispatch synthesizer to read all 6 files and emit:
1. `/tmp/runtime-sweep-report.md`
2. `/tmp/runtime-sweep-tasks.json`

Surface report path + task count; offer handoff to `ring:dev-cycle`.

---

# REFERENCE MODE

Full API reference in `sub-files/reference.md`. Load sections relevant to your task.

## Quick Navigation

| # | Section | What you'll find |
|---|---|---|
| 1 | API Surface | SafeGo / RecoverWithPolicy / HandlePanicValue / Init / SetProductionMode |
| 2 | Policy Decision Tree | KeepRunning vs CrashProcess |
| 3 | Pattern Catalog | Consumer loops, fan-out, tickers, Fiber/gRPC/RabbitMQ |
| 4 | Observability Trident | Log + span event + metric on panic |
| 5 | Testing Patterns | Proving recovery fires |
| 6 | Anti-Pattern Catalog | Six failure modes |
| 7 | Bootstrap Order | Where runtime setup fits in init |
| 8–10 | Cross-Cutting, Breaking Changes, Cross-References | v4→v5 delta |

Read `sub-files/reference.md` for full API detail.

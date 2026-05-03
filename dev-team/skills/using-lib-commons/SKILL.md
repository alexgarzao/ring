---
name: ring:using-lib-commons
description: |
  Dual-mode skill for github.com/LerianStudio/lib-commons — latest v5.x release. Lerian's shared Go library.

  Sweep Mode (primary): Dispatches 22 parallel explorer subagents to sweep any Lerian Go
  codebase for DIY implementations that should use lib-commons. Detects version drift,
  identifies replacement opportunities with file:line precision, generates tasks compatible
  with ring:dev-cycle for batched fixes.

  Reference Mode: Comprehensive catalog of lib-commons (latest v5.x) packages — database
  connections, messaging, multi-tenancy, observability, security, resilience, HTTP tooling,
  event-driven tenant discovery, webhook delivery, dead-letter queues, idempotency, TLS
  certificate management. Load for API discovery and initialization patterns.

trigger: |
  Sweep mode:
  - "Sweep the codebase for lib-commons opportunities"
  - "Find where we could use lib-commons instead of DIY"
  - "Audit this service for lib-commons compliance"
  - "Identify lib-commons migration opportunities"

  Reference mode:
  - Need to understand what lib-commons provides
  - Looking for the right package/API for a task
  - Setting up a new service that uses lib-commons
  - Need correct constructor/initialization patterns
  - Working with multi-tenancy (tenant-manager subsystem)
  - Working with event-driven tenant discovery

skip_when: |
  - Working on non-Go services
  - Working on frontend code
  - Target codebase is Ring itself (no lib-commons dependency)

related:
  similar: [ring:using-dev-team, ring:dev-refactor, ring:using-runtime, ring:using-assert]
---

# ring:using-lib-commons

## Mode Selection

| Request Shape | Mode |
|---|---|
| "Sweep / audit / find opportunities / migrate to lib-commons" | **Sweep** |
| "What does lib-commons provide for X?" | **Reference** |
| "How do I initialize Y from lib-commons?" | **Reference** |
| "Replace our DIY webhook delivery with lib-commons" | **Sweep** |

---

# SWEEP MODE

Orchestrate a 4-phase sweep. Each phase has a hard gate — do not proceed until the current phase produces its artifact.

```
Phase 1: Version Reconnaissance   → version-report.json
Phase 2: CHANGELOG Delta Analysis → delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 22 × libcommons-sweep-{N}-{angle}.json
Phase 4: Consolidated Report      → libcommons-sweep-report.md + tasks.json
```

## Phase 1: Version Reconnaissance

1. Read `go.mod` — extract pinned version of `github.com/LerianStudio/lib-commons/vN`
2. WebFetch `https://api.github.com/repos/LerianStudio/lib-commons/releases/latest` — extract `tag_name`
3. Classify drift: up-to-date / minor-drift / moderate-drift / major-upgrade / module-mismatch
4. If v4.x detected: add major upgrade advisory flag
5. Emit `version-report.json`: `{pinned_version, latest_version, drift_classification, major_upgrade_required, module_path}`

## Phase 2: CHANGELOG Delta Analysis

1. WebFetch `https://raw.githubusercontent.com/LerianStudio/lib-commons/main/CHANGELOG.md`
2. Extract entries between pinned_version (exclusive) and latest_version (inclusive)
3. Classify each: `new-package` / `new-api` / `breaking-change` / `security-fix` / `performance` / `bugfix`
4. Emit `delta-report.json` with classified entries

## Phase 3: Multi-Angle DIY Sweep

Dispatch all 22 explorer angles in **3 batches** (8+8+6). Wait for each batch before next.

| Batch | Angles | Focus |
|---|---|---|
| 1 | 1–8 | Infrastructure + HTTP |
| 2 | 9–16 | Ergonomics + security + observability |
| 3 | 17–22 | Resilience + multi-tenant + utilities |

**Per-explorer dispatch** (`subagent_type: ring:codebase-explorer`):

```
## Target
<absolute path to target repo root>

## Your Angle
<angle number + name>

## Severity Calibration / DIY Patterns / Replacement / Migration Complexity / Version Context
<verbatim from sub-files/sweep-angles.md for this angle>

## Output
Write findings to: /tmp/libcommons-sweep-{N}-{angle-slug}.json
Schema: { angle_number, angle_name, severity, migration_complexity, findings: [{file, line, diy_pattern, replacement, evidence_snippet, notes}], summary, requires_major_upgrade }
If no findings: write file with empty findings array and summary "No DIY patterns detected for this angle".
```

Full angle specifications: `sub-files/sweep-angles.md`

## Phase 4: Consolidated Report

Dispatch synthesizer (`subagent_type: ring:codebase-explorer`):

```
Read /tmp/version-report.json, /tmp/delta-report.json, /tmp/libcommons-sweep-*.json (22 files).
Emit:
1. /tmp/libcommons-sweep-report.md — aggregate findings by severity
2. /tmp/libcommons-sweep-tasks.json — one task per DIY pattern cluster (same file/package = one task)

MUST NOT invent findings. MUST NOT omit explorer findings. MUST NOT reclassify severity without justification.
```

Surface report path + task count to user; offer handoff to `ring:dev-cycle`.

---

# REFERENCE MODE

Full API catalog in `sub-files/reference.md`. Load the relevant sections for your current task.

## Quick Navigation

| # | Section | What you'll find |
|---|---|---|
| 1 | Package Catalog | All packages by domain |
| 2 | Common Initialization Pattern | Typical service bootstrap |
| 3 | Database Connections | postgres, mongo, redis, rabbitmq |
| 4 | HTTP Toolkit | Middleware, rate limiting, pagination, idempotency |
| 5 | Observability | Logger, tracing, metrics, runtime, assert |
| 6 | Resilience & Utilities | Circuit breaker, backoff, safe math |
| 7 | Security | JWT, encryption, sensitive fields, TLS |
| 8 | Transaction Domain | Intent planning, balance posting, outbox |
| 9 | Tenant Manager | Full multi-tenancy subsystem |
| 10 | Webhook Delivery | SSRF-safe HMAC-signed delivery |
| 11 | Dead Letter Queue | Redis-backed DLQ with exponential backoff |
| 12 | Root Package & Utilities | App lifecycle, errors, UUID, env vars |
| 13 | Cross-Cutting Patterns | Shared patterns across packages |
| 14 | Which Package Do I Need? | Decision tree |
| 15 | Breaking Changes | Migration notes v4.2.0 → v5.x |

Read `sub-files/reference.md` for full API detail.

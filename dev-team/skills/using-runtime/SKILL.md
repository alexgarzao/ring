---
name: ring:using-runtime
description: |
  Dual-mode skill for commons/runtime — the panic observability trident inside
  github.com/LerianStudio/lib-commons (latest v5.x). Deep-dive companion to ring:using-lib-commons,
  scoped entirely to the one package that turns silent goroutine deaths into
  observable production signal.

  Sweep Mode (primary): Dispatches 6 parallel explorer subagents to sweep any Lerian Go
  codebase for panic-handling DIY that commons/runtime should own — naked goroutine
  launches, unobservable `defer recover()`, missing panic-metric initialization, missing
  production mode, framework handlers that bypass the trident, and policy mismatches
  between KeepRunning and CrashProcess. Detects version drift, identifies replacements
  with file:line precision, and generates tasks compatible with ring:dev-cycle.

  Reference Mode: Full API surface of commons/runtime — SafeGo variants, RecoverWithPolicy
  variants, HandlePanicValue, InitPanicMetrics, SetProductionMode, SetErrorReporter,
  policy constants, the ErrorReporter interface. Plus the policy decision tree, a pattern
  catalog with framework integrations (Fiber, gRPC, RabbitMQ), a deep explanation of the
  observability trident (log + span event + metric + optional ErrorReporter callback),
  testing patterns, an anti-pattern catalog, bootstrap order, and cross-cutting concerns.
  Load for API discovery and correct usage patterns.

trigger: |
  Sweep mode:
  - "Audit this service for runtime / panic-recovery compliance"
  - "Sweep the codebase for naked goroutines"
  - "Find every go func() that should use SafeGo"
  - "Check panic handling across the repo"
  - "Are we observing recovered panics?"
  - "Migrate this service to commons/runtime"

  Reference mode:
  - "Which SafeGo variant should I use for a long-lived consumer?"
  - "How do I wire commons/runtime into Fiber's recover.New?"
  - "What does SetProductionMode actually change?"
  - "When KeepRunning vs CrashProcess?"
  - "How do I plug Sentry into runtime?"
  - "How do I test that panic recovery actually fires?"
  - "Where in bootstrap does InitPanicMetrics go?"

skip_when: |
  - Working on non-Go services
  - Working on frontend code
  - Target codebase is Ring itself (no lib-commons dependency)

related:
  similar: [ring:using-lib-commons, ring:using-assert, ring:using-dev-team, ring:dev-refactor]
---

# ring:using-runtime

This skill serves two distinct purposes. Choose the correct mode before proceeding.

The parent skill `ring:using-lib-commons` covers `commons/runtime` as 1 of 22 angles
(Angle 15: Panic handling DIY). This skill expands that single angle into 6 sub-angles
with deeper detection patterns, a full API reference, a policy decision tree, framework
integration patterns, and an anti-pattern catalog. Use it when panic handling is the
primary concern or when Angle 15 surfaced enough findings to warrant a focused sweep.

## Mode Selection

MUST choose mode based on the request shape:

| Request Shape                                                  | Mode          |
| -------------------------------------------------------------- | ------------- |
| "Sweep / audit panic handling / find naked goroutines"         | **Sweep**     |
| "Migrate this service to commons/runtime"                      | **Sweep**     |
| "Are our defer recover() calls observable?"                    | **Sweep**     |
| "Which SafeGo variant do I use for X?"                         | **Reference** |
| "How does the observability trident fire on panic?"            | **Reference** |
| "Show me the policy decision tree"                             | **Reference** |
| "How do I wire runtime into Fiber / gRPC / RabbitMQ?"          | **Reference** |
| "What does SetProductionMode do?"                              | **Reference** |

- **Sweep Mode** (primary): Active orchestration. Executes the same 4-phase protocol as
  the parent skill — version reconnaissance, CHANGELOG delta, multi-angle DIY sweep,
  consolidated report — but scoped to panic-handling patterns only. Emits tasks for
  `ring:dev-cycle` consumption.
- **Reference Mode**: Passive catalog. Read sections 1–10 below for API discovery,
  framework integration, testing, and anti-pattern avoidance.

Sweep Mode uses Reference Mode content as explorer context — each of the 6 explorers
receives the relevant catalog entries for its angle so it knows the target API surface.

## Table of Contents

| # | Section                            | Mode      | What You'll Find                                                    |
| - | ---------------------------------- | --------- | ------------------------------------------------------------------- |
| — | Mode Selection                     | Both      | How to choose sweep vs reference                                    |
| — | Sweep Protocol                     | Sweep     | 4-phase scan orchestration                                          |
| — | Explorer Angle Specs               | Sweep     | 6 DIY patterns and replacements                                     |
| — | Report Template                    | Sweep     | Findings format                                                     |
| — | Task Generation                    | Sweep     | ring:dev-cycle handoff format                                       |
| 1 | API Surface                        | Reference | Full exported-symbol catalog for commons/runtime                    |
| 2 | Policy Decision Tree               | Reference | KeepRunning vs CrashProcess — when to use which                     |
| 3 | Pattern Catalog                    | Reference | Consumer loops, fan-out, tickers, framework wiring, error reporter  |
| 4 | The Observability Trident          | Reference | What fires where on recovered panic                                 |
| 5 | Testing Patterns                   | Reference | How to prove recovery actually fires                                |
| 6 | Anti-Pattern Catalog               | Reference | Six ways to get this wrong + consequences                           |
| 7 | Bootstrap Order                    | Reference | Where runtime setup fits in service init                            |
| 8 | Cross-Cutting Patterns             | Reference | Nil-safety, stack truncation, ctx propagation, assertion interplay  |
| 9 | Breaking Changes                   | Reference | v4 → v5 notes for commons/runtime                                   |
| 10| Cross-References                   | Reference | Explicit pointers into ring:using-lib-commons and peers             |

---

# SWEEP MODE

MANDATORY: When invoked in Sweep Mode, the orchestrator MUST execute all four phases in
order. MUST NOT skip phases. MUST NOT shortcut Phase 3 by reducing explorer count.
FORBIDDEN: Producing a report based on the orchestrator's own code inspection — the 6
explorers are the source of truth for findings.

## Sweep Protocol

The sweep runs in four sequential phases. Each phase has a HARD GATE — MUST NOT proceed
to the next phase until the current phase produces its required artifact.

```
Phase 1: Version Reconnaissance   → /tmp/runtime-version-report.json
Phase 2: CHANGELOG Delta Analysis → /tmp/runtime-delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 6 × /tmp/runtime-sweep-{N}-{angle-slug}.json
Phase 4: Consolidated Report      → /tmp/runtime-sweep-report.md + /tmp/runtime-sweep-tasks.json
```

★ Insight ─────────────────────────────────────
The 4-phase separation is deliberate even when the scope is a single package. Version
drift (Phase 1) and CHANGELOG delta (Phase 2) guard against recommending APIs the
project's pinned version doesn't have. `runtime.SetErrorReporter` and the structured
`HandlePanicValue` signature are recent enough that v4-pinned projects may not have them
in the shape the report assumes. Run the phases in order — a sweep that skips Phases 1–2
can produce recommendations that don't compile.
─────────────────────────────────────────────────

### Phase 1: Version Reconnaissance

MANDATORY steps (orchestrator executes directly):

1. **Read `go.mod`** at the target project root.
   - Extract the line matching `github.com/LerianStudio/lib-commons/vN` (or the
     unversioned module path if pre-v2).
   - Capture the exact pinned version (e.g., `v5.1.0`, `v4.2.0`).
   - If the dependency is absent, STOP and report: "Target is not a lib-commons consumer.
     Sweep not applicable."

2. **WebFetch latest release:**

   ```
   https://api.github.com/repos/LerianStudio/lib-commons/releases/latest
   ```

   Extract `tag_name` (the latest v5.x release) and `published_at`.

3. **Compare versions** and flag drift:

   | Condition                                   | Classification      |
   | ------------------------------------------- | ------------------- |
   | Pinned == Latest                            | Up-to-date          |
   | Pinned is patch behind                      | Minor drift         |
   | Pinned is minor behind                      | Moderate drift      |
   | Pinned is major behind (v4.x → v5.x)        | **Major upgrade**   |
   | Module path mismatch (no `/vN` suffix)      | **Module mismatch** |

4. **If v4.x detected:** Add a "major upgrade advisory" flag to the report. Phase 3
   explorers MUST receive this flag so they adjust their recommendations — v5 tightened
   several runtime signatures and added `HandlePanicValue`. The report MUST call out the
   upgrade as a prerequisite for some recommendations.

5. **Emit `/tmp/runtime-version-report.json`** with fields:
   - `pinned_version` (string)
   - `latest_version` (string)
   - `drift_classification` (one of: up-to-date, minor-drift, moderate-drift, major-upgrade, module-mismatch)
   - `major_upgrade_required` (bool)
   - `module_path` (string, e.g., `github.com/LerianStudio/lib-commons/v5`)

### Phase 2: CHANGELOG Delta Analysis

MANDATORY steps:

1. **WebFetch CHANGELOG:**

   ```
   https://raw.githubusercontent.com/LerianStudio/lib-commons/main/CHANGELOG.md
   ```

2. **Extract entries** between `pinned_version` (exclusive) and `latest_version`
   (inclusive). Parse the standard Keep-a-Changelog sections: `Added`, `Changed`,
   `Fixed`, `Security`, `Deprecated`, `Removed`.

3. **Filter to commons/runtime entries only.** Entries that mention `commons/runtime`,
   `SafeGo`, `RecoverWithPolicy`, `HandlePanicValue`, `InitPanicMetrics`,
   `SetProductionMode`, `SetErrorReporter`, `ErrorReporter`, or `panic recovery` are in
   scope. Everything else is dropped (the parent skill covers other packages).

4. **Classify each entry** into one of:
   - `new-api` — a new exported symbol in commons/runtime
   - `breaking-change` — backward-incompatible change (requires migration)
   - `security-fix` — fix the consumer benefits from by upgrading
   - `bugfix` — consumer-facing bug resolved
   - `behavior-change` — observable behavior change without signature change

5. **Surface unadopted capabilities.** These become report highlights — features the
   consumer is eligible to adopt but hasn't yet.

6. **Emit `/tmp/runtime-delta-report.json`** with a list of entries, each shaped:

   ```json
   {
     "version": "v5.0.0",
     "section": "Added",
     "classification": "new-api",
     "summary": "runtime.HandlePanicValue — structured handler for framework-recovered panic values"
   }
   ```

### Phase 3: Multi-Angle DIY Sweep

MANDATORY: Dispatch all 6 explorer angles. MUST NOT skip any angle. MUST dispatch in
**ONE batch of 6** — no staging, no fan-out throttling. Six explorers is inside the safe
parallelism envelope. Wait for all six to complete before Phase 4.

**Per-explorer dispatch contract:**

Each explorer MUST be dispatched with `subagent_type: ring:codebase-explorer`. The
prompt MUST contain exactly these sections:

```
## Target
<absolute path to target repo root>

## Your Angle
<angle number + name, e.g., "Angle 1: Naked goroutine launches">

## Severity Calibration
<CRITICAL | HIGH | MEDIUM | LOW — from angle spec>

## What to Detect (DIY patterns)
<bullet list of grep patterns, import paths, code signatures>

## Replacement
<commons/runtime APIs + decision guidance>

## Migration Complexity
<trivial | moderate | complex>

## Version Context
Pinned: <from Phase 1>
Latest: <from Phase 1>
Major upgrade required: <bool from Phase 1>

## Output
Write findings to: /tmp/runtime-sweep-{N}-{angle-slug}.json
Schema: see below.
```

**Explorer output schema** (`/tmp/runtime-sweep-{N}-{angle-slug}.json`):

```json
{
  "angle_number": 1,
  "angle_name": "Naked goroutine launches",
  "severity": "CRITICAL",
  "migration_complexity": "moderate",
  "findings": [
    {
      "file": "internal/worker/consumer.go",
      "line": 34,
      "diy_pattern": "go func() launching long-lived consumer loop without SafeGo",
      "replacement": "runtime.SafeGoWithContextAndComponent",
      "evidence_snippet": "go func() { for msg := range deliveries { ... } }()",
      "notes": "Long-lived consumer — policy KeepRunning; panic here silently kills consumption"
    }
  ],
  "summary": "3 naked goroutine launches in consumer and fan-out paths",
  "requires_major_upgrade": false
}
```

**If an explorer finds nothing** for its angle, it MUST still write a file with an
empty `findings` array and a summary stating "No DIY patterns detected for this angle".
This lets the synthesizer distinguish "checked and clean" from "not checked".

### Phase 4: Consolidated Report + Task Generation

MANDATORY: Dispatch a synthesizer agent (`subagent_type: ring:codebase-explorer` is
acceptable; general-purpose is also acceptable) with this contract:

```
## Inputs
- /tmp/runtime-version-report.json
- /tmp/runtime-delta-report.json
- /tmp/runtime-sweep-*.json  (6 files)

## Outputs
1. /tmp/runtime-sweep-report.md  (human-readable report — see Report Template)
2. /tmp/runtime-sweep-tasks.json (ring:dev-cycle task array — see Task Generation)

## Your Job
MUST read all 6 explorer files. MUST aggregate findings by severity. MUST produce the
report following the exact template below. MUST generate one task per DIY pattern cluster
(group findings in the same file/package into one task). CRITICAL findings MUST be
standalone tasks.

MUST NOT invent findings not present in explorer outputs.
MUST NOT omit findings that explorers flagged.
MUST NOT reclassify severity without explicit justification in the task description.
```

After synthesis completes, the orchestrator surfaces the report path + task count to the
user and offers handoff to `ring:dev-cycle`.

---

## Explorer Angle Specifications

MANDATORY: All 6 angles run on every sweep. The catalog below is the source of truth
for what each explorer looks for. MUST NOT edit angle specs at dispatch time — copy
verbatim into the explorer prompt.

---

#### Angle 1: Naked goroutine launches

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- `go func()` in non-test code not wrapped by `runtime.SafeGo`, `runtime.SafeGoWithContext`, or `runtime.SafeGoWithContextAndComponent`
- `go someFunction(` — bare call-form goroutine launch
- `go method(` — bare method-form goroutine launch
- `go obj.Method(` — bare receiver-method-form goroutine launch
- Goroutines spawned inside HTTP handlers for per-request fan-out without recovery
- Long-lived consumer goroutines (RabbitMQ, Kafka, internal channels) launched raw
- Background workers launched from `init()`, `main()`, or package-level `func` without recovery

**lib-commons Replacement:**
- `runtime.SafeGo(logger, name, policy, fn)` — fire-and-forget with policy
- `runtime.SafeGoWithContext(ctx, logger, name, policy, fn)` — carries ctx into fn
- `runtime.SafeGoWithContextAndComponent(ctx, logger, component, name, policy, fn)` —
  **preferred for long-lived workers**; component label feeds the metric + log + span,
  making panics attributable to the subsystem that spawned them

**Split guidance:**

| Workload                                | Recommended API                                | Policy          |
| --------------------------------------- | ---------------------------------------------- | --------------- |
| HTTP handler per-request fan-out        | `SafeGoWithContext`                            | `KeepRunning`   |
| Long-lived consumer loop (AMQP/Kafka)   | `SafeGoWithContextAndComponent`                | `KeepRunning`   |
| Periodic worker (`time.NewTicker`)      | `SafeGoWithContextAndComponent`                | `KeepRunning`   |
| Bootstrap invariant goroutine           | `SafeGoWithContextAndComponent`                | `CrashProcess`  |

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE): long-lived consumer loop — panic here dies silently
go func() {
    for delivery := range deliveries {
        handleDelivery(delivery) // panic → goroutine dies, consumption stops, nothing logs
    }
}()

// lib-commons (AFTER):
runtime.SafeGoWithContextAndComponent(ctx, logger, "outbound-webhook-consumer",
    "amqp-consumer-loop", runtime.KeepRunning,
    func(ctx context.Context) {
        for delivery := range deliveries {
            handleDelivery(ctx, delivery) // panic → recovered, logged, metric++, span event, optional Sentry
        }
    },
)
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for naked goroutine launches. MUST find every `go func()`,
> `go someFunction(`, `go method(`, and `go obj.Method(` in non-test code that isn't
> wrapped by `runtime.SafeGo`, `runtime.SafeGoWithContext`, or
> `runtime.SafeGoWithContextAndComponent`. For each finding record file:line, the
> goroutine shape (fire-and-forget vs long-lived loop vs request fan-out), and whether
> the surrounding function has a `ctx context.Context` parameter in scope. MUST note the
> recommended API for each finding per the split guidance table (consumer loop →
> SafeGoWithContextAndComponent + KeepRunning; request fan-out → SafeGoWithContext +
> KeepRunning; bootstrap invariant goroutine → CrashProcess). Severity CRITICAL — naked
> goroutine panics are the single highest-signal silent-failure mode in Go services.

---

#### Angle 2: Unobservable `defer recover()`

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- `defer func() { if r := recover(); r != nil { ... } }()` where the recovery branch doesn't
  emit a metric, a structured log with stack, or an OTel span event
- `defer recover()` used as a silencer (recover called, return value discarded) — panic
  is swallowed, nothing surfaces anywhere
- Framework-style recovery (e.g., middleware) that logs via `fmt.Printf` or `log.Println`
  rather than the structured logger, and doesn't increment a metric
- Recovery branches that format `r` into an error and return it without also firing the
  observability trident — the caller sees an error, but dashboards never see the panic

**lib-commons Replacement:**
- `runtime.RecoverWithPolicyAndContext(ctx, logger, component, operation, policy)` —
  preferred: carries ctx so the active span receives the `panic.recovered` event
- `runtime.RecoverWithPolicy(logger, component, operation, policy)` — when no ctx is
  available (rare; almost every call site has one)
- `runtime.HandlePanicValue(ctx, logger, recoveredValue, component, operation)` — when
  the panic was recovered *by a framework* (Fiber, gRPC) and you need to feed the value
  into the trident pipeline manually

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
func createOrder(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    defer func() {
        if r := recover(); r != nil {
            // swallowed — no log, no metric, no span event
            _ = r
        }
    }()
    return processOrder(ctx, req)
}

// lib-commons (AFTER):
func createOrder(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    defer runtime.RecoverWithPolicyAndContext(ctx, logger,
        "order-service", "createOrder", runtime.KeepRunning)
    return processOrder(ctx, req)
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for unobservable `defer recover()` patterns. MUST find every
> `defer func() { if r := recover(); r != nil` (multi-line and single-line variants) and
> `defer recover()` in non-test code. For each, inspect the recovery branch: does it
> call a structured logger with stack trace, emit a span event, and increment a metric?
> If it lacks any of those three, flag it. Record file:line, what the recovery branch
> does (swallows, logs to stdlib, returns error, re-panics), and which component the
> function belongs to. MUST also flag recovery branches that format `r` into an error
> and return it without firing the trident — the error path masks a missing metric.
> Severity CRITICAL — unobserved recoveries make panics invisible in production.

---

#### Angle 3: Missing `InitPanicMetrics` at startup

**Severity:** HIGH

**DIY Patterns to Detect:**
- Service imports and uses `runtime.SafeGo` / `runtime.RecoverWithPolicy*` / 
  `runtime.SafeGoWithContext*` somewhere in the codebase
- Bootstrap package (`main.go`, `cmd/*/main.go`, `internal/bootstrap/`, `internal/app/`)
  has **no call** to `runtime.InitPanicMetrics`
- `InitPanicMetrics` is called with a `nil` factory (e.g., telemetry was disabled but the
  call was left in place — metric registrations silently no-op)
- `InitPanicMetrics` is called **before** telemetry setup completes (factory not yet
  initialized)

**Grep pattern** (two-step detection):
1. `grep -r "runtime.SafeGo\|runtime.RecoverWith" --include="*.go"` → presence
2. `grep -r "runtime.InitPanicMetrics" --include="*.go"` → absence → FINDING

**lib-commons Replacement:**
- Add `runtime.InitPanicMetrics(tl.MetricsFactory, logger)` after telemetry setup,
  before any SafeGo launches — canonical location is right after `tl.ApplyGlobals()`

**Consequence of missing:** Recovered panics are logged and emit span events, but the
`panic_recovered_total` counter is **never emitted** — dashboards show nothing, alerts
never fire. You get half the trident.

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE): bootstrap never wires panic metrics
logger, _ := zap.New(zapCfg)
tl, _ := opentelemetry.NewTelemetry(otelCfg)
_ = tl.ApplyGlobals()

// launches SafeGo goroutines — metric never emits because factory not registered
runtime.SafeGoWithContextAndComponent(ctx, logger, "worker", "loop",
    runtime.KeepRunning, workerFn)

// lib-commons (AFTER):
logger, _ := zap.New(zapCfg)
tl, _ := opentelemetry.NewTelemetry(otelCfg)
_ = tl.ApplyGlobals()

runtime.InitPanicMetrics(tl.MetricsFactory, logger)   // <-- wire metrics first
runtime.SetProductionMode(true)

runtime.SafeGoWithContextAndComponent(ctx, logger, "worker", "loop",
    runtime.KeepRunning, workerFn)                     // now the counter fires
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for missing `runtime.InitPanicMetrics` initialization. First,
> confirm the service actually uses `commons/runtime` by grep'ing for `runtime.SafeGo`,
> `runtime.RecoverWith`, `runtime.HandlePanicValue`. If the service uses runtime, MUST
> check for a call to `runtime.InitPanicMetrics` in bootstrap files (`main.go`,
> `cmd/*/main.go`, `internal/bootstrap/`, `internal/app/`). If the call is missing,
> flag it. If the call exists but is placed BEFORE telemetry setup or passes `nil` as
> the factory, flag it. Record file:line of the bootstrap sequence and the exact
> position where `InitPanicMetrics` should land (after `tl.ApplyGlobals()`, before any
> SafeGo launches). Severity HIGH — without this call, half the observability trident
> never emits and dashboards lie.

---

#### Angle 4: Missing `SetProductionMode(true)` in production services

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Bootstrap code lacks `runtime.SetProductionMode` call entirely
- `SetProductionMode` is called with a hardcoded `false`
- `SetProductionMode` is gated on a misconfigured or inverted env var (e.g.,
  `runtime.SetProductionMode(os.Getenv("DEBUG") == "true")` — reads wrong variable)
- `SetProductionMode(true)` called but then later in bootstrap `SetProductionMode(false)`
  is also called (rare but catches test scaffolding leaking into main)

**lib-commons Replacement:**
- `runtime.SetProductionMode(cfg.Env == "production")` — read from standard config, set
  deterministically once at startup, before any SafeGo launches

**Consequence of missing:**
- Panic value string flows verbatim into log fields, span events, and ErrorReporter
  payloads → **PII leakage risk** (the panic message may include user input, request
  bodies, or secrets that happened to be in the panicking stack frame)
- Stack traces are **not truncated** → 20 KB stack traces bloat span attributes, hit
  exporter limits, and may be rejected by the OTel collector
- Development-mode verbosity leaks into production log aggregators

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE): no production-mode switch — panic values leak to span events verbatim
logger, _ := zap.New(zapCfg)
tl, _ := opentelemetry.NewTelemetry(otelCfg)
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
// missing: SetProductionMode

// lib-commons (AFTER):
logger, _ := zap.New(zapCfg)
tl, _ := opentelemetry.NewTelemetry(otelCfg)
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
runtime.SetProductionMode(cfg.Env == "production")  // panic values redacted, stack capped
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for missing or misconfigured `runtime.SetProductionMode` calls.
> Search bootstrap files for `runtime.SetProductionMode`. If absent, flag the service.
> If present, check the argument: `true` is correct for production services, `false`
> is correct only in test scaffolding, a boolean expression should derive from the
> deployment environment variable (typically `cfg.Env == "production"` or similar). MUST
> flag hardcoded `false`, inverted env-var reads (reading `DEBUG` instead of `ENV`), and
> any path where `SetProductionMode` is toggled multiple times. For each finding record
> file:line and the current argument. Severity MEDIUM — correctness issue, PII leak
> risk, span-attribute bloat. The failure is slow-developing (you discover it when
> someone grep's production logs and sees a credit card number in a panic message).

---

#### Angle 5: Framework panic handlers bypassing `HandlePanicValue`

**Severity:** HIGH

**DIY Patterns to Detect:**
- Fiber `recover.New(recover.Config{StackTraceHandler: ...})` where the handler logs the
  recovered value but does **not** call `runtime.HandlePanicValue(c.UserContext(),
  logger, e, component, operation)`
- gRPC unary/stream interceptors that use bare `defer recover()` without feeding the
  recovered value through `runtime.HandlePanicValue`
- Custom RabbitMQ consumer wrappers that wrap handler calls in `defer recover()` and
  route errors manually (ignoring the trident pipeline)
- Handler libraries that swallow panics silently (e.g., `defer func() { _ = recover() }()`
  inside an interceptor — the framework logs nothing, the trident fires nothing)

**lib-commons Replacement:**
- Fiber: wire `StackTraceHandler` → `runtime.HandlePanicValue(c.UserContext(), logger, e,
  "api", c.Path())`
- gRPC: `defer runtime.RecoverWithPolicyAndContext(ctx, logger, "grpc", info.FullMethod,
  runtime.KeepRunning)` at the top of the interceptor
- RabbitMQ wrapper: wrap the handler call with `runtime.SafeGoWithContextAndComponent`
  for the consumer loop, and `runtime.RecoverWithPolicyAndContext` for per-message
  processing if the consumer can't afford to lose the goroutine

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE): Fiber recover middleware logs, but trident never fires
app.Use(recover.New(recover.Config{
    EnableStackTrace: true,
    StackTraceHandler: func(c *fiber.Ctx, e interface{}) {
        log.Printf("panic in handler %s: %v", c.Path(), e) // stdlib log — no metric, no span event
    },
}))

// lib-commons (AFTER):
app.Use(recover.New(recover.Config{
    EnableStackTrace: true,
    StackTraceHandler: func(c *fiber.Ctx, e interface{}) {
        runtime.HandlePanicValue(c.UserContext(), logger, e, "api", c.Path())
    },
}))
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for framework panic handlers that bypass
> `runtime.HandlePanicValue`. MUST search for `recover.New(` (Fiber),
> `grpc.UnaryInterceptor(`, `grpc.StreamInterceptor(`, and any custom consumer wrapper
> that mentions `recover()`. For each, inspect the recovery path: does it eventually
> call `runtime.HandlePanicValue`, `runtime.RecoverWithPolicyAndContext`, or
> `runtime.RecoverWithPolicy`? If it logs via stdlib `log`, emits to a custom logger
> without metric emission, or silently swallows the panic, flag it. For gRPC
> specifically, MUST flag interceptors that don't pass the ctx into the recovery
> pipeline (losing trace context). Record file:line, the framework involved, and the
> current recovery behavior. Severity HIGH — framework handlers are where 50% of
> server-side panics land; if they bypass the trident, half your panics are invisible.

---

#### Angle 6: Policy mismatch (`KeepRunning` vs `CrashProcess`)

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- `runtime.CrashProcess` passed to SafeGo for an HTTP request handler goroutine (wrong —
  one panicking request must not kill the service for all other tenants/users)
- `runtime.CrashProcess` in a consumer loop where one bad message should be routed to
  DLQ, not crash the whole service
- `runtime.KeepRunning` in a bootstrap-invariant goroutine where continuing past the
  panic leaves the service running in a corrupt state (e.g., license validation
  goroutine, schema migration runner)
- `runtime.KeepRunning` in a goroutine whose responsibility is a one-shot invariant
  check (e.g., "verify DB schema matches expected version") — silently continuing past
  a failed invariant check is worse than crashing

**lib-commons Replacement:**
- Apply the Reference Mode decision tree (Section 2). No mechanical rewrite — this is a
  **judgment call** per goroutine.

**Severity MEDIUM** because default usage is defensible; this is correctness-tuning, not
an outright bug. A service with `KeepRunning` everywhere usually works; a service with
`CrashProcess` everywhere restarts too often. The sweep flags the cases where the wrong
policy is measurably harmful.

**Migration Complexity:** moderate (requires per-goroutine decision, not a sed script)

**Example Transformation:**

```go
// DIY (BEFORE): bootstrap invariant using KeepRunning — service runs in corrupt state
runtime.SafeGoWithContextAndComponent(ctx, logger, "migrator", "apply-schema",
    runtime.KeepRunning, func(ctx context.Context) {
        if err := applySchemaMigrations(ctx); err != nil {
            panic(err) // recovered, logged, but service continues with unmigrated schema
        }
    })

// lib-commons (AFTER): flip to CrashProcess so k8s restarts the pod on failure.
// Mirror fix for the opposite case: request-handler fan-out using CrashProcess flips
// to KeepRunning so one bad request doesn't DoS the service replica.
runtime.SafeGoWithContextAndComponent(ctx, logger, "migrator", "apply-schema",
    runtime.CrashProcess, func(ctx context.Context) {
        if err := applySchemaMigrations(ctx); err != nil {
            panic(err)
        }
    })
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for policy mismatches between `runtime.KeepRunning` and
> `runtime.CrashProcess`. MUST find every call to `runtime.SafeGo`,
> `runtime.SafeGoWithContext`, `runtime.SafeGoWithContextAndComponent`,
> `runtime.RecoverWithPolicy`, and `runtime.RecoverWithPolicyAndContext`. For each,
> classify the goroutine's role: (a) HTTP/gRPC request handler, (b) per-request fan-out,
> (c) long-lived consumer loop, (d) periodic worker, (e) bootstrap invariant check, (f)
> one-shot migration/provisioning goroutine. MUST flag role (a), (b), (c), (d) using
> `CrashProcess` — these should use `KeepRunning`. MUST flag role (e), (f) using
> `KeepRunning` when continuing past a panic leaves the service in a corrupt state —
> these should use `CrashProcess`. For each finding record file:line, the goroutine
> role, the current policy, and the recommended policy with a one-sentence rationale.
> Severity MEDIUM — default usage is defensible, only flag cases where the wrong policy
> is measurably harmful.

---

## Report Template

MANDATORY: The synthesizer MUST produce `/tmp/runtime-sweep-report.md` following this
exact structure. MUST NOT add sections. MUST NOT reorder sections. MUST populate every
section even if empty (use "None detected" placeholders).

```markdown
# commons/runtime Sweep Report

**Target:** <absolute path to target repo>
**Generated:** <ISO-8601 timestamp>
**Sweep duration:** <seconds>

---

## Version Status

| Field                    | Value             |
| ------------------------ | ----------------- |
| Pinned version           | <v5.0.0>          |
| Latest stable            | <resolved at runtime> |
| Drift classification     | <minor-drift>     |
| Major upgrade required   | <yes / no>        |
| Module path              | <.../v5>          |

**Assessment:** <one-paragraph narrative — e.g., "project is 2 patch releases behind,
straightforward `go get -u` upgrade; commons/runtime API surface unchanged since pinned
version" or "project pinned to v4.2.0, v5 migration required before adopting
HandlePanicValue recommendations below">

---

## Unadopted Features

commons/runtime features added between the pinned version and latest stable that the
target has not yet adopted:

| Version | Feature                                        | Classification  | Relevant Finding Angle |
| ------- | ---------------------------------------------- | --------------- | ---------------------- |
| <vX>    | <e.g., runtime.HandlePanicValue>               | new-api         | Angle 5                |
| <vX>    | <e.g., SetErrorReporter hook>                  | new-api         | (standalone highlight) |

---

## Quick Wins

Severity LOW–MEDIUM, migration complexity trivial. Low-risk, high-ergonomics fixes
batchable in a single dev-cycle task.

<bulleted list of findings grouped by angle — each bullet: "Angle N: <summary>, <file count> files, trivial">

---

## Strategic Migrations

Severity HIGH–CRITICAL, migration complexity moderate–complex. High-value, multi-task
efforts that MUST go through the full dev-cycle.

<bulleted list of findings grouped by angle — each bullet: "Angle N: <summary>, <file count> files, complexity, expected impact">

---

## Full Findings

| Angle                                    | Severity  | File                        | Line | DIY Pattern                         | Replacement                               | Complexity |
| ---------------------------------------- | --------- | --------------------------- | ---- | ----------------------------------- | ----------------------------------------- | ---------- |
| 1 Naked goroutine launches               | CRITICAL  | internal/worker/consumer.go | 34   | go func() long-lived consumer       | runtime.SafeGoWithContextAndComponent     | moderate   |
| 2 Unobservable defer recover()           | CRITICAL  | internal/http/handler.go    | 89   | defer recover() swallows panic      | runtime.RecoverWithPolicyAndContext       | moderate   |
| 3 Missing InitPanicMetrics               | HIGH      | cmd/api/main.go             | 52   | bootstrap skips metric init          | runtime.InitPanicMetrics                  | trivial    |
| 4 Missing SetProductionMode              | MEDIUM    | cmd/api/main.go             | 54   | no SetProductionMode call           | runtime.SetProductionMode                 | trivial    |
| 5 Framework handler bypass               | HIGH      | internal/http/middleware.go | 18   | Fiber recover logs via stdlib       | runtime.HandlePanicValue                  | moderate   |
| 6 Policy mismatch                        | MEDIUM    | internal/worker/migrate.go  | 71   | KeepRunning on migration goroutine  | CrashProcess                              | moderate   |
| ...                                      | ...       | ...                         | ...  | ...                                 | ...                                       | ...        |

---

## Summary Statistics

| Severity | Findings | Files affected | Estimated effort |
| -------- | -------- | -------------- | ---------------- |
| CRITICAL | N        | N              | N days           |
| HIGH     | N        | N              | N days           |
| MEDIUM   | N        | N              | N days           |
| LOW      | N        | N              | N days           |
| **Total**| **N**    | **N**          | **N days**       |

**Angles clean:** <list of angles where no DIY was detected — signals codebase health>

---

## Recommended Next Step

`ring:dev-cycle` consuming `/tmp/runtime-sweep-tasks.json` — N tasks generated,
grouped by severity, CRITICAL first.
```

---

## Task Generation for ring:dev-cycle

MANDATORY: The synthesizer MUST also emit `/tmp/runtime-sweep-tasks.json` — a JSON
array of tasks shaped for `ring:dev-cycle` consumption. The format matches what
`ring:dev-refactor` and `ring:using-lib-commons` produce, so the downstream cycle
doesn't need to special-case runtime sweeps.

**Task grouping rules:**

1. MUST group findings by severity — CRITICAL first, then HIGH, MEDIUM, LOW.
2. Within a severity tier, MUST group findings from the same file or tightly-related
   files into a single task (avoid one-task-per-line fragmentation).
3. CRITICAL findings MUST be standalone tasks (no batching across concerns) — each gets
   its own dev-cycle pass. Angles 1 and 2 in particular are standalone.
4. MUST include dependency references when one task's correctness depends on another:
   - Angle 3 (`InitPanicMetrics`) SHOULD land before Angles 1, 2, 5 so fixes emit metrics
     from the first run.
   - Angle 4 (`SetProductionMode`) SHOULD land before Angles 1, 2, 5 so fixes respect
     production-mode redaction from the first run.
   - Version upgrade (when `major_upgrade_required = true`) MUST land as task #1, with
     every other task depending on it.

**Task schema:**

```json
{
  "id": "runtime-sweep-001",
  "title": "Wrap naked goroutines in commons/runtime.SafeGo",
  "severity": "CRITICAL",
  "description": "Target service launches N goroutines via raw `go func()` / `go someFunc(` across the worker and HTTP handler layers. Panics inside these goroutines silently kill the goroutine, stop the work it was responsible for, and surface nothing in logs, metrics, or traces — the service appears healthy while work is silently dropped. Wrap each site in `runtime.SafeGoWithContextAndComponent` (long-lived workers) or `runtime.SafeGoWithContext` (per-request fan-out) with policy `KeepRunning`. This is the single highest-leverage reliability fix in the sweep.",
  "files_affected": [
    "internal/worker/consumer.go:34",
    "internal/worker/dispatcher.go:71",
    "internal/http/handler.go:112"
  ],
  "acceptance_criteria": [
    "All `go func()` / `go someFunc(` / `go obj.Method(` calls in non-test code wrapped in a runtime.SafeGo* variant",
    "Long-lived workers use SafeGoWithContextAndComponent with a descriptive component label",
    "Per-request fan-out uses SafeGoWithContext",
    "Policy is KeepRunning for request handlers and consumer loops",
    "Test: forced panic inside a wrapped goroutine emits the panic_recovered_total metric",
    "Test: forced panic inside a wrapped goroutine does not terminate the surrounding goroutine scope"
  ],
  "estimated_complexity": "moderate",
  "depends_on": ["runtime-sweep-003"],
  "angle": 1,
  "replacement_api": "runtime.SafeGoWithContextAndComponent"
}
```

**Task emission verbatim example** (first task is the Angle-3 bootstrap fix;
subsequent tasks `depends_on` it so fixes emit clean telemetry from their first run):

```json
[
  {
    "id": "runtime-sweep-001",
    "title": "Initialize panic metrics and production mode in bootstrap",
    "severity": "HIGH",
    "description": "Target service uses commons/runtime but bootstrap never calls runtime.InitPanicMetrics (counter never emits) nor runtime.SetProductionMode (panic values leak verbatim to logs/spans). Land these two calls first so subsequent fixes emit clean telemetry.",
    "files_affected": ["cmd/api/main.go:52"],
    "acceptance_criteria": [
      "main.go calls runtime.InitPanicMetrics(tl.MetricsFactory, logger) after telemetry setup",
      "main.go calls runtime.SetProductionMode(cfg.Env == \"production\") before any SafeGo launches",
      "Integration test: forced panic emits panic_recovered_total with correct component label"
    ],
    "estimated_complexity": "trivial",
    "depends_on": [],
    "angle": 3,
    "replacement_api": "runtime.InitPanicMetrics + runtime.SetProductionMode"
  },
  {
    "id": "runtime-sweep-002",
    "title": "Wrap naked goroutines in commons/runtime.SafeGo",
    "severity": "CRITICAL",
    "description": "<as above>",
    "files_affected": ["internal/worker/consumer.go:34", "..."],
    "acceptance_criteria": ["..."],
    "estimated_complexity": "moderate",
    "depends_on": ["runtime-sweep-001"],
    "angle": 1,
    "replacement_api": "runtime.SafeGoWithContextAndComponent"
  }
]
```

**Handoff message template** (orchestrator surfaces to user after Phase 4):

```
commons/runtime sweep complete. Findings: <N> across <M> of 6 angles.
- CRITICAL: <N>   HIGH: <N>   MEDIUM: <N>   LOW: <N>

Report: /tmp/runtime-sweep-report.md
Tasks:  /tmp/runtime-sweep-tasks.json (<N> tasks)

Next: Invoke ring:dev-cycle with the task file to execute fixes. CRITICAL tasks
(Angles 1 and 2 — naked goroutines and unobservable defer recover) MUST be addressed
before the HIGH/MEDIUM tier. Angle 3 (InitPanicMetrics) is trivial and SHOULD land
first so all subsequent fixes emit metrics from the first run.
```

---

# REFERENCE MODE

Sections 1–10 below catalog commons/runtime's API surface, decision trees, patterns,
and anti-patterns. Read the sections relevant to your current task. Sweep Mode
explorers receive extracts from these sections as context for their angle.

---

## 1. API Surface

Full catalog of exported symbols in `commons/runtime` (lib-commons latest v5.x).

### Goroutine Launchers

| Symbol | Signature | Purpose | When to Use |
|---|---|---|---|
| `SafeGo` | `func(logger log.Logger, goroutineName string, policy PanicPolicy, fn func())` | Launch a goroutine with panic recovery. No ctx, no component label. | Legacy call sites or trivial fire-and-forget where you have no ctx in scope. Prefer the `WithContext` variants when possible. |
| `SafeGoWithContext` | `func(ctx context.Context, logger log.Logger, goroutineName string, policy PanicPolicy, fn func(context.Context))` | Launch a goroutine that carries the parent ctx. Trace context propagates. | Per-request fan-out inside HTTP handlers, short-lived workers that need cancellation. |
| `SafeGoWithContextAndComponent` | `func(ctx context.Context, logger log.Logger, component, goroutineName string, policy PanicPolicy, fn func(context.Context))` | Launch with ctx AND a component label. The component label becomes a metric/log/span attribute, making panics attributable. | **Preferred for long-lived workers.** Consumer loops, periodic workers, bootstrap goroutines. |

### Defer-Form Recovery

| Symbol | Signature | Purpose | When to Use |
|---|---|---|---|
| `RecoverWithPolicy` | `func(logger log.Logger, component, operation string, policy PanicPolicy)` | Deferred recovery with policy. No ctx — trace context is not captured. | Functions without a ctx in scope (rare). |
| `RecoverWithPolicyAndContext` | `func(ctx context.Context, logger log.Logger, component, operation string, policy PanicPolicy)` | Deferred recovery with ctx — the active span receives the `panic.recovered` event. | **Preferred.** Any function with ctx in scope. |

### Framework-Level Handling

| Symbol | Signature | Purpose | When to Use |
|---|---|---|---|
| `HandlePanicValue` | `func(ctx context.Context, logger log.Logger, recoveredValue any, component, operation string)` | Feed a recovered panic value into the trident pipeline. Does not itself recover — it handles the value someone else already recovered. | Framework handlers that recover panics themselves (Fiber `StackTraceHandler`, gRPC interceptors, custom wrappers). |

### Bootstrap

| Symbol | Signature | Purpose | When to Use |
|---|---|---|---|
| `InitPanicMetrics` | `func(factory metrics.Factory, logger log.Logger)` | Register the `panic_recovered_total` counter with the metrics factory. | Once, at bootstrap, after telemetry setup, before any SafeGo launches. |
| `SetProductionMode` | `func(on bool)` | Toggle production-mode behavior: redact panic values, truncate stack traces to 4096 bytes. | Once, at bootstrap. Pass `cfg.Env == "production"` (or equivalent). |
| `SetErrorReporter` | `func(reporter ErrorReporter)` | Register an external error reporter (Sentry, Bugsnag, etc.) that gets called on every recovered panic. | Once, at bootstrap, if the service uses external error tracking. Optional. |

### Policy Constants

| Symbol | Type | Behavior |
|---|---|---|
| `KeepRunning` | `PanicPolicy` | Recover, log, emit trident, continue. The goroutine's `fn` returns normally. |
| `CrashProcess` | `PanicPolicy` | Recover, log, emit trident, **re-panic**. The process terminates (or its container restarts). |

### Interface

```go
type ErrorReporter interface {
    CaptureException(ctx context.Context, err error, tags map[string]string)
}
```

A minimal contract for external error reporters. Implementations forward to Sentry,
Bugsnag, Rollbar, or any other service. Called **after** the trident fires, so the
log/metric/span emission is never gated on the reporter being reachable.

`SetErrorReporter(nil)` is explicitly allowed — it clears any previously set reporter.

---

## 2. Policy Decision Tree

`KeepRunning` vs `CrashProcess` is **the** decision that matters in this package. Get
it wrong and either one bad request kills the service for everyone (`CrashProcess` in a
handler), or the service runs in a corrupt state indefinitely (`KeepRunning` on a
broken invariant).

### Decision Table

| Workload                                                    | Policy          | Rationale                                                                 |
| ----------------------------------------------------------- | --------------- | ------------------------------------------------------------------------- |
| HTTP request handler (the handler itself, via RecoverWith*) | `KeepRunning`   | One bad request panicking must not kill the service for other requests.   |
| Per-request fan-out goroutine                               | `KeepRunning`   | Same — the outer request fails, but the service stays up.                 |
| gRPC handler goroutine                                      | `KeepRunning`   | Same reasoning as HTTP.                                                   |
| Long-lived AMQP/Kafka consumer loop                         | `KeepRunning`   | One bad message → DLQ, not service death. Consumption must continue.      |
| Background retry worker                                     | `KeepRunning`   | Retries are by definition fault-tolerant; crashing defeats the purpose.   |
| Periodic ticker worker                                      | `KeepRunning`   | One bad tick doesn't invalidate future ticks.                             |
| Bootstrap invariant check (e.g., license, DB schema)        | `CrashProcess`  | Running past a broken invariant corrupts state. Fail-closed is correct.   |
| Schema migration runner                                     | `CrashProcess`  | Continuing with an unmigrated schema corrupts every subsequent write.     |
| Data-integrity verification (e.g., startup reconciliation)  | `CrashProcess`  | Continuing past a detected inconsistency amplifies the inconsistency.     |
| One-shot provisioning job                                   | `CrashProcess`  | If the provisioning step panics, the running process is in a hybrid state. |

### Gray Areas

- **Kafka consumer with manual offset commit**: `KeepRunning`. A panic during message
  processing recovers; the offset is not committed; the message redelivers. This is the
  correct behavior.
- **Consumer whose dependencies fail to initialize at startup**: `CrashProcess` for the
  initialization goroutine, `KeepRunning` for the consumer loop. Two different
  goroutines, two different policies.
- **One-time data import run as a CLI command**: `CrashProcess`. If the import panics,
  the exit code must reflect failure so the orchestrator (cron, k8s Job) knows not to
  mark success.
- **Shared library code (e.g., a helper that spawns a goroutine)**: `KeepRunning`
  unless the helper's caller explicitly requests otherwise. The library doesn't know
  enough about the caller's invariants to choose `CrashProcess` safely.

★ Insight ─────────────────────────────────────
The mental model: `KeepRunning` = "this work is replaceable; losing it is survivable";
`CrashProcess` = "this work is a precondition for anything else being correct". When in
doubt, ask: "if this panics and I silently continue, is the service still producing
correct output?" If yes, `KeepRunning`. If no, `CrashProcess`. The default is almost
always `KeepRunning` — most goroutines run work that can fail without corrupting the
service.
─────────────────────────────────────────────────

---

## 3. Pattern Catalog

Real-world usage patterns. Each pattern is a full working snippet with realistic
variable names.

### 3.1 Long-lived consumer loop (RabbitMQ)

The canonical use case for `SafeGoWithContextAndComponent`. The consumer loop runs for
the lifetime of the service; a panic inside must not kill the goroutine because
consumption would silently stop.

```go
func startOutboundConsumer(ctx context.Context, logger log.Logger, deliveries <-chan amqp.Delivery, handler MessageHandler) {
    runtime.SafeGoWithContextAndComponent(ctx, logger,
        "outbound-webhook-service", "amqp-consumer-loop", runtime.KeepRunning,
        func(ctx context.Context) {
            for {
                select {
                case <-ctx.Done():
                    return
                case delivery, ok := <-deliveries:
                    if !ok {
                        return
                    }
                    if err := handler.Handle(ctx, delivery); err != nil {
                        _ = delivery.Nack(false, false) // route to DLQ
                        continue
                    }
                    _ = delivery.Ack(false)
                }
            }
        })
}
```

`ctx` propagation means a shutdown signal from the parent Launcher cancels the
consumer loop cleanly. Policy `KeepRunning` — a panic in `handler.Handle` recovers,
emits the trident, and the outer `for` resumes pulling deliveries. Without
`SafeGoWithContextAndComponent`, consumption would stop forever on the first panic.

### 3.2 Per-request fan-out

HTTP handler that spawns parallel sub-requests (e.g., enrichment calls). Each sub-call
runs in its own goroutine; panics there must not crash the service.

```go
func getOrderWithEnrichment(c *fiber.Ctx) error {
    ctx := c.UserContext()
    order, err := orderRepo.Get(ctx, c.Params("id"))
    if err != nil {
        return http.RenderError(c, err)
    }

    var wg sync.WaitGroup
    wg.Add(2)
    runtime.SafeGoWithContext(ctx, logger, "order-enrich-customer", runtime.KeepRunning,
        func(ctx context.Context) {
            defer wg.Done()
            if cust, err := customerClient.Fetch(ctx, order.CustomerID); err == nil {
                order.Customer = cust
            }
        })
    runtime.SafeGoWithContext(ctx, logger, "order-enrich-shipping", runtime.KeepRunning,
        func(ctx context.Context) {
            defer wg.Done()
            if ship, err := shippingClient.Fetch(ctx, order.ShippingID); err == nil {
                order.Shipping = ship
            }
        })
    wg.Wait()
    return http.Respond(c, 200, order)
}
```

Prefer `commons/errgroup` when you need first-error cancellation — `SafeGo*` is
appropriate when best-effort enrichment is acceptable.

### 3.3 Periodic ticker worker

Background worker on a fixed interval. `SafeGoWithContextAndComponent` — the component
label makes the ticker identifiable in metrics (`panic_recovered_total{component="cache-warmer"}`).

```go
func startCacheWarmer(ctx context.Context, logger log.Logger, warmer *Warmer) {
    runtime.SafeGoWithContextAndComponent(ctx, logger, "cache-warmer", "periodic-tick",
        runtime.KeepRunning, func(ctx context.Context) {
            ticker := time.NewTicker(5 * time.Minute)
            defer ticker.Stop()
            for {
                select {
                case <-ctx.Done():
                    return
                case <-ticker.C:
                    if err := warmer.Warm(ctx); err != nil {
                        logger.Errorf("cache warm failed: %v", err)
                    }
                }
            }
        })
}
```

### 3.4 Graceful shutdown coordination

`SafeGoWithContext*` variants carry the parent ctx into the goroutine. When the parent
cancels (shutdown signal, Launcher draining), the ctx propagates, and the goroutine
observes `ctx.Done()` and exits cleanly. Each `SafeGoWithContextAndComponent` call
spawns a worker under the same derived ctx; `<-ctx.Done()` in the parent blocks until
shutdown, at which point every child observes cancellation and exits. This is the
canonical pattern for service-level graceful shutdown using commons/runtime +
`commons.Launcher`.

### 3.5 Framework integration — Fiber

Fiber's `recover.New` middleware catches panics in handler chains. Wire its
`StackTraceHandler` into `runtime.HandlePanicValue` so the trident fires.

```go
app := fiber.New()
app.Use(recover.New(recover.Config{
    EnableStackTrace: true,
    StackTraceHandler: func(c *fiber.Ctx, e interface{}) {
        runtime.HandlePanicValue(c.UserContext(), logger, e, "api", c.Path())
    },
}))

app.Get("/orders/:id", getOrder)
```

`c.UserContext()` carries the request's trace context, so the `panic.recovered` span
event lands on the correct span. `c.Path()` feeds the `operation` attribute, making
panics attributable to the route that triggered them.

### 3.6 Framework integration — gRPC interceptors

gRPC unary and stream interceptors are goroutines from the perspective of recovery —
each RPC runs in its own goroutine pair (server side), and a panic inside the handler
must not kill the server.

```go
func RecoveryUnaryInterceptor(logger log.Logger) grpc.UnaryServerInterceptor {
    return func(ctx context.Context, req any, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (resp any, err error) {
        defer runtime.RecoverWithPolicyAndContext(ctx, logger,
            "grpc", info.FullMethod, runtime.KeepRunning)
        return handler(ctx, req)
    }
}

func RecoveryStreamInterceptor(logger log.Logger) grpc.StreamServerInterceptor {
    return func(srv any, ss grpc.ServerStream, info *grpc.StreamServerInfo, handler grpc.StreamHandler) (err error) {
        defer runtime.RecoverWithPolicyAndContext(ss.Context(), logger,
            "grpc", info.FullMethod, runtime.KeepRunning)
        return handler(srv, ss)
    }
}

// wire into the server
server := grpc.NewServer(
    grpc.UnaryInterceptor(RecoveryUnaryInterceptor(logger)),
    grpc.StreamInterceptor(RecoveryStreamInterceptor(logger)),
)
```

Unlike Fiber, gRPC does not have a built-in recovery middleware — you write it
yourself, and the canonical implementation is `defer RecoverWithPolicyAndContext`.

### 3.7 Framework integration — RabbitMQ consumer wrapper

If you wrap AMQP consumers with your own per-message function, guard the call with
`RecoverWithPolicyAndContext` so a panicking handler doesn't kill the consumer
goroutine.

```go
func wrapMessageHandler(logger log.Logger, component string, fn MessageHandler) MessageHandler {
    return MessageHandlerFunc(func(ctx context.Context, delivery amqp.Delivery) error {
        defer runtime.RecoverWithPolicyAndContext(ctx, logger,
            component, "handle-message", runtime.KeepRunning)
        return fn.Handle(ctx, delivery)
    })
}
```

Two-level protection: the outer consumer loop uses `SafeGoWithContextAndComponent`
(loop-level recovery); the inner wrapper uses `RecoverWithPolicyAndContext`
(message-level recovery). A panic on a single message is isolated to that message; the
loop keeps pulling deliveries.

### 3.8 Error reporter integration (Sentry-style)

Plug an external error tracker into the trident pipeline. The reporter is called
**after** the log/metric/span emission, so telemetry is never gated on reporter
reachability.

```go
type sentryReporter struct{ client *sentry.Client }

func (s *sentryReporter) CaptureException(ctx context.Context, err error, tags map[string]string) {
    hub := sentry.GetHubFromContext(ctx)
    if hub == nil {
        hub = sentry.CurrentHub()
    }
    hub.WithScope(func(scope *sentry.Scope) {
        for k, v := range tags {
            scope.SetTag(k, v)
        }
        hub.CaptureException(err)
    })
}

// at bootstrap, after InitPanicMetrics and SetProductionMode:
runtime.SetErrorReporter(&sentryReporter{client: sentryClient})
```

The `tags` map includes `component`, `operation`, and `goroutine_name` — grouping rules
in Sentry can fingerprint on these to avoid one-panic-per-unique-stack noise.

---

## 4. The Observability Trident

Every recovered panic produces four emissions:

```
panic happens
    ↓
runtime.SafeGo* or runtime.RecoverWith* catches it
    ↓
    ├─→ 1. Structured log  (via log.Logger)
    ├─→ 2. OTel span event (on the active span)
    ├─→ 3. Metric           (panic_recovered_total counter)
    └─→ 4. ErrorReporter    (if SetErrorReporter was called)
```

### Layer 1: Structured Log

Emitted via the `log.Logger` passed to `SafeGo*` or `RecoverWith*`. Log level is
`ERROR`. Fields:

| Field             | Value                                                                    |
| ----------------- | ------------------------------------------------------------------------ |
| `component`       | The component label (e.g., `"outbound-webhook-service"`)                 |
| `goroutine_name`  | Or `operation` for defer-form (e.g., `"amqp-consumer-loop"`)             |
| `recovered_value` | Stringified panic value (redacted to placeholder in production mode)     |
| `stack`           | Full stack trace (truncated to 4096 bytes in production mode)            |
| `trace_id`        | From ctx when `SafeGoWithContext*` / `RecoverWithPolicyAndContext` used  |
| `span_id`         | Same                                                                     |

### Layer 2: OTel Span Event

Emitted on the **active span** in the ctx passed to the recovery function. Event name:
`panic.recovered`. Attributes:

| Attribute                   | Value                                                                   |
| --------------------------- | ----------------------------------------------------------------------- |
| `panic.component`           | Component label                                                         |
| `panic.operation`           | Operation / goroutine name                                              |
| `panic.recovered_value`     | Stringified value (redacted in production mode)                         |
| `panic.stack`               | Stack (truncated in production mode)                                    |

Side effect: the span's status is set to `Error`. This means the trace view in your
observability backend shows the request's span as failed, not misleadingly green.

### Layer 3: Metric

Counter: `panic_recovered_total`.

Labels:

| Label          | Value                          |
| -------------- | ------------------------------ |
| `component`    | Component label                |
| `goroutine`    | Goroutine name / operation     |

Incremented by 1 on each recovery. **Requires `InitPanicMetrics` to have been called at
bootstrap** — otherwise the counter is never registered and the increment is a no-op.

### Layer 4: ErrorReporter Callback

Only fires if `SetErrorReporter` was called with a non-nil reporter. Signature:

```go
reporter.CaptureException(ctx, err, tags)
```

`err` is synthesized from the panic value (`fmt.Errorf("panic recovered: %v", r)` in
non-production mode; a redacted placeholder in production mode). `tags` includes
`component`, `operation`, and `goroutine_name`.

### Observing in Dashboards

| Use Case                                  | Query                                                                         |
| ----------------------------------------- | ----------------------------------------------------------------------------- |
| Recovered panics per service per minute   | `sum(rate(panic_recovered_total[1m])) by (component)`                         |
| Top panicking goroutines                  | `topk(10, sum(rate(panic_recovered_total[5m])) by (component, goroutine))`    |
| Traces containing panics                  | `event.name = "panic.recovered"` in Tempo/Jaeger/Datadog APM                  |
| Alert on regressions                      | `sum(rate(panic_recovered_total[5m])) > 0.1` (>1 recovery per 10 min average) |

★ Insight ─────────────────────────────────────
The trident's point is **defense in depth**. Logs can be dropped by an overwhelmed
aggregator; span events can be dropped by a sampling decision; metrics can be missed if
the dashboard query is wrong. By emitting all three, at least one signal reaches the
operator. Add the optional ErrorReporter callback and you have four independent
channels — the probability of a panic going unnoticed drops toward zero. This is the
whole reason `commons/runtime` exists.
─────────────────────────────────────────────────

---

## 5. Testing Patterns

Tests that prove the trident actually fires. All patterns use a deliberate panic
inside a wrapped goroutine and assert on the observable side effects.

### 5.1 Counter incremented

Inject an in-memory `MetricsFactory`, trigger a panic in a `SafeGo` goroutine, read the
counter.

```go
func TestSafeGo_PanicIncrementsMetric(t *testing.T) {
    factory := metricstesting.NewInMemoryFactory()
    logger := logtesting.NewBuffered()
    runtime.InitPanicMetrics(factory, logger)

    done := make(chan struct{})
    runtime.SafeGo(logger, "test-goroutine", runtime.KeepRunning, func() {
        defer close(done)
        panic("boom")
    })
    <-done

    // allow async metric emission to flush
    time.Sleep(10 * time.Millisecond)

    got := factory.CounterValue("panic_recovered_total",
        map[string]string{"goroutine": "test-goroutine"})
    if got != 1 {
        t.Fatalf("panic_recovered_total = %d, want 1", got)
    }
}
```

### 5.2 Span event emitted

Use an in-memory OTel exporter (`tracetest.NewInMemoryExporter`), start a parent span,
trigger a panic inside `runtime.SafeGoWithContext(ctx, ...)`, call `span.End()`, and
scan `exporter.GetSpans()` for an event named `panic.recovered`. Assert its attributes
include the expected `panic.component` and `panic.operation`. The span's status MUST be
`Error` — assert that too.

### 5.3 Structured log emitted

Use a buffered logger that captures entries. Wrap a closure with
`defer runtime.RecoverWithPolicyAndContext(ctx, logger, component, op, KeepRunning)`,
panic inside it, then assert the captured entries contain an Error-level entry with
`component` and `operation` fields matching the values passed to the defer.

### 5.4 ErrorReporter called

Implement a test reporter that records calls, trigger a panic, assert the reporter's
`CaptureException` fired with the expected tags (`component`, `operation`,
`goroutine_name`). Use `t.Cleanup(func() { runtime.SetErrorReporter(nil) })` to avoid
leaking the reporter across tests. The structure mirrors 5.1–5.3: inject a fake,
trigger, assert.

### 5.5 Leak detection alongside

`commons/runtime` does not leak goroutines by itself, but the code that uses it might.
Pair panic-recovery tests with `goleak` to catch goroutines that should have exited but
didn't. See `ring:dev-goroutine-leak-testing` skill for the full pattern.

```go
func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m)
}
```

This catches the case where a `SafeGo` goroutine panics, recovers, but was supposed to
signal a waitgroup that now leaks because `defer wg.Done()` was inside the recovered
block rather than outside it.

---

## 6. Anti-Pattern Catalog

Six ways to get this wrong. Each has a BEFORE example and a consequence narrative.

### 6.1 Naked goroutine

```go
go func() {
    for msg := range deliveries {
        process(msg)
    }
}()
```

**Consequence:** `process` panics, the goroutine dies, consumption of `deliveries`
stops forever, the `for range` loop is now an orphan. Nothing surfaces in logs (no
panic recovery = no log). Nothing surfaces in metrics. The service reports healthy to
its health check because the HTTP server is still up. The queue backs up. An operator
eventually notices the message backlog, investigates, and finds the goroutine never
existed in traces because there was no span on it.

### 6.2 `defer recover()` without trident

```go
defer func() {
    if r := recover(); r != nil {
        // ignored
    }
}()
```

**Consequence:** Panic recovery works — the function returns normally. But nothing
emits. No log, no metric, no span event. The panic is invisible. A latent bug (nil
dereference, divide-by-zero, map concurrent write) runs in production for months
before someone notices the symptom (corrupted data, missed transactions) and traces it
back. The recovery itself is what made the bug hard to find.

### 6.3 Missing `InitPanicMetrics`

```go
// bootstrap uses SafeGo but forgot to call InitPanicMetrics
runtime.SafeGo(logger, "worker", runtime.KeepRunning, workerFn)
```

**Consequence:** Logs fire, span events fire, ErrorReporter fires — but the
`panic_recovered_total` counter never registers, so alerts based on metrics never
trigger. Dashboards show zero panics. Operators trust the dashboards. The service
quietly accumulates recovered panics that no one sees until a different signal (slow
latency, customer complaint) prompts investigation.

### 6.4 `SetProductionMode(false)` in production

```go
// production bootstrap (misconfigured)
runtime.SetProductionMode(false)
```

**Consequence:** Panic values are emitted verbatim. A panic triggered by a malformed
request body that contains a credit card number causes the credit card number to land
in log aggregators (retained for 90 days), span attributes (kept by trace backend),
and ErrorReporter payloads (sent to a third-party service). Compliance incident.
Stack traces are not truncated either — 20 KB stack traces per recovery bloat the OTel
exporter and may be rejected by the collector.

### 6.5 `KeepRunning` for bootstrap invariants

```go
runtime.SafeGoWithContextAndComponent(ctx, logger, "bootstrap", "verify-schema",
    runtime.KeepRunning, func(ctx context.Context) {
        if !schemaMatches(ctx) {
            panic("schema mismatch")
        }
    })
```

**Consequence:** Schema mismatch detected, goroutine panics, recovery logs the panic,
goroutine returns. Service continues running. Every subsequent query operates on a
schema it doesn't understand. Data corruption accumulates. The log entry that would
have warned the operator is buried under request-log volume. A log-based alert might
catch it; a metric-based alert on `panic_recovered_total{component="bootstrap"}` is
more reliable. Either way, `CrashProcess` was the right choice — k8s restarts the pod,
the startup probe fails, and the operator is notified within minutes.

### 6.6 `CrashProcess` for request handlers

```go
app.Use(func(c *fiber.Ctx) error {
    defer runtime.RecoverWithPolicyAndContext(c.UserContext(), logger,
        "api", c.Path(), runtime.CrashProcess)
    return c.Next()
})
```

**Consequence:** One malformed request triggers a panic in a handler. Recovery fires,
logs, emits trident, then re-panics. The process dies. The k8s pod restarts (~30s
downtime). The load balancer marks the replica unhealthy and drains traffic to the
remaining replicas. If the attacker (or buggy client) sends the same malformed request
in a loop, they DoS the entire fleet replica-by-replica. Request handlers must use
`KeepRunning`; the cost of one failed request is strictly bounded, the cost of a
cascading restart is not.

---

## 7. Bootstrap Order

Where `commons/runtime` setup fits in service initialization.

**Requirements:**

- **AFTER** logger is constructed (runtime emits structured logs through it)
- **AFTER** telemetry is initialized (runtime registers metrics on the factory; span
  events need a TracerProvider)
- **BEFORE** any `SafeGo*` or `RecoverWith*` launches (obvious — metrics must be
  registered before increments fire)

**Canonical sequence:**

```
1. Logger                (zap.New)
2. Telemetry             (opentelemetry.NewTelemetry + ApplyGlobals)
3. runtime.InitPanicMetrics(tl.MetricsFactory, logger)
4. runtime.SetProductionMode(cfg.Env == "production")
5. runtime.SetErrorReporter(reporter)     // optional
6. assert.InitAssertionMetrics(...)       // independent, same section
7. DB connections, HTTP app, etc.
8. SafeGo launches for consumers / workers
```

For the full snippet with all surrounding init, see
[ring:using-lib-commons Section 2 "Common Initialization Pattern"](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/using-lib-commons/SKILL.md).
The runtime-specific lines are steps 3–5 above.

---

## 8. Cross-Cutting Patterns

### 8.1 Nil-safety of `logger`

If `logger` passed to `SafeGo*` or `RecoverWith*` is nil, the goroutine still runs and
recovery still fires, but the log emission is skipped. The **metric still fires** if
`InitPanicMetrics` was called at bootstrap. The **span event still fires** if a
tracer is globally registered. Nil-logger is therefore a degraded mode, not a crash.

This is intentional — it lets bootstrap code call `SafeGo` for very-early goroutines
before the logger is fully wired, without crashing on the very line that's supposed to
catch crashes. In production you should never rely on this; pass a real logger.

### 8.2 Stack-trace truncation in production mode

When `SetProductionMode(true)` is in effect, stack traces in logs, span events, and
ErrorReporter payloads are capped at 4096 bytes. This is a deliberate trade-off:

- **For**: prevents span-attribute bloat (OTel collectors reject events over a certain
  size), prevents log ingest cost explosion on panic storms, limits PII surface area
  (less stack = less chance of in-memory secrets leaking)
- **Against**: deep stacks get truncated; sometimes the root cause is at frame 40 of a
  50-frame stack

The default is correct for production. For development/staging, call
`SetProductionMode(false)` to get full stacks.

### 8.3 Context propagation through recovery

When you use `SafeGoWithContext` or `SafeGoWithContextAndComponent`, the ctx passed
into `fn` is the same ctx carried through recovery. If the goroutine panics, the
`panic.recovered` span event lands on the span attached to that ctx (the parent's
span, by default, since no new span was started inside the wrapper).

`RecoverWithPolicyAndContext` behaves the same way — the ctx argument is the span
anchor for the recovery event.

If you want the recovery event to land on a **child** span (e.g., you started a span
for the goroutine's unit of work), start that span inside `fn` and the recovery will
still land on the active span at panic time.

### 8.4 Interaction with `commons/assert`

Assertions in `commons/assert` return errors — they do not panic. Therefore:

- An assertion failure does **not** trigger runtime recovery.
- The observability of assertions is orthogonal: assertions fire their own trident
  (log + span event `assertion.failed` + `assertion_failed_total` metric).
- This separation is deliberate. Assertions are recoverable (caller decides what to
  do with the returned error); panics are not (the caller's stack is already unwinding).

Both packages share the trident idea, but they operate on different signals. A well-
instrumented service emits both `assertion_failed_total` and `panic_recovered_total`,
and dashboards track them as distinct reliability indicators.

See [ring:using-assert](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/using-assert/SKILL.md)
for the assertion side of the story.

★ Insight ─────────────────────────────────────
Together, `commons/runtime` and `commons/assert` cover both invisible-failure modes in
Go services: panics (the goroutine dies without emission) and silent invariant
violations (the function returns an error that no one aggregates). Assertion failures
are expected-but-suppressed-elsewhere bugs; panic recoveries are unexpected bugs.
Tracking both as separate metrics lets you distinguish "we're being defensive
correctly" from "we have a latent bug". A spike in assertions often predicts a spike
in recovered panics because the underlying code is drifting from its invariants.
─────────────────────────────────────────────────

---

## 9. Breaking Changes

No API-breaking changes in `commons/runtime` across v4.2.0 → v5.x. The Go module
major-version bump v4 → v5 applies — imports change from
`github.com/LerianStudio/lib-commons/v4/commons/runtime` to
`github.com/LerianStudio/lib-commons/v5/commons/runtime`, but function signatures,
constants, and interface definitions are source-compatible.

For the module-path migration (v4 → v5), see
[ring:using-lib-commons Section 15](https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/using-lib-commons/SKILL.md).

New capabilities added in v5.0.x that Phase 2 of a sweep will surface if the target is
still on v4:

| Version | Addition                                                                      |
| ------- | ----------------------------------------------------------------------------- |
| v5.0.0  | `HandlePanicValue` — structured framework-recovery handler (Angle 5 recommends it) |
| v5.0.0  | Refined `SetProductionMode` behavior — 4096-byte stack cap formalized         |
| v5.0.x  | Documentation and test hardening (no new symbols)                             |

---

## 10. Cross-References

Explicit pointers rather than duplicated content:

| Topic                                                    | Go To                                                                                       |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Full lib-commons package catalog                         | `ring:using-lib-commons` Section 1 "Package Catalog"                                        |
| Full bootstrap sequence snippet (all packages wired)     | `ring:using-lib-commons` Section 2 "Common Initialization Pattern"                          |
| Observability overview (logger, tracing, metrics basics) | `ring:using-lib-commons` Section 5 "Observability"                                          |
| Single-angle panic-handling sweep (higher level)         | `ring:using-lib-commons` Angle 15 "Panic handling DIY"                                      |
| The other half of the invisible-failure story            | `ring:using-assert` (assertion failures, not panics)                                        |
| Goroutine leak detection (companion to panic testing)    | `ring:dev-goroutine-leak-testing`                                                           |
| Overall development cycle that consumes sweep tasks      | `ring:dev-cycle`                                                                            |
| Generic codebase refactoring sweep                       | `ring:dev-refactor`                                                                         |
| Standards for Go code                                    | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md` |

MUST NOT duplicate content from the sources above. When the reader needs that content,
link to it.

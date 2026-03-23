<!-- Copyright 2025 Lerian Studio. -->
---
name: "ring:systemplane-migration"
version: "2.0.0"
type: skill
description: >
  Gate-based systemplane migration orchestrator. Migrates Lerian Go services from
  .env/YAML-based configuration to the systemplane — a database-backed, hot-reloadable
  runtime configuration and settings management plane with full audit history, optimistic
  concurrency, change feeds, component-granular bundle rebuilds, and atomic infrastructure
  replacement. Requires lib-commons v4.3.0+.
trigger_when:
  - User requests systemplane migration/adoption
  - Task mentions runtime configuration, hot-reload, config management
  - Service needs database-backed configuration with audit trail
  - BundleFactory or Reconciler development
prerequisites:
  - Go project
  - lib-commons/v4 dependency (v4.3.0+ required; upgrade first if older)
  - PostgreSQL or MongoDB backend available
NOT_skip_when:
  - Service already has systemplane code (verify compliance, do not skip)
  - "It looks like systemplane is already set up" (existence ≠ compliance)
sequence:
  after: ["ring:dev-cycle"]
input:
  type: object
  properties:
    execution_mode:
      type: string
      enum: ["FULL", "SCOPED"]
      description: "FULL = fresh migration. SCOPED = compliance audit of existing."
    detected_backend:
      type: string
      enum: ["postgres", "mongodb"]
    detected_dependencies:
      type: array
      items: { type: string }
      description: "Infrastructure detected: postgres, mongodb, redis, rabbitmq, s3"
    service_has_workers:
      type: boolean
    existing_systemplane:
      type: boolean
output:
  type: object
  properties:
    gates_completed:
      type: array
      items: { type: string }
    compliance_status:
      type: string
      enum: ["COMPLIANT", "NON-COMPLIANT", "NEW"]
    key_count:
      type: integer
    files_created:
      type: array
      items: { type: string }
---

# Systemplane Migration Orchestrator

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Implement systemplane code following the patterns in this document |
| **ring:codebase-explorer** | Analyze the codebase for configuration patterns (Gate 1) |
| **ring:visual-explainer** | Generate implementation preview HTML (Gate 1.5) |
| **7 reviewers** | Review at Gate 8 |

**CANNOT change scope:** the skill defines WHAT to implement. The agent implements HOW.

**FORBIDDEN: Orchestrator MUST NOT use Edit, Write, or Bash tools to modify source code files.**
All code changes MUST go through `Task(subagent_type="ring:backend-engineer-golang")`.
The orchestrator only verifies outputs (grep, go build, go test) — MUST NOT write implementation code.

</cannot_skip>

---

## Architecture Overview

The systemplane replaces traditional env-var-only / YAML-based configuration with a
three-tier architecture:

```
┌─ TIER 1: Bootstrap-Only ──────────────────────────────────────────┐
│  Env vars read ONCE at startup. Immutable for process lifetime.   │
│  Examples: SERVER_ADDRESS, AUTH_ENABLED, OTEL_* (telemetry)       │
│  Stored in: BootstrapOnlyConfig struct (frozen at init)           │
└───────────────────────────────────────────────────────────────────┘

┌─ TIER 2: Runtime-Managed (Hot-Reload) ────────────────────────────┐
│  Stored in database (PostgreSQL or MongoDB).                      │
│  Changed via PATCH /v1/system/configs or /v1/system/settings.     │
│  Propagation: ChangeFeed → Supervisor → Snapshot → Bundle/Reconcile│
│  Examples: rate limits, worker intervals, DB pool sizes, CORS     │
└───────────────────────────────────────────────────────────────────┘

┌─ TIER 3: Live-Read (Zero-Cost Per-Request) ───────────────────────┐
│  Read directly from Supervisor.Snapshot() on every request.       │
│  No rebuild, no reconciler, no locking.                           │
│  Examples: rate_limit.max, health_check_timeout_sec               │
└───────────────────────────────────────────────────────────────────┘
```

### Data Flow: Startup → Hot-Reload → Shutdown

```
STARTUP:
  ENV VARS → defaultConfig() → loadConfigFromEnv() → *Config → ConfigManager
  InitSystemplane():
    1. ExtractBootstrapOnlyConfig(cfg)         → BootstrapOnlyConfig (immutable)
    2. LoadSystemplaneBackendConfig(cfg)        → BootstrapConfig (PG/Mongo DSN)
    3. builtin.NewBackendFromConfig(ctx, cfg)   → Store + History + ChangeFeed
    4. registry.New() + Register{Service}Keys() → Registry (100+ key definitions)
    5. configureBackendWithRegistry()            → pass secret keys + apply behaviors
    6. NewSnapshotBuilder(registry, store)       → SnapshotBuilder
    7. New{Service}BundleFactory(bootstrapCfg)   → BundleFactory (full + incremental)
    8. seedStoreForInitialReload()               → Env overrides → Store
    9. buildReconcilers()                        → [HTTP, Publisher, Worker] (phased)
   10. NewSupervisor → Reload("initial-bootstrap") → First bundle
   11. NewManager(ManagerConfig{                  → HTTP API handler
           ConfigWriteValidator: productionGuards,
           StateSync: configManagerSync,
       })
  StartChangeFeed() → DebouncedFeed(200ms) → goroutine: subscribe(store changes)
  MountSystemplaneAPI() → 9 endpoints on /v1/system/*

HOT-RELOAD (on API PATCH or ChangeFeed signal):
  Signal → Supervisor.Reload(ctx, reason) →
    1. SnapshotBuilder.BuildFull() → new Snapshot (defaults + store overrides)
    2. BundleFactory.BuildIncremental(snap, prev, prevSnap) →
       a) Diff changed keys via keyComponentMap (postgres/redis/rabbitmq/s3/http/logger)
       b) Rebuild ONLY changed components
       c) Reuse unchanged components from previous bundle (pointer transfer)
       d) Falls back to full Build() when all components are affected
    3. Reconcilers run IN PHASE ORDER:
       a) PhaseStateSync:    (reserved — no current reconcilers)
       b) PhaseValidation:   HTTPPolicy, Publisher
       c) PhaseSideEffect:   Worker → WorkerManager.ApplyConfig()
    4. On success: atomic swap — snapshot.Store() + bundle.Store()
    5. AdoptResourcesFrom(previous) → nil-out transferred pointers
    6. Observer callback → bundleState.Update() + ConfigManager.UpdateFromSystemplane()
       + SwappableLogger.Swap() + SwapRuntimePublishers()
    7. previous.Close() → only tears down REPLACED components

SHUTDOWN:
  1. ConfigManager.Stop()         (prevent mutations)
  2. cancelChangeFeed()           (stop reload triggers)
  3. Supervisor.Stop()            (stop supervisory loop + close bundle)
  4. Backend.Close()              (close store connection)
  5. WorkerManager.Stop()         (stop all workers)
```

### The Three Configuration Authorities

| Phase | Authority | Scope | Mutability |
|-------|-----------|-------|------------|
| **Bootstrap** | Env vars → `defaultConfig()` + `loadConfigFromEnv()` | Server address, TLS, auth, telemetry | Immutable after startup |
| **Runtime** | Systemplane Store + Supervisor | Rate limits, workers, timeouts, DB pools, CORS | Hot-reloadable via API |
| **Legacy bridge** | `ConfigManager.Get()` | Backward-compat for existing code | Updated by StateSync callback + observer |

**Single source of truth**: `{service}KeyDefs()` is THE canonical source of all
default values. The `defaultConfig()` function derives its values from KeyDefs
via `defaultSnapshotFromKeyDefs()` → `configFromSnapshot()`. No manual sync
required between defaults, key definitions, or struct tags.

**Component-granular awareness**: Every key's `Component` field (e.g., `"postgres"`,
`"redis"`, `"rabbitmq"`, `"s3"`, `"http"`, `"logger"`, or `ComponentNone`) enables
the `IncrementalBundleFactory` to rebuild only the affected infrastructure component
when that key changes, instead of tearing down and rebuilding everything.

---

## Canonical Import Paths

The systemplane is a shared library in lib-commons (since v4.3.0). All services
import it via:

```go
import (
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/ports"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/registry"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/service"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/bootstrap"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/bootstrap/builtin"
    "github.com/LerianStudio/lib-commons/v4/commons/systemplane/adapters/changefeed"
    fiberhttp "github.com/LerianStudio/lib-commons/v4/commons/systemplane/adapters/http/fiber"

    // Swagger spec (for consuming app integration)
    systemswagger "github.com/LerianStudio/lib-commons/v4/commons/systemplane/swagger"
)
```

Requires `lib-commons v4.3.0+` in your `go.mod`.

**⛔ HARD GATE:** Agent must not use v2 or v3 import paths or invent sub-package paths. If any tool truncates output, this table is the authoritative reference.

---

## Severity Calibration

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Data loss, runtime panic, silent config corruption | Bundle not closed on shutdown (resource leak), snapshot reads nil (panic), ChangeFeed not started (hot-reload broken) |
| **HIGH** | Missing integration, broken hot-reload path | Keys registered but no BundleFactory, no HTTP Mount, no StateSync callback |
| **MEDIUM** | Incomplete but functional | Missing validators on some keys, incomplete secret redaction, no swagger merge |
| **LOW** | Polish and optimization | Missing config-map.example, incomplete descriptions, suboptimal component grouping |

MUST report all severities. CRITICAL: STOP immediately. HIGH: Fix before gate pass. MEDIUM: Fix in iteration. LOW: Document.

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "Keys are registered, migration is done" | SCOPE_REDUCTION | "Key registration is Gate 2 of 10. Without BundleFactory + Wiring + HTTP Mount, keys are metadata — nothing reads them at runtime. MUST complete ALL gates." |
| "We can wire it later" | SCOPE_REDUCTION | "Gate 7 is where the system comes alive. Without it, systemplane is dead code. Gate 7 is NEVER skippable." |
| "Swagger integration is cosmetic" | QUALITY_BYPASS | "Operators need API discoverability. Without swagger.MergeInto(), 9 endpoints are invisible in Swagger UI. MUST implement." |
| "Config bridge is backward compat only" | SCOPE_REDUCTION | "Existing code reads Config struct. Without StateSync, it reads stale bootstrap values forever. MUST implement Gate 6." |
| "Reconcilers are optional" | SCOPE_REDUCTION | "Without reconcilers, workers and HTTP policies ignore config changes. Hot-reload is partial." |
| "The service already has systemplane" | COMPLIANCE_BYPASS | "Existence ≠ compliance. MUST run compliance audit. If it doesn't match canonical patterns exactly, it is non-compliant." |
| "Skip code review, we tested it" | QUALITY_BYPASS | "MANDATORY: 7 reviewers. One wiring mistake = silent config corruption or resource leak." |
| "Agent says out of scope" | AUTHORITY_OVERRIDE | "Skill defines scope, not agent. Re-dispatch with gate context." |
| "ChangeFeed can be added later" | SCOPE_REDUCTION | "Without ChangeFeed, hot-reload is broken. Config changes in DB are invisible to the service. MUST start DebouncedFeed." |
| "Active bundle state is internal detail" | SCOPE_REDUCTION | "Without thread-safe accessor, request handlers cannot read live config. Race conditions. MUST implement active_bundle_state.go." |

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection + Prerequisite Audit | Always | Orchestrator |
| 1 | Codebase Analysis (Config Focus) | Always | ring:codebase-explorer |
| 1.5 | Implementation Preview | Always | Orchestrator (ring:visual-explainer) |
| 2 | Key Definitions + Registry | Always | ring:backend-engineer-golang |
| 3 | Bundle + BundleFactory | Always | ring:backend-engineer-golang |
| 4 | Reconcilers | Conditional (skip if no workers AND no RMQ AND no HTTP policy changes) | ring:backend-engineer-golang |
| 5 | Identity + Authorization | Always | ring:backend-engineer-golang |
| 6 | Config Manager Bridge | Always | ring:backend-engineer-golang |
| 7 | Wiring + HTTP Mount + Swagger + ChangeFeed | Always ⛔ NEVER SKIPPABLE | ring:backend-engineer-golang |
| 8 | Code Review | Always | 7 parallel reviewers |
| 9 | User Validation | Always | User |
| 10 | Activation Guide | Always | Orchestrator |

MUST execute gates sequentially. CANNOT skip or reorder.

### Gate Execution Rules

⛔ **HARD GATES — CANNOT be overridden:**
- All gates must execute in order (0→1→1.5→2→3→4→5→6→7→8→9→10)
- Gates execute with explicit dependencies — no gate can start until its predecessor completes
- Existence ≠ compliance: existing systemplane code triggers compliance audit, NOT a skip
- A gate can only be marked SKIP when ALL its compliance checks pass with evidence
- Gate 7 (Wiring) is NEVER skippable — it is the most critical gate

<cannot_skip>

### HARD GATE: Existence ≠ Compliance

**"The service already has systemplane code" is NOT a reason to skip any gate.**

MUST replace existing systemplane code that does not follow the canonical patterns — it is **non-compliant**. The only valid reason to skip a gate is when the existing implementation has been **verified** to match the exact patterns defined in this skill document.

**Compliance verification requires EVIDENCE, not assumption.** The Gate 0 Phase 2 compliance audit (S1-S8 grep checks) verifies each component against canonical patterns.

**If ANY audit check is NON-COMPLIANT → the corresponding gate MUST execute to fix it. CANNOT skip.**

</cannot_skip>

---

## Gate 0: Stack Detection + Prerequisite Audit

**Orchestrator executes directly. No agent dispatch.**

**This gate has THREE phases: detection, compliance audit, and non-canonical pattern detection.**

### Phase 1: Stack Detection

```text
DETECT (run in parallel):

1. lib-commons version:
   grep "lib-commons" go.mod
   (require v4.3.0+ — if older, MUST upgrade before proceeding)

2. PostgreSQL:
   grep -rn "postgresql\|pgx\|squirrel" internal/ go.mod

3. MongoDB:
   grep -rn "mongodb\|mongo" internal/ go.mod

4. Redis:
   grep -rn "redis\|valkey" internal/ go.mod

5. RabbitMQ:
   grep -rn "rabbitmq\|amqp" internal/ go.mod

6. S3/Object Storage:
   grep -rn "s3\|ObjectStorage\|PutObject\|GetObject\|Upload.*storage\|Download.*storage" internal/ pkg/ go.mod

7. Background workers:
   grep -rn "ticker\|time.NewTicker\|cron\|worker\|scheduler" internal/ --include="*.go" | grep -v _test.go

8. Existing systemplane code:
   - Imports:       grep -rn "systemplane" internal/ go.mod
   - BundleFactory: grep -rn "BundleFactory\|IncrementalBundleFactory" internal/ --include="*.go"
   - Supervisor:    grep -rn "service.NewSupervisor\|Supervisor" internal/ --include="*.go" | grep systemplane
   - Keys:          grep -rn "Register.*Keys\|KeyDefs()" internal/ --include="*.go"
   - HTTP Mount:    grep -rn "handler.Mount\|fiberhttp.NewHandler" internal/ --include="*.go"

9. Current config pattern:
   - Struct:     grep -rn "type Config struct" internal/ --include="*.go"
   - Env tags:   grep -rn "envDefault:" internal/ --include="*.go" | sort
   - Env reads:  grep -rn "os.Getenv\|viper\.\|envconfig" internal/ --include="*.go" | grep -v _test.go
   - YAML files: find . -name '.env*' -o -name '*.yaml' -o -name '*.yml' | grep -i config
```

**Output format for stack detection:**

```text
STACK DETECTION RESULTS:
| Component | Detected | Evidence |
|-----------|----------|----------|
| lib-commons v4.3.0+ | YES/NO | {go.mod version} |
| PostgreSQL | YES/NO | {file:line matches} |
| MongoDB | YES/NO | {file:line matches} |
| Redis | YES/NO | {file:line matches} |
| RabbitMQ | YES/NO | {file:line matches} |
| S3/Object Storage | YES/NO | {file:line matches} |
| Background workers | YES/NO | {file:line matches} |
| Existing systemplane | YES/NO | {file:line matches} |
| Config pattern | envDefault/viper/os.Getenv | {file:line matches} |
```

### Phase 2: Compliance Audit (MANDATORY if any existing systemplane code detected)

If Phase 1 step 8 detects any existing systemplane code, MUST run a compliance audit. MUST replace existing code that does not match canonical patterns — it is not "partially done", it is **wrong**.

```text
AUDIT (run in parallel — only if step 8 found existing systemplane code):

S1. Key Registry compliance:
    grep -rn "Register.*Keys\|KeyDefs()" internal/ --include="*.go"
    (no match = NON-COMPLIANT → Gate 2 MUST fix)

S2. BundleFactory compliance:
    grep -rn "IncrementalBundleFactory\|BundleFactory" internal/ --include="*.go"
    (no IncrementalBundleFactory = NON-COMPLIANT → Gate 3 MUST fix)

S3. AdoptResources compliance:
    grep -rn "AdoptResourcesFrom" internal/ --include="*.go"
    (no match but BundleFactory exists = NON-COMPLIANT → Gate 3 MUST fix)

S4. Reconciler compliance:
    grep -rn "BundleReconciler\|Reconcile.*context" internal/ --include="*.go" | grep -v _test.go
    (expected reconcilers missing = NON-COMPLIANT → Gate 4 MUST fix)

S5. Identity/Authorization compliance:
    grep -rn "IdentityResolver\|Authorizer" internal/ --include="*.go"
    (no match = NON-COMPLIANT → Gate 5 MUST fix)

S6. Config Bridge compliance:
    grep -rn "StateSync\|config_manager_systemplane\|configFromSnapshot" internal/ --include="*.go"
    (no StateSync callback or config hydration = NON-COMPLIANT → Gate 6 MUST fix)

S7. HTTP Mount compliance:
    grep -rn "handler.Mount\|fiberhttp.NewHandler" internal/ --include="*.go"
    (no match = NON-COMPLIANT → Gate 7 MUST fix)
    Also check all 9 routes are accessible:
    grep -rn "/v1/system" internal/ --include="*.go"

S8. Swagger compliance:
    grep -rn "swagger.MergeInto\|systemswagger" internal/ --include="*.go"
    (no match = NON-COMPLIANT → Gate 7 MUST fix)
```

**Output format for compliance audit:**

```text
COMPLIANCE AUDIT RESULTS:
| Check | Component | Status | Evidence | Gate Action |
|-------|-----------|--------|----------|-------------|
| S1 | Key Registry | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 2: SKIP / MUST FIX |
| S2 | BundleFactory | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 3: SKIP / MUST FIX |
| S3 | AdoptResources | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 3: SKIP / MUST FIX |
| S4 | Reconcilers | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 4: SKIP / MUST FIX |
| S5 | Identity/Auth | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 5: SKIP / MUST FIX |
| S6 | Config Bridge | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 6: SKIP / MUST FIX |
| S7 | HTTP Mount | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 7: SKIP / MUST FIX |
| S8 | Swagger | COMPLIANT / NON-COMPLIANT | {grep results} | Gate 7: SKIP / MUST FIX |
```

**⛔ HARD GATE: A gate can only be marked as SKIP when ALL its compliance checks are COMPLIANT with evidence. One NON-COMPLIANT row → gate MUST execute.**

### Phase 3: Non-Canonical Pattern Detection (MANDATORY)

MUST scan for custom config management outside the systemplane canonical patterns:

```text
DETECT non-canonical config patterns:

N1. Custom config hot-reload:
    grep -rln "hot.reload\|config.watch\|config.reload\|ConfigReload" internal/config/ pkg/config/ internal/bootstrap/ --include="*.go" 2>/dev/null
    (any match = NON-CANONICAL → MUST be removed and replaced with systemplane ChangeFeed)

N2. Custom file watchers:
    grep -rn "fsnotify\|viper.WatchConfig\|inotify\|file.watch" internal/ pkg/ --include="*.go"
    (any match = NON-CANONICAL → MUST be removed; systemplane uses database change feed)

N3. Custom change notification channels:
    grep -rn "chan.*config\|config.*chan\|ConfigChange\|configChanged" internal/ pkg/ --include="*.go" | grep -v systemplane
    (any match outside systemplane = NON-CANONICAL → MUST be replaced with systemplane ChangeFeed)
```

**If non-canonical files are found:** report them in the compliance audit as `NON-CANONICAL FILES DETECTED`. The implementing agent MUST remove these files and replace their functionality with systemplane during the appropriate gate.

**Store detection results:**

```json
{
  "skill": "ring:systemplane-migration",
  "gate": "0",
  "detection": {
    "lib_commons_version": "v4.3.2",
    "backend": "postgres",
    "dependencies": ["postgres", "redis", "rabbitmq"],
    "has_workers": true,
    "existing_systemplane": false,
    "config_pattern": "envDefault",
    "config_struct_location": "internal/bootstrap/config.go:15"
  },
  "compliance": {
    "status": "NEW",
    "checks": {}
  },
  "non_canonical": []
}
```

MUST confirm: user explicitly approves detection results before proceeding.

---

## Gate 1: Codebase Analysis (Config Focus)

**Always executes. This gate builds the configuration inventory for all subsequent gates.**

**Dispatch `ring:codebase-explorer` with systemplane-focused context:**

> TASK: Analyze this codebase exclusively under the systemplane migration perspective.
> DETECTED STACK: {databases and infrastructure from Gate 0}
>
> FOCUS AREAS (explore ONLY these — ignore everything else):
>
> 1. **Config struct location and fields**: Find the main Config struct, all env tags (`envDefault:`), default values. List every field with its current type, default, and env var name. Include nested structs (e.g., `Config.Postgres.Host`).
>
> 2. **Environment variable reads**: All `os.Getenv`, `envconfig`, `viper` usage. Include those outside the Config struct (ad-hoc reads in business logic).
>
> 3. **Infrastructure client creation**: How postgres, redis, rabbitmq, mongo, S3 clients are created. File:line for each constructor call. Connection strings, pool sizes, timeouts used. These become Bundle components.
>
> 4. **Background workers**: Ticker-based, cron-based, goroutine workers that need reconciliation. File:line for each worker start. Which config fields control their behavior (intervals, enable/disable, batch sizes).
>
> 5. **HTTP server configuration**: Listen address, TLS, CORS, rate limits, timeouts, body limits. Where these are read and applied. These become HTTP policy keys.
>
> 6. **Authentication/authorization**: JWT parsing, middleware, permission model. Where user ID and tenant ID are extracted from context. This drives Identity + Authorizer implementation.
>
> 7. **Existing config reload patterns**: Any hot-reload, file watching, config refresh mechanisms. Viper watchers, fsnotify, custom channels. These will be replaced by systemplane ChangeFeed.
>
> 8. **Swagger/OpenAPI setup**: How swagger is generated (`swag init` command?), where spec is served (middleware?), what tool (swaggo/swag? go-swagger?). This drives the swagger.MergeInto() integration in Gate 7.
>
> OUTPUT FORMAT: Structured report with file:line references for every point above.
> DO NOT write code. Analysis only.

**From the analysis, produce the Config Inventory Table:**

| Env Var Name | Config Field | Current Default | Go Type | Proposed Key | Proposed Tier | ApplyBehavior | Component | Secret | Validator | Group |
|-------------|-------------|-----------------|---------|-------------|--------------|---------------|-----------|--------|-----------|-------|
| `POSTGRES_HOST` | `Config.Postgres.Host` | `localhost` | `string` | `postgres.primary_host` | Runtime | BundleRebuild | `postgres` | No | — | `postgres` |
| `RATE_LIMIT_MAX` | `Config.RateLimit.Max` | `100` | `int` | `rate_limit.max` | Live-Read | LiveRead | `_none` | No | validatePositiveInt | `rate_limit` |
| `SERVER_ADDRESS` | `Config.Server.Address` | `:8080` | `string` | `server.address` | Bootstrap | BootstrapOnly | `_none` | No | — | `server` |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**This inventory becomes the CONTEXT for all subsequent gates.** Gate 2 uses it to create key definitions. Gate 3 uses it to build the Bundle. Gate 6 uses it for snapshot→Config hydration.

<block_condition>
HARD GATE: MUST complete the analysis report and config inventory before proceeding. All subsequent gates depend on this inventory.
</block_condition>

---

## Gate 1.5: Implementation Preview (Visual Report)

**Always executes. This gate generates a visual HTML report showing exactly what will change before any code is written.**

**Uses the `ring:visual-explainer` skill to produce a self-contained HTML page.**

The report is built from Gate 0 (stack detection) and Gate 1 (codebase analysis). It shows the developer a complete preview of every change that will be made across all subsequent gates.

**Orchestrator generates the report using `ring:visual-explainer` with this content:**

The HTML page MUST include these sections:

### 1. Current Architecture (Before)

- Mermaid diagram showing current config flow: env vars → Config struct → static injection into services
- Table of all files that will be created or modified, with purpose
- How infrastructure clients get their config today (static fields, constructor args)

### 2. Target Architecture (After)

- Mermaid diagram showing the three-tier architecture:
  ```
  Bootstrap env → Supervisor → Snapshot → BundleFactory → Bundle
                                       → Live-Read (per-request)
                                       → StateSync → Config struct (backward compat)
  ```
- Component map showing which infrastructure is managed by systemplane
- Change feed flow: DB change → pg_notify/change_stream → DebouncedFeed → Supervisor.Reload

### 3. Key Inventory Table

ALL keys with: name, tier (bootstrap/runtime/live-read), scope, ApplyBehavior, component, secret, validator, group. One row per key. This is the FULL inventory from Gate 1.

### 4. File Creation Plan

Every file to be created with gate assignment:

| Gate | File | Purpose | Lines (est.) |
|------|------|---------|-------------|
| 2 | `systemplane_keys.go` | Key orchestrator: Register + KeyDefs | ~50 |
| 2 | `systemplane_keys_{group}.go` | Per-group key definitions | ~30 each |
| 2 | `systemplane_keys_validation.go` | Validator functions | ~60 |
| 2 | `systemplane_keys_helpers.go` | concatKeyDefs utility | ~15 |
| 3 | `systemplane_bundle.go` | Bundle struct + Close + AdoptResources | ~80 |
| 3 | `systemplane_factory.go` | IncrementalBundleFactory | ~120 |
| 3 | `systemplane_factory_infra.go` | Per-component builders | ~100 |
| 4 | `systemplane_reconciler_*.go` | Reconcilers (if applicable) | ~50 each |
| 5 | `systemplane_identity.go` | JWT → Actor bridge | ~30 |
| 5 | `systemplane_authorizer.go` | Permission mapping | ~50 |
| 6 | `config_manager_systemplane.go` | Snapshot → Config hydration | ~150 |
| 6 | `config_manager_seed.go` | Env → Store seed | ~80 |
| 6 | `config_manager_helpers.go` | Type-safe comparison | ~40 |
| 6 | `config_validation.go` | Production config guards | ~60 |
| 7 | `systemplane_init.go` | 11-step init sequence | ~120 |
| 7 | `systemplane_mount.go` | HTTP route registration + swagger merge | ~40 |
| 7 | `active_bundle_state.go` | Thread-safe live-read accessor | ~40 |

### 5. ApplyBehavior Distribution

Visual breakdown showing how many keys per tier:

| ApplyBehavior | Count | Percentage | Example Keys |
|---------------|-------|-----------|-------------|
| BootstrapOnly | N | N% | server.address, auth.enabled |
| LiveRead | N | N% | rate_limit.max, timeout_sec |
| WorkerReconcile | N | N% | worker.interval_sec |
| BundleRebuild | N | N% | postgres.host, redis.host |
| BundleRebuildAndReconcile | N | N% | worker.enabled |

### 6. Component Map

| Component | Infrastructure | Keys | Rebuild Trigger |
|-----------|---------------|------|-----------------|
| `postgres` | PostgreSQL client | N | Connection string, pool size, credentials |
| `redis` | Redis client | N | Host, port, password |
| `rabbitmq` | RabbitMQ connection | N | URI, host, credentials |
| `s3` | Object storage | N | Endpoint, bucket, credentials |
| `http` | HTTP policy | N | Body limit, CORS |
| `logger` | Logger | N | Log level |
| `_none` | No infrastructure | N | Business logic only (live-read) |

### 7. Swagger Integration

Shows how systemplane routes will appear in the app's Swagger UI:

```go
import systemswagger "github.com/LerianStudio/lib-commons/v4/commons/systemplane/swagger"

// After swag init generates the base spec:
merged, err := systemswagger.MergeInto(baseSwaggerSpec)
// Use merged spec for swagger UI handler
```

All 9 `/v1/system/*` routes will be visible in the Swagger UI after merge.

### 8. Risk Assessment

| Risk | Mitigation | Verification |
|------|-----------|-------------|
| Config struct regression | StateSync hydrates Config from Snapshot on every change | Existing tests pass with systemplane active |
| Startup failure | Graceful degradation — service starts without systemplane if backend unavailable | Manual test with backend down |
| Resource leaks on hot-reload | AdoptResourcesFrom + ownership tracking in Bundle | Bundle factory tests verify resource reuse |
| Secret exposure | RedactPolicy on secret keys, AES-256-GCM encryption in store | Security review at Gate 8 |

### 9. Retro Compatibility Guarantee

**When systemplane store is unavailable**, the service degrades to bootstrap defaults:
- Config values from env vars still work (via `defaultConfig()` derived from KeyDefs)
- No runtime mutation API available (9 endpoints return 503)
- No hot-reload capability (static config for process lifetime)
- Workers run with static config from env vars
- **The service never fails to start due to systemplane issues**

**Output:** Save the HTML report to `docs/systemplane-preview.html` in the project root.

**Open in browser** for the developer to review.

<block_condition>
HARD GATE: Developer MUST explicitly approve the implementation preview before any code changes begin (Gates 2+). This prevents wasted effort on incorrect key classification or architectural decisions.
</block_condition>

**If the developer requests changes to the preview, regenerate the report and re-confirm.**

---

## Gate 2: Key Definitions + Registry

**Always executes.** This gate creates the key definition files that form the backbone of systemplane.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 config inventory:**

> TASK: Create systemplane key definition files based on the approved config inventory.
>
> CONTEXT FROM GATE 1: {Full config inventory table from analysis report}
> APPROVED KEY COUNT: {N keys from Gate 1.5 preview}
>
> **IMPORT PATHS (use exactly these):**
> ```go
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/registry"
> ```
>
> **FILES TO CREATE:**
>
> 1. **`systemplane_keys.go`** — Orchestrator:
>    ```go
>    func Register{Service}Keys(reg registry.Registry) error {
>        for _, def := range {service}KeyDefs() {
>            if err := reg.Register(def); err != nil {
>                return fmt.Errorf("register key %q: %w", def.Key, err)
>            }
>        }
>        return nil
>    }
>
>    func {service}KeyDefs() []domain.KeyDef {
>        return concatKeyDefs(
>            {service}KeyDefsAppServer(),
>            {service}KeyDefsPostgres(),
>            // ... one per group from inventory
>        )
>    }
>    ```
>
> 2. **`systemplane_keys_{group}.go`** — Per-group key definitions. Split by group names from inventory (app, server, postgres, redis, rabbitmq, auth, swagger, telemetry, rate_limit, worker, etc.)
>
> 3. **`systemplane_keys_validation.go`** — Validator functions:
>    - `validatePositiveInt(value any) error`
>    - `validateLogLevel(value any) error`
>    - `validateSSLMode(value any) error`
>    - `validateAbsoluteHTTPURL(value any) error`
>    - `validatePort(value any) error`
>    - Any service-specific validators
>
> 4. **`systemplane_keys_helpers.go`** — `concatKeyDefs()` utility
>
> **KEY DEFINITION RULES:**
>
> Every key MUST have ALL of these fields:
> - `Key` — dotted name (e.g., `"postgres.primary_host"`)
> - `Kind` — `domain.KindConfig` or `domain.KindSetting`
> - `AllowedScopes` — `[]domain.Scope{domain.ScopeGlobal}` or both
> - `DefaultValue` — THE single source of truth for defaults
> - `ValueType` — `domain.ValueString`, `domain.ValueInt`, `domain.ValueBool`, `domain.ValueFloat`
> - `ApplyBehavior` — classify using the 5-level taxonomy (see Appendix F)
> - `MutableAtRuntime` — `false` for bootstrap-only, `true` for everything else
> - `Secret` — `true` if contains credentials, tokens, keys
> - `RedactPolicy` — `domain.RedactFull` for secrets, `domain.RedactNone` otherwise
> - `Description` — human-readable description
> - `Group` — logical grouping matching file suffix
> - `Component` — infrastructure component: `"postgres"`, `"redis"`, `"rabbitmq"`, `"s3"`, `"http"`, `"logger"`, or `domain.ComponentNone` (`"_none"`)
> - `Validator` — custom validation function (nil if none needed)
>
> **DefaultValue is the SINGLE SOURCE OF TRUTH.** No separate config defaults. The `defaultConfig()` function will derive from KeyDefs via `configFromSnapshot(defaultSnapshotFromKeyDefs(...))`.

**Apply Behavior classification** — Include the 5-level taxonomy:

| ApplyBehavior | Constant | Strength | Runtime Effect | Use When |
|---------------|----------|----------|----------------|----------|
| **bootstrap-only** | `domain.ApplyBootstrapOnly` | 4 | Immutable after startup | Server address, TLS, auth, telemetry |
| **bundle-rebuild+worker-reconcile** | `domain.ApplyBundleRebuildAndReconcile` | 3 | Bundle swap AND worker restart | Worker enable/disable (needs new connections + restart) |
| **bundle-rebuild** | `domain.ApplyBundleRebuild` | 2 | Rebuild infra clients only | Connection strings, pool sizes, credentials |
| **worker-reconcile** | `domain.ApplyWorkerReconcile` | 1 | Restart workers only | Worker intervals, scheduler periods |
| **live-read** | `domain.ApplyLiveRead` | 0 | Zero-cost per-request reads | Rate limits, timeouts, TTLs, feature flags |

**Completion criteria:** All keys registered, `go build ./...` passes, key count matches inventory from Gate 1.5.

**Verification:** `grep "Register.*Keys\|KeyDefs()" internal/bootstrap/` + `go build ./...`

---

## Gate 3: Bundle + BundleFactory

**Always executes.** This gate creates the runtime resource container and its incremental builder.

**Dispatch `ring:backend-engineer-golang` with context from Gates 1-2:**

> TASK: Create the Bundle, BundleFactory, and per-component infrastructure builders.
>
> DETECTED INFRASTRUCTURE: {postgres, redis, rabbitmq, s3 — from Gate 0}
> KEY DEFINITIONS: {key groups and components from Gate 2}
>
> **IMPORT PATHS (use exactly these):**
> ```go
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/ports"
> ```
>
> **FILES TO CREATE:**
>
> 1. **`systemplane_bundle.go`** — Bundle struct with:
>    - Per-component ownership fields (postgres, redis, rabbitmq, mongo, s3, http, logger)
>    - `Close(ctx context.Context) error` method that closes all **owned** resources in REVERSE dependency order
>    - `AdoptResourcesFrom(previous domain.RuntimeBundle)` method that nil-outs transferred pointers in previous
>    - Ownership booleans per component (e.g., `ownsPostgres`, `ownsRedis`)
>
>    Pattern:
>    ```go
>    type {Service}Bundle struct {
>        Infra  *InfraBundle
>        HTTP   *HTTPPolicyBundle
>        Logger *LoggerBundle
>        ownsPostgres, ownsRedis, ownsRabbitMQ, ownsObjectStorage bool
>    }
>
>    func (b *{Service}Bundle) Close(ctx context.Context) error {
>        // Close in REVERSE dependency order, only owned resources
>        if b.ownsObjectStorage && b.Infra.ObjectStorage != nil { b.Infra.ObjectStorage.Close() }
>        if b.ownsRabbitMQ && b.Infra.RabbitMQ != nil { b.Infra.RabbitMQ.Close() }
>        if b.ownsRedis && b.Infra.Redis != nil { b.Infra.Redis.Close() }
>        if b.ownsPostgres && b.Infra.Postgres != nil { b.Infra.Postgres.Close() }
>        return nil
>    }
>
>    func (b *{Service}Bundle) AdoptResourcesFrom(previous domain.RuntimeBundle) {
>        prev, ok := previous.(*{Service}Bundle)
>        if !ok || prev == nil { return }
>        if !b.ownsPostgres { prev.Infra.Postgres = nil }
>        if !b.ownsRedis { prev.Infra.Redis = nil }
>        // ... etc
>    }
>    ```
>
> 2. **`systemplane_factory.go`** — IncrementalBundleFactory with:
>    - `Build(ctx, snapshot)` — full rebuild, creates everything from scratch
>    - `BuildIncremental(ctx, snapshot, previous, prevSnapshot)` — component-granular rebuild
>    - `keyComponentMap` — built once at factory construction from KeyDefs
>    - `diffChangedComponents(snap, prevSnap)` — uses keyComponentMap to find which components changed
>
>    Pattern:
>    ```go
>    type {Service}BundleFactory struct {
>        bootstrapCfg   *BootstrapOnlyConfig
>        keyComponentMap map[string]string // key → component
>    }
>
>    func (f *{Service}BundleFactory) Build(ctx context.Context, snap domain.Snapshot) (domain.RuntimeBundle, error) {
>        // Full rebuild — creates everything from scratch
>    }
>
>    func (f *{Service}BundleFactory) BuildIncremental(ctx context.Context, snap domain.Snapshot,
>        previous domain.RuntimeBundle, prevSnap domain.Snapshot) (domain.RuntimeBundle, error) {
>        // Diff changed components, rebuild only what changed, reuse the rest
>    }
>    ```
>
> 3. **`systemplane_factory_infra.go`** — Per-component builders:
>    - `buildPostgres(ctx, snapshot)` — creates postgres client from snapshot keys
>    - `buildRedis(ctx, snapshot)` — creates redis client from snapshot keys
>    - `buildRabbitMQ(ctx, snapshot)` — creates rabbitmq connection from snapshot keys
>    - `buildObjectStorage(ctx, snapshot)` — creates S3 client from snapshot keys
>    - `buildLogger(snapshot)` — creates logger from snapshot keys
>    - `buildHTTPPolicy(snapshot)` — extracts HTTP policy from snapshot keys
>    (one per detected infrastructure — omit unused components)

**Completion criteria:** Bundle builds successfully from snapshot, incremental rebuild reuses unchanged components, `go build ./...` passes.

**Verification:** `grep "IncrementalBundleFactory\|BundleFactory\|AdoptResourcesFrom" internal/bootstrap/` + `go build ./...`

---

## Gate 4: Reconcilers (Conditional)

**SKIP IF:** no background workers AND no RabbitMQ AND no HTTP policy changes detected in Gate 0.

**When to include each reconciler:**
- `HTTPPolicyReconciler` — if HTTP policy keys exist (body limit, CORS, timeouts)
- `PublisherReconciler` — if RabbitMQ detected
- `WorkerReconciler` — if background workers detected

**Dispatch `ring:backend-engineer-golang` with context from Gates 1-3:**

> TASK: Create reconcilers for side effects on config changes.
>
> DETECTED: {workers: Y/N, rabbitmq: Y/N, http_policy_keys: Y/N from Gates 0-2}
>
> **IMPORT PATHS (use exactly these):**
> ```go
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/ports"
> ```
>
> **FILES TO CREATE (only for detected components):**
>
> 1. **`systemplane_reconciler_http.go`** — PhaseValidation reconciler for HTTP config:
>    - Validates body limit is non-negative
>    - Validates CORS origins are present
>    - Can REJECT changes (returns error to abort the reload)
>    ```go
>    func (r *HTTPPolicyReconciler) Phase() domain.ReconcilerPhase { return domain.PhaseValidation }
>    ```
>
> 2. **`systemplane_reconciler_publishers.go`** — PhaseValidation for RabbitMQ publisher staging (if RMQ detected):
>    - When RabbitMQ connection changed, creates staged publishers on candidate bundle
>    - The observer callback swaps them in later
>    ```go
>    func (r *PublisherReconciler) Phase() domain.ReconcilerPhase { return domain.PhaseValidation }
>    ```
>
> 3. **`systemplane_reconciler_worker.go`** — PhaseSideEffect for worker restart (if workers detected):
>    - Reads worker config from snapshot
>    - Calls `workerManager.ApplyConfig(cfg)` to restart affected workers
>    - Runs LAST because it has external side effects
>    ```go
>    func (r *WorkerReconciler) Phase() domain.ReconcilerPhase { return domain.PhaseSideEffect }
>    ```
>
> **Phase ordering is enforced by the type system** — you cannot register a reconciler without declaring its phase. The supervisor stable-sorts by phase, so reconcilers within the same phase retain their registration order.
>
> Phase execution order: PhaseStateSync (0) → PhaseValidation (1) → PhaseSideEffect (2)

**Completion criteria:** Reconcilers compile, implement `ports.BundleReconciler` interface, phase ordering is correct. `go build ./...` passes.

**Verification:** `grep "BundleReconciler\|Reconcile\|Phase()" internal/bootstrap/systemplane_reconciler_*.go` + `go build ./...`

---

## Gate 5: Identity + Authorization

**Always executes.** Systemplane HTTP endpoints require identity resolution and permission checking.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement IdentityResolver and Authorizer for systemplane HTTP endpoints.
>
> CONTEXT FROM GATE 1: {Authentication/authorization analysis — how JWT is parsed, where user ID/tenant ID are extracted}
>
> **IMPORT PATHS (use exactly these):**
> ```go
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/ports"
> ```
>
> **FILES TO CREATE:**
>
> 1. **`systemplane_identity.go`** — Implements `ports.IdentityResolver`:
>    ```go
>    type {Service}IdentityResolver struct{}
>
>    func (r *{Service}IdentityResolver) Actor(ctx context.Context) (domain.Actor, error) {
>        uid := auth.GetUserID(ctx) // use the service's existing auth context extraction
>        if uid == "" { uid = "anonymous" }
>        return domain.Actor{ID: uid}, nil
>    }
>
>    func (r *{Service}IdentityResolver) TenantID(ctx context.Context) (string, error) {
>        return auth.GetTenantID(ctx) // use the service's existing tenant extraction
>    }
>    ```
>
> 2. **`systemplane_authorizer.go`** — Implements `ports.Authorizer`:
>    Maps 9 permissions to the service's auth model:
>    - `system/configs:read` — view config values
>    - `system/configs:write` — update config values
>    - `system/configs/schema:read` — view key definitions
>    - `system/configs/history:read` — view config change history
>    - `system/configs/reload:write` — force full reload
>    - `system/settings:read` — view settings
>    - `system/settings:write` — update settings
>    - `system/settings/schema:read` — view setting key definitions
>    - `system/settings:history:read` — view settings history (scope-dependent)
>
>    ```go
>    type {Service}Authorizer struct {
>        authEnabled bool
>    }
>
>    func (a *{Service}Authorizer) Authorize(ctx context.Context, permission string) error {
>        if !a.authEnabled { return nil } // dev mode bypass
>        // Map permission to the service's RBAC action, call auth.Authorize()
>    }
>    ```
>
> **When auth is disabled** (dev mode), authorizer returns nil for all permissions.
> **When auth is enabled**, map systemplane permissions to the service's existing permission model.

**Completion criteria:** Both interfaces implemented, `go build ./...` passes.

**Verification:** `grep "IdentityResolver\|Authorizer\|Actor\|TenantID\|Authorize" internal/bootstrap/systemplane_identity.go internal/bootstrap/systemplane_authorizer.go` + `go build ./...`

---

## Gate 6: Config Manager Bridge

**Always executes.** This gate ensures backward compatibility — existing code reading the Config struct continues to work.

**Dispatch `ring:backend-engineer-golang` with context from Gates 1-2:**

> TASK: Create the Config Manager bridge that hydrates the existing Config struct from systemplane Snapshot.
>
> CONTEXT FROM GATE 1: {Config struct location, all fields, current defaults}
> KEY DEFINITIONS: {All keys from Gate 2 with their snapshot key names}
>
> **FILES TO CREATE:**
>
> 1. **`config_manager_systemplane.go`** — StateSync callback + snapshot hydration:
>
>    Two core functions:
>    - `configFromSnapshot(snap domain.Snapshot) *Config` — builds a Config entirely from snapshot values. ALL fields come from the snapshot — no bootstrap overlay. This is used by `defaultConfig()`.
>    - `snapshotToFullConfig(snap domain.Snapshot, oldCfg *Config) *Config` — hydrates from snapshot, then overlays bootstrap-only fields from the previous config (they never change at runtime).
>
>    Helper functions for type-safe extraction with JSON coercion:
>    - `snapString(snap, key, fallback) string`
>    - `snapInt(snap, key, fallback) int`
>    - `snapBool(snap, key, fallback) bool`
>    - `snapFloat64(snap, key, fallback) float64`
>
>    The StateSync callback (registered on Manager):
>    ```go
>    StateSync: func(_ context.Context, snap domain.Snapshot) {
>        newCfg := snapshotToFullConfig(snap, baseCfg)
>        configManager.swapConfig(newCfg)
>    },
>    ```
>
> 2. **`config_manager_seed.go`** — One-time env → store seed:
>    - Reads current env vars and seeds them into systemplane store
>    - Only runs on first boot (when store is empty)
>    - Preserves existing configuration values during migration
>    - Skips bootstrap-only keys (they don't go into the store)
>    - Uses `store.Put()` with `domain.RevisionZero` for initial write
>
> 3. **`config_manager_helpers.go`** — Type-safe value comparison:
>    - `valuesEquivalent(a, b any) bool` — handles JSON coercion (float64 vs int)
>    - Used by seed logic to avoid overwriting store values that match env defaults
>
> 4. **`config_validation.go`** — Production config guards:
>    - Validates critical config combinations at startup
>    - Used as `ConfigWriteValidator` on the Manager
>    - Prevents invalid states (e.g., TLS enabled without cert path)
>    - Returns non-nil error to REJECT a write before persistence
>
> **CRITICAL: The `defaultConfig()` function MUST be updated to derive from KeyDefs:**
> ```go
> func defaultConfig() *Config {
>     return configFromSnapshot(defaultSnapshotFromKeyDefs({service}KeyDefs()))
> }
> ```
> This eliminates drift between defaults and key definitions. If you change a default in `{service}KeyDefs()`, the Config struct picks it up automatically.

**Completion criteria:** Config struct hydrates correctly from snapshot, existing code reading `configManager.Get()` gets updated values after StateSync, `go build ./...` passes.

**Verification:** `grep "configFromSnapshot\|snapshotToFullConfig\|StateSync\|seedStore" internal/bootstrap/` + `go build ./...`

---

## Gate 7: Wiring + HTTP Mount + Swagger + ChangeFeed ⛔ CRITICAL

<cannot_skip>

**This gate is NEVER skippable. It is the most critical gate.**

This is where the systemplane comes alive. Without Gate 7, keys are metadata, bundles are dead code, and reconcilers never fire. Gate 7 wires everything together: the 11-step init sequence, HTTP endpoint mount, Swagger merge, ChangeFeed subscription, active bundle state, and shutdown integration.

**⛔ HARD GATE: Gate 7 MUST be fully implemented. There is no "partial" Gate 7. Every subcomponent below is required.**

</cannot_skip>

**Dispatch `ring:backend-engineer-golang` with context from ALL previous gates:**

> TASK: Wire the complete systemplane lifecycle — init, HTTP mount, swagger merge, change feed, bundle state, and shutdown.
>
> ALL PREVIOUS GATES: {Key definitions from Gate 2, Bundle/Factory from Gate 3, Reconcilers from Gate 4, Identity/Auth from Gate 5, Config Bridge from Gate 6}
>
> **IMPORT PATHS (use exactly these):**
> ```go
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/domain"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/ports"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/registry"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/service"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/bootstrap"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/bootstrap/builtin"
> "github.com/LerianStudio/lib-commons/v4/commons/systemplane/adapters/changefeed"
> fiberhttp "github.com/LerianStudio/lib-commons/v4/commons/systemplane/adapters/http/fiber"
> systemswagger "github.com/LerianStudio/lib-commons/v4/commons/systemplane/swagger"
> ```
>
> **FILES TO CREATE:**
>
> ### 1. `systemplane_init.go` — The 11-step initialization sequence
>
> ```go
> func Init{Service}Systemplane(ctx context.Context, cfg *Config, configManager *ConfigManager,
>     workerManager *WorkerManager, logger log.Logger,
>     observer func(service.ReloadEvent)) (*SystemplaneComponents, error) {
>
>     // Step 1: Extract bootstrap-only config (immutable for process lifetime)
>     bootstrapCfg := ExtractBootstrapOnlyConfig(cfg)
>
>     // Step 2: Load backend config (default: reuse app's Postgres DSN)
>     backendCfg := Load{Service}BackendConfig(cfg)
>
>     // Step 3: Create registry + register ALL keys
>     reg := registry.New()
>     if err := Register{Service}Keys(reg); err != nil {
>         return nil, err
>     }
>
>     // Step 4: Configure backend with registry metadata (secret keys + apply behaviors)
>     configureBackendWithRegistry(backendCfg, reg)
>
>     // Step 5: Create backend (Store + History + ChangeFeed)
>     backend, err := builtin.NewBackendFromConfig(ctx, backendCfg)
>     if err != nil { return nil, fmt.Errorf("systemplane backend: %w", err) }
>
>     // Step 6: Create snapshot builder
>     snapBuilder, err := service.NewSnapshotBuilder(reg, backend.Store)
>     if err != nil { backend.Close(); return nil, err }
>
>     // Step 7: Create bundle factory (supports incremental builds)
>     bundleFactory := New{Service}BundleFactory(&bootstrapCfg)
>
>     // Step 8: Seed store from current env-var config (first boot only)
>     if err := seedStoreForInitialReload(ctx, configManager, reg, backend.Store); err != nil {
>         backend.Close(); return nil, err
>     }
>
>     // Step 9: Build reconcilers (phase-sorted by supervisor)
>     reconcilers := buildReconcilers(workerManager)
>
>     // Step 10: Create supervisor + initial reload
>     supervisor, err := service.NewSupervisor(service.SupervisorConfig{
>         Builder:     snapBuilder,
>         Factory:     bundleFactory,
>         Reconcilers: reconcilers,
>         Observer:    observer,
>     })
>     if err != nil { backend.Close(); return nil, err }
>
>     if err := supervisor.Reload(ctx, "initial-bootstrap"); err != nil {
>         backend.Close(); return nil, err
>     }
>
>     // Step 11: Create manager with callbacks
>     baseCfg := configManager.Get()
>     manager, err := service.NewManager(service.ManagerConfig{
>         Registry:   reg,
>         Store:      backend.Store,
>         History:    backend.History,
>         Supervisor: supervisor,
>         Builder:    snapBuilder,
>         ConfigWriteValidator: productionConfigGuards(baseCfg),
>         StateSync: func(_ context.Context, snap domain.Snapshot) {
>             newCfg := snapshotToFullConfig(snap, baseCfg)
>             configManager.swapConfig(newCfg)
>         },
>     })
>     if err != nil { backend.Close(); return nil, err }
>
>     return &SystemplaneComponents{
>         ChangeFeed: backend.ChangeFeed,
>         Supervisor: supervisor,
>         Manager:    manager,
>         Backend:    backend.Closer,
>     }, nil
> }
> ```
>
> ### 2. `systemplane_mount.go` — HTTP route registration
>
> ```go
> func MountSystemplaneAPI(app *fiber.App, manager service.Manager,
>     authEnabled bool) error {
>
>     authorizer := &{Service}Authorizer{authEnabled: authEnabled}
>     identity := &{Service}IdentityResolver{}
>
>     handler, err := fiberhttp.NewHandler(manager, identity, authorizer)
>     if err != nil {
>         return fmt.Errorf("create systemplane handler: %w", err)
>     }
>
>     handler.Mount(app) // registers all 9 /v1/system/* routes
>     return nil
> }
> ```
>
> This registers ALL 9 endpoints:
> - `GET    /v1/system/configs`
> - `PATCH  /v1/system/configs`
> - `GET    /v1/system/configs/schema`
> - `GET    /v1/system/configs/history`
> - `POST   /v1/system/configs/reload`
> - `GET    /v1/system/settings`
> - `PATCH  /v1/system/settings`
> - `GET    /v1/system/settings/schema`
> - `GET    /v1/system/settings/history`
>
> ### 3. Swagger Integration
>
> In the app's swagger setup (wherever the swagger middleware is configured):
> ```go
> import systemswagger "github.com/LerianStudio/lib-commons/v4/commons/systemplane/swagger"
>
> // After swag init generates the base spec:
> merged, err := systemswagger.MergeInto(baseSwaggerSpec)
> if err != nil {
>     return fmt.Errorf("merge systemplane swagger: %w", err)
> }
> // Use merged spec for swagger UI handler
> ```
>
> ### 4. `active_bundle_state.go` — Thread-safe live-read accessor
>
> ```go
> type activeBundleState struct {
>     mu     sync.RWMutex
>     bundle *{Service}Bundle
> }
>
> func (s *activeBundleState) Current() *{Service}Bundle {
>     s.mu.RLock()
>     defer s.mu.RUnlock()
>     return s.bundle
> }
>
> func (s *activeBundleState) Update(b *{Service}Bundle) {
>     s.mu.Lock()
>     defer s.mu.Unlock()
>     s.bundle = b
> }
> ```
>
> Used by infrastructure consumers for live-read access to the current bundle.
>
> ### 5. ChangeFeed integration (in init.go wiring)
>
> ```go
> debouncedFeed := changefeed.NewDebouncedFeed(
>     spComponents.ChangeFeed,
>     changefeed.WithWindow(200 * time.Millisecond),
> )
>
> feedCtx, cancelFeed := context.WithCancel(ctx)
> go func() {
>     _ = debouncedFeed.Subscribe(feedCtx, func(signal ports.ChangeSignal) {
>         _ = spComponents.Manager.ApplyChangeSignal(feedCtx, signal)
>     })
> }()
> ```
>
> ### 6. Shutdown sequence integration
>
> ```go
> func (s *Service) Stop(ctx context.Context) {
>     s.configManager.Stop()              // 1. Prevent mutations
>     s.cancelChangeFeed()                // 2. Stop change feed BEFORE supervisor
>     s.spComponents.Supervisor.Stop(ctx) // 3. Stop supervisor + close bundle
>     s.spComponents.Backend.Close()      // 4. Close store connection
>     s.workerManager.Stop()              // 5. Stop workers
> }
> ```
>
> ### 7. Observer callback (passed to InitSystemplane)
>
> ```go
> runtimeReloadObserver := func(event service.ReloadEvent) {
>     bundle := event.Bundle.(*{Service}Bundle)
>     bundleState.Update(bundle)
>     configManager.UpdateFromSystemplane(event.Snapshot)
>     // Swap logger, publishers, etc.
> }
> ```
>
> ### 8. Bootstrap config file — `config/.config-map.example`
>
> Lists all bootstrap-only keys with their env var names. Operator reference for deployment configuration.
>
> ```
> # {Service} — Bootstrap-Only Configuration (requires restart)
> #
> # These are the ONLY settings that require a container/pod restart.
> # Everything else is hot-reloadable via:
> #
> #   GET  /v1/system/configs          — view current runtime config
> #   PATCH /v1/system/configs         — change any runtime-managed key
> #   GET  /v1/system/configs/schema   — see all keys, types, and mutability
> #   GET  /v1/system/configs/history  — audit trail of changes
>
> ENV_NAME=development
> SERVER_ADDRESS=:8080
> AUTH_ENABLED=false
> ENABLE_TELEMETRY=false
> # ... all bootstrap-only keys
> ```

**Completion criteria:**
- All 9 HTTP routes accessible
- ChangeFeed fires on store changes
- Supervisor rebuilds bundle on config change
- Swagger UI shows systemplane routes (via MergeInto)
- Graceful shutdown closes all resources in correct order
- Active bundle state provides live-read access to request handlers
- Observer callback updates bundle state and config manager on reload

**Verification:**
```bash
grep "handler.Mount\|fiberhttp.NewHandler" internal/bootstrap/
grep "DebouncedFeed\|Subscribe\|ApplyChangeSignal" internal/bootstrap/
grep "swagger.MergeInto\|systemswagger" internal/bootstrap/ internal/
grep "activeBundleState\|bundleState.Update\|bundleState.Current" internal/bootstrap/
grep "cancelChangeFeed\|Supervisor.Stop\|Backend.Close" internal/bootstrap/
go build ./...
```

### ⛔ Gate 7 Anti-Rationalization Table

| Rationalization | WRONG BECAUSE | REQUIRED ACTION |
|-----------------|---------------|-----------------|
| "Mount is straightforward, I'll skip it" | Without Mount, 9 endpoints are unreachable — the entire management API is dead | MUST implement `handler.Mount(app)` |
| "Swagger is optional documentation" | Without swagger merge, operators cannot discover systemplane endpoints in Swagger UI | MUST call `systemswagger.MergeInto()` |
| "ChangeFeed can be added later" | Without ChangeFeed, hot-reload is broken — config changes in DB are invisible to the service | MUST start `DebouncedFeed` |
| "Shutdown is handled by the framework" | Supervisor, ChangeFeed, and Bundle hold resources that leak without explicit shutdown | MUST integrate 5-step shutdown sequence |
| "Active bundle state is internal detail" | Without thread-safe accessor, request handlers cannot read live config — race conditions | MUST implement `active_bundle_state.go` |
| "Init function is just boilerplate" | The 11-step sequence has strict ordering — wrong order causes nil panics or stale data | MUST follow exact step order |
| "Observer callback is optional" | Without observer, bundle state and config manager are never updated after reload | MUST register observer on Supervisor |
| "Config map example is nice-to-have" | Operators need to know which keys require restart vs hot-reload — without it, they restart for everything | MUST create `config/.config-map.example` |

---

## Gate 8: Code Review

**Dispatch 7 parallel reviewers (same pattern as ring:requesting-code-review).**

MUST include this context in ALL 7 reviewer dispatches:

> **SYSTEMPLANE REVIEW CONTEXT:**
> - Systemplane is a three-tier configuration system: bootstrap (env, immutable) → runtime (DB, hot-reload) → live-read (snapshot, per-request).
> - Every key has an ApplyBehavior that determines how changes propagate: BootstrapOnly → BundleRebuildAndReconcile → BundleRebuild → WorkerReconcile → LiveRead.
> - IncrementalBundleFactory rebuilds only changed components. Ownership tracking prevents double-free.
> - StateSync callback keeps the Config struct in sync for backward compatibility.
> - The 9 HTTP endpoints on /v1/system/* expose config management with If-Match/ETag concurrency.
> - ChangeFeed (pg_notify or change_stream) triggers automatic reload on database changes.
> - swagger.MergeInto() adds systemplane routes to the app's Swagger spec.

| Reviewer | Systemplane-Specific Focus |
|----------|---------------------------|
| ring:code-reviewer | Architecture, lib-commons v4 systemplane usage, three-tier separation, package boundaries, import paths |
| ring:business-logic-reviewer | Key classification correctness, ApplyBehavior assignments, component granularity, default values match current behavior |
| ring:security-reviewer | Secret key redaction (RedactFull/RedactMask), authorization model, no credential leaks in config API responses, AES-256-GCM encryption |
| ring:test-reviewer | Key registration tests, bundle factory tests, reconciler tests, contract tests, config hydration tests |
| ring:nil-safety-reviewer | Nil risks in snapshot reads, bundle adoption, reconciler error paths, active bundle state before first reload |
| ring:consequences-reviewer | Impact on existing config reads, backward compat via StateSync, degradation when store unavailable, shutdown resource cleanup |
| ring:dead-code-reviewer | Orphaned env-reading code, dead config helpers replaced by systemplane, unused YAML/viper imports, stale .env files |

**⛔ MANDATORY:** All 7 reviewers must PASS. 6/7 = FAIL. Critical findings → fix and re-review.

---

## Gate 9: User Validation

MUST approve: present checklist for explicit user approval.

```markdown
## Systemplane Migration Complete

- [ ] All keys registered and classified (count matches preview: {N} keys)
- [ ] BundleFactory builds successfully with IncrementalBundleFactory
- [ ] Incremental rebuild reuses unchanged components (ownership tracking works)
- [ ] Reconcilers fire on config changes (if applicable)
- [ ] Identity + Authorization wired (JWT → Actor, 9 permissions mapped)
- [ ] Config Manager bridge works (StateSync hydrates Config struct from Snapshot)
- [ ] `defaultConfig()` derives from KeyDefs (single source of truth)
- [ ] HTTP Mount: all 9 /v1/system/* endpoints accessible
- [ ] Swagger: systemplane routes visible in Swagger UI (via MergeInto)
- [ ] ChangeFeed: config changes in DB trigger supervisor reload
- [ ] Active bundle state: thread-safe live-read for request handlers
- [ ] Shutdown: clean 5-step resource release on SIGTERM
- [ ] Backward compat: service starts normally without systemplane store (degrades to defaults)
- [ ] Tests pass: `go test ./...`
- [ ] Code review passed: all 7 reviewers PASS
```

---

## Gate 10: Activation Guide

**MUST generate `docs/systemplane-guide.md` in the project root.** Direct, concise, no filler text.

The guide is built from Gate 0 (stack detection), Gate 1 (analysis), and Gate 2 (key inventory).

The guide MUST include:

### 1. Components Table

| Component | Purpose | Status |
|-----------|---------|--------|
| Registry | Key definitions (types, defaults, validators) | {N} keys registered |
| Supervisor | Reload lifecycle (snapshot → bundle → reconcile → swap) | Active |
| Manager | HTTP API backend (reads, writes, schema, history, resync) | Active |
| BundleFactory | IncrementalBundleFactory with component-granular rebuilds | Active |
| Reconcilers | Side-effect appliers (HTTP, Publisher, Worker) | {N} reconcilers |
| ChangeFeed | Database change → DebouncedFeed → Supervisor.Reload | Active |

### 2. Bootstrap-Only Config Reference

| Env Var | Default | Description | Requires Restart |
|---------|---------|-------------|-----------------|
| `ENV_NAME` | `development` | Environment name | Yes |
| `SERVER_ADDRESS` | `:8080` | Listen address | Yes |
| `AUTH_ENABLED` | `false` | Enable auth middleware | Yes |
| ... | ... | ... | ... |

### 3. Runtime-Managed Config Reference

| Key | Default | Type | ApplyBehavior | Hot-Reloadable |
|-----|---------|------|---------------|---------------|
| `rate_limit.max` | `100` | int | LiveRead | Yes (instant) |
| `postgres.primary_host` | `localhost` | string | BundleRebuild | Yes (rebuilds PG client) |
| ... | ... | ... | ... | ... |

### 4. Activation Steps

1. Ensure PostgreSQL (or MongoDB) is running
2. Set `SYSTEMPLANE_SECRET_MASTER_KEY` env var (32 bytes, raw or base64)
3. Start the service — systemplane auto-creates tables/collections
4. On first boot, env var values are seeded into the store
5. Verify: `curl http://localhost:{port}/v1/system/configs | jq`

### 5. Verification Commands

```bash
# View current runtime config
curl -s http://localhost:{port}/v1/system/configs | jq

# View schema (all keys, types, mutability)
curl -s http://localhost:{port}/v1/system/configs/schema | jq

# Change a runtime key
curl -X PATCH http://localhost:{port}/v1/system/configs \
  -H 'Content-Type: application/json' \
  -H 'If-Match: "current-revision"' \
  -d '{"values": {"rate_limit.max": 200}}'

# View change history
curl -s http://localhost:{port}/v1/system/configs/history | jq

# Force full reload
curl -X POST http://localhost:{port}/v1/system/configs/reload

# View settings
curl -s http://localhost:{port}/v1/system/settings?scope=global | jq
```

### 6. Degradation Behavior

| Scenario | Behavior |
|----------|----------|
| Systemplane backend unavailable at startup | Service starts with env var defaults (no hot-reload) |
| Systemplane backend goes down after startup | Last-known config remains active (no updates until reconnect) |
| ChangeFeed disconnects | Auto-reconnect with exponential backoff; manual `POST /v1/system/configs/reload` available |
| Invalid config write | ConfigWriteValidator rejects before persistence; no impact on running config |
| Bundle build failure | Previous bundle stays active; error logged; no disruption |

### 7. Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `systemplane backend: connection refused` | PostgreSQL/MongoDB not running | Start the database |
| `register key "X": duplicate key` | Key registered twice | Check for duplicate key names in key definition files |
| `revision mismatch` (409) | Concurrent write conflict | Re-read current revision, retry PATCH with updated `If-Match` |
| `key is not mutable at runtime` (400) | Tried to PATCH a bootstrap-only key | This key requires a restart — update env var instead |
| `secret master key required` | `SYSTEMPLANE_SECRET_MASTER_KEY` not set | Set the env var (32 bytes) |

---

## State Persistence

Save to `docs/ring-systemplane-migration/current-cycle.json` for resume support:

```json
{
  "skill": "ring:systemplane-migration",
  "version": "2.0.0",
  "service": "{service_name}",
  "started_at": "ISO8601",
  "current_gate": "2",
  "gates_completed": ["0", "1", "1.5"],
  "gates_skipped": [],
  "detection": {
    "backend": "postgres",
    "dependencies": ["postgres", "redis", "rabbitmq"],
    "has_workers": true,
    "existing_systemplane": false,
    "config_pattern": "envDefault",
    "key_count": 45
  },
  "compliance": {
    "status": "NEW",
    "checks": {}
  }
}
```

---

## Anti-Rationalization Table

| Rationalization | WRONG BECAUSE | REQUIRED ACTION |
|-----------------|---------------|-----------------|
| "Keys are registered, migration is done" | Without BundleFactory + Wiring, keys are just metadata — nothing reads them at runtime | Complete ALL gates through Gate 7 |
| "We can wire it later" | Gate 7 is where the system comes alive — without it, systemplane is dead code | Gate 7 is NEVER skippable |
| "Swagger integration is cosmetic" | Operators need API discoverability; without it, 9 endpoints are invisible | MUST call `systemswagger.MergeInto()` |
| "Config bridge is backward compat only" | Existing code reads Config struct — without StateSync, it reads stale bootstrap values forever | MUST implement Gate 6 |
| "Reconcilers are optional" | Without reconcilers, workers and HTTP policies ignore config changes — hot-reload is partial | Evaluate at Gate 4; implement if infra detected |
| "Service already has systemplane code" | Existence ≠ compliance. Code that doesn't follow canonical patterns is WRONG and must be fixed. | STOP. Run compliance audit (Gate 0 Phase 2). Fix every NON-COMPLIANT component. |
| "Partial systemplane is good enough" | Partial = broken. Without ChangeFeed, no hot-reload. Without Mount, no API. Without StateSync, stale config. | STOP. Every component is required. Execute all gates. |
| "The current approach works fine" | Working ≠ compliant. Custom config management creates drift and blocks standardization. | Replace with canonical systemplane implementation. |
| "Skip code review, we tested it" | One wiring mistake = resource leak, config corruption, or silent degradation. 7 reviewers catch what tests miss. | MANDATORY: All 7 reviewers must PASS. |
| "ChangeFeed can be added later" | Later = never. Without ChangeFeed, the database is a dead store — changes are invisible. | MUST start DebouncedFeed in Gate 7 |
| "Agent says out of scope" | Skill defines scope, not agent. | Re-dispatch with gate context |
| "Active bundle state is an implementation detail" | Without it, request handlers cannot safely read live config. Race conditions and nil panics. | MUST implement in Gate 7 |

---

## Appendix A: Package Structure Reference

The systemplane lives in `lib-commons/v4/commons/systemplane/` — a self-contained,
backend-agnostic library with **zero imports of internal application packages**.
It was extracted from Core two's `pkg/systemplane/` into lib-commons v4.3.0 to be
shared across all Lerian services.

### Directory Structure

```
commons/systemplane/                            # in lib-commons repo
├── doc.go                                      # Package doc
├── domain/                                     # Pure value objects, no infra deps
│   ├── actor.go                                # Actor{ID}
│   ├── apply_behavior.go                       # ApplyBehavior enum + Strength()
│   ├── backend_kind.go                         # BackendKind enum (postgres, mongodb)
│   ├── bundle.go                               # RuntimeBundle interface
│   ├── entry.go                                # Entry (persisted override record)
│   ├── errors.go                               # 14 sentinel errors
│   ├── key_def.go                              # KeyDef, ValueType, RedactPolicy, ValidatorFunc, ComponentNone
│   ├── kind.go                                 # Kind enum (config, setting)
│   ├── nil_value.go                            # IsNilValue() — reflect-based typed-nil detection
│   ├── reconciler_phase.go                     # ReconcilerPhase enum (3 phases)
│   ├── revision.go                             # Revision type (uint64 wrapper)
│   ├── scope.go                                # Scope enum (global, tenant)
│   ├── snapshot.go                             # Snapshot + EffectiveValue
│   └── target.go                               # Target (kind/scope/subject coordinate)
├── ports/                                      # Interface definitions (hex boundary)
│   ├── authorizer.go                           # Authorizer
│   ├── bundle_factory.go                       # BundleFactory + IncrementalBundleFactory
│   ├── changefeed.go                           # ChangeFeed + ChangeSignal
│   ├── history.go                              # HistoryStore + HistoryEntry + HistoryFilter
│   ├── identity.go                             # IdentityResolver
│   ├── reconciler.go                           # BundleReconciler (phased)
│   └── store.go                                # Store + WriteOp + ReadResult
├── registry/                                   # Thread-safe key definition registry
│   ├── registry.go                             # Registry interface + inMemoryRegistry
│   └── validation.go                           # Type validation with JSON coercion
├── service/                                    # Use-case orchestration
│   ├── escalation.go                           # Escalate() — strongest ApplyBehavior
│   ├── manager.go                              # Manager interface + ManagerConfig
│   ├── manager_helpers.go                      # Redaction, schema building
│   ├── manager_reads.go                        # GetConfigs, GetSettings, GetSchema, GetHistory, Resync
│   ├── manager_writes.go                       # PatchConfigs, PatchSettings, ApplyChangeSignal
│   ├── manager_writes_helpers.go               # Validation, escalation, snapshot preview
│   ├── snapshot_builder.go                     # 3-layer cascade: default → global → tenant
│   ├── supervisor.go                           # Supervisor interface + Reload lifecycle
│   └── supervisor_helpers.go                   # Build strategy, phase sort, resource adoption
├── bootstrap/                                  # Backend wiring from env/config
│   ├── backend.go                              # BackendFactory registry + NewBackendFromConfig
│   ├── classifier.go                           # IsBootstrapOnly / IsRuntimeManaged
│   ├── config.go                               # BootstrapConfig, PostgresBootstrapConfig, MongoBootstrapConfig
│   ├── defaults.go                             # Default table/collection names
│   ├── env.go                                  # LoadFromEnv() — SYSTEMPLANE_* env vars
│   ├── postgres_identifiers.go                 # Regex validation for PG identifiers
│   └── builtin/
│       └── backend.go                          # init()-registered factories (PG + Mongo)
├── adapters/
│   ├── store/
│   │   ├── secretcodec/
│   │   │   └── codec.go                        # AES-256-GCM encryption for secret values
│   │   ├── storetest/
│   │   │   └── contract.go                     # 15 shared contract tests (Store + History)
│   │   ├── postgres/                           # 3 tables, optimistic concurrency, pg_notify
│   │   │   ├── ddl.go                          # CREATE TABLE templates
│   │   │   ├── postgres.go                     # New(), NewFromDB() constructors
│   │   │   ├── store.go                        # Get(), Put()
│   │   │   ├── store_mutation.go               # applyOp, upsert, delete, insertHistory
│   │   │   ├── store_revision.go               # lock/read/update revision
│   │   │   ├── store_runtime.go                # encrypt/decrypt, notify, escalate
│   │   │   ├── json_decode.go                  # Integer-preserving JSON decoder
│   │   │   ├── history.go                      # ListHistory with dynamic builder
│   │   │   └── identifiers.go                  # qualify() helper
│   │   └── mongodb/                            # Sentinel revision doc, multi-doc txns
│   │       ├── mongodb.go                      # New(), ensureIndexes, txn support check
│   │       ├── store.go                        # Get(), Put() with sessions
│   │       ├── store_helpers.go                # applyOperation, encrypt, CRUD
│   │       ├── models.go                       # BSON models + normalization
│   │       └── history.go                      # ListHistory with BSON filter
│   ├── changefeed/
│   │   ├── debounce.go                         # Trailing-edge per-target debounce
│   │   ├── debounce_helpers.go                 # Timer management, jitter
│   │   ├── safe_handler.go                     # Panic-to-error conversion
│   │   ├── feedtest/
│   │   │   └── contract.go                     # 3 shared contract tests for ChangeFeed
│   │   ├── postgres/                           # LISTEN/NOTIFY, auto-reconnect, revision resync
│   │   │   ├── feed.go                         # Feed struct + Subscribe
│   │   │   ├── feed_subscribe.go               # subscribeLoop, reconnect, listenLoop
│   │   │   ├── feed_runtime.go                 # backoff, jitter, revision validation
│   │   │   └── options.go                      # WithReconnectBounds, WithRevisionSource
│   │   └── mongodb/                            # change_stream or poll mode
│   │       ├── feed.go                         # Feed struct + Subscribe
│   │       ├── feed_stream.go                  # subscribeChangeStream
│   │       ├── feed_poll.go                    # subscribePoll, pollRevisions
│   │       └── feed_bson.go                    # BSON helpers
│   └── http/
│       └── fiber/                              # 9 endpoints, DTOs, middleware
│           ├── handler.go                      # Handler struct, NewHandler, Mount()
│           ├── handler_configs.go              # Config CRUD + reload
│           ├── handler_settings.go             # Settings CRUD
│           ├── dto.go                          # All request/response DTOs
│           ├── middleware.go                   # requireAuth, settingsAuth
│           └── errors.go                       # Domain error → HTTP status mapping
├── swagger/                                    # Embedded OpenAPI spec for merge
│   └── ...                                     # swagger.MergeInto(baseSpec) ([]byte, error)
└── testutil/                                   # Test doubles
    ├── fake_store.go                           # In-memory Store with concurrency
    ├── fake_history.go                         # In-memory HistoryStore
    ├── fake_bundle.go                          # FakeBundle + FakeBundleFactory
    ├── fake_reconciler.go                      # Records all calls, configurable phase
    └── fake_incremental_bundle.go              # FakeIncrementalBundleFactory
```

---

## Appendix B: Domain Model Reference

Pure value objects. No infrastructure dependencies.

| Type | Purpose | Key Fields |
|------|---------|------------|
| `Entry` | Persisted config override | `Kind`, `Scope`, `Subject`, `Key`, `Value any`, `Revision`, `UpdatedAt`, `UpdatedBy`, `Source` |
| `Kind` | Config vs Setting | `KindConfig` (`"config"`) or `KindSetting` (`"setting"`) |
| `Scope` | Visibility | `ScopeGlobal` (`"global"`) or `ScopeTenant` (`"tenant"`) |
| `Target` | Coordinate for a group of entries | `Kind` + `Scope` + `SubjectID`; constructor `NewTarget()` validates |
| `Revision` | Monotonic version counter | `uint64`; `RevisionZero = 0`; methods: `Next()`, `Uint64()` |
| `Actor` | Who made the change | `ID string` |
| `KeyDef` | Registry metadata per key | `Key`, `Kind`, `AllowedScopes`, `DefaultValue`, `ValueType`, `Validator ValidatorFunc`, `Secret`, `RedactPolicy`, `ApplyBehavior`, `MutableAtRuntime`, `Description`, `Group`, `Component` |
| `ReconcilerPhase` | Reconciler execution ordering | `PhaseStateSync` (0), `PhaseValidation` (1), `PhaseSideEffect` (2) |
| `Snapshot` | Immutable point-in-time view | `Configs`, `GlobalSettings`, `TenantSettings map[string]map[string]EffectiveValue`, `Revision`, `BuiltAt` |
| `EffectiveValue` | Resolved value with override info | `Key`, `Value`, `Default`, `Override`, `Source`, `Revision`, `Redacted` |
| `RuntimeBundle` | App-defined resource container | Interface: `Close(ctx) error` |
| `ApplyBehavior` | How changes propagate | See [Appendix F](#appendix-f-apply-behavior-taxonomy); has `Strength() int` (0-4 scale) |
| `ValueType` | Type constraint | `"string"`, `"int"`, `"bool"`, `"float"`, `"object"`, `"array"` |
| `RedactPolicy` | Secret handling | `RedactNone`, `RedactFull`, `RedactMask` |
| `BackendKind` | Storage backend | `BackendPostgres` or `BackendMongoDB` |
| `ValidatorFunc` | Custom value validation | `func(value any) error` |
| `ComponentNone` | Sentinel for no-rebuild keys | `"_none"` — for pure business-logic keys |

**Snapshot accessor methods** (nil-safe):
- `GetConfig(key)`, `GetGlobalSetting(key)`, `GetTenantSetting(tenantID, key)` → `(EffectiveValue, bool)`
- `ConfigValue(key, fallback)`, `GlobalSettingValue(key, fallback)`, `TenantSettingValue(tenantID, key, fallback)` → `any`

**Sentinel errors** (14):

```go
var (
    ErrKeyUnknown          = errors.New("unknown configuration key")
    ErrValueInvalid        = errors.New("invalid configuration value")
    ErrRevisionMismatch    = errors.New("revision mismatch")
    ErrScopeInvalid        = errors.New("scope not allowed for this key")
    ErrPermissionDenied    = errors.New("permission denied")
    ErrReloadFailed        = errors.New("configuration reload failed")
    ErrKeyNotMutable       = errors.New("key is not mutable at runtime")
    ErrSnapshotBuildFailed = errors.New("snapshot build failed")
    ErrBundleBuildFailed   = errors.New("runtime bundle build failed")
    ErrBundleSwapFailed    = errors.New("runtime bundle swap failed")
    ErrReconcileFailed     = errors.New("bundle reconciliation failed")
    ErrNoCurrentBundle     = errors.New("no current runtime bundle")
    ErrSupervisorStopped   = errors.New("supervisor has been stopped")
    ErrRegistryRequired    = errors.New("registry is required")
)
```

Per-enum parse errors: `ErrInvalidKind`, `ErrInvalidBackendKind`, `ErrInvalidScope`,
`ErrInvalidApplyBehavior`, `ErrInvalidValueType`, `ErrInvalidReconcilerPhase`.

---

## Appendix C: Ports Interface Reference

Seven interfaces defining all external dependencies:

```go
// Persistence — read/write config entries
type Store interface {
    Get(ctx context.Context, target domain.Target) (ReadResult, error)
    Put(ctx context.Context, target domain.Target, ops []WriteOp,
        expected domain.Revision, actor domain.Actor, source string) (domain.Revision, error)
}

type WriteOp struct { Key string; Value any; Reset bool }
type ReadResult struct { Entries []domain.Entry; Revision domain.Revision }

// Audit trail — change history
type HistoryStore interface {
    ListHistory(ctx context.Context, filter HistoryFilter) ([]HistoryEntry, error)
}

type HistoryEntry struct {
    Revision  domain.Revision
    Key       string
    Scope     string
    SubjectID string
    OldValue  any
    NewValue  any
    ActorID   string
    ChangedAt time.Time
}

type HistoryFilter struct { Kind, Scope, SubjectID, Key string; Limit, Offset int }

// Real-time change notifications
type ChangeFeed interface {
    Subscribe(ctx context.Context, handler func(ChangeSignal)) error  // blocks until ctx cancelled
}

type ChangeSignal struct {
    Target        domain.Target
    Revision      domain.Revision
    ApplyBehavior domain.ApplyBehavior
}

// Permission checking
type Authorizer interface {
    Authorize(ctx context.Context, permission string) error
}

// Identity extraction from request context
type IdentityResolver interface {
    Actor(ctx context.Context) (domain.Actor, error)
    TenantID(ctx context.Context) (string, error)
}

// Application-specific runtime dependency builder (FULL rebuild)
type BundleFactory interface {
    Build(ctx context.Context, snap domain.Snapshot) (domain.RuntimeBundle, error)
}

// INCREMENTAL rebuild — extends BundleFactory with component-granular rebuilds.
// When the Supervisor detects only a subset of components changed, it calls
// BuildIncremental instead of Build, reusing unchanged components.
type IncrementalBundleFactory interface {
    BundleFactory
    BuildIncremental(ctx context.Context, snap domain.Snapshot,
        previous domain.RuntimeBundle, prevSnap domain.Snapshot) (domain.RuntimeBundle, error)
}

// Side-effect applier when bundles change.
// Reconcilers are sorted by Phase before execution:
//   PhaseStateSync  → update shared state (ConfigManager, caches)
//   PhaseValidation → gates that can reject the change
//   PhaseSideEffect → external side effects (worker restarts)
type BundleReconciler interface {
    Name() string
    Phase() domain.ReconcilerPhase
    Reconcile(ctx context.Context, previous, candidate domain.RuntimeBundle,
              snap domain.Snapshot) error
}
```

---

## Appendix D: Service Layer Reference

### Registry (`commons/systemplane/registry/`)

Thread-safe in-memory registry of key definitions:

```go
type Registry interface {
    Register(def domain.KeyDef) error
    MustRegister(def domain.KeyDef)         // panics — startup only
    Get(key string) (domain.KeyDef, bool)
    List(kind domain.Kind) []domain.KeyDef  // sorted by key name
    Validate(key string, value any) error   // nil value always valid (reset)
}

func New() Registry   // returns *inMemoryRegistry (RWMutex-protected)
```

**Validation** (`validation.go`):
- `validateValue(def, value)` → type check + custom validator
- **JSON coercion**: `float64` without fractional part accepted as `int`; `int`/`int64` widened to `float`
- `isObjectCompatible(value)` uses `reflect.Map`; `isArrayCompatible(value)` uses `reflect.Array`/`Slice`
- Nil values always pass validation (they mean "reset to default")

### Manager

```go
type Manager interface {
    GetConfigs(ctx context.Context) (ResolvedSet, error)
    GetSettings(ctx context.Context, subject Subject) (ResolvedSet, error)
    PatchConfigs(ctx context.Context, req PatchRequest) (WriteResult, error)
    PatchSettings(ctx context.Context, subject Subject, req PatchRequest) (WriteResult, error)
    GetConfigSchema(ctx context.Context) ([]SchemaEntry, error)
    GetSettingSchema(ctx context.Context) ([]SchemaEntry, error)
    GetConfigHistory(ctx context.Context, filter HistoryFilter) ([]HistoryEntry, error)
    GetSettingHistory(ctx context.Context, filter HistoryFilter) ([]HistoryEntry, error)
    ApplyChangeSignal(ctx context.Context, signal ChangeSignal) error
    Resync(ctx context.Context) error
}
```

**`ManagerConfig`** (constructor dependencies):

```go
type ManagerConfig struct {
    Registry             registry.Registry
    Store                ports.Store
    History              ports.HistoryStore
    Supervisor           Supervisor
    Builder              *SnapshotBuilder

    // ConfigWriteValidator is called BEFORE persistence with a preview snapshot.
    // Return non-nil error to reject the write.
    ConfigWriteValidator func(ctx context.Context, snapshot domain.Snapshot) error

    // StateSync is called AFTER successful writes for live-read escalation.
    // Used to update ConfigManager atomically.
    StateSync            func(ctx context.Context, snapshot domain.Snapshot)
}
```

**Key behaviors:**
- **Read path**: Uses supervisor's cached snapshot when available; falls back to builder
- **Write path**: `validate ops → preview snapshot (if ConfigWriteValidator configured) → escalate → store.Put → apply escalation`
- **Escalation application**: Maps strongest `ApplyBehavior` to supervisor method:
  - `ApplyBootstrapOnly` → no-op
  - `ApplyLiveRead` → `PublishSnapshot` + `StateSync` callback
  - `ApplyWorkerReconcile` → `ReconcileCurrent`
  - `ApplyBundleRebuild` / `ApplyBundleRebuildAndReconcile` → full `Reload`
- **Redaction**: All read results and history entries are redacted per `RedactPolicy`/`Secret` flag
- **Masking**: `RedactMask` shows last 4 runes; `RedactFull` and `Secret=true` show `"****"`

**Supporting types:**
- `Subject { Scope, SubjectID }` — settings target
- `PatchRequest { Ops []WriteOp, ExpectedRevision, Actor, Source }` — write input
- `WriteResult { Revision }` — write output
- `ResolvedSet { Values map[string]EffectiveValue, Revision }` — read output
- `SchemaEntry { Key, Kind, AllowedScopes, ValueType, DefaultValue, MutableAtRuntime, ApplyBehavior, Secret, RedactPolicy, Description, Group }` — schema metadata

### Supervisor

```go
type Supervisor interface {
    Current() domain.RuntimeBundle
    Snapshot() domain.Snapshot
    PublishSnapshot(ctx context.Context, snap domain.Snapshot, reason string) error
    ReconcileCurrent(ctx context.Context, snap domain.Snapshot, reason string) error
    Reload(ctx context.Context, reason string, extraTenantIDs ...string) error
    Stop(ctx context.Context) error
}
```

**`SupervisorConfig`**:

```go
type SupervisorConfig struct {
    Builder     *SnapshotBuilder
    Factory     ports.BundleFactory
    Reconcilers []ports.BundleReconciler

    // Observer is invoked AFTER each successful reload with structured info
    // about the build strategy (full vs incremental).
    Observer func(ReloadEvent)
}

type ReloadEvent struct {
    Strategy BuildStrategy              // "full" or "incremental"
    Reason   string                     // caller-supplied (e.g., "changefeed-signal")
    Snapshot domain.Snapshot
    Bundle   domain.RuntimeBundle
}
```

**Reload lifecycle** (the heart of the system):

1. **Build snapshot**: `builder.BuildFull(ctx, tenantIDs...)`
2. **Build bundle**: Try incremental first (if factory implements `IncrementalBundleFactory` and previous exists), fall back to full
3. **Reconcile BEFORE commit**: Run all reconcilers against candidate while previous is still active (prevents state corruption on failure)
4. **Atomic swap**: `snapshot.Store(&snap)` + `bundle.Store(&holder{candidate})`
5. **Resource adoption**: If candidate implements `resourceAdopter`, call `AdoptResourcesFrom(previous)` to nil-out transferred pointers
6. **Observer callback**: Notify host application (e.g., update bundleState, swap loggers)
7. **Close previous**: `previous.Close()` — only tears down REPLACED components since transferred pointers are nil

**Hidden interfaces** (implement on your bundle for advanced patterns):
- `resourceAdopter { AdoptResourcesFrom(previous RuntimeBundle) }` — called after commit to mark transferred resources
- `rollbackDiscarder { Discard(ctx) error }` — called on failed candidate instead of `Close()`

### SnapshotBuilder

```go
type SnapshotBuilder struct { registry Registry; store Store }

func NewSnapshotBuilder(reg, store) (*SnapshotBuilder, error)

func (b) BuildConfigs(ctx) (map[string]EffectiveValue, Revision, error)
func (b) BuildGlobalSettings(ctx) (map[string]EffectiveValue, Revision, error)
func (b) BuildSettings(ctx, Subject) (map[string]EffectiveValue, Revision, error)
func (b) BuildFull(ctx, tenantIDs ...string) (Snapshot, error)
```

**Override cascade** (3-layer for tenant settings):
1. `initDefaults(defs)` → populate from KeyDef.DefaultValue
2. `applyOverrides(effective, entries, source)` → overlay store entries
3. **Tenant path**: `registry defaults → global override → per-tenant override`

### Escalation

```go
func Escalate(reg Registry, ops []WriteOp) (ApplyBehavior, []string, error)
```

- Returns strongest `ApplyBehavior` across all ops (by `Strength()` 0-4)
- Rejects `ApplyBootstrapOnly` and `MutableAtRuntime=false` keys
- Rejects duplicate keys in batch
- Empty batch → `ApplyLiveRead`
- Returns the list of keys that drove the escalation

---

## Appendix E: Bootstrap Configuration

| File | Purpose |
|------|---------|
| `config.go` | `BootstrapConfig`, `PostgresBootstrapConfig`, `MongoBootstrapConfig`, `SecretStoreConfig` |
| `backend.go` | `BackendFactory` registry, `RegisterBackendFactory()`, `NewBackendFromConfig()` → `BackendResources{Store, History, ChangeFeed, Closer}` |
| `builtin/backend.go` | `init()` registers Postgres + MongoDB factories |
| `env.go` | `LoadFromEnv()` reads `SYSTEMPLANE_*` env vars |
| `classifier.go` | `IsBootstrapOnly(def)` — `!MutableAtRuntime || ApplyBootstrapOnly`; `IsRuntimeManaged(def)` — inverse |
| `defaults.go` | Default table/collection names |
| `postgres_identifiers.go` | Regex validation for PG identifiers (`^[a-z_][a-z0-9_]{0,62}$`) |

**Environment variables** for standalone systemplane backend:

| Variable | Default | Description |
|----------|---------|-------------|
| `SYSTEMPLANE_BACKEND` | — | `postgres` or `mongodb` |
| `SYSTEMPLANE_POSTGRES_DSN` | — | PostgreSQL DSN (falls back to app's PG DSN) |
| `SYSTEMPLANE_POSTGRES_SCHEMA` | `system` | Schema name |
| `SYSTEMPLANE_POSTGRES_ENTRIES_TABLE` | `runtime_entries` | Entries table |
| `SYSTEMPLANE_POSTGRES_HISTORY_TABLE` | `runtime_history` | History table |
| `SYSTEMPLANE_POSTGRES_REVISION_TABLE` | `runtime_revisions` | Revisions table |
| `SYSTEMPLANE_POSTGRES_NOTIFY_CHANNEL` | `systemplane_changes` | PG LISTEN/NOTIFY channel |
| `SYSTEMPLANE_SECRET_MASTER_KEY` | — | AES-256-GCM master key (32 bytes, raw or base64) |
| `SYSTEMPLANE_MONGODB_URI` | — | MongoDB connection URI |
| `SYSTEMPLANE_MONGODB_DATABASE` | `systemplane` | MongoDB database |
| `SYSTEMPLANE_MONGODB_ENTRIES_COLLECTION` | `runtime_entries` | Entries collection |
| `SYSTEMPLANE_MONGODB_HISTORY_COLLECTION` | `runtime_history` | History collection |
| `SYSTEMPLANE_MONGODB_WATCH_MODE` | `change_stream` | `change_stream` or `poll` |
| `SYSTEMPLANE_MONGODB_POLL_INTERVAL_SEC` | `5` | Poll interval (poll mode only) |

---

## Appendix F: Apply Behavior Taxonomy

Every config key MUST be classified with exactly one `ApplyBehavior`:

| ApplyBehavior | Code Constant | Strength | Runtime Effect | Use When |
|---------------|---------------|----------|----------------|----------|
| **bootstrap-only** | `domain.ApplyBootstrapOnly` | 4 | Immutable after startup. Never changes. | Server listen address, TLS, auth enable, telemetry endpoints |
| **bundle-rebuild+worker-reconcile** | `domain.ApplyBundleRebuildAndReconcile` | 3 | Full bundle swap: new infra clients AND worker restart | Worker enable/disable (needs new connections + restart) |
| **bundle-rebuild** | `domain.ApplyBundleRebuild` | 2 | Full bundle swap: new PG/Redis/RMQ/S3 clients | Connection strings, pool sizes, credentials |
| **worker-reconcile** | `domain.ApplyWorkerReconcile` | 1 | Reconciler restarts affected workers | Worker intervals, scheduler periods |
| **live-read** | `domain.ApplyLiveRead` | 0 | Read from snapshot on every request. Zero cost. | Rate limits, timeouts, cache TTLs — anything read per-request |

**Strength** determines escalation: when a PATCH contains multiple keys with different
behaviors, `Escalate()` picks the strongest (highest number). If any key is
`ApplyBootstrapOnly` or `MutableAtRuntime=false`, the entire write is rejected.

**Classification decision tree**:

```
Is this key needed BEFORE the systemplane itself can start?
  YES → ApplyBootstrapOnly (server address, auth enable, telemetry)
  NO ↓

Can this key be read per-request from a snapshot without side effects?
  YES → ApplyLiveRead (rate limits, timeouts, TTLs)
  NO ↓

Does changing this key require rebuilding infrastructure clients?
  YES → Does it ALSO require restarting background workers?
    YES → ApplyBundleRebuildAndReconcile (worker enable + storage changes)
    NO  → ApplyBundleRebuild (DB connections, pool sizes, credentials)
  NO ↓

Does changing this key require restarting background workers?
  YES → ApplyWorkerReconcile (worker intervals, scheduler periods)
  NO  → ApplyLiveRead (safe default for read-only configs)
```

---

## Appendix G: Screening Methodology

Before implementing, screen the target service to build the key inventory:

### G.1 Identify All Configuration Sources

```bash
# In the target repo:

# 1. Find the Config struct
grep -rn 'type Config struct' internal/ --include='*.go'

# 2. Find all envDefault tags
grep -rn 'envDefault:' internal/ --include='*.go' | sort

# 3. Find env var reads outside Config struct
grep -rn 'os.Getenv\|viper.Get' internal/ --include='*.go' | grep -v _test.go

# 4. Find .env files
find . -name '.env*' -o -name '*.yaml.example' | head -20

# 5. Find file-based config loading
grep -rn 'viper\.\|yaml.Unmarshal\|json.Unmarshal.*config' internal/ --include='*.go'
```

### G.2 Classify Infrastructure vs Application Config

**Infrastructure (stays as env-var with defaults in code)**:
- Database connection strings (PG host, port, user, password) → `Component: "postgres"`
- Redis connection (host, master name, password) → `Component: "redis"`
- RabbitMQ connection (URI, host, port, user, password) → `Component: "rabbitmq"`
- Object storage (endpoint, bucket, credentials) → `Component: "s3"`
- These become `ApplyBundleRebuild` keys in systemplane

**Bootstrap-Only (env-var, immutable after startup)**:
- Server listen address and port → `Component: ComponentNone` (not mutable)
- TLS certificate paths
- Auth enable/disable
- Auth service address
- Telemetry endpoints (OTEL collector)
- These become `ApplyBootstrapOnly` keys

**Application Runtime (hot-reloadable)**:
- Rate limits → `Component: ComponentNone` + `ApplyLiveRead`
- Worker intervals and enable/disable flags → `Component: ComponentNone` + `ApplyWorkerReconcile`
- Timeouts (webhook, health check) → `Component: ComponentNone` + `ApplyLiveRead`
- Feature flags → `Component: ComponentNone` + `ApplyLiveRead`
- Cache TTLs → `Component: ComponentNone` + `ApplyLiveRead`

### G.3 Identify Runtime Dependencies (Bundle Candidates)

List all infrastructure clients that the service creates at startup:

```bash
# Find client constructors
grep -rn 'libPostgres.New\|libRedis.New\|libRabbitmq.New\|storage.New' internal/ --include='*.go'

# Find connection pools
grep -rn 'sql.Open\|pgx\|redis.New\|amqp.Dial' internal/ --include='*.go'
```

Each of these becomes a field in the `InfraBundle` and a component name in
`keyComponentMap`.

### G.4 Identify Background Workers

```bash
# Find worker patterns
grep -rn 'ticker\|time.NewTicker\|cron\|worker\|scheduler' internal/ --include='*.go' | grep -v _test.go
```

Each worker with configurable intervals becomes a `WorkerReconciler` candidate.

### G.5 Generate the Key Inventory

Create a table with columns:
- Key name (dotted: `postgres.primary_host`)
- Current env var (`POSTGRES_HOST`)
- Default value
- Type (`string`, `int`, `bool`, `float`)
- Kind (`config` or `setting`)
- Scope (`global` or `tenant`)
- ApplyBehavior
- Component (`postgres`, `redis`, `rabbitmq`, `s3`, `http`, `logger`, `_none`)
- Secret (yes/no)
- MutableAtRuntime (yes/no)
- Group
- Validator (if any)

---

## Appendix H: Testing Patterns

### H.1 Key Registration Tests

```go
func TestRegister{Service}Keys_AllKeysValid(t *testing.T) {
    reg := registry.New()
    err := Register{Service}Keys(reg)
    require.NoError(t, err)

    configs := reg.List(domain.KindConfig)
    settings := reg.List(domain.KindSetting)
    assert.Greater(t, len(configs)+len(settings), 0)
}

func TestRegister{Service}Keys_DefaultsMatchConfig(t *testing.T) {
    reg := registry.New()
    _ = Register{Service}Keys(reg)
    defaults := defaultConfig()

    for _, def := range reg.List(domain.KindConfig) {
        // Compare def.DefaultValue against defaults struct field
    }
}
```

### H.2 Bundle Factory Tests

```go
func TestBundleFactory_Build_Success(t *testing.T) {
    snap := buildTestSnapshot(t)
    factory := New{Service}BundleFactory(testBootstrapConfig())

    bundle, err := factory.Build(context.Background(), snap)
    require.NoError(t, err)
    defer bundle.Close(context.Background())

    b := bundle.(*{Service}Bundle)
    assert.NotNil(t, b.Infra.Postgres)
    assert.NotNil(t, b.Infra.Redis)
}

func TestBundleFactory_BuildIncremental_ReusesUnchangedComponents(t *testing.T) {
    snap1 := buildTestSnapshot(t)
    snap2 := modifySnapshot(snap1, "rate_limit.max", 500) // only changes _none component

    factory := New{Service}BundleFactory(testBootstrapConfig())
    ctx := context.Background()
    prev, _ := factory.Build(ctx, snap1)

    candidate, _ := factory.BuildIncremental(ctx, snap2, prev, snap1)
    b := candidate.(*{Service}Bundle)

    // Postgres should be reused (not owned by candidate)
    assert.False(t, b.ownsPostgres)
}
```

### H.3 Reconciler Tests

```go
func TestWorkerReconciler_AppliesConfig(t *testing.T) {
    wm := NewTestWorkerManager()
    reconciler := NewWorkerReconciler(wm)

    snap := buildModifiedSnapshot(t, "export_worker.enabled", true)
    err := reconciler.Reconcile(context.Background(), nil, nil, snap)
    require.NoError(t, err)

    assert.True(t, wm.LastAppliedConfig().ExportWorkerEnabled)
}
```

### H.4 Contract Tests (Backend-Agnostic)

Run the `storetest` and `feedtest` contract suites against your backend:

```go
func TestPostgresStore_ContractSuite(t *testing.T) {
    store, history := setupPostgresStore(t) // testcontainers
    storetest.RunAll(t, /* factory that returns store+history */)
}

func TestPostgresChangeFeed_ContractSuite(t *testing.T) {
    feed := setupPostgresFeed(t) // testcontainers
    feedtest.RunAll(t, /* factory that returns store+feed */)
}
```

**Store contract tests (15):**
- GetEmptyTarget, PutSingleOp, PutBatch, OptimisticConcurrency, ResetOp
- NilValueOp, EmptyBatchIsNoOp, TypedNilValueOp, PutPreservesOtherKeys
- RevisionMonotonicallyIncreasing, ConcurrentPuts
- HistoryRecording, BatchHistoryConsistency, HistoryFiltering, HistoryPagination

**Feed contract tests (3):**
- SubscribeReceivesSignal, ContextCancellationStops, MultipleSignals

### H.5 ConfigWriteValidator Tests

```go
func TestConfigWriteValidator_RejectsInvalidConfig(t *testing.T) {
    // Test that production guards prevent persisting invalid config
    snap := buildSnapshot(t)
    snap.Configs["rate_limit.enabled"] = ev(false) // can't disable in production

    err := validator(context.Background(), snap)
    assert.Error(t, err)
}
```

---

## Appendix I: Operational Guide

### I.1 For Operators: What Changes

| Before | After |
|--------|-------|
| Edit `.env` + restart | `PATCH /v1/system/configs` (no restart) |
| Edit YAML + wait for fsnotify | `PATCH /v1/system/configs` (instant) |
| No audit trail | `GET /v1/system/configs/history` |
| No schema discovery | `GET /v1/system/configs/schema` |
| No concurrency protection | `If-Match` / `ETag` headers |
| Manual rollback | Change feed propagates across replicas |
| Full restart for any change | Only `ApplyBootstrapOnly` keys need restart |

### I.2 Bootstrap-Only Keys (Require Restart)

Document in `config/.config-map.example`:

```
# {Service} — Bootstrap-Only Configuration (requires restart)
#
# These are the ONLY settings that require a container/pod restart.
# Everything else is hot-reloadable via:
#
#   GET  /v1/system/configs          — view current runtime config
#   PATCH /v1/system/configs         — change any runtime-managed key
#   GET  /v1/system/configs/schema   — see all keys, types, and mutability
#   GET  /v1/system/configs/history  — audit trail of changes

ENV_NAME=development
SERVER_ADDRESS=:8080
AUTH_ENABLED=false
ENABLE_TELEMETRY=false
# ... etc
```

### I.3 Docker Compose (Zero-Config)

```yaml
services:
  myservice:
    build: .
    ports:
      - "${SERVER_PORT:-8080}:8080"
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST:-postgres}
      - POSTGRES_PORT=${POSTGRES_PORT:-5432}
      - REDIS_HOST=${REDIS_HOST:-redis}
    # NO env_file directive — defaults baked into binary
    depends_on:
      postgres:
        condition: service_healthy
```

### I.4 Systemplane Backend Config

By default, the systemplane reuses the application's primary PostgreSQL connection.
Override with `SYSTEMPLANE_*` env vars for a separate backend:

```bash
# Use app's Postgres (default — no extra config needed)
# The init function builds the DSN from the app's POSTGRES_* env vars

# Or use a dedicated backend:
SYSTEMPLANE_BACKEND=postgres
SYSTEMPLANE_POSTGRES_DSN=postgres://user:pass@host:5432/systemplane?sslmode=require

# Secret encryption (REQUIRED — rejected in production without it):
SYSTEMPLANE_SECRET_MASTER_KEY=<32-byte key, raw or base64>
```

### I.5 Graceful Degradation

If the systemplane fails to initialize, the service continues without it:
- Config values from env vars still work
- No runtime mutation API available
- No hot-reload capability
- Workers run with static config

This is by design — the service never fails to start due to systemplane issues.

### I.6 HTTP API Endpoints

After migration, the service exposes these endpoints:

| Method | Path | Description | Auth Permission |
|--------|------|-------------|-----------------|
| `GET` | `/v1/system/configs` | View all resolved config values | `system/configs:read` |
| `PATCH` | `/v1/system/configs` | Update config values (with `If-Match` for concurrency) | `system/configs:write` |
| `GET` | `/v1/system/configs/schema` | View all key definitions (types, defaults, mutability) | `system/configs/schema:read` |
| `GET` | `/v1/system/configs/history` | Audit trail of config changes | `system/configs/history:read` |
| `POST` | `/v1/system/configs/reload` | Force a full reload | `system/configs/reload:write` |
| `GET` | `/v1/system/settings` | View resolved settings (`?scope=global\|tenant`) | `system/settings:read` |
| `PATCH` | `/v1/system/settings` | Update settings | `system/settings:write` |
| `GET` | `/v1/system/settings/schema` | View setting key definitions | `system/settings/schema:read` |
| `GET` | `/v1/system/settings/history` | Settings audit trail | scope-dependent |

Settings routes have an extra `settingsScopeAuthorization` middleware that
elevates to `system/settings/global:{action}` when `?scope=global` is queried.

**PATCH Request Format:**

```json
PATCH /v1/system/configs
If-Match: "42"
Content-Type: application/json

{
  "values": {
    "rate_limit.max": 200,
    "rate_limit.expiry_sec": 120,
    "export_worker.enabled": false
  }
}
```

**PATCH Response Format:**

```json
HTTP/1.1 200 OK
ETag: "43"

{
  "revision": 43
}
```

**Schema Response Format:**

```json
{
  "keys": [
    {
      "key": "rate_limit.max",
      "kind": "config",
      "valueType": "int",
      "defaultValue": 100,
      "mutableAtRuntime": true,
      "applyBehavior": "live-read",
      "secret": false,
      "description": "Maximum requests per window",
      "group": "rate_limit",
      "allowedScopes": ["global"]
    }
  ]
}
```

**HTTP Error Mapping:**

| Domain Error | HTTP Status | Code |
|-------------|-------------|------|
| `ErrKeyUnknown` | 400 | `system_key_unknown` |
| `ErrValueInvalid` | 400 | `system_value_invalid` |
| `ErrKeyNotMutable` | 400 | `system_key_not_mutable` |
| `ErrScopeInvalid` | 400 | `system_scope_invalid` |
| `ErrRevisionMismatch` | 409 | `system_revision_mismatch` |
| `ErrPermissionDenied` | 403 | `system_permission_denied` |
| `ErrReloadFailed` | 500 | `system_reload_failed` |
| `ErrSupervisorStopped` | 503 | `system_unavailable` |

### I.7 Adapters Reference

| Adapter | Location | Key Feature |
|---------|----------|-------------|
| PostgreSQL Store | `adapters/store/postgres/` | 3 tables + indexes, optimistic concurrency, `pg_notify`, integer-preserving JSON decode |
| MongoDB Store | `adapters/store/mongodb/` | Sentinel revision doc (`__revision_meta__`), multi-doc transactions, requires replica set |
| Secret Codec | `adapters/store/secretcodec/` | AES-256-GCM with random nonce, AAD = `"kind\|scope\|subject\|key"`, envelope format `{__systemplane_secret_v: 1, alg, nonce, ciphertext}` |
| PostgreSQL ChangeFeed | `adapters/changefeed/postgres/` | LISTEN/NOTIFY, exponential backoff reconnect, revision resync on reconnect |
| MongoDB ChangeFeed | `adapters/changefeed/mongodb/` | Change stream or poll mode, auto-reconnect, revision-jump escalation |
| DebouncedFeed | `adapters/changefeed/debounce.go` | Per-target trailing-edge debounce (default 100ms + 50ms jitter), escalates to strongest ApplyBehavior in window |
| SafeInvokeHandler | `adapters/changefeed/safe_handler.go` | Catches handler panics, returns `ErrHandlerPanic` |
| Fiber HTTP | `adapters/http/fiber/` | 9 endpoints, DTOs, `If-Match`/`ETag` concurrency, middleware, domain→HTTP error mapping |
| Store Contract Tests | `adapters/store/storetest/` | 15 backend-agnostic tests: CRUD, concurrency, reset, history, pagination |
| Feed Contract Tests | `adapters/changefeed/feedtest/` | 3 backend-agnostic tests: signal receipt, cancellation, multiple signals |

**PostgreSQL Store DDL** (created automatically):
- `runtime_entries`: PK (`kind`, `scope`, `subject`, `key`), JSONB `value`, BIGINT `revision`
- `runtime_history`: BIGSERIAL `id`, `old_value`/`new_value` JSONB, `actor_id`, `changed_at`
- `runtime_revisions`: PK (`kind`, `scope`, `subject`), `revision` counter, `apply_behavior`

### I.8 Test Utilities

| Fake | Implements | Key Features |
|------|-----------|--------------|
| `FakeStore` | `ports.Store` | In-memory, optimistic concurrency, `Seed()` for pre-population |
| `FakeHistoryStore` | `ports.HistoryStore` | In-memory, newest-first, `Append()`/`AppendForKind()` |
| `FakeBundle` / `FakeBundleFactory` | `RuntimeBundle` / `BundleFactory` | Tracks Close state, `SetError()`, `CallCount()` |
| `FakeReconciler` | `BundleReconciler` | Configurable phase, records all `ReconcileCall`s, `SetError()` |
| `FakeIncrementalBundleFactory` | `IncrementalBundleFactory` | Embeds `FakeBundleFactory` + `IncrementalBuildFunc`, `IncrementalCallCount()` |

---

## Appendix J: Core two Service Reference

The Core two service registers **~130 keys** across 20 groups, split into 9 focused
sub-files. Here's the breakdown by group and ApplyBehavior:

| Group | Keys | BootstrapOnly | BundleRebuild | LiveRead | WorkerReconcile | Rebuild+Reconcile |
|-------|------|---------------|---------------|----------|-----------------|-------------------|
| `app` | 2 | 1 | 1 | - | - | - |
| `server` | 8 | 4 | 4 | - | - | - |
| `tenancy` | 11 | - | 11 | - | - | - |
| `postgres` | 19 | - | 18 | 1 | - | - |
| `redis` | 12 | - | 12 | - | - | - |
| `rabbitmq` | 8 | - | 8 | - | - | - |
| `auth` | 3 | 3 | - | - | - | - |
| `swagger` | 3 | - | 3 | - | - | - |
| `telemetry` | 7 | 7 | - | - | - | - |
| `rate_limit` | 7 | - | - | 7 | - | - |
| `infrastructure` | 2 | - | 1 | 1 | - | - |
| `idempotency` | 3 | 1 | 2 | - | - | - |
| `callback_rate_limit` | 1 | - | - | 1 | - | - |
| `fetcher` | 9 | - | 4 | - | 3 | 2 |
| `deduplication` | 1 | - | - | 1 | - | - |
| `object_storage` | 6 | - | 6 | - | - | - |
| `export_worker` | 4 | - | - | 1 | 1 | 2 |
| `webhook` | 1 | - | - | 1 | - | - |
| `cleanup_worker` | 4 | - | - | - | 2 | 2 |
| `scheduler` | 1 | - | - | - | 1 | - |
| `archival` | 12 | - | - | 1 | 3 | 8 |

**Secrets**: ~9 keys with `RedactFull` policy (passwords, tokens, certificates, access keys).

**Components referenced**: `postgres`, `redis`, `rabbitmq`, `s3`, `http`, `logger`, `_none`.

### Key Sub-File Organization (Reference)

| Sub-File | Groups Covered | Key Count |
|----------|---------------|-----------|
| `systemplane_keys_app_server.go` | app, server | ~11 |
| `systemplane_keys_tenancy.go` | tenancy | ~11 |
| `systemplane_keys_postgres.go` | postgres | ~19 |
| `systemplane_keys_messaging.go` | redis, rabbitmq | ~20 |
| `systemplane_keys_runtime_http.go` | auth, swagger, telemetry, rate_limit | ~17 |
| `systemplane_keys_runtime_services.go` | infrastructure, idempotency, callback_rate_limit, fetcher | ~14 |
| `systemplane_keys_storage_export.go` | deduplication, object_storage, export_worker | ~11 |
| `systemplane_keys_workers.go` | webhook, cleanup_worker | ~5 |
| `systemplane_keys_archival.go` | scheduler, archival | ~12 |

---

## Appendix K: Quick Reference Commands

```bash
# LOCAL DEV ONLY — requires AUTH_ENABLED=false

# View current runtime config
curl -s http://localhost:4018/v1/system/configs | jq

# View schema (all keys, types, mutability)
curl -s http://localhost:4018/v1/system/configs/schema | jq

# Change a runtime key
curl -X PATCH http://localhost:4018/v1/system/configs \
  -H 'Content-Type: application/json' \
  -H 'If-Match: "current-revision"' \
  -d '{"values": {"rate_limit.max": 200}}'

# View change history
curl -s http://localhost:4018/v1/system/configs/history | jq

# Force full reload
curl -X POST http://localhost:4018/v1/system/configs/reload

# View settings
curl -s http://localhost:4018/v1/system/settings?scope=global | jq

# Change a setting
curl -X PATCH http://localhost:4018/v1/system/settings \
  -H 'Content-Type: application/json' \
  -H 'If-Match: "current-revision"' \
  -d '{"scope": "global", "values": {"feature.enabled": true}}'
```

---

## Appendix L: Files to Create per Service

### Core Systemplane Wiring

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `systemplane_init.go` | Init function with 11-step boot + change feed start | `internal/bootstrap/systemplane_init.go` |
| `systemplane_mount.go` | HTTP route registration + swagger merge | `internal/bootstrap/systemplane_mount.go` |

### Key Definitions (split by group)

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `systemplane_keys.go` | Orchestrator: `Register{Service}Keys()` + `{service}KeyDefs()` | `internal/bootstrap/systemplane_keys.go` |
| `systemplane_keys_{group}.go` | Per-group key definitions | `internal/bootstrap/systemplane_keys_{group}.go` |
| `systemplane_keys_validation.go` | Validator functions used by KeyDef.Validator | `internal/bootstrap/systemplane_keys_validation.go` |
| `systemplane_keys_helpers.go` | `concatKeyDefs()` utility | `internal/bootstrap/systemplane_keys_helpers.go` |

### Bundle + Factory

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `systemplane_bundle.go` | Bundle struct + Close + AdoptResourcesFrom (ownership tracking) | `internal/bootstrap/systemplane_bundle.go` |
| `systemplane_factory.go` | BundleFactory + IncrementalBundleFactory (full + incremental) | `internal/bootstrap/systemplane_factory.go` |
| `systemplane_factory_infra.go` | Per-component builders: buildPostgres, buildRedis, buildRabbitMQ, buildS3 | `internal/bootstrap/systemplane_factory_infra.go` |

### Reconcilers

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `systemplane_reconciler_http.go` | HTTP policy validation (PhaseValidation) | `internal/bootstrap/systemplane_reconciler_http.go` |
| `systemplane_reconciler_publishers.go` | RabbitMQ publisher staging (PhaseValidation) | `internal/bootstrap/systemplane_reconciler_publishers.go` |
| `systemplane_reconciler_worker.go` | Worker restart (PhaseSideEffect) | `internal/bootstrap/systemplane_reconciler_worker.go` |

### Identity + Authorization

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `systemplane_identity.go` | JWT → Actor bridge | `internal/bootstrap/systemplane_identity.go` |
| `systemplane_authorizer.go` | Permission mapping | `internal/bootstrap/systemplane_authorizer.go` |

### Config Manager Integration

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `config_manager_systemplane.go` | Snapshot → Config hydration | `internal/bootstrap/config_manager_systemplane.go` |
| `config_manager_seed.go` | Env → Store one-time seed | `internal/bootstrap/config_manager_seed.go` |
| `config_manager_helpers.go` | Type-safe value comparison | `internal/bootstrap/config_manager_helpers.go` |
| `config_validation.go` | Production config guards | `internal/bootstrap/config_validation.go` |

### Runtime Integration

| File | Purpose | Core two Reference |
|------|---------|-------------------|
| `active_bundle_state.go` | Thread-safe live-read accessor for current bundle | `internal/bootstrap/active_bundle_state.go` |
| `config/.config-map.example` | Bootstrap-only key reference (operators) | `config/.config-map.example` |

### Files to Delete

| File | Reason |
|------|--------|
| `config/.env.example` | Replaced by code defaults + `.config-map.example` |
| `config/*.yaml.example` | No more YAML config |
| Config API handlers (old) | Replaced by systemplane HTTP adapter |
| Config file watcher | Replaced by change feed |
| Config audit publisher (old) | Replaced by systemplane history |
| Config YAML loader | No more YAML |

### Files to Modify

| File | Change |
|------|--------|
| `config_loading.go` | Remove YAML loading, keep env-only |
| `config_defaults.go` | Derive from `{service}KeyDefs()` via `configFromSnapshot(defaultSnapshotFromKeyDefs(...))` |
| `config_manager.go` | Add `UpdateFromSystemplane()`, `enterSeedMode()`, `atomic.Pointer[Config]` for lock-free reads |
| `init.go` | Wire systemplane init after workers, before HTTP mount; add reload observer callback |
| `service.go` | Add systemplane shutdown sequence (5-step) |
| `docker-compose.yml` | Remove `env_file`, inline defaults with `${VAR:-default}` |
| `Makefile` | Remove `set-env`, `clear-envs` targets |

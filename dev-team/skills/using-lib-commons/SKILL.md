---
name: ring:using-lib-commons
description: |
  Dual-mode skill for github.com/LerianStudio/lib-commons v5.0.2 — Lerian's shared Go library.

  Sweep Mode (primary): Dispatches 22 parallel explorer subagents to sweep any Lerian Go
  codebase for DIY implementations that should use lib-commons. Detects version drift,
  identifies replacement opportunities with file:line precision, generates tasks compatible
  with ring:dev-cycle for batched fixes.

  Reference Mode: Comprehensive catalog of lib-commons v5.0.2 packages — database
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
  - Need database, messaging, or infrastructure patterns
  - Migrating from older lib-commons versions (v4 → v5)
  - Implementing webhooks with SSRF protection and HMAC signing
  - Implementing Redis-backed dead-letter queues
  - Adding HTTP idempotency middleware
  - Managing TLS certificates with hot reload

skip_when: |
  - Working on non-Go services
  - Working on frontend code
  - Target codebase is Ring itself (no lib-commons dependency)

related:
  similar: [ring:using-dev-team, ring:dev-refactor, ring:production-readiness-audit]
---

# ring:using-lib-commons

This skill serves two distinct purposes. Choose the correct mode before proceeding.

## Mode Selection

MUST choose mode based on the request shape:

| Request Shape                                                | Mode          |
| ------------------------------------------------------------ | ------------- |
| "Sweep / audit / find opportunities / migrate to lib-commons"| **Sweep**     |
| "What does lib-commons provide for X?"                       | **Reference** |
| "How do I initialize Y from lib-commons?"                    | **Reference** |
| "Replace our DIY webhook delivery with lib-commons"          | **Sweep**     |
| "Show me the JWT API"                                        | **Reference** |

- **Sweep Mode** (primary): Active orchestration. Executes a 4-phase protocol that scans a
  target Lerian Go codebase, identifies DIY implementations that should be replaced with
  lib-commons calls, and emits tasks for `ring:dev-cycle` consumption.
- **Reference Mode**: Passive catalog. Read sections 1–15 below for API discovery and
  initialization patterns.

Sweep Mode uses Reference Mode content as explorer context — each explorer receives the
relevant catalog entries for its angle so it knows the target API surface.

## Table of Contents

| # | Section                          | Mode      | What You'll Find                                                          |
| - | -------------------------------- | --------- | ------------------------------------------------------------------------- |
| — | Mode Selection                   | Both      | How to choose sweep vs reference                                          |
| — | Sweep Protocol                   | Sweep     | 4-phase scan orchestration                                                |
| — | Explorer Angle Specs             | Sweep     | 22 DIY patterns and replacements                                          |
| — | Report Template                  | Sweep     | Findings format                                                           |
| — | Task Generation                  | Sweep     | ring:dev-cycle handoff format                                             |
| 1 | Package Catalog                  | Reference | all packages by domain                                                    |
| 2 | Common Initialization Pattern    | Reference | Typical service bootstrap                                                 |
| 3 | Database Connections             | Reference | postgres, mongo, redis, rabbitmq                                          |
| 4 | HTTP Toolkit                     | Reference | Middleware, rate limiting, pagination, validation, idempotency            |
| 5 | Observability                    | Reference | Logger, tracing, metrics, runtime, assert                                 |
| 6 | Resilience & Utilities           | Reference | Circuit breaker, backoff, safe math, pointers                             |
| 7 | Security                         | Reference | JWT, encryption, sensitive fields, AWS secrets, TLS certificate hot-reload|
| 8 | Transaction Domain               | Reference | Intent planning, balance posting, outbox                                  |
| 9 | Tenant Manager                   | Reference | Full multi-tenancy subsystem with event-driven discovery                  |
| 10| Webhook Delivery                 | Reference | SSRF-safe HMAC-signed delivery with retries                               |
| 11| Dead Letter Queue                | Reference | Redis-backed DLQ with exponential-backoff retry                           |
| 12| Root Package & Utilities         | Reference | App lifecycle, context helpers, business errors, UUID, env vars           |
| 13| Cross-Cutting Patterns           | Reference | Patterns shared across all packages                                       |
| 14| Which Package Do I Need?         | Reference | Decision tree for package selection                                       |
| 15| Breaking Changes                 | Reference | Migration notes for v4.2.0 through v5.0.2                                 |

---

# SWEEP MODE

MANDATORY: When invoked in Sweep Mode, the orchestrator MUST execute all four phases in
order. MUST NOT skip phases. MUST NOT shortcut Phase 3 by reducing explorer count.
FORBIDDEN: Producing a report based on the orchestrator's own code inspection — the 22
explorers are the source of truth for findings.

## Sweep Protocol

The sweep runs in four sequential phases. Each phase has a HARD GATE — MUST NOT proceed
to the next phase until the current phase produces its required artifact.

```
Phase 1: Version Reconnaissance   → version-report.json
Phase 2: CHANGELOG Delta Analysis → delta-report.json
Phase 3: Multi-Angle DIY Sweep    → 22 × libcommons-sweep-{N}-{angle}.json
Phase 4: Consolidated Report      → libcommons-sweep-report.md + tasks.json
```

★ Insight ─────────────────────────────────────
The 4-phase separation is deliberate. Version drift (Phase 1) and CHANGELOG delta
(Phase 2) provide the **upgrade posture** — is the codebase even on a version that has
the capabilities we're about to recommend? Phase 3 without Phases 1–2 produces findings
that may recommend APIs the project's pinned version doesn't have. Run them in order.
─────────────────────────────────────────────────

### Phase 1: Version Reconnaissance

MANDATORY steps (orchestrator executes directly):

1. **Read `go.mod`** at the target project root.
   - Extract the line matching `github.com/LerianStudio/lib-commons/vN` (or the
     unversioned module path if pre-v2).
   - Capture the exact pinned version (e.g., `v5.0.2`, `v4.2.0`).
   - If the dependency is absent, STOP and report: "Target is not a lib-commons consumer.
     Sweep not applicable."

2. **WebFetch latest release:**

   ```
   https://api.github.com/repos/LerianStudio/lib-commons/releases/latest
   ```

   Extract `tag_name` (e.g., `v5.0.2`) and `published_at`.

3. **Compare versions** and flag drift:

   | Condition                                   | Classification      |
   | ------------------------------------------- | ------------------- |
   | Pinned == Latest                            | Up-to-date          |
   | Pinned is patch behind                      | Minor drift         |
   | Pinned is minor behind                      | Moderate drift      |
   | Pinned is major behind (v4.x → v5.x)        | **Major upgrade**   |
   | Module path mismatch (no `/vN` suffix)      | **Module mismatch** |

4. **If v4.x detected:** Add a "major upgrade advisory" flag to the report. Phase 3
   explorers MUST receive this flag so they adjust their recommendations — some v5 APIs
   do not exist in v4 and the report must call out the upgrade as a prerequisite.

5. **Emit `version-report.json`** with fields:
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

3. **Classify each entry** into one of:
   - `new-package` — a package that did not exist at pinned version
   - `new-api` — a new exported symbol in an existing package
   - `breaking-change` — backward-incompatible change (requires migration)
   - `security-fix` — fix the consumer benefits from by upgrading
   - `performance` — optimization-only
   - `bugfix` — consumer-facing bug resolved

4. **Surface unadopted capabilities.** These become report highlights — features the
   consumer is eligible to adopt but hasn't yet.

5. **Emit `delta-report.json`** with a list of entries, each shaped:

   ```json
   {
     "version": "v5.0.0",
     "section": "Added",
     "classification": "new-package",
     "summary": "commons/webhook — SSRF-safe HMAC-signed webhook delivery"
   }
   ```

### Phase 3: Multi-Angle DIY Sweep

MANDATORY: Dispatch all 22 explorer angles. MUST NOT skip any angle. MUST dispatch in
**3 batches** (8 + 8 + 6) to avoid overwhelming parallelism. MUST wait for each batch to
complete before dispatching the next.

**Batch composition:**

| Batch | Angles                                      | Focus                                |
| ----- | ------------------------------------------- | ------------------------------------ |
| 1     | Angles 1, 2, 3, 4, 5, 6, 7, 8               | Infrastructure + HTTP                |
| 2     | Angles 9, 10, 11, 12, 13, 14, 15, 16        | Ergonomics + security + observability|
| 3     | Angles 17, 18, 19, 20, 21, 22               | Resilience + multi-tenant + utilities|

**Per-explorer dispatch contract:**

Each explorer MUST be dispatched with `subagent_type: ring:codebase-explorer`. The
prompt MUST contain exactly these sections:

```
## Target
<absolute path to target repo root>

## Your Angle
<angle number + name, e.g., "Angle 12: JWT DIY">

## Severity Calibration
<CRITICAL | HIGH | MEDIUM | LOW — from angle spec>

## What to Detect (DIY patterns)
<bullet list of grep patterns, import paths, code signatures>

## Replacement
<lib-commons package path + key APIs>

## Migration Complexity
<trivial | moderate | complex>

## Version Context
Pinned: <from Phase 1>
Latest: <from Phase 1>
Major upgrade required: <bool from Phase 1>

## Output
Write findings to: /tmp/libcommons-sweep-{N}-{angle-slug}.json
Schema: see below.
```

**Explorer output schema** (`/tmp/libcommons-sweep-{N}-{angle-slug}.json`):

```json
{
  "angle_number": 12,
  "angle_name": "JWT DIY",
  "severity": "CRITICAL",
  "migration_complexity": "moderate",
  "findings": [
    {
      "file": "internal/auth/parser.go",
      "line": 47,
      "diy_pattern": "jwt.Parse with no algorithm allowlist",
      "replacement": "commons/jwt.ParseAndValidate",
      "evidence_snippet": "token, err := jwt.Parse(raw, ...)",
      "notes": "Algorithm confusion vulnerable — accepts 'none'"
    }
  ],
  "summary": "2 files use raw jwt.Parse without algorithm allowlist",
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
- /tmp/version-report.json
- /tmp/delta-report.json
- /tmp/libcommons-sweep-*.json  (22 files)

## Outputs
1. /tmp/libcommons-sweep-report.md  (human-readable report — see Report Template)
2. /tmp/libcommons-sweep-tasks.json  (ring:dev-cycle task array — see Task Generation)

## Your Job
MUST read all 22 explorer files. MUST aggregate findings by severity. MUST produce the
report following the exact template below. MUST generate one task per DIY pattern cluster
(group findings in the same file/package into one task).

MUST NOT invent findings not present in explorer outputs.
MUST NOT omit findings that explorers flagged.
MUST NOT reclassify severity without explicit justification in the task description.
```

After synthesis completes, the orchestrator surfaces the report path + task count to the
user and offers handoff to `ring:dev-cycle`.

---

## Explorer Angle Specifications

MANDATORY: All 22 angles run on every sweep. The catalog below is the source of truth
for what each explorer looks for. MUST NOT edit angle specs at dispatch time — copy
verbatim into the explorer prompt.

---

#### Angle 1: Bootstrap & lifecycle

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- `signal.Notify(` with `os.Interrupt` or `syscall.SIGTERM` in `main.go` or `cmd/*/main.go`
- Manual `go func()` launches without panic recovery
- Custom `sync.WaitGroup` orchestration for shutdown
- Hand-rolled "start N goroutines, wait for signal, cancel context, wait for all" patterns
- `context.WithCancel(context.Background())` in `main()` wired manually through app layers

**lib-commons Replacement:**
- `commons.Launcher` — standard app lifecycle (start, run, shutdown, signal handling)
- `commons/server.ServerManager` — HTTP/gRPC server lifecycle with graceful drain

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

    var wg sync.WaitGroup
    wg.Add(1)
    go func() {
        defer wg.Done()
        runServer(ctx)
    }()

    <-sigCh
    cancel()
    wg.Wait()
}

// lib-commons (AFTER):
func main() {
    launcher := commons.NewLauncher(
        commons.WithServer(server.NewServerManager(cfg)),
        commons.WithLogger(logger),
    )
    if err := launcher.Run(context.Background()); err != nil {
        logger.Fatal("launcher failed", err)
    }
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for service bootstrap DIY. Search `main.go`, `cmd/*/main.go`, and
> any `internal/app/` or `internal/bootstrap/` packages. MUST flag manual
> `signal.Notify(os.Interrupt)` handlers, raw `go func()` launches in main, custom
> `sync.WaitGroup` shutdown orchestration, and hand-wired `context.WithCancel` +
> cancel-on-signal patterns. For each finding record file:line, the specific pattern, and
> whether the fix requires `commons.Launcher` (app-level) or `commons/server.ServerManager`
> (HTTP/gRPC only). Severity MEDIUM — these patterns work, but miss observability and
> graceful-drain integration.

---

#### Angle 2: PostgreSQL DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- `sql.Open("postgres"` or `sql.Open("pgx"` in any file
- `pgx.Connect(`, `pgxpool.New(`, `pgxpool.Connect(`
- Manual `SetMaxOpenConns` / `SetMaxIdleConns` / `SetConnMaxLifetime` tuning
- Hand-rolled migration runners (walking a directory, executing `.sql` files)
- Custom primary/replica routing logic
- Connection structs wrapping `*sql.DB` or `*pgxpool.Pool` without using `commons/postgres`

**lib-commons Replacement:**
- `commons/postgres.New(cfg)` — primary/replica pools, lazy connect, pool tuning defaults
- `commons/postgres.Connection` — exposes `Primary()`, `Replica()`, health checks
- Built-in migration runner

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
db, err := sql.Open("postgres", cfg.PostgresURL)
if err != nil {
    return nil, err
}
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)
if err := db.PingContext(ctx); err != nil {
    return nil, err
}

// lib-commons (AFTER):
pg, err := postgres.New(postgres.Config{
    PrimaryURL: cfg.PostgresPrimaryURL,
    ReplicaURL: cfg.PostgresReplicaURL,
    MaxOpen:    25,
})
if err != nil {
    return nil, err
}
// pg.Primary() and pg.Replica() return tuned pools
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for PostgreSQL DIY. Search for `sql.Open(`, `pgx.Connect(`,
> `pgxpool.New(`, `pgxpool.Connect(`, and any struct that embeds `*sql.DB` or
> `*pgxpool.Pool` directly (as opposed to going through `commons/postgres.Connection`).
> MUST flag manual pool tuning calls (`SetMaxOpenConns`, `SetMaxIdleConns`,
> `SetConnMaxLifetime`) and hand-rolled migration runners. For each finding record
> file:line, whether the code reads from replicas (and does so correctly), and whether
> migrations are handled. Severity HIGH — DIY here costs pool health, replica offload, and
> observability hooks.

---

#### Angle 3: MongoDB DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- `mongo.Connect(` without a wrapper that handles lazy reconnect
- `client.Database(...).Collection(...)` calls without index guarantees
- Hand-rolled `EnsureIndexes` equivalents (creating indexes without idempotent check-and-create)
- Missing `client.Ping()` before usage
- Custom reconnect loops using `time.Sleep`

**lib-commons Replacement:**
- `commons/mongo.NewClient(cfg)` — double-checked locking for lazy reconnect, idempotent
  `EnsureIndexes`, built-in health checks
- `commons/mongo.Client.Database()` / `Collection()` helpers

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
client, err := mongo.Connect(ctx, options.Client().ApplyURI(cfg.MongoURL))
if err != nil {
    return nil, err
}
coll := client.Database("app").Collection("users")
_, _ = coll.Indexes().CreateOne(ctx, mongo.IndexModel{
    Keys: bson.M{"email": 1},
    Options: options.Index().SetUnique(true),
})

// lib-commons (AFTER):
mc, err := mongo.NewClient(mongo.Config{URI: cfg.MongoURL, Database: "app"})
if err != nil {
    return nil, err
}
if err := mc.EnsureIndexes(ctx, "users", []mongo.IndexSpec{
    {Keys: bson.M{"email": 1}, Unique: true},
}); err != nil {
    return nil, err
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for MongoDB DIY. Search for `mongo.Connect(`, direct
> `client.Database().Collection()` access outside a `commons/mongo` wrapper, and any
> index creation that isn't idempotent (missing `EnsureIndexes` pattern). MUST flag
> custom reconnect loops (`time.Sleep` + retry) and missing `Ping` before first use. For
> each finding record file:line, the collection being accessed, and whether indexes are
> enforced. Severity HIGH — DIY here costs reconnection safety and index drift detection.

---

#### Angle 4: Redis DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- `redis.NewClient(` (standalone) without topology abstraction
- `redis.NewFailoverClient(` with manual sentinel config
- `redis.NewClusterClient(` with manual node list
- Custom Redlock implementations (multi-node lock acquisition)
- Hand-rolled distributed locks using `SET NX EX` without safety primitives (no lock
  token, no unlock-by-token Lua script)

**lib-commons Replacement:**
- `commons/redis.New(cfg)` — single entry point for standalone/sentinel/cluster
- `commons/redis.RedisLockManager` — safe distributed locks with token-based unlock

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
client := redis.NewClient(&redis.Options{
    Addr:     cfg.RedisAddr,
    Password: cfg.RedisPassword,
    DB:       0,
})
ok, err := client.SetNX(ctx, "lock:tx:123", "held", 30*time.Second).Result()
if err != nil || !ok {
    return errors.New("lock not acquired")
}
defer client.Del(ctx, "lock:tx:123") // unsafe — no token check

// lib-commons (AFTER):
r, err := redis.New(redis.Config{Topology: redis.Standalone, Addr: cfg.RedisAddr})
if err != nil {
    return err
}
locks := redis.NewLockManager(r)
lock, err := locks.Acquire(ctx, "tx:123", 30*time.Second)
if err != nil {
    return err
}
defer lock.Release(ctx) // token-based, safe against expired-then-reacquired
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for Redis DIY. Search for `redis.NewClient(`,
> `redis.NewFailoverClient(`, `redis.NewClusterClient(`, and custom Redlock or
> `SetNX`-based lock implementations. MUST flag any `defer client.Del(ctx, lockKey)`
> pattern that doesn't validate a lock token (unsafe unlock — can release another
> process's lock after expiry). For each finding record file:line, the topology in use,
> and whether distributed locks are token-safe. Severity HIGH — unsafe locks corrupt
> state under contention.

---

#### Angle 5: RabbitMQ DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- `amqp.Dial(` or `amqp091.Dial(` without a reconnect-capable wrapper
- Publishers without `channel.Confirm()` (fire-and-forget, message loss on broker crash)
- Consumer loops that don't re-establish channel on connection errors
- Manual exchange/queue declarations scattered across handlers
- DLQ topology absent or hand-rolled (no `x-dead-letter-exchange` header, no retry queue
  with TTL-based re-enqueue)

**lib-commons Replacement:**
- `commons/rabbitmq.RabbitMQConnection` — managed reconnect, channel pool
- `commons/rabbitmq.ConfirmablePublisher` — publisher with `Confirm()` mode enabled
- `commons/rabbitmq.SetupDLQTopology` — declares exchange, main queue, DLX, DLQ, retry
  queue with TTL-based republish

**Migration Complexity:** complex

**Example Transformation:**

```go
// DIY (BEFORE):
conn, err := amqp.Dial(cfg.RabbitMQURL)
if err != nil {
    return err
}
ch, err := conn.Channel()
if err != nil {
    return err
}
// no Confirm mode — silent message loss if broker crashes mid-publish
err = ch.PublishWithContext(ctx, "", "events", false, false, amqp.Publishing{
    Body: payload,
})

// lib-commons (AFTER):
rmq, err := rabbitmq.New(rabbitmq.Config{URL: cfg.RabbitMQURL})
if err != nil {
    return err
}
if err := rmq.SetupDLQTopology(ctx, "events"); err != nil {
    return err
}
pub := rmq.ConfirmablePublisher("events")
if err := pub.Publish(ctx, payload); err != nil {
    return err // confirmed — broker ack'd or error returned
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for RabbitMQ DIY. Search for `amqp.Dial(`, `amqp091.Dial(`,
> direct `conn.Channel()` usage outside a reconnect-capable wrapper, and publishers that
> don't call `Confirm()`. MUST flag consumer goroutines that don't handle connection loss
> (no reconnect loop). MUST flag manual exchange/queue declarations scattered through
> handler code instead of centralized topology setup. MUST flag any queue that lacks DLQ
> wiring (no `x-dead-letter-exchange` argument). For each finding record file:line, the
> queue/exchange name, and whether confirms are enabled. Severity HIGH — the failure
> modes here cause silent message loss, which is worse than outage.

---

#### Angle 6: HTTP middleware DIY

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Custom Fiber (or gin/chi/echo) middleware implementing CORS, request logging, or
  OpenTelemetry tracing
- Inline `c.Set("Access-Control-Allow-Origin", ...)` scattered across handlers
- Hand-rolled request ID / correlation ID propagation
- Manual `otel.Tracer(...).Start(...)` wrapping handler logic

**lib-commons Replacement:**
- `commons/net/http.WithCORS` — configurable CORS with safe defaults
- `commons/net/http.WithHTTPLogging` — structured request logging via zap
- `commons/net/http.NewTelemetryMiddleware` — OTel span per request + metrics emission

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE):
app.Use(func(c *fiber.Ctx) error {
    c.Set("Access-Control-Allow-Origin", "*")
    c.Set("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE")
    return c.Next()
})
app.Use(func(c *fiber.Ctx) error {
    start := time.Now()
    err := c.Next()
    log.Printf("%s %s %d %dms", c.Method(), c.Path(), c.Response().StatusCode(), time.Since(start).Milliseconds())
    return err
})

// lib-commons (AFTER):
app.Use(http.WithCORS(http.CORSConfig{AllowedOrigins: cfg.AllowedOrigins}))
app.Use(http.WithHTTPLogging(logger))
app.Use(http.NewTelemetryMiddleware(tracer, meter))
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for HTTP middleware DIY. Search for `app.Use(func(c *fiber.Ctx)`
> (and gin/chi/echo equivalents) where the middleware implements CORS headers, request
> logging, tracing, or correlation ID propagation. MUST flag inline CORS header setting
> in handlers. For each finding record file:line and which concern the DIY middleware
> covers. Severity MEDIUM — the DIY usually works, but misses structured logging fields
> and OTel attribute conventions.

---

#### Angle 7: Rate limiting DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- In-memory counter maps (`map[string]int` with a mutex) used as rate limiters
- `time.Ticker`-based token buckets without shared state
- `golang.org/x/time/rate.Limiter` instantiated per-process (not distributed)
- Rate-limit logic that doesn't survive across replicas

**lib-commons Replacement:**
- `commons/net/http/ratelimit` — Redis-backed sliding window, atomic Lua `INCR + PEXPIRE`,
  shared state across replicas

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
var (
    mu      sync.Mutex
    counts  = map[string]int{}
    windows = map[string]time.Time{}
)

func rateLimit(key string, limit int, window time.Duration) bool {
    mu.Lock()
    defer mu.Unlock()
    now := time.Now()
    if now.Sub(windows[key]) > window {
        counts[key] = 0
        windows[key] = now
    }
    counts[key]++
    return counts[key] <= limit
}

// lib-commons (AFTER):
limiter := ratelimit.New(redisClient, ratelimit.Config{
    Limit:  100,
    Window: time.Minute,
})
app.Use(limiter.Middleware(func(c *fiber.Ctx) string {
    return c.IP() // key function
}))
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for rate-limiting DIY. Search for in-memory counter patterns
> (`map[string]int` + mutex used for throttling), `time.Ticker`-based limiters, and
> per-process `rate.Limiter` instances used in HTTP handlers. MUST flag any rate limit
> that claims to protect a multi-replica service without Redis or another shared store.
> For each finding record file:line and what's being rate-limited (IP, user, tenant).
> Severity HIGH — per-process limiters silently multiply allowed traffic by replica
> count.

---

#### Angle 8: Idempotency DIY

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Custom `idempotency_keys` table with hand-written dedupe logic
- `Idempotency-Key` header handling without response replay (returns generic "duplicate"
  instead of original response)
- Idempotency keys not scoped by tenant (cross-tenant key collision risk)
- DB-backed idempotency when Redis is already available (wrong substrate)

**lib-commons Replacement:**
- `commons/net/http/idempotency` — Redis `SetNX`-based, tenant-scoped keys, faithful
  response replay (same status + body + headers)

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
func handler(c *fiber.Ctx) error {
    key := c.Get("Idempotency-Key")
    if key == "" {
        return c.Status(400).JSON(fiber.Map{"error": "missing key"})
    }
    var exists bool
    _ = db.QueryRow("SELECT EXISTS(SELECT 1 FROM idem_keys WHERE key=$1)", key).Scan(&exists)
    if exists {
        return c.Status(409).JSON(fiber.Map{"error": "duplicate"}) // wrong — should replay
    }
    _, _ = db.Exec("INSERT INTO idem_keys(key) VALUES($1)", key)
    return processRequest(c)
}

// lib-commons (AFTER):
app.Use(idempotency.Middleware(idempotency.Config{
    Redis:    redisClient,
    TTL:      24 * time.Hour,
    TenantFn: func(c *fiber.Ctx) string { return c.Locals("tenantId").(string) },
}))
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for idempotency DIY. Search for `Idempotency-Key` header handling,
> `idempotency_keys` table references, and custom dedupe tables. MUST flag implementations
> that return "duplicate" errors instead of replaying the original response. MUST flag
> keys stored without tenant scoping in multi-tenant services. For each finding record
> file:line and the substrate (DB vs Redis). Severity MEDIUM — correctness issue when
> clients retry after network errors.

---

#### Angle 9: Pagination DIY

**Severity:** LOW

**DIY Patterns to Detect:**
- Hand-rolled offset pagination (`LIMIT ? OFFSET ?` with manual `page` + `per_page`
  params)
- Custom cursor encoding (base64 of JSON blob) without standard format
- Inconsistent link header formats across endpoints
- Missing `next`/`prev` cursor tokens on list responses

**lib-commons Replacement:**
- `commons/net/http` pagination helpers: offset pagination, UUID cursor, timestamp
  cursor, sort cursor — all with consistent link format

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE):
page, _ := strconv.Atoi(c.Query("page", "1"))
perPage, _ := strconv.Atoi(c.Query("per_page", "20"))
offset := (page - 1) * perPage
rows, _ := db.Query("SELECT ... LIMIT $1 OFFSET $2", perPage, offset)

// lib-commons (AFTER):
pg := http.ParseOffsetPagination(c)
rows, _ := db.Query("SELECT ... LIMIT $1 OFFSET $2", pg.Limit, pg.Offset)
return http.Respond(c, http.PaginatedResponse{Data: items, Pagination: pg.Response(totalCount)})
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for pagination DIY. Search for inline `LIMIT ? OFFSET ?` SQL with
> `page`/`per_page` query param parsing, custom base64 cursor encoding, and inconsistent
> list-response shapes. MUST flag endpoints returning arrays without pagination metadata.
> For each finding record file:line and the pagination mode (offset vs cursor). Severity
> LOW — mostly ergonomic, but consistency matters for API consumers.

---

#### Angle 10: Validation DIY

**Severity:** LOW

**DIY Patterns to Detect:**
- Inline `validator.New().Struct(x)` calls scattered across handlers
- Custom `validator.RegisterValidation(` calls for financial types (`positive_decimal`,
  `nonnegative_amount`, currency codes)
- Hand-rolled body parsing + validation (`c.BodyParser(&req); if err := validate.Struct(req)`)

**lib-commons Replacement:**
- `commons/net/http.ParseBodyAndValidate` — single call parses body + validates
- `commons/net/http.ValidateStruct` — standalone validation
- Pre-registered financial tags: `positive_decimal`, `nonnegative_amount`, `currency`,
  `iso_country`, etc.

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE):
var req CreateTransactionRequest
if err := c.BodyParser(&req); err != nil {
    return c.Status(400).JSON(fiber.Map{"error": err.Error()})
}
validate := validator.New()
if err := validate.Struct(req); err != nil {
    return c.Status(400).JSON(fiber.Map{"error": err.Error()})
}

// lib-commons (AFTER):
var req CreateTransactionRequest
if err := http.ParseBodyAndValidate(c, &req); err != nil {
    return http.RenderError(c, err)
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for validation DIY. Search for `validator.New()`,
> `validator.RegisterValidation(`, and inline `BodyParser + Struct` two-step patterns. MUST
> flag custom validator tags that duplicate lib-commons financial tags (positive_decimal,
> nonnegative_amount, currency, iso_country). For each finding record file:line and the
> validated struct. Severity LOW — ergonomic, but inconsistent validator config causes
> subtle bugs (e.g., required-vs-optional mismatches).

---

#### Angle 11: Response helpers DIY

**Severity:** LOW

**DIY Patterns to Detect:**
- Scattered `c.Status(status).JSON(body)` calls without a response helper
- Inconsistent error response shapes (some `{"error": msg}`, some `{"message": msg}`,
  some `{"code": X, "detail": Y}`)
- Missing standard fields (no `traceId`, no `timestamp`, no `errorCode`)

**lib-commons Replacement:**
- `commons/net/http.Respond(c, body)` — standard success shape
- `commons/net/http.RespondError(c, err)` — standard error shape with trace ID
- `commons/net/http.RespondStatus(c, status, body)` — explicit status
- `commons/net/http.RenderError(c, err)` — error with correct HTTP status inference

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE):
if err != nil {
    return c.Status(500).JSON(fiber.Map{"error": err.Error()})
}
return c.Status(200).JSON(result)

// lib-commons (AFTER):
if err != nil {
    return http.RenderError(c, err)
}
return http.Respond(c, result)
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for response helper DIY. Search for `c.Status(...).JSON(` and
> `c.JSON(` calls in HTTP handlers that don't route through `commons/net/http.Respond`,
> `RespondError`, `RespondStatus`, or `RenderError`. MUST flag inconsistent error shapes
> across handlers. For each finding record file:line and the response shape in use.
> Severity LOW — consistency for API consumers.

---

#### Angle 12: JWT DIY

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- Direct imports of `github.com/golang-jwt/jwt` (any version) in application code
- `jwt.Parse(` or `jwt.ParseWithClaims(` without an algorithm allowlist in the keyfunc
  (algorithm confusion vulnerability — accepts `none` or swaps HS/RS)
- HMAC signature comparison using `==` or `bytes.Equal` (timing attack) instead of
  `hmac.Equal`
- Token signing with hardcoded secrets or secrets read directly from env without
  `commons/jwt`

**lib-commons Replacement:**
- `commons/jwt.ParseAndValidate(token, key, opts)` — enforced HS256/384/512 allowlist,
  constant-time HMAC comparison
- `commons/jwt.Sign(claims, key, alg)` — sign with vetted algorithms only

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
token, err := jwt.Parse(raw, func(t *jwt.Token) (interface{}, error) {
    return []byte(os.Getenv("JWT_SECRET")), nil
})
// Missing alg check — accepts "none" algorithm and bypasses signature

// lib-commons (AFTER):
claims, err := jwt.ParseAndValidate(raw, key, jwt.Options{
    AllowedAlgs: []string{jwt.HS256},
})
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for JWT DIY. Search for imports of `github.com/golang-jwt/jwt`
> (v4 or v5) in non-lib-commons code, `jwt.Parse(`, `jwt.ParseWithClaims(`, and any HMAC
> comparison that doesn't use `hmac.Equal` (constant-time). MUST flag any keyfunc that
> doesn't verify `token.Method.Alg()` against an allowlist — this is the algorithm
> confusion vulnerability (CVE-class). For each finding record file:line, the parse
> pattern, and whether `none` algorithm would be accepted. Severity CRITICAL — these are
> auth bypass vulnerabilities.

---

#### Angle 13: Crypto DIY

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- Raw `aes.NewCipher(` usage with CBC mode (missing authenticated encryption — malleable
  ciphertext)
- `cipher.NewGCM(` used correctly but without HMAC wrapping for associated data integrity
- Hand-rolled HMAC-SHA256 implementations instead of `crypto/hmac`
- Hardcoded encryption keys in source
- Error messages that include plaintext or key material (`fmt.Errorf("decrypt failed for
  key %s", keyMaterial)`)

**lib-commons Replacement:**
- `commons/crypto.Crypto` — AES-256-GCM + HMAC-SHA256 envelope, constant-time verification,
  credential redaction in error paths

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
block, _ := aes.NewCipher(key)
mode := cipher.NewCBCEncrypter(block, iv) // CBC — malleable
ciphertext := make([]byte, len(plaintext))
mode.CryptBlocks(ciphertext, plaintext)

// lib-commons (AFTER):
c, err := crypto.New(crypto.Config{Key: key})
if err != nil {
    return err
}
ciphertext, err := c.Encrypt(plaintext) // GCM + HMAC
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for crypto DIY. Search for `aes.NewCipher(`, `cipher.NewCBC*`,
> `cipher.NewGCM(`, raw `hmac.New(`, and any hardcoded byte slice or string literal used
> as an encryption key. MUST flag CBC mode usage (malleable ciphertext — use GCM). MUST
> flag error messages that may leak plaintext or key material. For each finding record
> file:line, the cipher mode, and key provenance (env, config, hardcoded). Severity
> CRITICAL — crypto bugs are silent until exploited.

---

#### Angle 14: Observability setup DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- Custom `zap.NewProduction()` / `zap.NewDevelopment()` without `commons/zap` wrapper
- Manual `otel.Tracer(...)` / `otel.Meter(...)` creation without centralized factory
- Hardcoded OTLP exporter endpoints in app code
- Metrics created ad-hoc (`meter.Int64Counter(...)`) without a `MetricsFactory`
- No trace context propagation between services

**lib-commons Replacement:**
- `commons/zap.New(cfg)` — structured logger with standard fields
- `commons/opentelemetry.NewTelemetry(cfg)` — tracer + meter + propagator setup
- `tl.MetricsFactory` — pre-registered metric builders with standard labels

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
logger, _ := zap.NewProduction()
exp, _ := otlptracegrpc.New(ctx, otlptracegrpc.WithEndpoint("localhost:4317"))
tp := sdktrace.NewTracerProvider(sdktrace.WithBatcher(exp))
otel.SetTracerProvider(tp)
tracer := otel.Tracer("my-service")

// lib-commons (AFTER):
logger := zap.New(zap.Config{ServiceName: "my-service", Env: cfg.Env})
tl, err := opentelemetry.NewTelemetry(opentelemetry.Config{
    ServiceName: "my-service",
    OTLPEndpoint: cfg.OTLPEndpoint,
})
if err != nil {
    return err
}
tracer := tl.Tracer()
metrics := tl.MetricsFactory()
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for observability DIY. Search for `zap.NewProduction()`,
> `zap.NewDevelopment()`, `otel.Tracer(`, `otel.Meter(`, direct OTLP exporter setup, and
> ad-hoc metric creation without a factory. MUST flag hardcoded exporter endpoints. MUST
> flag logger instantiation outside `commons/zap`. For each finding record file:line and
> the instrumentation component (logger, tracer, meter, exporter). Severity HIGH —
> inconsistent instrumentation cripples observability in production.

---

#### Angle 15: Panic handling DIY

**Severity:** CRITICAL

**DIY Patterns to Detect:**
- Raw `defer func() { if r := recover(); r != nil { ... } }()` without emitting a metric,
  a log, or a trace span
- Goroutines launched with `go func()` or `go someFunction()` without any panic recovery
  (silent crashes — goroutine dies, process keeps running, work is lost)
- Goroutine launches inside hot paths (HTTP handlers, message consumers) without
  `SafeGo` equivalent

**lib-commons Replacement:**
- `commons/runtime.SafeGo(fn)` — wraps goroutine with recovery + observability
- `commons/runtime.SafeGoWithContextAndComponent(ctx, component, fn)` — attaches
  contextual metadata to panic reports
- `commons/runtime.RecoverWithPolicyAndContext(ctx, policy)` — deferred recovery inside
  existing functions with policy-driven response

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
go func() {
    for msg := range consumer.Messages() {
        process(msg) // panic here silently kills this goroutine
    }
}()

// lib-commons (AFTER):
runtime.SafeGoWithContextAndComponent(ctx, "msg-consumer", func(ctx context.Context) {
    for msg := range consumer.Messages() {
        process(ctx, msg) // panic → recovered, logged, metric emitted, traced
    }
})
```

★ Insight ─────────────────────────────────────
This is the highest-leverage angle in the sweep. Naked `go func()` is the single most
common cause of silent production failures in Go services — a goroutine panics, dies, the
work it was responsible for stops happening, and nothing surfaces in metrics or logs.
Services appear healthy while silently failing. `SafeGo` is not an optimization; it's a
reliability baseline.
─────────────────────────────────────────────────

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for panic-handling DIY. MUST find every `go func()` and
> `go someFunction(...)` in the codebase that isn't wrapped by `commons/runtime.SafeGo`
> or equivalent. MUST find every `defer recover()` that lacks observability emission
> (metric, log, span). For each finding record file:line and whether the goroutine is
> long-lived (consumer loop, worker) or short-lived (request fan-out). Severity CRITICAL
> — silent goroutine crashes are the highest-signal reliability defect this sweep
> catches.

---

#### Angle 16: Assertions DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- Inline `if x == nil { return errors.New("nil x") }` defensive checks without metric
  emission
- `panic()` or `log.Fatal()` on invariant violations (zero-panic policy violation —
  forbidden in Lerian code)
- Invalid-state propagation (function returns silently when invariant is broken, caller
  proceeds with corrupt state)
- Hand-rolled domain predicates (`func isPositiveDecimal(d decimal.Decimal) bool`)

**lib-commons Replacement:**
- `commons/assert.New(logger, metrics)` — assertion handler with observability
- Domain predicates: `PositiveDecimal`, `NonNegativeDecimal`, `DebitsEqualCredits`,
  `ValidTransactionStatus`, `NotEmpty`, etc.

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
if amount.IsNegative() {
    panic("amount must be positive") // forbidden — zero-panic policy
}
if debits != credits {
    return errors.New("unbalanced") // no metric, no trace, silent in dashboards
}

// lib-commons (AFTER):
a := assert.New(logger, metrics)
if err := a.PositiveDecimal(ctx, "amount", amount); err != nil {
    return err
}
if err := a.DebitsEqualCredits(ctx, debits, credits); err != nil {
    return err
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for assertion DIY. MUST find every `panic(`, `log.Fatal(`,
> `log.Panic(`, and `.Must*(` helper call in non-test code (zero-panic policy violation —
> only `regexp.MustCompile` with compile-time constants is allowed). MUST find inline
> invariant checks that return errors without metric emission. For each finding record
> file:line and the invariant being checked. Severity HIGH — panics crash services,
> silent invariant violations corrupt state.

---

#### Angle 17: Resilience DIY

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Custom retry loops using `time.Sleep(time.Duration(attempt) * time.Second)` (linear
  backoff, no jitter)
- Inline exponential backoff math (`time.Sleep(time.Duration(math.Pow(2, float64(i))) * time.Second)`)
- Hand-rolled circuit breakers (state machines tracking success/failure ratios)
- `sync.WaitGroup` + error channel patterns for parallel fan-out without cancellation on
  first error

**lib-commons Replacement:**
- `commons/backoff.ExponentialWithJitter(cfg)` — vetted backoff with jitter
- `commons/circuitbreaker.Manager` — named breakers with shared config
- `commons/errgroup.New(ctx)` — errgroup with telemetry and cancellation

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
for i := 0; i < 5; i++ {
    err := call()
    if err == nil {
        break
    }
    time.Sleep(time.Duration(1<<i) * time.Second) // no jitter — thundering herd
}

// lib-commons (AFTER):
b := backoff.ExponentialWithJitter(backoff.Config{MaxAttempts: 5, BaseDelay: time.Second})
err := b.Retry(ctx, call)
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for resilience DIY. Search for retry loops using `time.Sleep` with
> fixed or exponential durations, inline `math.Pow(2, ...)` backoff math, and hand-rolled
> circuit breaker state machines. MUST flag retries without jitter (thundering herd risk
> when multiple replicas retry in lockstep). For each finding record file:line and the
> backoff strategy in use. Severity MEDIUM — works until it doesn't, and when it doesn't
> it tends to take the downstream with it.

---

#### Angle 18: Multi-tenancy DIY

**Severity:** CRITICAL (security)

**DIY Patterns to Detect:**
- Manual `tenantId` extraction from request context in handlers (instead of middleware)
- Per-tenant DB pools managed via `map[string]*sql.DB` + mutex
- Ad-hoc cache key namespacing (`fmt.Sprintf("%s:user:%s", tenantID, userID)`) without
  a central key-scoping mechanism
- Tenant lookup via direct DB query on every request (instead of event-driven cache)
- RabbitMQ consumers that don't filter by tenant or don't route to per-tenant exchanges
- MongoDB collection access without per-tenant database routing

**lib-commons Replacement:**
- `commons/tenant-manager/client` — tenant metadata client
- `commons/tenant-manager/postgres` — per-tenant PostgreSQL routing
- `commons/tenant-manager/mongo` — per-tenant MongoDB routing
- `commons/tenant-manager/rabbitmq` — per-tenant queue routing
- `commons/tenant-manager/middleware` — HTTP middleware extracting `tenantId` from JWT
- `commons/tenant-manager/consumer` — tenant-aware consumer wrapper
- `commons/tenant-manager/event-listener` — event-driven tenant discovery via Redis
  Pub/Sub
- `commons/tenant-manager/cache` — tenant metadata cache with invalidation
- `commons/tenant-manager/log` — tenant-scoped log wrapper

**Migration Complexity:** complex

**Example Transformation:**

```go
// DIY (BEFORE):
func handler(c *fiber.Ctx) error {
    tenantID := c.Get("X-Tenant-ID") // trusting client header — IDOR risk
    db := pools[tenantID]             // map access, no lock, panics on miss
    rows, _ := db.Query("SELECT ...") // no tenant scoping inside query either
    return c.JSON(rows)
}

// lib-commons (AFTER):
app.Use(tenantmw.WithPG(tenantManager)) // extracts tenantId from JWT, attaches scoped DB
func handler(c *fiber.Ctx) error {
    db := tenantmw.DB(c) // tenant-scoped pool, safe
    rows, _ := db.Query("SELECT ...")
    return http.Respond(c, rows)
}
```

★ Insight ─────────────────────────────────────
Multi-tenancy DIY is the angle where the cost of being wrong is unbounded — cross-tenant
data leaks are regulatory, legal, and reputational all at once. Unlike most other angles
where "DIY works, lib-commons is nicer", here DIY is frequently outright unsafe (trusting
client-supplied tenant headers, mutex-less tenant pool maps, ad-hoc key namespacing).
Treat any finding here as a stop-the-presses concern.
─────────────────────────────────────────────────

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for multi-tenancy DIY. MUST search for any `tenantId` /
> `tenant_id` / `X-Tenant-ID` extraction in handler code (middleware is the only correct
> location). MUST flag tenant identity sourced from client headers (only JWT claims are
> trustworthy). MUST flag per-tenant DB pool maps (`map[string]*sql.DB`) without central
> tenant-manager wrapping. MUST flag cache keys built via `fmt.Sprintf` with tenantID
> (should be central key-scoping). MUST flag RabbitMQ consumers that don't use
> `commons/tenant-manager/consumer`. For each finding record file:line, the isolation
> mechanism (or lack thereof), and the data plane affected (DB, cache, queue). Severity
> CRITICAL — security.

---

#### Angle 19: Webhook delivery DIY

**Severity:** CRITICAL (security)

**DIY Patterns to Detect:**
- `http.Post(` or `http.Client.Do(` to URLs sourced from user/tenant input without SSRF
  validation
- Missing DNS rebinding defense (lookup once, connect, rely on lookup — attacker can
  respond with public IP on lookup, private IP on connect)
- No HMAC signing on outbound webhook body (receivers can't verify origin)
- Credentials embedded in webhook URLs (`https://user:pass@host/path`) that leak into
  logs
- No retry with exponential backoff on 5xx / transient failures

**lib-commons Replacement:**
- `commons/webhook.Deliverer` — two-layer SSRF defense (pre-connect URL validation + dial
  hook that rechecks resolved IP), HMAC-SHA256 v0/v1 signing, retry with exponential
  backoff, credential scrubbing in logs and errors

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
req, _ := http.NewRequestWithContext(ctx, "POST", tenant.WebhookURL, bytes.NewReader(body))
req.Header.Set("Content-Type", "application/json")
_, err := http.DefaultClient.Do(req) // no SSRF check, no signature, no retry

// lib-commons (AFTER):
deliverer := webhook.NewDeliverer(webhook.Config{
    HMACSecret: tenant.WebhookSecret,
    SSRF:       webhook.DefaultSSRFPolicy(), // blocks 127.0.0.0/8, 10/8, 172.16/12, 169.254/16
})
if err := deliverer.Deliver(ctx, tenant.WebhookURL, body); err != nil {
    return err
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for webhook delivery DIY. MUST search for `http.Post(`,
> `http.Client.Do(`, and any request construction where the URL is sourced from
> user/tenant input (tenant config, webhook subscription, user preference). MUST flag any
> such call that doesn't route through `commons/webhook.Deliverer`. MUST flag missing
> HMAC signing on outbound webhooks. MUST flag credentials in URL (`user:pass@host`
> format). For each finding record file:line, the URL source (which table/field), and the
> SSRF protections (or lack thereof). Severity CRITICAL — webhook delivery is the single
> easiest SSRF vector in a service.

---

#### Angle 20: DLQ DIY

**Severity:** MEDIUM

**DIY Patterns to Detect:**
- Custom "failed messages" tables in PostgreSQL/MongoDB for retry tracking
- Manual retry state machines (status columns like `pending`, `failed`, `abandoned` with
  worker polling)
- DLQ keys not scoped by tenant (cross-tenant retry collision)
- Missing or absent exponential backoff between retries
- Retry floor below 5s (tight-loop retries hammer downstream)

**lib-commons Replacement:**
- `commons/dlq.Handler` — push failed work to DLQ with tenant scoping
- `commons/dlq.Consumer` — poll DLQ with exponential backoff, 5s floor, max-attempts
  bound

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
_, _ = db.Exec(`INSERT INTO failed_messages (queue, payload, attempts, next_retry)
                VALUES ($1, $2, 0, NOW() + interval '1 second')`, queue, payload)
// separate worker polls this table — but no tenant scoping, no backoff floor

// lib-commons (AFTER):
dlqHandler := dlq.New(redisClient, dlq.Config{
    MaxAttempts: 10,
    MinBackoff:  5 * time.Second,
    TenantFn:    tenantFromCtx,
})
if err := dlqHandler.Push(ctx, "events", payload, reason); err != nil {
    return err
}
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for DLQ DIY. Search for tables/collections named `failed_*`,
> `dlq_*`, `retry_*`, or similar, and worker loops that poll them. MUST flag DLQ keys or
> table rows that aren't tenant-scoped. MUST flag retry loops with backoff below 5
> seconds (5s floor is a correctness requirement — faster retries hammer downstreams).
> For each finding record file:line, the substrate (DB, Redis, queue), and the backoff
> policy. Severity MEDIUM — DIY DLQs work until load spikes, then they amplify outages.

---

#### Angle 21: TLS certificate DIY

**Severity:** HIGH

**DIY Patterns to Detect:**
- `tls.LoadX509KeyPair(` called once at startup with no hot-reload path
- `cert, _ := tls.LoadX509KeyPair(...)` assignment to a package variable
- `x509.ParseCertificate(` without `x509.ParsePKCS8PrivateKey` / `ParsePKCS1PrivateKey` /
  EC-specific parsers to cover all key formats
- No expiry monitoring (no metric emission for `NotAfter - time.Now()`)
- Service requires restart to pick up rotated certificates

**lib-commons Replacement:**
- `commons/certificate.Manager` — zero-downtime `Rotate(newCertPEM, newKeyPEM)`,
  PKCS#8/PKCS#1/EC key format support, `GetCertificateFunc` wired into `tls.Config`,
  `DaysUntilExpiry()` for metric emission

**Migration Complexity:** moderate

**Example Transformation:**

```go
// DIY (BEFORE):
cert, err := tls.LoadX509KeyPair(cfg.CertFile, cfg.KeyFile)
if err != nil {
    return err
}
tlsConfig := &tls.Config{Certificates: []tls.Certificate{cert}}
// rotation requires restart

// lib-commons (AFTER):
cm, err := certificate.NewManager(cfg.CertFile, cfg.KeyFile)
if err != nil {
    return err
}
tlsConfig := &tls.Config{GetCertificate: cm.GetCertificateFunc()}
// rotate hot: cm.Rotate(newCertPEM, newKeyPEM) — no restart
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for TLS certificate DIY. Search for `tls.LoadX509KeyPair(`,
> `x509.ParseCertificate(`, raw `tls.Config{Certificates: ...}` assignment, and any
> comment or code implying "restart to rotate certs". MUST flag missing expiry metric
> emission. For each finding record file:line and the rotation strategy (none, restart,
> hot). Severity HIGH — expired certs cause hard outages that scale with fleet size.

---

#### Angle 22: Utility DIY

**Severity:** LOW

**DIY Patterns to Detect:**
- `uuid.New()` / `uuid.NewV4()` — v4 UUIDs are random, not time-ordered, cause index
  locality problems in PostgreSQL/MongoDB
- `uuid.NewUUID()` — v1 UUIDs leak MAC address
- Custom env var parsing (`os.Getenv` + `strconv.Atoi` + default fallback scattered through
  config struct initialization)
- Hand-rolled `ToSnakeCase` / `ToCamelCase` / `RemoveAccents` / `Slugify` helpers

**lib-commons Replacement:**
- `commons.GenerateUUIDv7()` — time-ordered UUIDs (good index locality)
- `commons.GetenvOrDefault(key, default)` — typed env reader
- `commons.SetConfigFromEnvVars(&cfg)` — reflection-based struct-tag-driven env loader
- `commons.ToSnakeCase(s)` / `commons.ToCamelCase(s)` / `commons.RemoveAccents(s)`

**Migration Complexity:** trivial

**Example Transformation:**

```go
// DIY (BEFORE):
id := uuid.New().String() // v4 — random, bad index locality
port, _ := strconv.Atoi(os.Getenv("PORT"))
if port == 0 {
    port = 8080
}
snake := strings.ToLower(regexp.MustCompile(`([a-z])([A-Z])`).ReplaceAllString(s, "${1}_${2}"))

// lib-commons (AFTER):
id := commons.GenerateUUIDv7()
port := commons.GetenvOrDefault("PORT", 8080)
snake := commons.ToSnakeCase(s)
```

**Explorer Dispatch Prompt Template:**

> Sweep the target repo for utility DIY. Search for `uuid.New()`, `uuid.NewV4()`,
> `uuid.NewUUID()`, scattered `os.Getenv` + `strconv.Atoi` + default patterns, and
> hand-rolled case-conversion or accent-removal helpers. MUST flag UUID v4 usage on
> columns used as primary keys or indexed fields (v7 has better index locality). For
> each finding record file:line and the utility category (UUID, env, string). Severity
> LOW — ergonomic and consistency, except UUID-v4-as-pk which has measurable DB impact.

---

## Report Template

MANDATORY: The synthesizer MUST produce `/tmp/libcommons-sweep-report.md` following this
exact structure. MUST NOT add sections. MUST NOT reorder sections. MUST populate every
section even if empty (use "None detected" placeholders).

```markdown
# lib-commons Sweep Report

**Target:** <absolute path to target repo>
**Generated:** <ISO-8601 timestamp>
**Sweep duration:** <seconds>

---

## Version Status

| Field                    | Value             |
| ------------------------ | ----------------- |
| Pinned version           | <v5.0.0>          |
| Latest stable            | <v5.0.2>          |
| Drift classification     | <minor-drift>     |
| Major upgrade required   | <yes / no>        |
| Module path              | <.../v5>          |

**Assessment:** <one-paragraph narrative — "project is 2 patch releases behind,
straightforward `go get -u` upgrade" or "project pinned to v4.2.0, v5 migration required
before adopting recommendations below">

---

## Unadopted Features

Features added to lib-commons between the pinned version and latest stable that the
target has not yet adopted:

| Version | Feature                     | Classification  | Relevant Finding Angle |
| ------- | --------------------------- | --------------- | ---------------------- |
| v5.0.0  | commons/webhook             | new-package     | Angle 19               |
| v5.0.0  | commons/dlq                 | new-package     | Angle 20               |
| v5.0.1  | commons/certificate.Rotate  | new-api         | Angle 21               |

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

| Angle                       | Severity  | File                        | Line | DIY Pattern                                | Replacement                      | Complexity |
| --------------------------- | --------- | --------------------------- | ---- | ------------------------------------------ | -------------------------------- | ---------- |
| 12 JWT DIY                  | CRITICAL  | internal/auth/parser.go     | 47   | jwt.Parse w/o alg allowlist                | commons/jwt.ParseAndValidate     | moderate   |
| 18 Multi-tenancy DIY        | CRITICAL  | internal/http/handler.go    | 89   | tenantId from X-Tenant-ID header           | tenant-manager middleware        | complex    |
| 15 Panic handling DIY       | CRITICAL  | internal/worker/consumer.go | 34   | go func() w/o SafeGo                       | runtime.SafeGoWithContext...     | moderate   |
| ...                         | ...       | ...                         | ...  | ...                                        | ...                              | ...        |

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

`ring:dev-cycle` consuming `/tmp/libcommons-sweep-tasks.json` — N tasks generated,
grouped by severity, CRITICAL first.
```

---

## Task Generation for ring:dev-cycle

MANDATORY: The synthesizer MUST also emit `/tmp/libcommons-sweep-tasks.json` — a JSON
array of tasks shaped for `ring:dev-cycle` consumption. The format matches what
`ring:dev-refactor` produces.

**Task grouping rules:**

1. MUST group findings by severity — CRITICAL first, then HIGH, MEDIUM, LOW.
2. Within a severity tier, MUST group findings from the same file or tightly-related
   files into a single task (avoid one-task-per-line fragmentation).
3. CRITICAL findings MUST be standalone tasks (no batching across concerns) — each gets
   its own dev-cycle pass.
4. MUST include dependency references when one task's correctness depends on another
   (e.g., "Switch to tenant-manager middleware" depends on "Upgrade lib-commons to v5").

**Task schema:**

```json
{
  "id": "libcommons-sweep-001",
  "title": "Replace DIY JWT parsing with commons/jwt",
  "severity": "CRITICAL",
  "description": "Target service uses raw github.com/golang-jwt/jwt without an algorithm allowlist in the keyfunc, creating an algorithm confusion vulnerability (accepts 'none' algorithm and bypasses signature verification). Replace with commons/jwt.ParseAndValidate which enforces an HS256/384/512 allowlist and uses constant-time HMAC comparison. This eliminates a CVE-class auth bypass.",
  "files_affected": [
    "internal/auth/parser.go:47",
    "internal/auth/middleware.go:22",
    "internal/auth/refresh.go:61"
  ],
  "acceptance_criteria": [
    "All jwt.Parse / jwt.ParseWithClaims calls replaced with commons/jwt.ParseAndValidate",
    "No direct imports of github.com/golang-jwt/jwt in application code",
    "Algorithm allowlist explicitly passed as HS256 (or HS384/512 if service uses longer keys)",
    "Existing auth integration tests pass unchanged",
    "New test: malformed token with alg=none is rejected"
  ],
  "estimated_complexity": "moderate",
  "depends_on": [],
  "angle": 12,
  "replacement_api": "commons/jwt.ParseAndValidate"
}
```

**Task emission verbatim example:**

```json
[
  {
    "id": "libcommons-sweep-001",
    "title": "Upgrade lib-commons from v4.2.0 to v5.0.2",
    "severity": "HIGH",
    "description": "Target service pins github.com/LerianStudio/lib-commons/v4 at v4.2.0. Latest stable is v5.0.2. Module path changes to v5 require go.mod update and import path rewrites. v5 introduces commons/webhook, commons/dlq, commons/certificate.Rotate, and tenant-manager subsystem — all unavailable in v4. This task MUST complete before any other sweep task lands (all recommendations below assume v5 APIs).",
    "files_affected": ["go.mod", "go.sum", "<all Go files importing lib-commons>"],
    "acceptance_criteria": [
      "go.mod declares github.com/LerianStudio/lib-commons/v5 v5.0.2",
      "All imports updated from /v4 to /v5",
      "go build ./... passes",
      "go test ./... passes",
      "No reference to removed v4 APIs remains"
    ],
    "estimated_complexity": "complex",
    "depends_on": [],
    "angle": "version",
    "replacement_api": "lib-commons/v5"
  },
  {
    "id": "libcommons-sweep-002",
    "title": "Replace DIY JWT parsing with commons/jwt",
    "severity": "CRITICAL",
    "description": "<as above>",
    "files_affected": ["internal/auth/parser.go:47", "..."],
    "acceptance_criteria": ["..."],
    "estimated_complexity": "moderate",
    "depends_on": ["libcommons-sweep-001"],
    "angle": 12,
    "replacement_api": "commons/jwt.ParseAndValidate"
  }
]
```

**Handoff message template** (orchestrator surfaces to user after Phase 4):

```
Sweep complete. Findings: <N> across <M> angles.
- CRITICAL: <N>   HIGH: <N>   MEDIUM: <N>   LOW: <N>

Report: /tmp/libcommons-sweep-report.md
Tasks:  /tmp/libcommons-sweep-tasks.json (<N> tasks)

Next: Invoke ring:dev-cycle with the task file to execute fixes. CRITICAL tasks
(especially multi-tenancy, JWT, webhook, crypto, panic handling) MUST be addressed
before the HIGH/MEDIUM/LOW tier.
```

---

# REFERENCE MODE

Sections 1–15 below catalog lib-commons v5.0.2 packages, APIs, and initialization
patterns. Read the sections relevant to your current task. Sweep Mode explorers receive
extracts from these sections as context for their angle.

## 1. Package Catalog (Quick Reference)

### Root Package

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `commons` | `commons` | App lifecycle (`Launcher`), request-scoped context helpers, business error mapping, UUID generation, struct-to-JSON, metrics, string utilities, date/time validation, env var helpers |

### Database & Data

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `postgres` | `commons/postgres` | PostgreSQL primary/replica connections with lazy connect, migrations, connection pooling |
| `mongo` | `commons/mongo` | MongoDB client with lazy reconnect, TLS, idempotent index creation |
| `redis` | `commons/redis` | Redis/Valkey with 3 topologies (standalone/sentinel/cluster), GCP IAM auth, distributed locks (RedLock) |
| `rabbitmq` | `commons/rabbitmq` | RabbitMQ AMQP 0-9-1 with confirmable publisher, auto-recovery, DLQ topology |
| `transaction` | `commons/transaction` | Financial transaction intent planning, balance posting, share/amount/remainder allocation |
| `outbox` | `commons/outbox` | Transactional outbox pattern — event model, dispatcher, handler registry, multi-tenant support |
| `outbox/postgres` | `commons/outbox/postgres` | PostgreSQL outbox repository with schema-per-tenant and column-per-tenant strategies |

### Security & Auth

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `jwt` | `commons/jwt` | HMAC JWT signing/verification (HS256/384/512), constant-time comparison, algorithm allowlist |
| `crypto` | `commons/crypto` | AES-256-GCM encryption + HMAC-SHA256 hashing with credential redaction |
| `security` | `commons/security` | Sensitive field detection (90+ patterns) for log/trace obfuscation |
| `secretsmanager` | `commons/secretsmanager` | AWS Secrets Manager M2M credential fetching with path traversal protection |
| `license` | `commons/license` | License validation failure handling with fail-open/fail-closed policies |
| `certificate` | `commons/certificate` | **v5.0.0**: Thread-safe TLS certificate manager with hot reload (PKCS#8/PKCS#1/EC keys, DER chain support, zero-downtime `Rotate`) |

### Observability & Runtime

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `log` | `commons/log` | Logger interface (`Logger`) — the universal logging contract across all packages |
| `zap` | `commons/zap` | Zap-backed Logger implementation with OTel log bridge, runtime level adjustment. **v4.3.0+**: timestamp field changed from `"ts"` (Unix epoch) to `"timestamp"` (ISO 8601) |
| `opentelemetry` | `commons/opentelemetry` | Full OTel lifecycle — TracerProvider, MeterProvider, LoggerProvider, OTLP exporters, redaction. Registers noop global providers when collector endpoint is empty |
| `opentelemetry/metrics` | `commons/opentelemetry/metrics` | Thread-safe metrics factory with builders (Counter, Gauge, Histogram) |
| `runtime` | `commons/runtime` | Safe goroutine launching, panic recovery, production mode, error reporter integration |
| `server` | `commons/server` | HTTP (Fiber) + gRPC graceful shutdown manager with ordered teardown |
| `cron` | `commons/cron` | 5-field cron expression parser, computes next execution time |

### HTTP & Networking

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `net/http` | `commons/net/http` | Fiber HTTP toolkit: middleware (CORS, logging, telemetry, basic auth), validation, 3 cursor pagination styles, health checks, SSRF-safe reverse proxy, ownership verification, response helpers, tenant-scoped ID parsing |
| `net/http/ratelimit` | `commons/net/http/ratelimit` | Redis-backed distributed fixed-window rate limiting with atomic Lua script, tiered presets, dynamic tier selection, identity extractors, fail-open/fail-closed policy, `X-RateLimit-*` headers |
| `net/http/idempotency` | `commons/net/http/idempotency` | **v5.0.0**: Fiber middleware for best-effort at-most-once request semantics via Redis SetNX, tenant-scoped keys, faithful response replay (status/headers/body), fail-open on Redis outage |

### Webhooks & Dead Letter Queue (New in v5.0.0)

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `webhook` | `commons/webhook` | Secure webhook delivery engine: two-layer SSRF protection (pre-resolution IP check + DNS-pinned delivery), HMAC-SHA256 signing (v0 payload-only or v1 timestamp-bound for replay protection), exponential backoff with jitter, concurrent delivery with configurable semaphore |
| `dlq` | `commons/dlq` | Redis-backed dead letter queue with tenant-isolated keys, exponential backoff retry (AWS Full Jitter, 5s floor, 30s base), background `Consumer` polling, per-source `RetryFunc` callbacks, configurable `MaxRetries` |

### Resilience & Utilities

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `circuitbreaker` | `commons/circuitbreaker` | Per-service circuit breakers (sony/gobreaker) with health checker, state metrics |
| `backoff` | `commons/backoff` | Exponential backoff with jitter, context-aware sleep |
| `errgroup` | `commons/errgroup` | Error group with first-error cancellation and panic-to-error recovery |
| `safe` | `commons/safe` | Panic-free division, bounds-checked slice access, cached regex compilation |
| `pointers` | `commons/pointers` | Pointer-to-literal helpers (`String`, `Bool`, `Time`, `Int64`, `Float64`) |
| `assert` | `commons/assert` | Production runtime assertions with OTel span events + metrics on failure |
| `constants` | `commons/constants` | Shared constants (headers, error codes, pagination defaults, OTel attributes) |

### Multi-Tenancy (Major Subsystem)

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `tenant-manager` | `commons/tenant-manager` | Complete database-per-tenant isolation system with sub-packages for each resource type |
| `tenant-manager/core` | `...core` | Shared types: TenantConfig, **variadic** context helpers (`ContextWithPG(ctx, pg, ...module)`, `GetPGContext(ctx, ...module)`) |
| `tenant-manager/client` | `...client` | HTTP client for Tenant Manager API with cache + circuit breaker. **v4.2.0+**: endpoint `/connections`, path prefix `/v1/associations/` |
| `tenant-manager/postgres` | `...postgres` | Per-tenant PostgreSQL connection pool manager with LRU eviction |
| `tenant-manager/mongo` | `...mongo` | Per-tenant MongoDB client manager |
| `tenant-manager/rabbitmq` | `...rabbitmq` | Per-tenant RabbitMQ connection manager (vhost isolation) |
| `tenant-manager/s3` | `...s3` | Tenant-aware S3 key namespacing (`{tenantID}/{key}`). **v4.6.0**: `GetS3KeyStorageContext` (renamed from `GetObjectStorageKeyForTenant`) |
| `tenant-manager/valkey` | `...valkey` | Tenant-aware Redis key namespacing (`tenant:{tenantID}:{key}`) |
| `tenant-manager/middleware` | `...middleware` | Fiber middleware: JWT-to-tenantId extraction, DB resolution, context injection. **v4.6.0**: unified `WithPG`/`WithMB` API (MultiPoolMiddleware removed) |
| `tenant-manager/consumer` | `...consumer` | Multi-tenant RabbitMQ consumer with dynamic tenant discovery, `EnsureConsumerStarted` / `StopConsumer` lifecycle |
| `tenant-manager/event` | `...event` | **v4.5.0**: Event-driven tenant discovery via Redis pub/sub. Events: `tenant.added`, `tenant.connections.updated`, `tenant.credentials.rotated`. `TenantEventListener` for HTTP-only services |
| `tenant-manager/redis` | `...redis` | **v4.6.0**: `NewTenantPubSubRedisClient` helper for Redis pub/sub with TLS support |
| `tenant-manager/tenantcache` | `...tenantcache` | **v4.6.0**: `TenantLoader` with `WithOnTenantLoaded` callback for event-driven tenant addition |
| `tenant-manager/cache` | `...cache` | **v5.0.0**: `ConfigCache` interface for tenant config caching; `InMemoryCache` default implementation. Passed into the TM client via `client.WithCache()` |
| `tenant-manager/log` | `...log` | **v5.0.0**: `TenantAwareLogger` wraps a `log.Logger` and automatically injects `tenant_id` from context into every log entry |

### Build & Shell Utilities

| Package | Import Path Suffix | Purpose |
|---|---|---|
| `shell` | `commons/shell` | Build/shell utilities — Makefiles, shell scripts, ASCII art banners for Lerian services |

---

## 2. Common Initialization Pattern

Most Lerian services follow this bootstrap sequence. The order matters — each layer depends on the previous one.

```go
// 1. Logger — first because everything else logs
logger, _ := zap.New(zap.Config{
    Environment:     zap.EnvironmentProduction,
    OTelLibraryName: "my-service",
})
defer logger.Sync(ctx)

// 2. Telemetry — second because DB/HTTP packages emit traces and metrics
//    When CollectorExporterEndpoint is empty, noop global providers are registered
//    so trace/metric calls are no-ops instead of errors.
tl, _ := opentelemetry.NewTelemetry(opentelemetry.TelemetryConfig{
    LibraryName:               "my-service",
    ServiceName:               "my-service",
    ServiceVersion:            "1.0.0",
    DeploymentEnv:             "production",
    CollectorExporterEndpoint: "otel-collector:4317",
    EnableTelemetry:           true,
    Logger:                    logger,
})
_ = tl.ApplyGlobals()
defer tl.ShutdownTelemetry()

// 3. Runtime — panic metrics and production mode
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
runtime.SetProductionMode(true)

// 4. Assert metrics — production assertions with OTel
assert.InitAssertionMetrics(tl.MetricsFactory)

// 5. PostgreSQL
pgClient, _ := postgres.New(postgres.Config{
    PrimaryDSN:     os.Getenv("PRIMARY_DSN"),
    ReplicaDSN:     os.Getenv("REPLICA_DSN"),
    Logger:         logger,
    MetricsFactory: tl.MetricsFactory,
})
defer pgClient.Close()

// 6. MongoDB (if needed)
mongoClient, _ := mongo.NewClient(ctx, mongo.Config{
    URI:            os.Getenv("MONGO_URI"),
    Database:       "mydb",
    Logger:         logger,
    MetricsFactory: tl.MetricsFactory,
})
defer mongoClient.Close(ctx)

// 7. Redis
redisClient, _ := redis.New(ctx, redis.Config{
    Topology: redis.Topology{
        Standalone: &redis.StandaloneTopology{Address: "redis:6379"},
    },
    Auth: redis.Auth{
        StaticPassword: &redis.StaticPasswordAuth{Password: os.Getenv("REDIS_PASS")},
    },
    Logger:         logger,
    MetricsFactory: tl.MetricsFactory,
})
defer redisClient.Close()

// 8. RabbitMQ
rmqConn := &rabbitmq.RabbitMQConnection{
    Host:           "rabbitmq",
    Port:           "5672",
    User:           "guest",
    Pass:           "guest",
    Logger:         logger,
    MetricsFactory: tl.MetricsFactory,
}
_ = rmqConn.Connect()
defer rmqConn.Close()

// 9. Fiber App with middleware
app := fiber.New(fiber.Config{ErrorHandler: http.FiberErrorHandler})
app.Use(http.WithCORS())
app.Use(http.WithHTTPLogging(http.WithCustomLogger(logger)))
tm := http.NewTelemetryMiddleware(tl)
app.Use(tm.WithTelemetry(tl, "/health", "/version"))
app.Get("/health", http.HealthWithDependencies(...))
app.Get("/version", http.Version)

// 10. Graceful shutdown
sm := server.NewServerManager(nil, tl, logger).
    WithHTTPServer(app, ":3000").
    WithShutdownTimeout(30 * time.Second)
sm.StartWithGracefulShutdown()
```

**Key observations:**

- Logger and telemetry are always first — every subsequent package accepts them as dependencies.
- All `defer` calls run in LIFO order, so the server shuts down before DB connections close.
- Every infrastructure client accepts `MetricsFactory` (optional, nil disables metrics).
- `tl.ApplyGlobals()` sets the global TracerProvider/MeterProvider for libraries that use `otel.Tracer()`.
- When `CollectorExporterEndpoint` is empty, noop providers are registered globally so code that calls `otel.Tracer()` or `otel.Meter()` does not error — it simply no-ops.

### Alternative: Using the `Launcher` (Root Package)

For services that want concurrent lifecycle management, the root `commons` package provides a `Launcher`:

```go
launcher := commons.NewLauncher(logger)
launcher.Add("http-server", func(ctx context.Context) error {
    return sm.StartWithGracefulShutdown()
})
launcher.Add("consumer", func(ctx context.Context) error {
    return consumer.Run(ctx)
})
// Launcher starts all components concurrently, cancels all on first error
err := launcher.Run(ctx)
```

---

## 3. Database Connections

### PostgreSQL (`commons/postgres`)

**Constructor**: `postgres.New(config)` returns a `*postgres.Client` with primary and optional replica.

**Key config fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `PrimaryDSN` | `string` | Primary database connection string |
| `ReplicaDSN` | `string` | Read-replica connection string (optional) |
| `MaxOpenConns` | `int` | Maximum open connections (default: 25) |
| `MaxIdleConns` | `int` | Maximum idle connections (default: 25) |
| `ConnMaxLifetime` | `time.Duration` | Connection maximum lifetime |
| `ConnMaxIdleTime` | `time.Duration` | Connection maximum idle time |
| `Logger` | `log.Logger` | Logger instance |
| `MetricsFactory` | `metrics.Factory` | Metrics factory (nil = no metrics) |

**Key interface**: `dbresolver.DB` — provides `Exec`, `Query`, `QueryRow`, `BeginTx` with automatic primary/replica routing.

**Lazy connect**: The first call to `Resolver()` triggers the actual TCP connection. This means `postgres.New()` never blocks on DNS or TCP.

**Migrations**: `pgClient.RunMigrations(migrationsFS)` applies embedded SQL migrations.

### MongoDB (`commons/mongo`)

**Constructor**: `mongo.NewClient(ctx, config)` returns a `*mongo.Client`.

**Lazy reconnect**: `ResolveClient()` and `ResolveDatabase()` use double-checked locking — read-lock fast path for the common case, write-lock slow path with backoff for reconnection.

**TLS**: Configured via `TLSConfig` field. Supports custom CA certificates.

**Indexes**: `EnsureIndexes(ctx, collection, indexes)` is idempotent — safe to call on every startup.

### Redis (`commons/redis`)

**Constructor**: `redis.New(ctx, config)` returns a `*redis.Connection`.

**Three topologies:**

| Topology | Config Field | Use Case |
|----------|-------------|----------|
| Standalone | `Topology.Standalone` | Development, single-node |
| Sentinel | `Topology.Sentinel` | High availability with failover |
| Cluster | `Topology.Cluster` | Horizontal scaling |

**Authentication modes:**

| Mode | Config Field | Use Case |
|------|-------------|----------|
| Static password | `Auth.StaticPassword` | Standard Redis AUTH |
| GCP IAM | `Auth.GCPIAMAuth` | Google Cloud Memorystore |

**Distributed locks**: `redis.NewRedisLockManager(client, logger)` provides RedLock-based distributed locking via `AcquireLock` / `ReleaseLock`.

**Key interface**: `redis.UniversalClient` — works across all three topologies.

### RabbitMQ (`commons/rabbitmq`)

**Constructor**: Create a `rabbitmq.RabbitMQConnection` struct, then call `Connect()`.

**Confirmable publisher**: `rabbitmq.NewConfirmablePublisher(conn)` enables publisher confirms — every message is ACKed by the broker before `Publish` returns.

**Auto-recovery**: On connection loss, the client reconnects with exponential backoff (capped at 30s).

**DLQ topology**: `rabbitmq.SetupDLQTopology(channel, exchangeName, queueName)` creates the exchange, queue, DLQ exchange, and DLQ queue in one call.

**Credential sanitization**: Connection errors automatically strip usernames and passwords from error messages.

---

## 4. HTTP Toolkit (`net/http`)

### Middleware Stack

The recommended middleware order (outermost first):

```
CORS → Logging → Telemetry → Rate Limit → Auth → Handler
```

| Middleware | Constructor | Purpose |
|-----------|------------|---------|
| CORS | `http.WithCORS()` | Cross-origin resource sharing |
| Logging | `http.WithHTTPLogging(http.WithCustomLogger(logger))` | Request/response logging |
| Telemetry | `http.NewTelemetryMiddleware(tl).WithTelemetry(tl, skipPaths...)` | OTel span creation, metrics |
| Rate Limit | `ratelimit.WithDefaultRateLimit(redisConn)` | Distributed rate limiting (one-liner setup) |
| Basic Auth | `http.WithBasicAuth(username, password)` | HTTP Basic authentication |

### Rate Limiting (`net/http/ratelimit`) — Deep Reference

**Added in v4.2.0.** Redis-backed distributed fixed-window rate limiting with atomic Lua script (INCR + PEXPIRE in a single round-trip).

#### Quick Setup (One-Liner)

```go
// WithDefaultRateLimit sets up rate limiting with sensible defaults.
// Returns nil middleware (no-op) when RATE_LIMIT_ENABLED != "true".
app.Use(ratelimit.WithDefaultRateLimit(redisConn))
```

#### Full Setup (Custom Configuration)

```go
// New returns *RateLimiter (nil when disabled — all methods are nil-safe)
rl := ratelimit.New(redisConn,
    ratelimit.WithTier(ratelimit.AggressiveTier()),
    ratelimit.WithIdentityExtractor(ratelimit.IdentityFromIPAndHeader("X-API-Key")),
    ratelimit.WithFailPolicy(ratelimit.FailOpen),
    ratelimit.WithOnLimited(func(ctx *fiber.Ctx, identity string) {
        logger.Warn("rate limited", "identity", identity, "path", ctx.Path())
    }),
)

// Static tier — same limits for all requests
app.Use(rl.WithRateLimit(ratelimit.DefaultTier()))

// Dynamic tier — different limits based on request characteristics
app.Use(rl.WithDynamicRateLimit(func(ctx *fiber.Ctx) ratelimit.Tier {
    if ctx.Method() == "GET" {
        return ratelimit.RelaxedTier()
    }
    return ratelimit.DefaultTier()
}))

// Method-based tier selector (convenience for write-vs-read split)
app.Use(rl.WithDynamicRateLimit(ratelimit.MethodTierSelector))
```

#### Preset Tiers

All tiers are configurable via environment variables:

| Tier | Default Max | Default Window | Env Override (Max) | Env Override (Window) |
|------|------------|---------------|--------------------|-----------------------|
| `DefaultTier()` | 100 | 60s | `RATE_LIMIT_MAX` | `RATE_LIMIT_WINDOW_SEC` |
| `AggressiveTier()` | 30 | 60s | `RATE_LIMIT_AGGRESSIVE_MAX` | `RATE_LIMIT_AGGRESSIVE_WINDOW_SEC` |
| `RelaxedTier()` | 500 | 60s | `RATE_LIMIT_RELAXED_MAX` | `RATE_LIMIT_RELAXED_WINDOW_SEC` |

#### Identity Extractors

Determine who is being rate-limited:

| Extractor | Identifies By | Use Case |
|-----------|--------------|----------|
| `IdentityFromIP` | Client IP address | Public APIs |
| `IdentityFromHeader(name)` | Specific header value | API key-based limiting |
| `IdentityFromIPAndHeader(name)` | IP + header combined | Defense-in-depth |

#### Fail Policies

| Policy | On Redis Error | Use Case |
|--------|---------------|----------|
| `FailOpen` | Allow request through | Availability-first services |
| `FailClosed` | Reject request (429) | Security-first services |

#### Response Headers

When rate limiting is active, responses include:

| Header | Value | Description |
|--------|-------|-------------|
| `X-RateLimit-Limit` | Max requests | Tier's maximum requests per window |
| `X-RateLimit-Remaining` | Remaining | Requests remaining in current window |
| `X-RateLimit-Reset` | Unix timestamp | When the current window resets |
| `Retry-After` | Seconds | Seconds until next request allowed (only on 429) |

#### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `RATE_LIMIT_ENABLED` | `"false"` | Master switch — `"true"` to enable |
| `RATE_LIMIT_MAX` | `100` | Default tier max requests per window |
| `RATE_LIMIT_WINDOW_SEC` | `60` | Default tier window in seconds |
| `RATE_LIMIT_AGGRESSIVE_MAX` | `30` | Aggressive tier max |
| `RATE_LIMIT_AGGRESSIVE_WINDOW_SEC` | `60` | Aggressive tier window |
| `RATE_LIMIT_RELAXED_MAX` | `500` | Relaxed tier max |
| `RATE_LIMIT_RELAXED_WINDOW_SEC` | `60` | Relaxed tier window |

#### Third-Party Middleware Integration (`RedisStorage`)

For integrating with other middleware that needs a rate-limit storage backend:

```go
storage := ratelimit.NewRedisStorage(redisConn)
// Use storage with third-party rate-limit middleware that accepts a storage interface
```

### Idempotency (`net/http/idempotency`) — v5.0.0

**Added in v5.0.0.** Fiber middleware for best-effort at-most-once request semantics using Redis SetNX. Fails open on Redis outages to preserve availability; callers needing strict guarantees must pair with application-level safeguards.

#### Quick Setup

```go
import "github.com/LerianStudio/lib-commons/v5/commons/net/http/idempotency"

idem := idempotency.New(redisConn,
    idempotency.WithKeyPrefix("idempotency:"),   // default: "idempotency:"
    idempotency.WithKeyTTL(7*24*time.Hour),       // default: 7 days
    idempotency.WithMaxKeyLength(256),            // default: 256
    idempotency.WithMaxBodyCache(1<<20),          // default: 1 MB
    idempotency.WithRedisTimeout(500*time.Millisecond),
    idempotency.WithLogger(logger),
)

// Apply to specific mutating routes — GET/HEAD/OPTIONS pass through unconditionally
app.Post("/orders", idem.Check(), createOrderHandler)
app.Patch("/orders/:id", idem.Check(), updateOrderHandler)
```

#### Request Header

Clients opt in per request by sending `X-Idempotency: <unique-key>`. Keys are client-generated (UUIDs are typical). The header constant is `constants.IdempotencyKey`.

#### Key Composition

Composite Redis key format: `<prefix><tenantID>:<idempotencyKey>`

- Tenant ID is extracted from tenant-manager context (`tmcore.GetTenantIDContext`)
- When no tenant is in context, the **middleware bypasses idempotency** (mutating requests proceed normally) — this prevents collapsing all tenantless requests onto a shared key space, which would break isolation
- A companion `:response` key caches the replay payload

#### Behavior Branches (in order)

| Condition | Behavior |
|---|---|
| Method is GET/HEAD/OPTIONS | Pass through (idempotency not applied to safe methods) |
| No `X-Idempotency` header | Pass through (idempotency is opt-in per request) |
| No tenant in context | Pass through (preserves tenant isolation) |
| Key > `maxKeyLength` | Rejected handler invoked; default 400 with code `VALIDATION_ERROR` |
| Redis unavailable | Fail-open — request proceeds, WARN logged |
| Duplicate key, response cached | Faithful replay: status, headers (Location, ETag, Set-Cookie), content-type, body — with `X-Idempotency-Replayed: true` |
| Duplicate key, still processing | 409 Conflict with code `IDEMPOTENCY_CONFLICT` |
| Duplicate key, complete but body oversized | 200 OK with code `IDEMPOTENT` |
| Handler success | Response cached via Redis pipeline; key marked `complete` |
| Handler failure | Lock + response keys deleted so client can retry with same key |

#### Response Replay Headers Preserved

Cached responses preserve `Location`, `ETag`, `Set-Cookie`, and other headers so a replayed response is indistinguishable from the original to the client. `X-Idempotency-Replayed: true` is added to signal a replay.

#### Nil Safety

`idempotency.New(nil)` returns `nil`. A nil `*Middleware` returns a pass-through handler from `Check()`, so bootstrap code that conditionally configures Redis won't crash.

### Response Helpers

Standard response helpers for consistent API responses:

| Helper | Purpose | Example |
|--------|---------|---------|
| `http.Respond(ctx, statusCode, body)` | Send JSON response with status code | `http.Respond(ctx, 200, entity)` |
| `http.RespondStatus(ctx, statusCode)` | Send status-only response (no body) | `http.RespondStatus(ctx, 204)` |
| `http.RespondError(ctx, err)` | Send error response with appropriate status | `http.RespondError(ctx, err)` |
| `http.RenderError(ctx, statusCode, msg)` | Send error with custom status and message | `http.RenderError(ctx, 400, "invalid input")` |

### Request Validation

`http.ParseBodyAndValidate(ctx, &request)` parses the Fiber request body and runs struct tag validation.

**Additional validation helpers:**

| Helper | Purpose | Example |
|--------|---------|---------|
| `http.ValidateStruct(v)` | Validate any struct against its tags | `http.ValidateStruct(request)` |
| `http.ValidateSortDirection(dir)` | Validate sort direction ("asc"/"desc") | `http.ValidateSortDirection(query.Sort)` |
| `http.ValidateLimit(limit)` | Validate pagination limit is within bounds | `http.ValidateLimit(query.Limit)` |

**Custom validation tags:**

| Tag | Purpose | Example |
|-----|---------|---------|
| `positive_decimal` | Decimal > 0 | Amount fields |
| `positive_amount` | Amount > 0 | Transaction values |
| `nonnegative_amount` | Amount >= 0 | Balance fields |

### Context & Ownership Verification

| Helper | Purpose |
|--------|---------|
| `http.ParseAndVerifyTenantScopedID(ctx, paramName)` | Parse ID from path param and verify it belongs to the authenticated tenant |
| `http.ParseAndVerifyResourceScopedID(ctx, paramName, ownerID)` | Parse ID and verify it belongs to the specified resource owner |
| `http.VerifyOwnership(ctx, expectedOwnerID)` | Check that the authenticated user owns the requested resource (403 if not) |

### Pagination (Three Styles)

| Style | Use Case | Cursor Type |
|-------|----------|-------------|
| Offset/Limit | Simple lists | Page number + size |
| Keyset (UUID) | UUID-based cursor | Last-seen UUID |
| Timestamp | Time-ordered data | Last-seen timestamp |
| Sort Cursor | Custom sort orders | Encoded sort position |

All pagination helpers return a standard `CursorPagination` response with `next` / `previous` links.

### Health Checks

`http.HealthWithDependencies(deps...)` returns a handler that checks all dependencies and reports circuit breaker state.

`http.Version` returns the service version from build-time variables.

### SSRF-Safe Reverse Proxy

`http.ServeReverseProxy(target, ctx)` proxies requests with DNS rebinding prevention — the target hostname is resolved and validated before the connection is established.

---

## 5. Observability

### Logger (`commons/log` + `commons/zap`)

**Interface**: Always program against `log.Logger`. This is the universal logging contract — every package in lib-commons accepts it.

**Implementation**: Use `zap.New(config)` for production. It provides:

- Structured JSON logging
- OTel log bridge (logs appear as OTel log records)
- Runtime level adjustment (`logger.SetLevel("debug")`)
- `logger.Sync(ctx)` flushes buffered logs on shutdown
- **v4.3.0+**: Timestamp field changed from `"ts"` (Unix epoch float) to `"timestamp"` (ISO 8601 string). If you parse logs programmatically, update your parsers.
- **Multi-tenant**: In multi-tenant contexts, `tenant_id` is automatically injected into log entries when the tenant context is present.

### Tracing (`commons/opentelemetry`)

Every I/O package in lib-commons auto-creates OTel spans. You rarely need to create spans manually.

**Error recording**: Use `opentelemetry.HandleSpanError(&span, err)` to record errors on spans. This sets the span status and adds the error as an event.

**Redaction**: The OTel setup automatically redacts sensitive fields from span attributes using the `security` package.

**Noop providers**: When `CollectorExporterEndpoint` is empty, `NewTelemetry` registers noop global TracerProvider, MeterProvider, and LoggerProvider. This means services can always call `otel.Tracer()` and `otel.Meter()` without checking whether telemetry is configured — calls simply no-op.

### Metrics (`commons/opentelemetry/metrics`)

`tl.MetricsFactory` provides thread-safe builders:

| Builder | Method | Use Case |
|---------|--------|----------|
| Counter | `metrics.NewCounter(name, desc)` | Monotonic counts (requests, errors) |
| Gauge | `metrics.NewGauge(name, desc)` | Point-in-time values (connections, queue depth) |
| Histogram | `metrics.NewHistogram(name, desc)` | Distributions (latency, payload sizes) |

**Pre-defined metrics** (emitted by various packages):

- `*_connection_failures_total` — every infrastructure package
- `runtime_panic_recovered_total` — `runtime.SafeGo`
- `assertion_failures_total` — `assert`

### Panic Recovery (`commons/runtime`) — Defense-in-Depth Crown Jewel

The `runtime` package is not just "safe goroutine launching" — it's a **complete panic observability pipeline** that ensures no panic ever goes unnoticed in production. Every recovered panic triggers a three-layer response:

1. **Structured log** with stack trace, goroutine name, component label
2. **OTel span event** (`panic.recovered`) on the active trace, with sanitized value + stack + component attributes, span status set to `Error`
3. **Metric increment** on `panic_recovered_total` counter, labeled by component and goroutine name
4. **Error reporter callback** (optional, e.g., Sentry) via `SetErrorReporter`

**MUST launch goroutines with `runtime.SafeGo`**:

```go
// Context-aware variant (preferred) — carries trace context into the goroutine
runtime.SafeGoWithContextAndComponent(ctx, logger, "transaction-service", "balance-updater",
    runtime.KeepRunning, func(ctx context.Context) {
        // your goroutine logic — ctx carries the parent trace
    },
)

// Simple variant
runtime.SafeGo(logger, "worker-name", runtime.KeepRunning, func() {
    // your goroutine logic
})
```

**Panic Policies** — choose per goroutine:

| Policy | Behavior | Use When |
|--------|----------|----------|
| `runtime.KeepRunning` | Recover, log, continue | HTTP/gRPC handlers, background workers |
| `runtime.CrashProcess` | Recover, log, re-panic | Critical invariant violations where continuing is unsafe |

**For defer-based recovery** (inside your own goroutines or framework handlers):

```go
func handleRequest(ctx context.Context) {
    defer runtime.RecoverWithPolicyAndContext(ctx, logger, "api", "handleRequest", runtime.KeepRunning)
    // ... handler logic
}
```

**For framework integration** (Fiber, gRPC interceptors that recover panics themselves):

```go
// Fiber's recover.New() catches the panic — pass the recovered value into the pipeline
app.Use(recover.New(recover.Config{
    EnableStackTrace: true,
    StackTraceHandler: func(c *fiber.Ctx, e interface{}) {
        runtime.HandlePanicValue(c.UserContext(), logger, e, "api", c.Path())
    },
}))
```

**Production mode** — controls data sensitivity:

```go
runtime.SetProductionMode(true)
// Effect: panic values are replaced with "panic recovered (details redacted)"
// in span events and logs. Stack traces are truncated to 4096 bytes.
// Sensitive patterns (password=, token=, api_key=) are always redacted regardless of mode.
```

**Error reporter integration** — plug in external error tracking (Sentry, Bugsnag, etc.):

```go
runtime.SetErrorReporter(mySentryReporter) // implements ErrorReporter interface
// Every panic now also calls: reporter.CaptureException(ctx, err, tags)
```

**Startup initialization** (required once, after telemetry is set up):

```go
runtime.InitPanicMetrics(tl.MetricsFactory, logger)
runtime.SetProductionMode(true)
runtime.SetErrorReporter(myReporter) // optional
```

### Assertions (`commons/assert`) — Defense-in-Depth Crown Jewel

The `assert` package provides **production-grade runtime assertions** — not test assertions, not debug-only checks. These assertions are designed to remain **permanently enabled in production** and fire a **three-layer observability trident** on every failure:

1. **Structured log** with assertion type, message, component, operation, and key-value context
2. **OTel span event** (`assertion.failed`) on the active trace with all attributes
3. **Metric increment** on `assertion_failed_total` counter, labeled by component, operation, and assertion type

Assertions **never panic** — they return errors, making them safe for production hot paths.

**Creating an asserter** — scoped to a component and operation for observability labeling:

```go
a := assert.New(ctx, logger, "transaction-service", "create-posting")
```

**Assertion methods** — each fires the full observability trident on failure:

```go
// General condition check
if err := a.That(ctx, amount.IsPositive(), "amount must be positive",
    "amount", amount.String(), "account_id", accountID); err != nil {
    return err
}

// Nil check (handles typed nils via reflect — catches (*MyStruct)(nil) in interfaces)
if err := a.NotNil(ctx, dbConn, "database connection is nil",
    "tenant_id", tenantID); err != nil {
    return err
}

// Empty string check
if err := a.NotEmpty(ctx, tenantID, "tenant ID is empty"); err != nil {
    return err
}

// Error check — auto-includes error type in context
if err := a.NoError(ctx, dbErr, "database query failed",
    "query", "SELECT balance", "account_id", accountID); err != nil {
    return err
}

// Unreachable code — always fails, use for impossible states
if err := a.Never(ctx, "reached impossible branch",
    "status", status, "operation", op); err != nil {
    return err
}

// Goroutine halt — calls runtime.Goexit() (defers still run, other goroutines unaffected)
a.Halt(err) // only halts if err != nil
```

**Domain predicates** — composable pure functions for financial validations:

```go
// Numeric
assert.Positive(n)                    // int64 > 0
assert.NonNegative(n)                 // int64 >= 0
assert.InRange(n, min, max)           // min <= n <= max

// Financial (shopspring/decimal)
assert.PositiveDecimal(amount)        // amount > 0
assert.NonNegativeDecimal(amount)     // amount >= 0
assert.ValidAmount(amount)            // exponent in [-18, 18]
assert.ValidScale(scale)              // 0 <= scale <= 18
assert.DebitsEqualCredits(d, c)       // double-entry bookkeeping invariant
assert.NonZeroTotals(d, c)            // both sides are non-zero
assert.BalanceSufficientForRelease(onHold, releaseAmt)

// Transaction state machine
assert.ValidTransactionStatus(status)             // CREATED, APPROVED, PENDING, CANCELED, NOTED
assert.TransactionCanTransitionTo(current, target) // e.g., PENDING → APPROVED OK, APPROVED → CREATED NOT OK
assert.TransactionCanBeReverted(status, hasParent) // only APPROVED + no parent
assert.TransactionHasOperations(ops)
assert.TransactionOperationsContain(ops, allowed)  // subset check

// Network / infrastructure
assert.ValidUUID(s)
assert.ValidPort(port)                // "1" to "65535"
assert.ValidSSLMode(mode)             // PostgreSQL SSL modes

// Time
assert.DateNotInFuture(date)
assert.DateAfter(date, reference)
```

**Composing predicates with assertions** — the predicates return `bool`, the asserter provides observability:

```go
a := assert.New(ctx, logger, "ledger", "post-transaction")

if err := a.That(ctx, assert.DebitsEqualCredits(totalDebits, totalCredits),
    "double-entry violation: debits != credits",
    "debits", totalDebits.String(), "credits", totalCredits.String(),
    "transaction_id", txnID); err != nil {
    return err // observability trident already fired
}

if err := a.That(ctx, assert.TransactionCanTransitionTo(currentStatus, targetStatus),
    "invalid status transition",
    "from", currentStatus, "to", targetStatus); err != nil {
    return err
}
```

**How the observability trident works** — a single assertion failure produces:

```
// 1. Structured log:
ERROR assertion failed: double-entry violation: debits != credits
  component=ledger operation=post-transaction assertion=That
  debits=150.00 credits=149.50 transaction_id=abc-123

// 2. OTel span event (on the active trace):
Event: assertion.failed
  assertion.type = "That"
  assertion.message = "double-entry violation: debits != credits"
  assertion.component = "ledger"
  assertion.operation = "post-transaction"
  // + all key-value pairs as attributes

// 3. Metric:
assertion_failed_total{component="ledger", operation="post-transaction", assertion="That"} += 1
```

**Production mode behavior:**
- Stack traces are **suppressed** in assertion failure logs and span events (controlled by `runtime.SetProductionMode(true)` or `ENV=production`)
- In development mode, stack traces are included for debugging

**The `AssertionError` type** — rich, unwrappable error:

```go
var assertErr *assert.AssertionError
if errors.As(err, &assertErr) {
    fmt.Println(assertErr.Component)  // "ledger"
    fmt.Println(assertErr.Operation)  // "post-transaction"
    fmt.Println(assertErr.Assertion)  // "That"
}
// Also: errors.Is(err, assert.ErrAssertionFailed) == true
```

**Why this matters for every Lerian service:**
- Every `nil` receiver in lib-commons fires an assertion — so nil-pointer bugs are visible in metrics dashboards before they become incidents
- Financial invariants (debits == credits, valid status transitions) are continuously verified in production, not just in tests
- The metric `assertion_failed_total` is an early warning system — a spike means a code path hit an unexpected state

**Startup initialization** (required once, after telemetry is set up):

```go
assert.InitAssertionMetrics(tl.MetricsFactory)
```

---

## 6. Resilience & Utilities

### Circuit Breaker (`commons/circuitbreaker`)

```go
manager := circuitbreaker.NewManager(logger)
result, err := manager.Execute("service-name", func() (interface{}, error) {
    return callExternalService()
})
```

**Pre-built configurations:**

| Config | Threshold | Timeout | Use Case |
|--------|-----------|---------|----------|
| `Default` | 5 failures | 60s | General purpose |
| `Aggressive` | 3 failures | 30s | Fast-fail services |
| `Conservative` | 10 failures | 120s | Tolerant services |
| `HTTPService` | 5 failures | 60s | HTTP backends |
| `Database` | 3 failures | 30s | Database connections |

The manager tracks per-service state and emits health check data consumable by `http.HealthWithDependencies`.

### Backoff (`commons/backoff`)

```go
delay := backoff.ExponentialWithJitter(100*time.Millisecond, attempt)
```

Uses the AWS Full Jitter strategy: `sleep = random_between(0, min(cap, base * 2^attempt))`.

Context-aware: `backoff.SleepWithContext(ctx, delay)` cancels the sleep if the context is done.

### Safe Math (`commons/safe`)

| Function | Purpose | Example |
|----------|---------|---------|
| `safe.DivideOrZero(a, b)` | Division that returns 0 instead of panicking | `safe.DivideOrZero(100, 0)` returns `0` |
| `safe.First(slice)` | Returns `(T, error)` instead of panicking on empty | `val, err := safe.First(items)` |
| `safe.CachedRegexp(pattern)` | Compile-once regex | `re := safe.CachedRegexp(`\d+`)` |

### Error Group (`commons/errgroup`)

```go
g := errgroup.New(ctx)
g.Go(func() error { return task1() })
g.Go(func() error { return task2() })
err := g.Wait() // returns first error, cancels remaining
```

Difference from `golang.org/x/sync/errgroup`: panics in goroutines are recovered and converted to errors instead of crashing the process.

### Pointers (`commons/pointers`)

Literal-to-pointer helpers for struct initialization:

```go
entity := &Entity{
    Name:      pointers.String("example"),
    Active:    pointers.Bool(true),
    CreatedAt: pointers.Time(time.Now()),
    Count:     pointers.Int64(42),
    Rate:      pointers.Float64(0.95),
}
```

### Constants (`commons/constants`)

Shared constants used across Lerian services:

- HTTP headers (e.g., `X-Request-ID`, `X-Tenant-ID`)
- Error codes
- Pagination defaults
- OTel attribute keys

---

## 7. Security

### JWT (`commons/jwt`)

**Parse + verify in one call:**

```go
claims, err := jwt.ParseAndValidate(tokenString, secretKey, []string{"HS256"})
```

- Supports HS256, HS384, HS512
- Constant-time signature comparison
- Algorithm allowlist prevents algorithm confusion attacks
- `jwt.ValidateTimeClaims(claims)` checks `exp`, `nbf`, `iat`

**Sign:**

```go
token, err := jwt.Sign(claims, secretKey, "HS256")
```

### Encryption (`commons/crypto`)

```go
c := &crypto.Crypto{
    HashSecretKey:    "hmac-secret",
    EncryptSecretKey: "hex-encoded-32-byte-key",
}
_ = c.InitializeCipher()

encrypted, _ := c.Encrypt("sensitive data")
decrypted, _ := c.Decrypt(encrypted)
hashed       := c.Hash("data to hash")
```

- AES-256-GCM for encryption (authenticated encryption)
- HMAC-SHA256 for hashing
- Credential redaction in error messages

### Sensitive Field Detection (`commons/security`)

```go
isSensitive := security.IsSensitiveField("password")    // true
isSensitive = security.IsSensitiveField("userName")       // false
isSensitive = security.IsSensitiveField("credit_card")    // true
```

Matches 90+ patterns, case-insensitive, supports both camelCase and snake_case. Used internally by the OTel redaction layer and log sanitization.

### AWS Secrets Manager (`commons/secretsmanager`)

```go
creds, err := secretsmanager.GetM2MCredentials(
    ctx, awsClient, "production", tenantOrgID, "my-app", "target-service",
)
```

- Path traversal protection (rejects `../` in inputs)
- Returns structured credentials (client ID, client secret, endpoint)
- Used by plugins for per-tenant M2M authentication with product APIs

### TLS Certificate Hot-Reload (`commons/certificate`) — v5.0.0

**Added in v5.0.0.** Thread-safe X.509 certificate manager with zero-downtime rotation — load PEM files, serve them via TLS config, and swap them atomically without restarting the process.

#### Constructor

```go
m, err := certificate.NewManager("server.crt", "server.key")
if err != nil {
    return err
}

// Both paths empty → returns an unconfigured manager (useful when TLS is optional)
m, _ := certificate.NewManager("", "")
```

If exactly one of `certPath` / `keyPath` is provided, `NewManager` returns `ErrIncompleteConfig`.

#### Key Formats

Private keys are parsed in order: **PKCS#8 → PKCS#1 (RSA) → EC (SEC 1)**. Supported key types: RSA, ECDSA, Ed25519. At load time, the manager validates that the certificate's public key matches the private key (`ErrKeyMismatch` otherwise).

#### Hot Rotation

```go
// Pre-flight: load the new pair before touching the manager
cert, signer, chain, err := certificate.LoadFromFilesWithChain("new.crt", "new.key")
if err != nil {
    logger.Errorf("pre-flight validation failed: %v", err)
    return
}

// Rotate includes a full chain (leaf + intermediates)
if err := m.Rotate(cert, signer, chain[1:]...); err != nil {
    logger.Errorf("certificate rotation failed: %v", err)
}
```

`Rotate` rejects expired certificates (`ErrExpired`), not-yet-valid certificates, nil cert/key, and key-mismatches. It deep-copies the certificate DER to prevent aliasing caller-owned memory.

#### TLS Integration

```go
tlsConfig := &tls.Config{
    GetCertificate: m.GetCertificateFunc(), // live closure — respects subsequent Rotates
}
```

`GetCertificateFunc` on a nil `*Manager` returns a closure that always returns `ErrNilManager`, so bootstrap code that conditionally configures TLS won't crash.

#### Accessors (all Nil-Receiver Safe)

| Method | Returns |
|---|---|
| `GetCertificate()` | `*x509.Certificate` (leaf) |
| `GetSigner()` | `crypto.Signer` (private key) |
| `PublicKey()` | leaf's public key |
| `TLSCertificate()` | `tls.Certificate` (leaf + chain + signer) |
| `ExpiresAt()` | `time.Time` (leaf's `NotAfter`) |
| `DaysUntilExpiry()` | `int` (days from `time.Now()`) |

Read accessors on a nil `*Manager` return zero values without panicking.

#### Sentinel Errors

`ErrNilManager`, `ErrCertRequired`, `ErrKeyRequired`, `ErrExpired`, `ErrNoPEMBlock`, `ErrKeyParseFailure`, `ErrNotSigner`, `ErrKeyMismatch`, `ErrIncompleteConfig`.

---

## 8. Transaction Domain

### Intent Planning (`commons/transaction`)

```go
plan, err := transaction.BuildIntentPlan(input, status)
```

Supports three allocation strategies:

| Strategy | Description | Example |
|----------|-------------|---------|
| **Amount** | Fixed amount per entry | `{Amount: 100.00}` |
| **Share** | Percentage-based allocation | `{Share: 50}` means 50% |
| **Remainder** | Gets whatever is left | One entry per side |

### Balance Validation

```go
err := transaction.ValidateBalanceEligibility(plan, balances)
```

Checks:
- Sufficient funds for debits
- Account eligibility for the operation type
- Cross-scope validation (no mixing incompatible accounts)

### Posting

```go
updatedBalance, err := transaction.ApplyPosting(balance, posting)
```

Implements the operation/status state machine:

| Operation | Status | Effect |
|-----------|--------|--------|
| `DEBIT` | `ACTIVE` | Decreases available balance |
| `CREDIT` | `ACTIVE` | Increases available balance |
| `ON_HOLD` | `ACTIVE` | Moves funds to on-hold |
| `RELEASE` | `ACTIVE` | Releases held funds back to available |

### Outbox Pattern (`commons/outbox`)

**Repository:**

```go
repo := outboxpg.NewRepository(pgClient, tenantResolver, tenantDiscoverer)
```

**Dispatcher:**

```go
dispatcher := outbox.NewDispatcher(repo, handlers, logger, tracer, opts...)
dispatcher.Run(launcher)
```

**Event lifecycle**: `PENDING` -> `PROCESSING` -> `PUBLISHED` (success) or `FAILED` -> `INVALID` (after max attempts).

**Multi-tenant strategies:**

| Strategy | How It Works | Config |
|----------|-------------|--------|
| Schema-per-tenant | Each tenant has its own PostgreSQL schema | `SchemaResolver` |
| Column-per-tenant | Shared table with `tenant_id` column filter | `ColumnResolver` |

**Sensitive data**: Error messages are sanitized before storage — URLs, tokens, and card numbers are redacted automatically.

---

## 9. Tenant Manager (Deep Reference)

The tenant-manager subsystem provides complete database-per-tenant isolation. This is a major subsystem with its own middleware, connection pool managers, consumer infrastructure, and **event-driven tenant discovery** (v4.5.0+).

### Architecture Flow

```
HTTP request
  → JWT middleware (extract tenantId from token)
    → tenant-manager client (fetch tenant config from TM API)
      → per-tenant connection pool (get or create DB connection)
        → context injection (db available via ctx)
          → repository layer (uses ctx to get tenant-scoped DB)

Event-driven flow (v4.5.0+):
  Redis pub/sub → TenantEventListener → callback
    → tenant.added: provision new tenant connections
    → tenant.connections.updated: refresh connection pools
    → tenant.credentials.rotated: rotate credentials in pools
```

### Setup Pattern

```go
// 1. Create the TM client
//    v4.2.0+: endpoint is /connections, path prefix is /v1/associations/
tmClient, _ := client.NewClient("https://tenant-manager:8080", logger,
    client.WithServiceAPIKey(os.Getenv("TM_API_KEY")),
    client.WithCache(cache.NewInMemoryCache()),
    client.WithCacheTTL(5*time.Minute),
    client.WithCircuitBreaker(5, 30*time.Second),
)

// 2. Create per-resource managers
pgManager := tmpostgres.NewManager(tmClient, "my-service",
    tmpostgres.WithLogger(logger),
    tmpostgres.WithModule("transaction"),
    tmpostgres.WithMaxTenantPools(100),
)

mongoManager := tmmongo.NewManager(tmClient, "my-service",
    tmmongo.WithLogger(logger),
    tmmongo.WithModule("transaction"),
)

// 3. Attach middleware
//    v4.6.0: Use unified WithPG/WithMB API (MultiPoolMiddleware removed)
//    WithPG/WithMB accept optional module parameter for multi-module services
mw := middleware.NewTenantMiddleware(
    middleware.WithPG(pgManager),
    middleware.WithMB(mongoManager),
    middleware.WithTenantCache(tenantCache),
    middleware.WithTenantLoader(tenantLoader),
)
app.Use(mw.WithTenantDB)

// 4. In repositories, access tenant-scoped connections
//    v4.6.0: Context functions are variadic — module parameter is optional
func (r *Repo) Get(ctx context.Context, id string) (*Entity, error) {
    db := tmcore.GetPGContext(ctx)  // no module = default
    if db == nil {
        return nil, fmt.Errorf("tenant postgres connection missing from context")
    }
    // use db for queries — automatically scoped to the tenant's database
}

// For multi-module services, pass the module name:
func (r *Repo) GetFromAudit(ctx context.Context, id string) (*AuditEntry, error) {
    db := tmcore.GetPGContext(ctx, "audit")  // specific module
    if db == nil {
        return nil, fmt.Errorf("audit postgres connection missing from context")
    }
    // ...
}
```

### Variadic Context API (v4.6.0)

The context functions now use variadic module parameters instead of separate per-module functions:

| Old API (pre-v4.6.0) | New API (v4.6.0) |
|----------------------|-------------------|
| `ContextWithTenantPG(ctx, pg)` | `ContextWithPG(ctx, pg)` (default module) |
| `ContextWithTenantPG(ctx, pg)` for module X | `ContextWithPG(ctx, pg, "moduleX")` (specific module) |
| `GetPGContext(ctx)` | `GetPGContext(ctx)` (default module) |
| Per-module context function | `GetPGContext(ctx, "moduleX")` (specific module) |
| `ContextWithTenantMB(ctx, mb)` | `ContextWithMB(ctx, mb)` (default module) |
| Per-module MB context function | `GetMBContext(ctx, "moduleX")` (specific module) |

### Event-Driven Tenant Discovery (v4.5.0+)

**Replaces the watcher-based model** (watcher removed in v4.5.0). Tenants are discovered via Redis pub/sub events instead of polling.

#### Events

| Event | Channel | Payload | When |
|-------|---------|---------|------|
| `tenant.added` | `tenant-events` | Tenant config JSON | New tenant registered in TM |
| `tenant.connections.updated` | `tenant-events` | Updated connection info | Tenant DB connection changed |
| `tenant.credentials.rotated` | `tenant-events` | Rotation metadata | Credentials rotated (scheduled or emergency) |

#### TenantEventListener (HTTP-Only Services)

For services that only handle HTTP requests (no RabbitMQ consumer), use `TenantEventListener`:

```go
import tmevent "github.com/LerianStudio/lib-commons/v5/commons/tenant-manager/event"

listener := tmevent.NewTenantEventListener(redisClient, logger,
    tmevent.WithOnTenantAdded(func(ctx context.Context, tenant TenantConfig) {
        // Provision connections for new tenant
        pgManager.Provision(ctx, tenant.ID)
        mongoManager.Provision(ctx, tenant.ID)
        logger.Info("new tenant provisioned", "tenant_id", tenant.ID)
    }),
    tmevent.WithOnConnectionsUpdated(func(ctx context.Context, tenant TenantConfig) {
        // Refresh connection pools with new connection info
        pgManager.Refresh(ctx, tenant.ID)
        mongoManager.Refresh(ctx, tenant.ID)
    }),
    tmevent.WithOnCredentialsRotated(func(ctx context.Context, tenant TenantConfig) {
        // Rotate credentials in existing pools
        pgManager.RotateCredentials(ctx, tenant.ID)
    }),
)

// Start listening (blocks — run in a goroutine or via Launcher)
runtime.SafeGoWithContextAndComponent(ctx, logger, "my-service", "tenant-listener",
    runtime.KeepRunning, func(ctx context.Context) {
        listener.Listen(ctx)
    },
)
```

#### NewTenantPubSubRedisClient (v4.6.0)

Helper for creating a Redis client specifically configured for tenant pub/sub with TLS:

```go
import tmredis "github.com/LerianStudio/lib-commons/v5/commons/tenant-manager/redis"

pubsubClient := tmredis.NewTenantPubSubRedisClient(
    os.Getenv("MULTI_TENANT_REDIS_HOST"),
    os.Getenv("MULTI_TENANT_REDIS_PORT"),
    os.Getenv("MULTI_TENANT_REDIS_PASSWORD"),
    logger,
)
// Use pubsubClient with TenantEventListener or consumer
```

**Environment variable**: `MULTI_TENANT_REDIS_TLS` — set to `"true"` to enable TLS for the pub/sub Redis connection.

#### TenantLoader with Callback (v4.6.0 — `tenantcache` package)

The `tenantcache` package provides `TenantLoader` with a callback for event-driven tenant addition:

```go
import "github.com/LerianStudio/lib-commons/v5/commons/tenant-manager/tenantcache"

loader := tenantcache.NewTenantLoader(tmClient, logger,
    tenantcache.WithOnTenantLoaded(func(ctx context.Context, tenant TenantConfig) {
        // Called for each tenant loaded — useful for provisioning side effects
        logger.Info("tenant loaded into cache", "tenant_id", tenant.ID)
    }),
)
```

### Isolation Modes

| Mode | How It Works | When to Use |
|------|-------------|-------------|
| `isolated` (default) | Separate database per tenant | Maximum isolation, regulatory compliance |
| `schema` | Shared database, separate PostgreSQL schemas | Lower overhead, acceptable isolation |

### S3 and Valkey (Key Namespacing)

These packages do not manage connection pools — they provide key namespacing utilities:

**S3:**
```go
// v4.6.0: Renamed from GetObjectStorageKeyForTenant
key := s3.GetS3KeyStorageContext(ctx, "my-file.pdf")
// returns "{tenantID}/my-file.pdf"
```

**Valkey (Redis):**
```go
key := valkey.GetKeyContext(ctx, "session:abc")
// returns "tenant:{tenantID}:session:abc"
```

### Multi-Tenant Consumer (RabbitMQ)

For processing messages across tenants with automatic tenant context injection:

```go
consumer, _ := consumer.NewMultiTenantConsumerWithError(
    rmqManager, redisClient, config, logger,
    consumer.WithPG(pgManager),
    consumer.WithMB(mongoManager),
)

consumer.Register("my-queue", func(ctx context.Context, d amqp.Delivery) error {
    db := tmcore.GetPGContext(ctx)                     // auto-resolved for this tenant
    if db == nil {
        return fmt.Errorf("tenant postgres connection missing from context")
    }
    // process message with tenant-scoped database
    return nil
})

// EnsureConsumerStarted starts the consumer if not already running
consumer.EnsureConsumerStarted(ctx)

// StopConsumer gracefully stops the consumer
defer consumer.StopConsumer(ctx)
```

The consumer dynamically discovers tenants and creates per-tenant connections on demand.

### Unified Middleware API (v4.6.0)

**MultiPoolMiddleware has been removed.** Use the unified `WithPG`/`WithMB` options on `NewTenantMiddleware`:

```go
// v4.6.0 — unified API with optional module parameter
mw := middleware.NewTenantMiddleware(
    middleware.WithPG(pgManager),              // default module
    middleware.WithPG(auditPGManager, "audit"), // named module
    middleware.WithMB(mongoManager),            // default module
)
app.Use(mw.WithTenantDB)
```

In request handlers, retrieve the correct connection by module:

```go
defaultDB := tmcore.GetPGContext(ctx)          // default module
auditDB := tmcore.GetPGContext(ctx, "audit")    // "audit" module
defaultMB := tmcore.GetMBContext(ctx)           // default module
```

### Cache Abstraction (v5.0.0 — `tenant-manager/cache`)

v5.0.0 extracted the tenant-config cache into its own interface so services can plug in Redis or a custom implementation instead of the default in-memory cache:

```go
import "github.com/LerianStudio/lib-commons/v5/commons/tenant-manager/cache"

// Default: process-local in-memory cache with TTL
inMem := cache.NewInMemoryCache()

tmClient, _ := client.NewClient("https://tenant-manager:8080", logger,
    client.WithCache(inMem),
    client.WithCacheTTL(5*time.Minute),
)
```

The `ConfigCache` interface (`Get(ctx, key)` / `Set(ctx, key, val, ttl)` / `Del(ctx, key)`) returns `cache.ErrCacheMiss` on miss or expiry. Implementations must be safe for concurrent use.

### Tenant-Aware Logger (v5.0.0 — `tenant-manager/log`)

Wraps any `log.Logger` to auto-inject `tenant_id` from context into every log entry:

```go
import tmlog "github.com/LerianStudio/lib-commons/v5/commons/tenant-manager/log"

baseLogger, _ := zap.New(zap.Config{...})
logger := tmlog.NewTenantAwareLogger(baseLogger)

// Every log call now carries tenant_id when the context has one
logger.Log(ctx, log.LevelInfo, "transaction processed", log.String("txn_id", id))
// → fields include tenant_id=<tenant-from-ctx> automatically
```

This removes the need for every call site to pass `tenant_id` manually, and guarantees the field is present in multi-tenant log aggregators even when handlers forget to add it.

---

## 10. Webhook Delivery

**Added in v5.0.0.** `commons/webhook` is a secure webhook delivery engine with SSRF protection, HMAC-SHA256 signing, and exponential-backoff retries. Construct one `Deliverer` per service and reuse it — the internal HTTP client maintains a connection pool.

### Core Types

| Type | Purpose |
|---|---|
| `Endpoint` | `{ID, URL, Secret, Active}` — the receiver. `Secret` can be plaintext or `"enc:<ciphertext>"` (decrypted via `WithSecretDecryptor`). |
| `Event` | `{Type, Payload, Timestamp}` — the message to deliver. `Payload` is the JSON-encoded body; `Timestamp` is Unix-epoch seconds. |
| `EndpointLister` | Interface: `ListActiveEndpoints(ctx) ([]Endpoint, error)` — typically backed by a DB query filtered by tenant ID. |
| `DeliveryResult` | `{EndpointID, StatusCode, Success, Error, Attempts}` |
| `DeliveryMetrics` | Interface: `RecordDelivery(ctx, endpointID, success, statusCode, attempts)` |
| `SecretDecryptor` | `func(encrypted string) (string, error)` for decrypting `"enc:"`-prefixed secrets. |

### Constructor

```go
import "github.com/LerianStudio/lib-commons/v5/commons/webhook"

d := webhook.NewDeliverer(lister,
    webhook.WithLogger(logger),
    webhook.WithTracer(tracer),
    webhook.WithMetrics(metrics),
    webhook.WithMaxConcurrency(20),             // default: 20
    webhook.WithMaxRetries(3),                  // default: 3
    webhook.WithHTTPClient(customClient),       // redirects always blocked for SSRF safety
    webhook.WithSecretDecryptor(decryptor),     // optional — fail-closed if "enc:" secrets appear without one
    webhook.WithSignatureVersion(webhook.SignatureV1), // default: SignatureV0
)
```

`NewDeliverer(nil, ...)` returns `nil` — Deliverer methods are nil-safe.

### SSRF Protection (Two Layers)

Webhook URLs are user-controlled, so the package defends against SSRF aggressively:

1. **Pre-resolution IP validation** — hostname resolved, resolved IPs checked against RFC 1918 private ranges, loopback, link-local, and multicast before the connection is opened
2. **DNS-pinned delivery** — the resolved IP is pinned for the actual connection, preventing DNS rebinding between validation and connect
3. **Redirects always blocked** — even a user-supplied `*http.Client` is cloned with `CheckRedirect = http.ErrUseLastResponse` so an attacker cannot bounce the request via a 302 to a private IP

### HMAC Signatures — Two Versions

| Version | Format | Replay Protection |
|---|---|---|
| `SignatureV0` (default, backward-compatible) | `sha256=<hex(HMAC(payload, secret))>` | **None** — receivers must implement their own (event-ID tracking, etc.) |
| `SignatureV1` (recommended for new deployments) | `v1,sha256=<hex(HMAC("v1:<timestamp>.<payload>", secret))>` | **Yes** — timestamp is bound into the HMAC input |

The default is V0 to avoid breaking existing consumers. Migration path:

1. Update all receivers to use `VerifySignature` (auto-detects both formats)
2. Switch senders to `SignatureV1` via `WithSignatureVersion`
3. Optionally enforce V1-only after the transition window

### Receiver-Side Verification

```go
// Auto-detects v0 or v1 from the signature string
if err := webhook.VerifySignature(payload, timestamp, secret, receivedSig); err != nil {
    return http.StatusUnauthorized
}

// For v1 signatures: verify + enforce freshness in one call
if err := webhook.VerifySignatureWithFreshness(payload, timestamp, secret, receivedSig, 5*time.Minute); err != nil {
    // rejects on signature mismatch OR stale timestamp
    return http.StatusUnauthorized
}
```

### Delivery Headers (Sent by Deliverer)

| Header | Purpose |
|---|---|
| `X-Webhook-Signature` | HMAC signature (v0 or v1 format) |
| `X-Webhook-Timestamp` | Decimal Unix epoch seconds (informational in v0, HMAC-covered in v1) |
| `Content-Type` | `application/json` |

### Retry Behavior

- Exponential backoff with jitter (1s base, 2x doubling)
- Up to `maxRetries` attempts per endpoint (default 3)
- Concurrent delivery across endpoints, bounded by `maxConcurrency` semaphore (default 20)
- Response body drain capped at 64 KiB so the TCP connection can be reused

### Credential Hygiene

URL query parameters and userinfo (`user:pass@host`) are stripped from log output before emission to prevent credential leakage into log aggregators.

---

## 11. Dead Letter Queue

**Added in v5.0.0.** `commons/dlq` is a Redis-backed DLQ for messages that failed processing. Tenant-isolated keys, exponential-backoff retry, and a background `Consumer` that polls for retryable messages.

### Core Types

| Type | Purpose |
|---|---|
| `FailedMessage` | `{Source, OriginalData, ErrorMessage, RetryCount, MaxRetries, CreatedAt, NextRetryAt, TenantID}` |
| `Handler` | Enqueue/dequeue interface on top of Redis lists |
| `Consumer` | Background poller that invokes a `RetryFunc` per message |
| `RetryFunc` | `func(ctx, *FailedMessage) error` — return nil to discard, error to re-enqueue |
| `DLQMetrics` | Interface: `RecordRetried` / `RecordExhausted` / `RecordLost` |

### Handler

```go
import "github.com/LerianStudio/lib-commons/v5/commons/dlq"

h := dlq.New(redisConn, "dlq:", 3,              // keyPrefix, maxRetries
    dlq.WithLogger(logger),
    dlq.WithTracer(tracer),
    dlq.WithMetrics(metrics),
    dlq.WithModule("transaction-outbound"),
)

// Enqueue a failed message — TenantID is resolved from context if not already set.
// On initial enqueue, msg.MaxRetries=0 is overwritten with the handler's configured value.
err := h.Enqueue(ctx, &dlq.FailedMessage{
    Source:       "outbound",
    OriginalData: payload,
    ErrorMessage: originalErr.Error(),
})
```

`dlq.New(nil, ...)` returns `nil` — `Handler` methods are nil-safe and return `ErrNilHandler`.

### Key Composition

Keys are tenant-scoped to prevent cross-tenant mixing:

| Context | Redis Key |
|---|---|
| Tenant present | `dlq:<tenantID>:<source>` |
| No tenant | `dlq:<source>` (global) |

Invalid tenant IDs (containing `:`, `*`, `?`, `[`, `]`, `\`) are **rejected fail-closed** — the Enqueue returns an error rather than falling back to the global key, which would corrupt isolation.

### Consumer

```go
consumer, err := dlq.NewConsumer(handler, retryFn,
    dlq.WithConsumerLogger(logger),
    dlq.WithConsumerTracer(tracer),
    dlq.WithConsumerMetrics(metrics),
    dlq.WithConsumerModule("transaction-outbound"),
    dlq.WithPollInterval(30*time.Second),  // default: 30s
    dlq.WithBatchSize(10),                  // default: 10
    dlq.WithSources("outbound", "inbound"),
)

// Start blocks until ctx is canceled — run under a Launcher or SafeGo
runtime.SafeGoWithContextAndComponent(ctx, logger, "my-service", "dlq-consumer",
    runtime.KeepRunning, func(ctx context.Context) {
        _ = consumer.Start(ctx)
    },
)
```

### Retry Function Contract

```go
retryFn := func(ctx context.Context, msg *dlq.FailedMessage) error {
    // ctx automatically carries the TenantID from msg.TenantID via tmcore.
    switch msg.Source {
    case "outbound":
        return resendWebhook(ctx, msg.OriginalData)
    case "inbound":
        return reprocessEvent(ctx, msg.OriginalData)
    }
    return errors.New("unknown source")
}
```

- Return `nil` → message is discarded (`RecordRetried`)
- Return `error` → message is re-enqueued with incremented `RetryCount` and updated `NextRetryAt`
- `RetryCount >= MaxRetries` → message is discarded as permanently failed (`RecordExhausted`)

### Backoff

30s base with AWS Full Jitter (via `commons/backoff`), floored at 5s so attempt 0 gets genuine jitter spread over `[5s, 30s)` rather than always resolving to exactly 30s.

### Integration with RabbitMQ Consumers

The typical pattern: a RabbitMQ consumer that fails to process a message Enqueues to the DLQ, Acks the original, and the DLQ Consumer retries it later out-of-band. This moves slow retries off the main consumer loop and off the broker, which is particularly useful for multi-tenant deployments where per-tenant retries on the broker can cause head-of-line blocking.

---

## 12. Root Package & Utilities

The root `commons` package (`github.com/LerianStudio/lib-commons/v5/commons`) provides foundational utilities used across all Lerian services. These are building blocks that other packages and services depend on.

### App Lifecycle (`app.go`)

The `Launcher` provides concurrent app component lifecycle management:

```go
launcher := commons.NewLauncher(logger)

// Add components — each runs concurrently
launcher.Add("http-server", func(ctx context.Context) error {
    return sm.StartWithGracefulShutdown()
})
launcher.Add("consumer", func(ctx context.Context) error {
    return consumer.Run(ctx)
})
launcher.Add("event-listener", func(ctx context.Context) error {
    return listener.Listen(ctx)
})

// Run blocks until all complete or first error — cancels remaining on error
err := launcher.Run(ctx)
```

### Request-Scoped Context Helpers (`context.go`)

Context utilities for carrying request-scoped data:

```go
// Attach values to context
ctx = commons.ContextWithRequestID(ctx, requestID)
ctx = commons.ContextWithTenantID(ctx, tenantID)
ctx = commons.ContextWithUserID(ctx, userID)

// Retrieve values from context
requestID := commons.GetRequestID(ctx)
tenantID := commons.GetTenantID(ctx)

// Safe timeout — creates a derived context with timeout, returning cancel func
ctx, cancel := commons.WithTimeoutSafe(ctx, 30*time.Second)
defer cancel()
```

### Business Error Mapping (`errors.go`)

Maps domain-level errors to HTTP status codes consistently:

```go
// ValidateBusinessError checks an error against known business error patterns
// and returns the appropriate HTTP status code and user-friendly message
statusCode, message := commons.ValidateBusinessError(err)

// Common mappings:
// ErrNotFound → 404
// ErrConflict → 409
// ErrValidation → 422
// ErrUnauthorized → 401
// ErrForbidden → 403
```

### UUID Generation (`utils.go`)

```go
// Generate a UUIDv7 (time-ordered, sortable)
id := commons.GenerateUUIDv7()
```

**Why UUIDv7**: Time-ordered UUIDs improve database index locality and make natural ordering possible without additional timestamp columns.

### Struct-to-JSON & Metrics Helpers (`utils.go`)

```go
// Convert any struct to JSON bytes (convenience wrapper)
jsonBytes, err := commons.StructToJSON(entity)

// Metrics registration helpers used internally by other packages
```

### String Utilities (`stringUtils.go`)

```go
// Remove accents from strings (useful for search normalization)
normalized := commons.RemoveAccents("café")  // returns "cafe"

// Case conversion
snake := commons.ToSnakeCase("myFieldName")   // returns "my_field_name"
camel := commons.ToCamelCase("my_field_name")  // returns "myFieldName"

// Hashing utilities
hash := commons.HashString("input-data")
```

### Date/Time Validation (`time.go`)

```go
// Validate date strings
valid := commons.IsValidDate("2026-03-28")  // true
valid = commons.IsValidDate("not-a-date")    // false

// Parse dates with known formats
t, err := commons.ParseDate("2026-03-28")

// Validate and parse datetime
t, err := commons.ParseDateTime("2026-03-28T10:30:00Z")
```

### Environment Variable Helpers (`os.go`)

```go
// Get environment variable with fallback default
value := commons.GetenvOrDefault("PORT", "3000")

// Set struct fields from environment variables using struct tags
type Config struct {
    Port     string `env:"PORT" default:"3000"`
    LogLevel string `env:"LOG_LEVEL" default:"info"`
    Debug    bool   `env:"DEBUG" default:"false"`
}

cfg := &Config{}
commons.SetConfigFromEnvVars(cfg)
```

---

## 13. Cross-Cutting Patterns

These patterns appear consistently across all lib-commons packages. Understanding them helps predict how any package behaves.

### 1. Nil-Receiver Safety with Telemetry

Every exported method on a struct guards against nil receiver. Before returning a sentinel error, the method fires an OTel assertion so the nil-receiver call is observable in traces and metrics.

### 2. Lazy Connect with Double-Checked Locking

Database packages (`postgres.Resolver()`, `mongo.ResolveClient()`, `redis.GetClient()`) defer the actual TCP connection to first use. The pattern:

- **Read-lock fast path**: If already connected, return immediately (no write lock contention).
- **Write-lock slow path**: If not connected, acquire write lock, check again (double-check), connect with backoff.

This means constructors (`postgres.New`, `mongo.NewClient`, `redis.New`) never block on DNS or TCP.

### 3. Create-Verify-Swap

When reconnecting, new connections are created and pinged before old ones are closed. This ensures there is no availability gap during reconnection — the old connection serves requests until the new one is verified healthy.

### 4. Credential Sanitization

All infrastructure packages strip credentials from error messages automatically:

- PostgreSQL DSNs: Regex-based password removal
- MongoDB URIs: `url.Redacted()` built-in
- RabbitMQ: Username/password stripped
- Redis: Password removed from connection strings

### 5. OTel Tracing on All I/O

Every exported method that performs I/O starts an OTel span. This means you get distributed tracing for free — database queries, HTTP calls, message publishing, and cache operations all appear in your trace waterfall without manual instrumentation.

### 6. Metrics via MetricsFactory

All connection packages accept a `MetricsFactory` (optional — nil disables metrics). Standard metric emitted by all: `{package}_connection_failures_total` counter. Additional package-specific metrics are documented per-package.

### 7. Exponential Backoff with Jitter

Used for reconnect rate-limiting in `postgres`, `mongo`, `redis`, and `rabbitmq`. The backoff cap is 30 seconds. The jitter strategy is AWS Full Jitter: `sleep = random_between(0, min(cap, base * 2^attempt))`.

### 8. Event-Driven Tenant Discovery (v4.5.0+)

Instead of polling the Tenant Manager API for new tenants (watcher model, removed in v4.5.0), services now subscribe to Redis pub/sub events. This provides:

- **Lower latency**: New tenants are discovered in milliseconds, not at the next poll interval
- **Lower load**: No periodic HTTP calls to the Tenant Manager API
- **Consistency**: All services receive tenant events simultaneously

The pattern: `TenantEventListener` subscribes to Redis pub/sub, receives `tenant.added`, `tenant.connections.updated`, and `tenant.credentials.rotated` events, and invokes the registered callbacks.

### 9. Variadic Context Pattern (v4.6.0)

Context functions for tenant-scoped resources use variadic module parameters instead of separate per-module functions:

```go
// Without module — uses default
db := tmcore.GetPGContext(ctx)

// With module — explicit module scope
db := tmcore.GetPGContext(ctx, "audit")
```

This pattern applies to both PG and MB context functions. The variadic approach allows a single middleware to inject multiple module-scoped connections, and repositories to retrieve the correct one without coupling to module-specific function names.

---

## 14. Which Package Do I Need?

Use this decision tree to find the right package quickly:

| I need to... | Package |
|-------------|---------|
| **Database** | |
| Connect to PostgreSQL | `postgres` |
| Connect to MongoDB | `mongo` |
| Connect to Redis/Valkey | `redis` |
| Acquire a distributed lock | `redis` (RedisLockManager) |
| **Messaging** | |
| Publish messages to RabbitMQ | `rabbitmq` (ConfirmablePublisher) |
| Consume messages from RabbitMQ (multi-tenant) | `rabbitmq` + `tenant-manager/consumer` |
| **HTTP** | |
| Add HTTP middleware (CORS, logging, telemetry) | `net/http` |
| Rate-limit HTTP endpoints | `net/http/ratelimit` |
| Enforce idempotency on mutating endpoints | `net/http/idempotency` (v5.0.0) |
| Paginate API responses | `net/http` (offset, UUID cursor, timestamp cursor, sort cursor) |
| Validate HTTP request bodies | `net/http` (`ParseBodyAndValidate`, `ValidateStruct`) |
| Send consistent API responses | `net/http` (`Respond`, `RespondStatus`, `RespondError`, `RenderError`) |
| Add health checks | `net/http` (`HealthWithDependencies`) |
| Parse and verify tenant-scoped IDs | `net/http` (`ParseAndVerifyTenantScopedID`, `ParseAndVerifyResourceScopedID`) |
| **Resilience** | |
| Add circuit breakers | `circuitbreaker` |
| Add retry logic with backoff | `backoff` (compute delay) + your own loop |
| Launch goroutines safely | `runtime` (`SafeGo`) |
| Run concurrent tasks with error handling | `errgroup` (panic-safe, first-error cancellation) |
| Do safe math (no panics) | `safe` (DivideOrZero, First, CachedRegexp) |
| **Security** | |
| Handle JWTs | `jwt` (Parse, Sign, ValidateTimeClaims) |
| Encrypt/decrypt data | `crypto` (AES-GCM encrypt/decrypt, HMAC hash) |
| Check if a field name is sensitive | `security` (`IsSensitiveField`) |
| Fetch AWS secrets for M2M auth | `secretsmanager` (`GetM2MCredentials`) |
| Handle license validation | `license` (fail-open/fail-closed policies) |
| Manage TLS certs with hot reload | `certificate` (v5.0.0 — `NewManager`, `Rotate`, `GetCertificateFunc`) |
| **Multi-Tenancy** | |
| Add multi-tenancy (database-per-tenant) | `tenant-manager` (full isolation system) |
| Discover tenants via events (HTTP services) | `tenant-manager/event` (`TenantEventListener`) |
| Discover tenants via events (consumer services) | `tenant-manager/consumer` (built-in event support) |
| Create Redis pub/sub client for tenant events | `tenant-manager/redis` (`NewTenantPubSubRedisClient`) |
| Cache tenants with load callback | `tenant-manager/tenantcache` (`TenantLoader` with `WithOnTenantLoaded`) |
| Get tenant-scoped PG/MB from context | `tenant-manager/core` (`GetPGContext(ctx, ...module)`, `GetMBContext(ctx, ...module)`) |
| Plug a custom cache into the TM client | `tenant-manager/cache` (v5.0.0 — `ConfigCache` interface, `InMemoryCache`) |
| Auto-inject `tenant_id` into every log line | `tenant-manager/log` (v5.0.0 — `TenantAwareLogger`) |
| **Webhooks & DLQ** | |
| Deliver webhooks with SSRF protection + HMAC signing | `webhook` (v5.0.0) |
| Verify incoming webhook signatures | `webhook` (v5.0.0 — `VerifySignature`, `VerifySignatureWithFreshness`) |
| Route failed messages to a retry queue | `dlq` (v5.0.0 — `Handler.Enqueue` + `Consumer`) |
| **Transactions** | |
| Process financial transactions | `transaction` (intent planning, balance posting) |
| Implement transactional outbox | `outbox` + `outbox/postgres` |
| **Observability** | |
| Add structured logging | `log` (interface) + `zap` (implementation) |
| Set up OpenTelemetry | `opentelemetry` (tracer, meter, logger providers) |
| Build custom metrics | `opentelemetry/metrics` (Counter, Gauge, Histogram builders) |
| Add production-safe assertions | `assert` (with OTel observability) |
| Manage graceful shutdown | `server` (ServerManager) |
| **Root Package Utilities** | |
| Generate UUIDv7 | `commons` (`GenerateUUIDv7`) |
| Map business errors to HTTP status | `commons` (`ValidateBusinessError`) |
| Get env var with default | `commons` (`GetenvOrDefault`) |
| Set config from env vars | `commons` (`SetConfigFromEnvVars`) |
| Remove accents / convert case | `commons` (`RemoveAccents`, `ToSnakeCase`, `ToCamelCase`) |
| Validate/parse dates | `commons` (`IsValidDate`, `ParseDate`, `ParseDateTime`) |
| Manage concurrent app lifecycle | `commons` (`Launcher`) |
| Carry request-scoped context | `commons` (`ContextWith*`, `WithTimeoutSafe`) |
| **Other** | |
| Parse cron expressions | `cron` (parse expression, compute next time) |
| Create pointers from literals | `pointers` (String, Bool, Time, Int64, Float64) |
| Use shared constants | `constants` (headers, error codes, OTel attributes) |
| Build scripts, Makefiles, ASCII banners | `shell` |

---

## 15. Breaking Changes

This section documents breaking changes across lib-commons releases. Consult when upgrading.

### v5.0.2

Patch release — no API changes. Hotfixes:

- `commons/rabbitmq`: Close leaked connections on concurrent reconnect in `EnsureChannelContext`
- `commons/net/http` telemetry: Copy Fiber context strings before `c.Next()` to prevent `UnsafeString` race (caused corrupted span attributes like `GET` → `GETT`)

### v5.0.1

Patch release — no API changes. Internal test improvements and minor fixes.

### v5.0.0

**Major release.** Module path bump + several new packages.

#### Module Path

| Change | Migration |
|---|---|
| **Go module major version bump** | Replace all `github.com/LerianStudio/lib-commons/v4/...` imports with `github.com/LerianStudio/lib-commons/v5/...`. Update `go.mod` to require `v5.0.2` (or latest). Run `go mod tidy`. |
| **Minimum Go version** | Now `go 1.25` — update your service's `go.mod` if it was on an older Go toolchain. |

#### New Packages

| Package | Purpose |
|---|---|
| `commons/certificate` | TLS certificate manager with hot reload |
| `commons/dlq` | Redis-backed dead letter queue with exponential-backoff retry |
| `commons/webhook` | SSRF-safe HMAC-signed webhook delivery engine (includes SSRF validation — does **not** live in a separate `ssrf` package) |
| `commons/net/http/idempotency` | Fiber idempotency middleware with Redis SetNX, tenant-scoped keys, faithful response replay |
| `commons/tenant-manager/cache` | `ConfigCache` interface + `InMemoryCache` default implementation for the TM client |
| `commons/tenant-manager/log` | `TenantAwareLogger` — wraps a `log.Logger` and auto-injects `tenant_id` from context |

No packages were renamed. No public APIs changed signatures — the v5 core (postgres, mongo, redis, rabbitmq, opentelemetry, tenant-manager middleware/consumer/event/core, etc.) is source-compatible with v4.6.0 after the module-path bump.

### v4.6.0

| Change | Migration |
|--------|-----------|
| **MultiPoolMiddleware removed** | Use unified `WithPG`/`WithMB` API on `NewTenantMiddleware` with optional module parameter |
| **Context API unified (PG)** | `ContextWithTenantPG(ctx, pg)` → `ContextWithPG(ctx, pg, ...module)` (variadic) |
| **Context API unified (MB)** | `ContextWithTenantMB(ctx, mb)` → `ContextWithMB(ctx, mb, ...module)` (variadic) |
| **GetPGContext variadic** | `GetPGContext(ctx)` still works; for modules use `GetPGContext(ctx, "module")` |
| **GetMBContext variadic** | `GetMBContext(ctx)` still works; for modules use `GetMBContext(ctx, "module")` |
| **S3 key function renamed** | `GetObjectStorageKeyForTenant` → `GetS3KeyStorageContext` |
| **Settings option renamed** | `WithSettingsCheckInterval` → `WithConnectionsCheckInterval` |

### v4.5.0

| Change | Migration |
|--------|-----------|
| **Watcher removed** | Replace watcher-based tenant discovery with event-driven model using `TenantEventListener` (Redis pub/sub) |
| **New dependency**: Redis pub/sub | Services discovering tenants now need a Redis connection for pub/sub |

### v4.3.0

| Change | Migration |
|--------|-----------|
| **Zap timestamp format** | `"ts"` field (Unix epoch float) → `"timestamp"` field (ISO 8601 string). Update log parsers, Fluentd/Logstash configs, and Grafana queries |

### v4.2.0

| Change | Migration |
|--------|-----------|
| **TM client endpoint** | `/settings` → `/connections` |
| **TM client path prefix** | Added `/v1/associations/` prefix to all TM API calls |
| **Rate limiting added** | New package `net/http/ratelimit` — not a breaking change but new capability with env vars |

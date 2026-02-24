---
name: ring:dev-multi-tenant
version: 1.0.0
type: skill
description: |
  Multi-tenant development cycle orchestrator following Ring Standards.
  Auto-detects the service stack (PostgreSQL, MongoDB, Redis, RabbitMQ),
  then executes a gate-based implementation using tenantId from JWT
  for database-per-tenant isolation via lib-commons v3 TenantConnectionManager.
  Each gate dispatches ring:backend-engineer-golang with context and section references.
  The agent loads multi-tenant.md via WebFetch and has all code examples.

trigger: |
  - User requests multi-tenant implementation for a Go service
  - User asks to add tenant isolation to an existing service
  - Task mentions "multi-tenant", "tenant isolation", "TenantConnectionManager"

prerequisite: |
  - Go service with existing single-tenant functionality

NOT_skip_when: |
  - "organization_id already exists" → organization_id is NOT multi-tenant. tenantId via JWT is required.
  - "Just need to connect the wiring" → Multi-tenant requires lib-commons v3 TenantConnectionManager.
  - "lib-commons v3 upgrade is too risky" → Multi-tenant REQUIRES v3. No v3 = no multi-tenant.

sequence:
  after: [ring:dev-devops]

related:
  complementary: [ring:dev-cycle, ring:dev-implementation, ring:dev-devops, ring:dev-unit-testing, ring:requesting-code-review, ring:dev-validation]

output_schema:
  format: markdown
  required_sections:
    - name: "Multi-Tenant Cycle Summary"
      pattern: "^## Multi-Tenant Cycle Summary"
      required: true
    - name: "Stack Detection"
      pattern: "^## Stack Detection"
      required: true
    - name: "Gate Results"
      pattern: "^## Gate Results"
      required: true
    - name: "Verification"
      pattern: "^## Verification"
      required: true
  metrics:
    - name: gates_passed
      type: integer
    - name: gates_failed
      type: integer
    - name: total_files_changed
      type: integer

examples:
  - name: "Add multi-tenant to a service"
    invocation: "/ring:dev-multi-tenant"
    expected_flow: |
      1. Gate 0: Auto-detect stack
      2. Gate 1: Analyze codebase (build implementation roadmap)
      3. Gates 2-6: Implementation (agent loads multi-tenant.md, follows roadmap)
      4. Gate 7: Metrics & Backward compatibility
      5. Gate 8: Tests
      6. Gate 9: Code review
      7. Gate 10: User validation
---

# Multi-Tenant Development Cycle

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Load multi-tenant.md via WebFetch, implement following the standards |
| **6 reviewers** | Review at Gate 8 |

**⛔ CANNOT change scope:** the skill defines WHAT to implement. The agent implements HOW.

**⛔ MANDATORY: TDD for all implementation gates (Gates 2-6).** MUST follow RED-GREEN: write a failing test first, then implement to make it pass. MUST include in every dispatch: "Follow TDD: write failing test (RED), then implement (GREEN)."

</cannot_skip>

---

## How Multi-Tenant Works

Multi-tenant isolation is 100% based on `tenantId` from JWT → `TenantConnectionManager` → database-per-tenant. Each tenant has its own database. `organization_id` is NOT part of multi-tenant.

**Standards reference:** All code examples and implementation patterns are in `multi-tenant.md`. MUST load via WebFetch before implementing any gate.

**WebFetch URL:** `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md`

### MANDATORY: Agent Instruction (include in EVERY gate dispatch)

MUST include these instructions in every dispatch to `ring:backend-engineer-golang`:

> **STANDARDS: WebFetch `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` and follow the sections referenced below. All code examples, patterns, and implementation details are in that document. Use them as-is.**
>
> **TDD: For implementation gates (2-6), follow TDD methodology — write a failing test first (RED), then implement to make it pass (GREEN). MUST have test coverage for every change.**

This ensures the agent loads the standards first, uses canonical code examples, and follows TDD for all implementation work.

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection | Always | Orchestrator |
| 1 | Codebase Analysis (multi-tenant focus) | Always | ring:codebase-explorer |
| 2 | lib-commons v3 Upgrade | Skip if already v3 | ring:backend-engineer-golang |
| 3 | Multi-Tenant Configuration | Skip if already configured | ring:backend-engineer-golang |
| 4 | TenantMiddleware | Always (core) | ring:backend-engineer-golang |
| 5 | Repository Adaptation | Per detected DB | ring:backend-engineer-golang |
| 6 | RabbitMQ Multi-Tenant (lazy init, vhosts, ConsumerTrigger) | Skip if no RabbitMQ | ring:backend-engineer-golang |
| 7 | Metrics & Backward Compat | Always | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review | Always | 6 parallel reviewers |
| 10 | User Validation | Always | User |
| 11 | Activation Guide | Always | Orchestrator |

**⛔ Gates are SEQUENTIAL. No skipping. No reordering.**

---

## Gate 0: Stack Detection

**Orchestrator executes directly. No agent dispatch.**

```text
DETECT (run in parallel):

1. lib-commons version:  grep "lib-commons" go.mod
2. PostgreSQL:           grep -rn "postgresql\|pgx\|squirrel" internal/ go.mod
3. MongoDB:              grep -rn "mongodb\|mongo" internal/ go.mod
4. Redis:                grep -rn "redis\|valkey" internal/ go.mod
5. RabbitMQ:             grep -rn "rabbitmq\|amqp" internal/ go.mod
6. Existing multi-tenant:
   - Config:     grep -rn "MULTI_TENANT_ENABLED" internal/
   - Middleware: grep -rn "tenantmanager\|WithTenantDB" internal/
   - Context:    grep -rn "GetMongoForTenant\|GetPostgresForTenant" internal/
   - RMQ:        grep -rn "X-Tenant-ID" internal/
```

**MUST confirm: user explicitly approves detection results before proceeding.**

---

## Gate 1: Codebase Analysis (Multi-Tenant Focus)

**Always executes. This gate builds the implementation roadmap for all subsequent gates.**

**Dispatch `ring:codebase-explorer` with multi-tenant-focused context:**

> TASK: Analyze this codebase exclusively under the multi-tenant perspective.
> DETECTED STACK: {databases and messaging from Gate 0}
>
> CRITICAL: Multi-tenant is ONLY about tenantId from JWT → TenantConnectionManager → database-per-tenant.
> IGNORE organization_id completely — it is NOT multi-tenant. A tenant can have multiple organizations inside its database. organization_id is a domain entity, not a tenant identifier.
>
> FOCUS AREAS (explore ONLY these — ignore everything else):
>
> 1. **Service name, modules, and components**: What is the service called? (Look for `const ApplicationName`.) How many components/modules does it have? Each module needs a constant (e.g., `const ModuleManager = "manager"`). Identify: service name (ApplicationName), module names per component, and whether constants exist or need to be created. Hierarchy: Service → Module → Resource.
> 2. **Bootstrap/initialization**: Where does the service start? Where are database connections created? Where is the middleware chain registered? Identify the exact insertion point for TenantMiddleware.
> 3. **Database connections**: How do repositories get their DB connection today? Static field in struct? Constructor injection? Context? List EVERY repository file with file:line showing where the connection is obtained.
> 4. **Middleware chain**: What middleware exists and in what order? Where would TenantMiddleware fit (after auth, before handlers)?
> 5. **Config struct**: Where is the Config struct? What fields exist? Where is it loaded? Identify exact location for MULTI_TENANT_ENABLED vars.
> 6. **RabbitMQ** (if detected): Where are producers? Where are consumers? How are messages published? Where would X-Tenant-ID header be injected? Are producer and consumer in the SAME process or SEPARATE components? Is there already a config split (`if cfg.IsMultiTenant()`) for RabbitMQ initialization? Are there dual constructors (`NewProducerMultiTenant` vs `NewProducerRabbitMQ`)? Is there a `RabbitMQManager` pool? Does the service struct have both `*MultiQueueConsumer` and `*MultiTenantRabbitMQConsumer`?
> 7. **Redis** (if detected): Where are Redis operations? Any Lua scripts? Where would GetKeyFromContext be needed?
> 8. **Existing multi-tenant code**: Any tenantmanager imports? TenantMiddleware? GetPostgresForTenant/GetMongoForTenant calls? MULTI_TENANT_ENABLED config? (NOTE: organization_id is NOT related to multi-tenant — ignore it completely. Multi-tenant is exclusively tenantId from JWT → database routing)
>
> OUTPUT FORMAT: Structured report with file:line references for every point above.
> DO NOT write code. Analysis only.

**The explorer produces a report like:**

```markdown
## Multi-Tenant Codebase Analysis

### Bootstrap
- Config struct: internal/bootstrap/config.go:15 — no MULTI_TENANT_* fields
- Service init: internal/bootstrap/service.go:42 — DB connections created here
- Middleware registration: internal/bootstrap/server.go:78 — insert TenantMiddleware after auth middleware (line 82)

### Database Connections ({N} repository files)
- internal/adapters/mongodb/report/report.mongodb.go:34 — static conn field `conn *libMongo.MongoConnection`, used at lines 56, 89, 124
- internal/adapters/mongodb/template/template.mongodb.go:28 — static conn field, used at lines 45, 78, 112
- internal/adapters/redis/cache.go:22 — static client, used at lines 38, 55

### RabbitMQ (if applicable)
- Producer: internal/adapters/rabbitmq/producer.go:45 — publishes at line 67, no X-Tenant-ID header
- Consumer: internal/adapters/rabbitmq/consumer.go:32 — processes at line 58, no tenant context

### Redis (if applicable)
- internal/adapters/redis/cache.go:38 — Set() without key prefix
- internal/adapters/redis/cache.go:55 — Get() without key prefix

### Gap Summary
| # | Item | Current State | Required State | Action | Files |
|---|------|--------------|----------------|--------|-------|
| 1 | lib-commons version | v2 / v3 | v3 | Upgrade if v2 | go.mod |
| 2 | ApplicationName const | Exists / Missing | `const ApplicationName = "..."` (service name) | Create if missing | pkg/constant/ |
| 3 | Module consts | Exists / Missing | `const Module{Name} = "..."` per component | Create if missing | pkg/constant/ |
| 4 | MULTI_TENANT_ENABLED config | Exists / Missing | 7 env vars in Config struct (both components) | Add if missing | bootstrap/config.go |
| 5 | Conditional initialization | Exists / Missing | `if cfg.IsMultiTenant()` with log message | Add if missing | bootstrap/ |
| 6 | Tenant Manager client | Exists / Missing | `tenantmanager.NewClient(url, logger, opts...)` | Create if missing | bootstrap/ |
| 7 | Circuit breaker | Exists / Missing | `WithCircuitBreaker(threshold, timeout)` on client | Add if configured | bootstrap/ |
| 8 | Connection managers | Exists / Missing | NewMongoManager/NewPostgresManager per module with `WithModule(const)` | Create per detected DB | bootstrap/ |
| 9 | TenantMiddleware | Exists / Missing | `WithTenantDB` registered after auth, before handlers | Implement if missing | bootstrap/ |
| 10 | JWT tenantId extraction | Exists / Missing | Middleware extracts `tenantId` claim from JWT | Verify in middleware | bootstrap/ |
| 11 | Repository connections | Static / Context | `GetMongoForTenant(ctx)` / `GetPostgresForTenant(ctx)` | Adapt per repo file | adapters/ |
| 12 | Redis key prefixing | No prefix / Prefixed | `GetKeyFromContext(ctx, key)` for all ops + Lua scripts | Add if Redis detected | adapters/ |
| 13 | RabbitMQ producer (header) | Missing / Present | `X-Tenant-ID` header injection in AMQP messages | Add if RabbitMQ detected | adapters/ |
| 14 | RabbitMQ producer (dual constructor) | Missing / Present | `NewProducerMultiTenant(pool)` vs `NewProducerRabbitMQ(conn)` | Add if RabbitMQ detected | adapters/ |
| 15 | RabbitMQ consumer (header) | Missing / Present | Extract `X-Tenant-ID` from AMQP header + inject tenant DB | Add if RabbitMQ detected | adapters/ |
| 16 | RabbitMQ consumer (lazy init) | Missing / Present | `MultiTenantConsumer` with handler registration (NOT started at boot) | Add if RabbitMQ detected | bootstrap/ |
| 17 | RabbitMQ config split | Missing / Present | `if cfg.IsMultiTenant()` branches for producer AND consumer init | Add if RabbitMQ detected | bootstrap/ |
| 18 | RabbitMQManager pool | Missing / Present | `NewRabbitMQManager(tmClient, serviceName, WithRabbitMQModule(...))` | Add if RabbitMQ detected | bootstrap/ |
| 19 | ConsumerTrigger interface | Missing / Present | `EnsureConsumerStarted(ctx, tenantID)` wired to middleware | MANDATORY if RabbitMQ detected | bootstrap/ |
| 20 | Service struct (both consumers) | Missing / Present | `*MultiQueueConsumer` (single) + `*MultiTenantRabbitMQConsumer` (multi) | Add if RabbitMQ detected | bootstrap/ |
| 21 | Public endpoint bypass | Exists / Missing | /health, /version, /swagger skip tenant middleware | Verify | bootstrap/ |
| 22 | Backward compatibility | N/A | `IsMultiTenant()` passthrough, single-tenant works unchanged | Verify + write test | bootstrap/ |
| 23 | Metrics | Missing / Present | `tenant_connections_total`, `tenant_connection_errors_total` (+2 if RabbitMQ) | Add | bootstrap/ |
| 24 | Error handling | Missing / Present | Map tenant errors to HTTP: 401/404/422/403/503 | Add in error handler | adapters/ |
| 25 | Graceful shutdown | Exists / Missing | Close tenant managers on shutdown (LIFO cleanup) | Verify in cleanup stack | bootstrap/ |
| 26 | Tests — unit | Missing / Present | Mock tenant context, verify per-repo | Write | tests/ |
| 27 | Tests — isolation | Missing / Present | Two tenants, data separation | Write | tests/ |
| 28 | Tests — error cases | Missing / Present | Missing JWT, tenant not found, not provisioned | Write | tests/ |
| 29 | Tests — backward compat | Missing / Present | `TestMultiTenant_BackwardCompatibility` | Write | tests/ |
```

**This report becomes the CONTEXT for all subsequent gates.** Each gate receives: "Here is what needs to change (from Gate 1 analysis), now implement Gate N following multi-tenant.md."

**⛔ HARD GATE: MUST complete the analysis report before proceeding. All subsequent gates use this report to know exactly what to change.**

**⛔ MUST ensure backward compatibility context:** The analysis MUST identify how the service works today in single-tenant mode, so subsequent gates preserve this behavior when `MULTI_TENANT_ENABLED=false`.

---

## Gate 2: lib-commons v3 Upgrade

**SKIP IF:** already v3.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Upgrade lib-commons from v2 to v3. Update go.mod and all import paths.
> Follow multi-tenant.md section "Required lib-commons Version".
> DO NOT implement multi-tenant code yet — only upgrade the dependency.
> Verify: go build ./... and go test ./... MUST pass.

**Verification:** `grep "lib-commons/v3" go.mod` + `go build ./...` + `go test ./...`

**⛔ HARD GATE: MUST pass build and tests before proceeding.**

---

## Gate 3: Multi-Tenant Configuration

**SKIP IF:** config already has `MULTI_TENANT_ENABLED`.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Add multi-tenant environment variables to the Config struct.
> CONTEXT FROM GATE 1: {Config struct location and current fields from analysis report}
> Follow multi-tenant.md sections "Environment Variables", "Configuration", and "Conditional Initialization".
> Add conditional log: "Multi-tenant mode enabled" vs "Running in SINGLE-TENANT MODE".
> DO NOT implement TenantMiddleware yet — only configuration.

**Verification:** `grep "MULTI_TENANT_ENABLED" internal/bootstrap/config.go` + `go build ./...`

---

## Gate 4: TenantMiddleware (Core)

**SKIP IF:** middleware already exists.

**This is the CORE gate. Without TenantMiddleware, there is no tenant isolation.**

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement TenantMiddleware using lib-commons/v3 tenant-manager package.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N} (from Gate 0)
> CONTEXT FROM GATE 1: {Bootstrap location, middleware chain insertion point, service init from analysis report}
>
> CRITICAL — HIERARCHY: Service → Module → Resource
>
> The Tenant Manager API follows this hierarchy:
> - **Service**: The top-level application name. Passed as `serviceName` to connection managers. Used in: `GET /tenants/{tenantID}/services/{serviceName}/settings`
> - **Module**: A component within the service. Each module has its own database credentials in the `/settings` response. Passed via `WithModule()` / `WithMongoModule()`.
> - **Resource**: The database type within a module (postgresql, mongodb, rabbitmq). Provisioned per module in the Tenant Manager.
>
> ```
> Service: {ApplicationName}
>   ├── Module: {component-a}  → Resources (PostgreSQL, MongoDB, ...)
>   └── Module: {component-b}  → Resources (MongoDB, RabbitMQ, ...)
> ```
>
> MUST define constants for service name and module names — never pass raw strings:
> ```go
> // pkg/constant/app.go
> const (
>     ApplicationName = "my-service"     // SERVICE — registered in Tenant Manager
>     ModuleAPI       = "api"            // MODULE — component within the service
>     ModuleWorker    = "worker"         // MODULE — component within the service
> )
> ```
>
> In bootstrap, the first parameter is always the SERVICE (ApplicationName),
> and WithModule/WithMongoModule receives the MODULE (component name):
> ```go
> // API component bootstrap:
> NewMongoManager(client, constant.ApplicationName,          // ← SERVICE (not module)
>     tenantmanager.WithMongoModule(constant.ModuleAPI),     // ← MODULE (not service)
> )
>
> // Worker component bootstrap:
> NewMongoManager(client, constant.ApplicationName,          // ← same SERVICE
>     tenantmanager.WithMongoModule(constant.ModuleWorker),  // ← different MODULE
> )
> ```
>
> The `/settings` response groups credentials by MODULE name:
> ```json
> GET /tenants/{tenantId}/services/{ApplicationName}/settings
> {
>   "databases": {
>     "api":    { "mongodb": { "host": "...", ... } },
>     "worker": { "mongodb": { "host": "...", ... } }
>   }
> }
> ```
>
> Examples:
> - Service with 2 components: service=`"reporter"`, modules=`"manager"`, `"worker"`
> - Service with 2 domains: service=`"ledger"`, modules=`"onboarding"`, `"transaction"`
>
> Follow multi-tenant.md sections "Generic TenantMiddleware", "JWT Tenant Extraction", and "Conditional Initialization".
> Create connection managers ONLY for detected databases.
> Public endpoints (/health, /version, /swagger) MUST bypass tenant middleware.
>
> CRITICAL: tenantId comes from JWT, NOT from URL path parameters.
> The middleware resolves which DATABASE to connect to.
> When MULTI_TENANT_ENABLED=false, middleware calls c.Next() immediately (single-tenant passthrough).
>
> **IF RabbitMQ DETECTED:**
> MUST accept an optional `ConsumerTrigger` parameter in the TenantMiddleware handler.
> When not nil, the middleware calls `consumerTrigger.EnsureConsumerStarted(ctx, tenantID)` AFTER tenant ID extraction
> to trigger lazy consumer activation for that tenant's RabbitMQ vhost.
> DO NOT block the request on consumer startup — this is a fire-and-forget call.
> MUST keep the existing single-tenant code path untouched: when `ConsumerTrigger` is nil (single-tenant mode or no RabbitMQ), this is a no-op.
> MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode — connections are resolved lazily per-tenant.
>
> ```go
> // Example middleware with ConsumerTrigger
> func NewTenantMiddlewareHandler(
>     tenantMid *tenantmanager.TenantMiddleware,
>     consumerTrigger ConsumerTrigger,  // nil when no RabbitMQ or single-tenant
> ) fiber.Handler {
>     return func(c *fiber.Ctx) error {
>         if tenantMid == nil { return c.Next() }       // single-tenant passthrough
>         if isPublicPath(c.Path()) { return c.Next() } // public endpoints
>
>         err := tenantMid.WithTenantDB(c)              // resolve tenant DB
>         if err != nil { return err }
>
>         // Lazy consumer trigger (fire-and-forget)
>         if consumerTrigger != nil {
>             tenantID := tenantmanager.GetTenantID(c.UserContext())
>             if tenantID != "" {
>                 consumerTrigger.EnsureConsumerStarted(c.UserContext(), tenantID)
>             }
>         }
>         return c.Next()
>     }
> }
> ```

**Verification:** `grep "tenantmanager.NewTenantMiddleware" internal/bootstrap/` + `go build ./...`

**⛔ HARD GATE: Cannot proceed without TenantMiddleware.**

---

## Gate 5: Repository Adaptation

**SKIP IF:** repositories already use context-based connections.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Adapt all repository implementations to get database connections from tenant context instead of static connections.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N, redis: Y/N} (from Gate 0)
> CONTEXT FROM GATE 1: {List of ALL repository files with file:line showing static connections from analysis report}
>
> Follow multi-tenant.md sections:
> - "Database Connection in Repositories" (PostgreSQL)
> - "MongoDB Multi-Tenant Repository" (MongoDB)
> - "Redis Key Prefixing" and "Redis Key Prefixing for Lua Scripts" (Redis)
>
> MUST work in both modes: multi-tenant (connection from context) and single-tenant (default connection via passthrough).

**Verification:** grep for `GetPostgresForTenant` / `GetMongoForTenant` / `GetKeyFromContext` in `internal/adapters/` + `go build ./...`

---

## Gate 6: RabbitMQ Multi-Tenant

**SKIP IF:** no RabbitMQ detected.

**This gate implements the FULL multi-tenant RabbitMQ pattern: lazy initialization, per-tenant vhosts, dual constructors, and ConsumerTrigger.**

**MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode:** each tenant has its own RabbitMQ vhost and connections are resolved lazily per-tenant via `RabbitMQManager.GetChannel(ctx, tenantID)`.

**Standards reference:** See `../../docs/standards/golang/multi-tenant.md` sections "RabbitMQ Multi-Tenant Producer", "Multi-Tenant Message Queue Consumers (Lazy Mode)", and "ConsumerTrigger Interface" for canonical patterns and code examples.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement RabbitMQ multi-tenant patterns with lazy initialization.
> CONTEXT FROM GATE 1: {Producer and consumer file:line locations from analysis report}
> DETECTED ARCHITECTURE: {Are producer and consumer in the same process or separate components?}
>
> MUST follow multi-tenant.md sections "RabbitMQ Multi-Tenant Producer", "Multi-Tenant Message Queue Consumers (Lazy Mode)", and "ConsumerTrigger Interface".
>
> ## Gate-specific orchestration:
>
> **1. CONFIG SPLIT (MANDATORY):** MUST branch on `cfg.IsMultiTenant()` for both producer and consumer in bootstrap:
>
> ```go
> // Producer initialization
> if cfg.IsMultiTenant() {
>     result := initMultiTenantProducer(cfg, logger)      // NO connection at startup
>     producerRepo = result.Producer
>     rabbitMQPool = result.Pool                           // RabbitMQManager for lazy channels
> } else {
>     result := initSingleTenantProducer(cfg, logger)      // IMMEDIATE connection (current behavior)
>     producerRepo = result.Producer
> }
>
> // Consumer initialization
> if cfg.IsMultiTenant() {
>     multiTenantConsumer = initMultiTenantConsumer(cfg, rabbitMQPool, redisClient, useCase, logger)  // NO connection
> } else {
>     staticConsumer = initSingleTenantConsumer(cfg, useCase, logger)                    // IMMEDIATE connection
> }
> ```
>
> **⛔ MUST keep the existing single-tenant code path untouched.** Only the multi-tenant branch is new.
>
> **2. RABBITMQMANAGER POOL (MANDATORY):** MUST create the pool in bootstrap with no connection:
>
> ```go
> rabbitMQPool := tenantmanager.NewRabbitMQManager(tmClient, constant.ApplicationName,
>     tenantmanager.WithRabbitMQModule(constant.ModuleWorker),
>     tenantmanager.WithRabbitMQLogger(logger),
>     tenantmanager.WithRabbitMQMaxTenantPools(cfg.MultiTenantMaxTenantPools),
>     tenantmanager.WithRabbitMQIdleTimeout(idleTimeout),
> )
> ```
>
> **3. CONSUMERTRIGGER (MANDATORY):** MUST implement the `ConsumerTrigger` interface (see multi-tenant.md "ConsumerTrigger Interface") and wire `EnsureConsumerStarted(ctx, tenantID)` to the TenantMiddleware (see Gate 4). The Service struct MUST hold both consumer types:
>
> ```go
> type Service struct {
>     *MultiQueueConsumer              // Single-tenant only (nil in multi-tenant mode)
>     *MultiTenantRabbitMQConsumer     // Multi-tenant only (nil in single-tenant mode)
> }
>
> func (app *Service) GetConsumerTrigger() ConsumerTrigger {
>     if app.MultiTenantRabbitMQConsumer == nil {
>         return nil
>     }
>     return app.MultiTenantRabbitMQConsumer
> }
> ```
>
> **4. X-Tenant-ID AMQP HEADER (MANDATORY):**
> - MUST inject `X-Tenant-ID` header in producer when tenant context is present
> - MUST extract `X-Tenant-ID` from AMQP headers in consumer and inject tenant context
> - MUST place the header in the AMQP headers table, NOT in the message body
>
> **Summary: Single-Tenant vs Multi-Tenant Startup**
>
> | Phase | Single-Tenant | Multi-Tenant |
> |-------|---------------|--------------|
> | Startup | Producer: `GetNewConnect()` blocks | Producer: pool created, NO connection |
> | Startup | Consumer: `RunConsumers()` blocks | Consumer: handlers registered, NOT started |
> | First request | N/A (already connected) | `EnsureConsumerStarted(tenantID)` spawns consumer |
> | Publish | Static channel | `GetChannel(ctx, tenantID)` → tenant vhost |

**Verification:**
- `grep "RabbitMQManager\|NewProducerMultiTenant\|EnsureConsumerStarted\|ConsumerTrigger" internal/` + `go build ./...`
- Multi-tenant mode: service starts WITHOUT connecting to RabbitMQ
- Single-tenant mode: service starts WITH immediate RabbitMQ connection (backward compat)

**⛔ HARD GATE: MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode.**

---

## Gate 7: Metrics & Backward Compatibility

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Add multi-tenant metrics and validate backward compatibility.
>
> Follow multi-tenant.md sections "Multi-Tenant Metrics" and "Single-Tenant Backward Compatibility Validation (MANDATORY)".
>
> BACKWARD COMPATIBILITY IS NON-NEGOTIABLE:
> - MUST start without any MULTI_TENANT_* env vars
> - MUST start without Tenant Manager running
> - MUST pass all existing tests with MULTI_TENANT_ENABLED=false
> - Health/version endpoints MUST work without tenant context
>
> Write TestMultiTenant_BackwardCompatibility integration test.

**Verification:** `MULTI_TENANT_ENABLED=false go test ./...` MUST pass.

**⛔ HARD GATE: Backward compatibility MUST pass.**

---

## Gate 8: Tests

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Write multi-tenant tests.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, rabbitmq: Y/N} (from Gate 0)
>
> Follow multi-tenant.md section "Testing Multi-Tenant Code" (all subsections).
>
> Required tests: unit tests with mock tenant context, tenant isolation tests (two tenants, data separation), error case tests (missing JWT, tenant not found), plus RabbitMQ and Redis tests if detected.

**Verification:** `go test ./... -v -count=1` + `go test ./... -cover`

---

## Gate 9: Code Review

**Dispatch 6 parallel reviewers (same pattern as ring:requesting-code-review).**

MUST include this context in ALL 6 reviewer dispatches:

> **MULTI-TENANT REVIEW CONTEXT:**
> - Multi-tenant isolation is based on `tenantId` from JWT → `TenantConnectionManager` → database-per-tenant.
> - `organization_id` is NOT a tenant identifier. It is a business filter within the tenant's database. A single tenant can have multiple organizations. Do NOT flag organization_id as a multi-tenant issue.
> - Backward compatibility is required: when `MULTI_TENANT_ENABLED=false`, the service MUST work exactly as before (single-tenant mode, no tenant context needed).

| Reviewer | Focus |
|----------|-------|
| ring:code-reviewer | Architecture, lib-commons v3 usage, TenantMiddleware placement |
| ring:business-logic-reviewer | Tenant context propagation via tenantId (NOT organization_id) |
| ring:security-reviewer | Cross-tenant DB isolation, JWT tenantId validation, no data leaks between tenant databases |
| ring:test-reviewer | Coverage, isolation tests between two tenants, backward compat tests |
| ring:nil-safety-reviewer | Nil risks in tenant context extraction from JWT and context getters |
| ring:consequences-reviewer | Impact on single-tenant paths, backward compat when MULTI_TENANT_ENABLED=false |

**MUST pass all 6 reviewers. Critical findings → fix and re-review.**

---

## Gate 10: User Validation

**MUST approve: present checklist for explicit user approval.**

```markdown
## Multi-Tenant Implementation Complete

- [ ] lib-commons v3
- [ ] MULTI_TENANT_ENABLED config
- [ ] TenantMiddleware (JWT tenantId → DB routing)
- [ ] Repositories use context-based connections
- [ ] RabbitMQ X-Tenant-ID (if applicable)
- [ ] Backward compat (MULTI_TENANT_ENABLED=false works)
- [ ] Tests pass
- [ ] Code review passed
```

---

## Gate 11: Activation Guide

**MUST generate `docs/multi-tenant-guide.md` in the project root.** Direct, concise, no filler text.

The file is built from Gate 0 (stack) and Gate 1 (analysis). Template:

```markdown
# Multi-Tenant Guide — {service_name}

## Components

| Component | Service (const) | Module (const) | Resources | Adapted |
|-----------|----------------|----------------|-----------|---------|
| {name}    | {ApplicationName} | {ModuleName} | {MongoDB, PostgreSQL, Redis, RabbitMQ...} | {GetMongoForTenant, GetKeyFromContext, X-Tenant-ID...} |

**Service** = `const ApplicationName` — the top-level service registered in Tenant Manager.
**Module** = `const Module{Name}` — the component within the service. Each module has its own credentials in `/settings`.
Both MUST be constants (never raw strings). The service must match: `GET /tenants/{tenantID}/services/{ApplicationName}/settings`.

## Environment Variables

Add to **every component** listed above:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MULTI_TENANT_ENABLED` | Yes | `false` | Activate multi-tenant |
| `MULTI_TENANT_URL` | If enabled | — | Tenant Manager URL |
| `MULTI_TENANT_ENVIRONMENT` | Only if RabbitMQ | `staging` | Cache key segmentation for lazy consumer tenant discovery |
| `MULTI_TENANT_MAX_TENANT_POOLS` | No | `100` | Connection pool soft limit (LRU) |
| `MULTI_TENANT_IDLE_TIMEOUT_SEC` | No | `300` | Idle eviction timeout |
| `MULTI_TENANT_CIRCUIT_BREAKER_THRESHOLD` | No | `5` | Failures before circuit opens |
| `MULTI_TENANT_CIRCUIT_BREAKER_TIMEOUT_SEC` | No | `30` | Circuit reset timeout |

## Activate

1. Add `MULTI_TENANT_ENABLED=true` and `MULTI_TENANT_URL` to each component
2. Tenant Manager must be running with tenant provisioned (database credentials configured)

## Verify

- Logs: "Multi-tenant mode enabled with Tenant Manager URL: ..."
- JWT with `tenantId` → routes to tenant database
- JWT without `tenantId` → 401 TENANT_ID_REQUIRED

## Deactivate

Set `MULTI_TENANT_ENABLED=false` or remove it. Single-tenant mode, no Tenant Manager needed.

## Errors

| Status | Code | Fix |
|--------|------|-----|
| 401 | TENANT_ID_REQUIRED | Add `tenantId` to JWT |
| 404 | TENANT_NOT_FOUND | Provision tenant in Tenant Manager |
| 503 | Connection error | Check MULTI_TENANT_URL |
| 503 | Circuit breaker open | Tenant Manager down, wait or fix |
```

---

## State Persistence

Save to `docs/ring-dev-multi-tenant/current-cycle.json` for resume support:

```json
{
  "cycle": "multi-tenant",
  "stack": {"postgresql": false, "mongodb": true, "redis": true, "rabbitmq": true},
  "gates": {"0": "PASS", "1": "PASS", "2": "IN_PROGRESS", "3": "PENDING"},
  "current_gate": 2
}
```

---

## Anti-Rationalization Table

See [multi-tenant.md](../../docs/standards/golang/multi-tenant.md) for the canonical anti-rationalization tables on tenantId vs organization_id.

**Skill-specific rationalizations:**

| Rationalization | Why It's WRONG | Required Action |
|-----------------|----------------|-----------------|
| "Agent says out of scope" | Skill defines scope, not agent. | **Re-dispatch with gate context** |
| "Skip tests" | Gate 8 proves isolation works. | **MANDATORY** |
| "Skip review" | Security implications. One mistake = data leak. | **MANDATORY** |

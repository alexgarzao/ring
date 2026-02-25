---
name: ring:dev-multi-tenant
slug: dev-multi-tenant
version: 2.0.0
type: skill
description: |
  Multi-tenant development cycle orchestrator following Ring Standards.
  Auto-detects the service stack (PostgreSQL, MongoDB, Redis, RabbitMQ, S3),
  then executes a gate-based implementation using tenantId from JWT
  for database-per-tenant isolation via lib-commons v3 tenant-manager sub-packages (postgres.Manager, mongo.Manager).
  MUST update lib-commons v3 first; lib-auth v2 depends on it. Both are required dependencies.
  Each gate dispatches ring:backend-engineer-golang with context and section references.
  The agent loads multi-tenant.md via WebFetch and has all code examples.

trigger: |
  - User requests multi-tenant implementation for a Go service
  - User asks to add tenant isolation to an existing service
  - Task mentions "multi-tenant", "tenant isolation", "tenant-manager", "postgres.Manager", "MultiPoolMiddleware"

prerequisite: |
  - Go service with existing single-tenant functionality

NOT_skip_when: |
  - "organization_id already exists" → organization_id is NOT multi-tenant. tenantId via JWT is required.
  - "Just need to connect the wiring" → Multi-tenant requires lib-commons v3 tenant-manager sub-packages.
  - "lib-commons v3 upgrade is too risky" → REQUIRES lib-commons v3 tenant-manager sub-packages. No v3 = no multi-tenant.

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
      3. Gate 1.5: Visual implementation preview (HTML report for developer approval)
      4. Gates 2-6: Implementation (agent loads multi-tenant.md, follows roadmap)
      5. Gate 7: Metrics & Backward compatibility
      6. Gate 8: Tests
      7. Gate 9: Code review
      8. Gate 10: User validation
      9. Gate 11: Activation guide
---

# Multi-Tenant Development Cycle

<cannot_skip>

## CRITICAL: This Skill ORCHESTRATES. Agents IMPLEMENT.

| Who | Responsibility |
|-----|----------------|
| **This Skill** | Detect stack, determine gates, pass context to agent, verify outputs, enforce order |
| **ring:backend-engineer-golang** | Load multi-tenant.md via WebFetch, implement following the standards |
| **6 reviewers** | Review at Gate 9 |

**CANNOT change scope:** the skill defines WHAT to implement. The agent implements HOW.

**FORBIDDEN: Orchestrator MUST NOT use Edit, Write, or Bash tools to modify source code files.**
All code changes MUST go through `Task(subagent_type="ring:backend-engineer-golang")`.
The orchestrator only verifies outputs (grep, go build, go test) — MUST NOT write implementation code.

**MANDATORY: TDD for all implementation gates (Gates 2-6).** MUST follow RED → GREEN → REFACTOR: write a failing test first, then implement to make it pass, then refactor for clarity/performance. MUST include in every dispatch: "Follow TDD: write failing test (RED), implement to make it pass (GREEN), then refactor for clarity/performance (REFACTOR)."

</cannot_skip>

---

## Multi-Tenant Architecture

Multi-tenant isolation is 100% based on `tenantId` from JWT → tenant-manager middleware → database-per-tenant. Connection managers (`postgres.Manager`, `mongo.Manager`, `rabbitmq.Manager`) resolve tenant-specific credentials via the Tenant Manager API. `organization_id` is NOT part of multi-tenant.

**Standards reference:** All code examples and implementation patterns are in [multi-tenant.md](../../docs/standards/golang/multi-tenant.md). MUST load via WebFetch before implementing any gate.

**WebFetch URL:** `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md`

### MANDATORY: Agent Instruction (include in EVERY gate dispatch)

MUST include these instructions in every dispatch to `ring:backend-engineer-golang`:

> **STANDARDS: WebFetch `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` and follow the sections referenced below. All code examples, patterns, and implementation details are in that document. Use them as-is.**
>
> **TDD: For implementation gates (2-6), follow TDD methodology — write a failing test first (RED), then implement to make it pass (GREEN). MUST have test coverage for every change.**

---

## Pressure Resistance

| User Says | This Is | Response |
|-----------|---------|----------|
| "Skip the lib-commons upgrade" | QUALITY_BYPASS | "CANNOT proceed without lib-commons v3. Tenant-manager sub-packages do not exist in v2." |
| "Just do the happy path, skip backward compat" | SCOPE_REDUCTION | "Backward compatibility is NON-NEGOTIABLE. Single-tenant deployments depend on it." |
| "organization_id is our tenant identifier" | AUTHORITY_OVERRIDE | "STOP. organization_id is NOT multi-tenant. tenantId from JWT is the only mechanism." |
| "Skip code review, we tested it" | QUALITY_BYPASS | "MANDATORY: 6 reviewers. One security mistake = cross-tenant data leak." |
| "We don't need RabbitMQ multi-tenant" | SCOPE_REDUCTION | "MUST execute Gate 6 if RabbitMQ was detected. CANNOT skip detected stack." |
| "I'll make a quick edit directly" | CODE_BYPASS | "FORBIDDEN: All code changes go through ring:backend-engineer-golang. Dispatch the agent." |
| "It's just one line, no need for an agent" | CODE_BYPASS | "FORBIDDEN: Even single-line changes MUST be dispatched. Agent ensures standards compliance." |
| "Agent is slow, I'll edit faster" | CODE_BYPASS | "FORBIDDEN: Speed is not a justification. Agent applies TDD and standards checks." |

---

## Gate Overview

| Gate | Name | Condition | Agent |
|------|------|-----------|-------|
| 0 | Stack Detection | Always | Orchestrator |
| 1 | Codebase Analysis (multi-tenant focus) | Always | ring:codebase-explorer |
| 1.5 | Implementation Preview (visual report) | Always | Orchestrator (ring:visual-explainer) |
| 2 | lib-commons v3 + lib-auth v2 Upgrade | Skip if already v3 AND lib-auth v2 | ring:backend-engineer-golang |
| 3 | Multi-Tenant Configuration | Skip if already configured | ring:backend-engineer-golang |
| 4 | Tenant Middleware (TenantMiddleware or MultiPoolMiddleware) | Always (core) | ring:backend-engineer-golang |
| 5 | Repository Adaptation | Per detected DB/storage | ring:backend-engineer-golang |
| 6 | RabbitMQ Multi-Tenant | Skip if no RabbitMQ | ring:backend-engineer-golang |
| 7 | Metrics & Backward Compat | Always | ring:backend-engineer-golang |
| 8 | Tests | Always | ring:backend-engineer-golang |
| 9 | Code Review | Always | 6 parallel reviewers |
| 10 | User Validation | Always | User |
| 11 | Activation Guide | Always | Orchestrator |

MUST execute gates sequentially. CANNOT skip or reorder.

---

## Gate 0: Stack Detection

**Orchestrator executes directly. No agent dispatch.**

```text
DETECT (run in parallel):

1. lib-commons version:  grep "lib-commons" go.mod
1b. lib-auth v2:         grep "lib-auth" go.mod
2. PostgreSQL:           grep -rn "postgresql\|pgx\|squirrel" internal/ go.mod
3. MongoDB:              grep -rn "mongodb\|mongo" internal/ go.mod
4. Redis:                grep -rn "redis\|valkey" internal/ go.mod
5. RabbitMQ:             grep -rn "rabbitmq\|amqp" internal/ go.mod
6. S3/Object Storage:    grep -rn "s3\|ObjectStorage\|PutObject\|GetObject\|Upload.*storage\|Download.*storage" internal/ pkg/ go.mod
7. Existing multi-tenant:
   - Config:     grep -rn "MULTI_TENANT_ENABLED" internal/
   - Middleware: grep -rn "tenant-manager/middleware\|WithTenantDB\|MultiPoolMiddleware" internal/
   - Context:    grep -rn "tenant-manager/core\|GetMongoForTenant\|GetPostgresForTenant" internal/
   - S3 keys:    grep -rn "tenant-manager/s3\|GetObjectStorageKeyForTenant" internal/
   - RMQ:        grep -rn "X-Tenant-ID" internal/
```

MUST confirm: user explicitly approves detection results before proceeding.

---

## Gate 1: Codebase Analysis (Multi-Tenant Focus)

**Always executes. This gate builds the implementation roadmap for all subsequent gates.**

**Dispatch `ring:codebase-explorer` with multi-tenant-focused context:**

> TASK: Analyze this codebase exclusively under the multi-tenant perspective.
> DETECTED STACK: {databases and messaging from Gate 0}
>
> CRITICAL: Multi-tenant is ONLY about tenantId from JWT → tenant-manager middleware → database-per-tenant.
> IGNORE organization_id completely — it is NOT multi-tenant. A tenant can have multiple organizations inside its database. organization_id is a domain entity, not a tenant identifier.
>
> FOCUS AREAS (explore ONLY these — ignore everything else):
>
> 1. **Service name, modules, and components**: What is the service called? (Look for `const ApplicationName`.) How many components/modules does it have? Each module needs a constant (e.g., `const ModuleManager = "manager"`). Identify: service name (ApplicationName), module names per component, and whether constants exist or need to be created. Hierarchy: Service → Module → Resource.
> 2. **Bootstrap/initialization**: Where does the service start? Where are database connections created? Where is the middleware chain registered? Identify the exact insertion point for TenantMiddleware.
> 3. **Database connections**: How do repositories get their DB connection today? Static field in struct? Constructor injection? Context? List EVERY repository file with file:line showing where the connection is obtained.
> 4. **Middleware chain**: What middleware exists and in what order? Where would TenantMiddleware fit (after auth, before handlers)?
> 5. **Config struct**: Where is the Config struct? What fields exist? Where is it loaded? Identify exact location for MULTI_TENANT_ENABLED vars.
> 6. **RabbitMQ** (if detected): Where are producers? Where are consumers? How are messages published? Where would X-Tenant-ID header be injected? Are producer and consumer in the SAME process or SEPARATE components? Is there already a config split? Are there dual constructors? Is there a RabbitMQManager pool? Does the service struct have both consumer types?
> 7. **Redis** (if detected): Where are Redis operations? Any Lua scripts? Where would GetKeyFromContext be needed?
> 8. **S3/Object Storage** (if detected): Where are Upload/Download/Delete operations? How are object keys constructed? List every file:line that builds an S3 key. What bucket env var is used?
> 9. **Existing multi-tenant code**: Any tenant-manager sub-package imports (`tenant-manager/core`, `tenant-manager/middleware`, `tenant-manager/postgres`, etc.)? TenantMiddleware or MultiPoolMiddleware? `core.GetPostgresForTenant`/`core.GetMongoForTenant`/`s3.GetObjectStorageKeyForTenant` calls? MULTI_TENANT_ENABLED config? (NOTE: organization_id is NOT related to multi-tenant — ignore it completely)
>
> OUTPUT FORMAT: Structured report with file:line references for every point above.
> DO NOT write code. Analysis only.

**The explorer produces a gap summary.** For the full checklist of required items, see [multi-tenant.md § Checklist](../../docs/standards/golang/multi-tenant.md).

**This report becomes the CONTEXT for all subsequent gates.**

<block_condition>
HARD GATE: MUST complete the analysis report before proceeding. All subsequent gates use this report to know exactly what to change.
</block_condition>

MUST ensure backward compatibility context: the analysis MUST identify how the service works today in single-tenant mode, so subsequent gates preserve this behavior when `MULTI_TENANT_ENABLED=false`.

---

## Gate 1.5: Implementation Preview (Visual Report)

**Always executes. This gate generates a visual HTML report showing exactly what will change before any code is written.**

**Uses the `ring:visual-explainer` skill to produce a self-contained HTML page.**

The report is built from Gate 0 (stack detection) and Gate 1 (codebase analysis). It shows the developer a complete preview of every change that will be made across all subsequent gates, with backward compatibility analysis.

**Orchestrator generates the report using `ring:visual-explainer` with this content:**

The HTML page MUST include these sections:

### 1. Current Architecture (Before)
- Mermaid diagram showing current request flow (how connections work today in single-tenant mode)
- Table of all files that will be modified, with current line counts
- How repositories get DB connections today (static field, constructor injection, etc.)

### 2. Target Architecture (After)
- Mermaid diagram showing the multi-tenant request flow (JWT → middleware → tenant pool → handler)
- Which middleware will be used: `TenantMiddleware` (single-module) or `MultiPoolMiddleware` (multi-module)
- How repositories will get DB connections (context-based: `core.GetPostgresForTenant(ctx)`)

### 3. Change Map (per gate)
Table with columns: Gate, File, Current Code, New Code, Lines Changed. One row per file that will be modified. Example:

| Gate | File | What Changes | Impact |
|------|------|-------------|--------|
| 2 | `go.mod` | lib-commons v2 → v3 + lib-auth v2, import paths | All files |
| 3 | `config.go` | Add 7 MULTI_TENANT_* env vars to Config struct | ~20 lines added |
| 4 | `config.go` | Add TenantMiddleware/MultiPoolMiddleware setup | ~30 lines added |
| 4 | `routes.go` | Register middleware in Fiber chain | ~5 lines added |
| 5 | `organization.postgresql.go` | `c.connection.GetDB()` → `core.GetModulePostgresForTenant(ctx, module)` | ~3 lines per method |
| 5 | `metadata.mongodb.go` | Static mongo → `core.GetMongoForTenant(ctx)` | ~2 lines per method |
| 5 | `consumer.redis.go` | Key prefixing with `valkey.GetKeyFromContext(ctx, key)` | ~1 line per operation |
| 5 | `storage.go` | S3 key prefixing with `s3.GetObjectStorageKeyForTenant(ctx, key)` | ~1 line per operation |
| 6 | `producer.rabbitmq.go` | Dual constructor (single-tenant + multi-tenant) | ~20 lines added |
| 6 | `rabbitmq.server.go` | MultiTenantConsumer setup with lazy mode | ~40 lines added |
| 7 | `config.go` | Backward compat validation | ~10 lines added |

**MANDATORY: Below the summary table, show per-file code diff panels for every file that will be modified.**

For each file in the change map, generate a before/after diff panel showing:
- **Before:** The exact current code from the codebase (sourced from the Gate 1 analysis)
- **After:** The exact code that will be written (following multi-tenant.md patterns)
- Use syntax highlighting and line numbers (read `default/skills/visual-explainer/templates/code-diff.html` for patterns)

Example diff panel for a repository file:

```go
// BEFORE: organization.postgresql.go
func (r *OrganizationPostgreSQLRepository) Create(ctx context.Context, org *Organization) error {
    db := r.connection.GetDB()
    result := db.Model(&OrganizationPostgreSQLModel{}).Create(toModel(org))
    // ...
}

// AFTER: organization.postgresql.go
func (r *OrganizationPostgreSQLRepository) Create(ctx context.Context, org *Organization) error {
    db, err := core.GetModulePostgresForTenant(ctx, "organization")
    if err != nil {
        return fmt.Errorf("getting tenant db for organization: %w", err)
    }
    result := db.Model(&OrganizationPostgreSQLModel{}).Create(toModel(org))
    // ...
}
```

The developer MUST be able to see the exact code that will be implemented to approve it. High-level descriptions alone are not sufficient for approval.

**When many files have identical changes** (e.g., 10+ repository files all changing `r.connection.GetDB()` to `core.GetPostgresForTenant(ctx)`): show one representative diff panel, then list the remaining files with "Same pattern applied to: [file list]."

### 4. Backward Compatibility Analysis

**MANDATORY: Show complete conditional initialization code, not just the if/else skeleton.**

For each component (PostgreSQL, MongoDB, Redis, RabbitMQ, S3), show:
1. **Current initialization code** (exact lines from codebase, sourced from Gate 1)
2. **New initialization code** with the `if cfg.MultiTenantEnabled` branch
3. **Explicit callout:** "When MULTI_TENANT_ENABLED=false, execution follows the ELSE branch which is IDENTICAL to current behavior"

Side-by-side comparison showing:
- **MULTI_TENANT_ENABLED=false (default):** Exact current behavior preserved. No JWT parsing, no Tenant Manager calls, no pool routing. Middleware calls `c.Next()` immediately.
- **MULTI_TENANT_ENABLED=true:** New behavior with tenant isolation.

Code diff showing the complete conditional initialization (not skeleton):
```go
if cfg.MultiTenantEnabled && cfg.MultiTenantURL != "" {
    // Multi-tenant path (NEW)
    tmClient := client.NewClient(cfg.MultiTenantURL, logger, clientOpts...)
    pgManager := postgres.NewManager(tmClient, logger)
    // ... show complete initialization
} else {
    // Single-tenant path (UNCHANGED — exactly how it works today)
    // Show the exact same constructor calls that exist in the current codebase
    logger.Info("Running in SINGLE-TENANT MODE")
}
```

Show the middleware bypass explicitly:
```go
// When MULTI_TENANT_ENABLED=false, TenantMiddleware is NOT registered.
// Requests flow directly to handlers without any JWT parsing or tenant resolution.
```

The developer MUST understand that:
- No new code paths execute in single-tenant mode
- The `else` branch preserves the exact current constructor calls
- No additional dependencies are loaded when disabled
- No performance impact when disabled (middleware calls c.Next() immediately)

### 5. New Dependencies
Table showing what gets added to go.mod and which sub-packages are imported:
- `tenant-manager/core` — types, errors, context helpers
- `tenant-manager/client` — Tenant Manager HTTP client
- `tenant-manager/middleware` — TenantMiddleware or MultiPoolMiddleware
- `tenant-manager/postgres` — PostgresManager (if PG detected)
- `tenant-manager/mongo` — MongoManager (if Mongo detected)
- etc.

### 6. Environment Variables
Table with the 7 MULTI_TENANT_* vars that will be added to Config struct.

### 7. Risk Assessment
Table with: Risk, Mitigation, Verification. Examples:
- Single-tenant regression → Backward compat gate (Gate 7) → `MULTI_TENANT_ENABLED=false go test ./...`
- Cross-tenant data leak → Context-based isolation → Tenant isolation integration tests (Gate 8)
- Startup performance → Lazy consumer mode → `consumer.Run(ctx)` returns in <1s

### 8. Retro Compatibility Guarantee

Explicit explanation of backward compatibility strategy:

**Method:** Feature flag with `MULTI_TENANT_ENABLED` environment variable (default: `false`).

**Guarantee:** When `MULTI_TENANT_ENABLED=false`:
- No tenant middleware is registered in the HTTP chain
- No JWT parsing or tenant resolution occurs
- All database connections use the original static constructors
- All Redis keys are unprefixed (original behavior)
- All S3 keys are unprefixed (original behavior)
- RabbitMQ connects directly at startup (original behavior)
- `go test ./...` passes with zero changes to existing tests

**Verification (Gate 7):** The agent MUST run `MULTI_TENANT_ENABLED=false go test ./...` and verify all existing tests pass unchanged.

**Output:** Save the HTML report to `docs/multi-tenant-preview.html` in the project root.

**Open in browser** for the developer to review.

<block_condition>
HARD GATE: Developer MUST explicitly approve the implementation preview before any code changes begin. This prevents wasted effort on misunderstood requirements or incorrect architectural decisions.
</block_condition>

**If the developer requests changes to the preview, regenerate the report and re-confirm.**

---

## Gate 2: lib-commons v3 + lib-auth v2 Upgrade

**SKIP IF:** already lib-commons v3 AND lib-auth v2.

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Upgrade lib-commons to v3 first, then update lib-auth to v2 (lib-auth v2 depends on lib-commons v3).
> For both libraries, fetch the latest tag (may be beta/rc in dev).
> Check latest tags: `git ls-remote --tags https://github.com/LerianStudio/lib-commons.git | tail -5` and `git ls-remote --tags https://github.com/LerianStudio/lib-auth.git | tail -5`
> Run in order:
> 1. `go get github.com/LerianStudio/lib-commons/v3@{latest-tag}`
> 2. `go get github.com/LerianStudio/lib-auth/v2@{latest-tag}`
> Update go.mod and all import paths from v2 to v3 for lib-commons.
> Follow multi-tenant.md section "Required lib-commons Version".
> DO NOT implement multi-tenant code yet — only upgrade the dependencies.
> Verify: go build ./... and go test ./... MUST pass.

**Verification:** `grep "lib-commons/v3" go.mod` + `grep "lib-auth/v2" go.mod` + `go build ./...` + `go test ./...`

<block_condition>
HARD GATE: MUST pass build and tests before proceeding.
</block_condition>

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

> TASK: Implement tenant middleware using lib-commons/v3 tenant-manager sub-packages.
> DETECTED DATABASES: {postgresql: Y/N, mongodb: Y/N} (from Gate 0)
> SERVICE ARCHITECTURE: {single-module OR multi-module} (from Gate 1)
> CONTEXT FROM GATE 1: {Bootstrap location, middleware chain insertion point, service init from analysis report}
>
> **For single-module services:** Follow multi-tenant.md § "Generic TenantMiddleware (Standard Pattern)" for imports, constructor, and options.
> **For multi-module services:** Follow multi-tenant.md § "Multi-module middleware (MultiPoolMiddleware)" for WithRoute/WithDefaultRoute pattern.
> **For sub-package import aliases:** See multi-tenant.md § sub-package import table.
>
> Follow multi-tenant.md § "JWT Tenant Extraction" for tenantId claim handling.
> Follow multi-tenant.md § "Conditional Initialization" for the bootstrap pattern.
>
> MUST define constants for service name and module names — never pass raw strings.
> Create connection managers ONLY for detected databases.
> Public endpoints (/health, /version, /swagger) MUST bypass tenant middleware.
> When MULTI_TENANT_ENABLED=false, middleware calls c.Next() immediately (single-tenant passthrough).
>
> **IF RabbitMQ DETECTED:** Follow multi-tenant.md § "ConsumerTrigger interface" for the wiring pattern.

**Verification:** `grep "tmmiddleware.NewTenantMiddleware\|tmmiddleware.NewMultiPoolMiddleware" internal/bootstrap/` + `go build ./...`

<block_condition>
HARD GATE: CANNOT proceed without TenantMiddleware.
</block_condition>

---

## Gate 5: Repository Adaptation

**SKIP IF:** repositories already use context-based connections.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Adapt all repository implementations to get database connections from tenant context instead of static connections. Also adapt S3/object storage operations to prefix keys with tenant ID.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, s3: Y/N} (from Gate 0)
> CONTEXT FROM GATE 1: {List of ALL repository files and storage operations with file:line from analysis report}
>
> Follow multi-tenant.md sections:
> - "Database Connection in Repositories" (PostgreSQL)
> - "MongoDB Multi-Tenant Repository" (MongoDB)
> - "Redis Key Prefixing" and "Redis Key Prefixing for Lua Scripts" (Redis)
> - "S3/Object Storage Key Prefixing" (S3)
>
> MUST work in both modes: multi-tenant (prefixed keys / context connections) and single-tenant (unchanged keys / default connections).

**Verification:** grep for `core.GetPostgresForTenant` / `core.GetMongoForTenant` / `core.GetModulePostgresForTenant` (multi-module) / `valkey.GetKeyFromContext` / `s3.GetObjectStorageKeyForTenant` in `internal/` + `go build ./...`

---

## Gate 6: RabbitMQ Multi-Tenant

**SKIP IF:** no RabbitMQ detected.

**Dispatch `ring:backend-engineer-golang` with context from Gate 1 analysis:**

> TASK: Implement RabbitMQ multi-tenant patterns with lazy initialization.
> CONTEXT FROM GATE 1: {Producer and consumer file:line locations from analysis report}
> DETECTED ARCHITECTURE: {Are producer and consumer in the same process or separate components?}
>
> Follow multi-tenant.md sections:
> - "RabbitMQ Multi-Tenant Producer" for dual constructor and X-Tenant-ID header
> - "Multi-Tenant Message Queue Consumers (Lazy Mode)" for lazy initialization
> - "ConsumerTrigger Interface" for the trigger wiring
>
> Gate-specific constraints:
> 1. CONFIG SPLIT (MANDATORY): Branch on `cfg.MultiTenantEnabled` for both producer and consumer in bootstrap
> 2. MUST keep the existing single-tenant code path untouched
> 3. MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode
> 4. X-Tenant-ID goes in AMQP headers, NOT in message body

**Verification:** `grep "tmrabbitmq.Manager\|NewProducerMultiTenant\|EnsureConsumerStarted\|tmmiddleware.ConsumerTrigger" internal/` + `go build ./...`

<block_condition>
HARD GATE: MUST NOT connect directly to RabbitMQ at startup in multi-tenant mode.
</block_condition>

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

<block_condition>
HARD GATE: Backward compatibility MUST pass.
</block_condition>

---

## Gate 8: Tests

**Dispatch `ring:backend-engineer-golang` with context:**

> TASK: Write multi-tenant tests.
> DETECTED STACK: {postgresql: Y/N, mongodb: Y/N, redis: Y/N, s3: Y/N, rabbitmq: Y/N} (from Gate 0)
>
> Follow multi-tenant.md section "Testing Multi-Tenant Code" (all subsections).
>
> Required tests: unit tests with mock tenant context, tenant isolation tests (two tenants, data separation), error case tests (missing JWT, tenant not found), plus RabbitMQ, Redis, and S3 tests if detected.

**Verification:** `go test ./... -v -count=1` + `go test ./... -cover`

---

## Gate 9: Code Review

**Dispatch 6 parallel reviewers (same pattern as ring:requesting-code-review).**

MUST include this context in ALL 6 reviewer dispatches:

> **MULTI-TENANT REVIEW CONTEXT:**
> - Multi-tenant isolation is based on `tenantId` from JWT → tenant-manager middleware (TenantMiddleware or MultiPoolMiddleware) → database-per-tenant.
> - `organization_id` is NOT a tenant identifier. It is a business filter within the tenant's database. A single tenant can have multiple organizations. Do NOT flag organization_id as a multi-tenant issue.
> - Backward compatibility is required: when `MULTI_TENANT_ENABLED=false`, the service MUST work exactly as before (single-tenant mode, no tenant context needed).

| Reviewer | Focus |
|----------|-------|
| ring:code-reviewer | Architecture, lib-commons v3 usage, TenantMiddleware/MultiPoolMiddleware placement, sub-package usage |
| ring:business-logic-reviewer | Tenant context propagation via tenantId (NOT organization_id) |
| ring:security-reviewer | Cross-tenant DB isolation, JWT tenantId validation, no data leaks between tenant databases |
| ring:test-reviewer | Coverage, isolation tests between two tenants, backward compat tests |
| ring:nil-safety-reviewer | Nil risks in tenant context extraction from JWT and context getters |
| ring:consequences-reviewer | Impact on single-tenant paths, backward compat when MULTI_TENANT_ENABLED=false |

MUST pass all 6 reviewers. Critical findings → fix and re-review.

---

## Gate 10: User Validation

MUST approve: present checklist for explicit user approval.

```markdown
## Multi-Tenant Implementation Complete

- [ ] lib-commons v3
- [ ] MULTI_TENANT_ENABLED config
- [ ] Tenant middleware (TenantMiddleware or MultiPoolMiddleware for multi-module services)
- [ ] Repositories use context-based connections
- [ ] S3 keys prefixed with tenantId (if applicable)
- [ ] RabbitMQ X-Tenant-ID (if applicable)
- [ ] Backward compat (MULTI_TENANT_ENABLED=false works)
- [ ] Tests pass
- [ ] Code review passed
```

---

## Gate 11: Activation Guide

**MUST generate `docs/multi-tenant-guide.md` in the project root.** Direct, concise, no filler text.

The file is built from Gate 0 (stack) and Gate 1 (analysis). See [multi-tenant.md § Checklist](../../docs/standards/golang/multi-tenant.md) for the canonical env var list and requirements.

<!-- Template: values filled from Gate 0/1 results. Canonical source: multi-tenant.md -->

The guide MUST include:
1. **Components table**: Component name, Service const, Module const, Resources, what was adapted
2. **Environment variables**: the 7 MULTI_TENANT_* vars with required/default/description
3. **How to activate**: set envs + start alongside Tenant Manager
4. **How to verify**: check logs, test with JWT tenantId
5. **How to deactivate**: set MULTI_TENANT_ENABLED=false
6. **Common errors**: see [multi-tenant.md § Error Handling](../../docs/standards/golang/multi-tenant.md)

---

## State Persistence

Save to `docs/ring-dev-multi-tenant/current-cycle.json` for resume support:

```json
{
  "cycle": "multi-tenant",
  "stack": {"postgresql": false, "mongodb": true, "redis": true, "rabbitmq": true, "s3": true},
  "gates": {"0": "PASS", "1": "PASS", "1.5": "PASS", "2": "IN_PROGRESS", "3": "PENDING"},
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

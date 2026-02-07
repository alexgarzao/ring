---
name: production-readiness-audit
title: Production Readiness Audit
category: operations
tier: advanced
description: Comprehensive Ring-standards-aligned 37-dimension production readiness audit. Detects project stack, loads Ring standards via WebFetch, and runs in batches of explorers appending incrementally to a single report file. Categories - Structure (pagination, errors, routes, bootstrap, runtime, core deps, naming, domain modeling), Security (auth, SQL, validation, IDOR* and multi-tenant* conditional), Operations (telemetry, health, config, connections, logging), Quality (idempotency, docs, debt, unit-testing, fuzz-testing, property-testing, integration-testing, chaos-testing, dependencies, performance, concurrency, migrations, linting), Infrastructure (containers, hardening, cicd, async, makefile, license). Produces scored report with severity ratings and standards cross-reference.
allowed-tools: Task, Read, Glob, Grep, Write, TodoWrite, WebFetch
---

# Production Readiness Audit

A comprehensive, multi-agent audit system that evaluates codebase production readiness across **35 dimensions in 5 categories** (plus 2 conditional), aligned with **Ring development standards** as the source of truth. This skill detects the project stack, loads relevant standards via WebFetch, and runs explorer agents in batches, appending results incrementally to a single report file to prevent context bloat while maintaining thorough coverage.

## When This Skill Activates

Use this skill when:

- Preparing for production deployment
- Conducting periodic security/quality reviews
- Onboarding to understand codebase health
- Evaluating technical debt before major releases
- Validating compliance with Ring engineering standards
- Assessing a codebase's maturity level against Ring standards

## Audit Dimensions

### Category A: Code Structure & Patterns (8 dimensions)

| # | Dimension | Focus Area |
|---|-----------|------------|
| 1 | **Pagination Standards** | Cursor-based pagination (MANDATORY), limit validation, response structure |
| 2 | **Error Framework** | Domain errors, error codes convention, error handling, error propagation |
| 3 | **Route Organization** | Hexagonal structure, handler construction, route registration |
| 4 | **Bootstrap & Initialization** | Staged startup, cleanup handlers, graceful shutdown |
| 5 | **Runtime Safety** | Panic recovery, production mode handling |
| 28 | **Core Dependencies & Frameworks** | lib-commons v2, framework version minimums, no custom utility duplication |
| 29 | **Naming Conventions** | snake_case DB, camelCase JSON body, snake_case query params |
| 30 | **Domain Modeling** | ToEntity/FromEntity, always-valid constructors, private fields + getters |

### Category B: Security & Access Control (4 dimensions + 2 conditional)

| # | Dimension | Focus Area |
|---|-----------|------------|
| 6 | **Auth Protection** | Route protection, JWT validation, tenant extraction, Access Manager |
| 7 | **IDOR & Access Control** *(CONDITIONAL)* | Ownership verification, tenant isolation — only if MULTITENANT=true |
| 8 | **SQL Safety** | Parameterized queries, identifier escaping, injection prevention |
| 9 | **Input Validation** | Request body validation, query params, VO validation |
| 33 | **Multi-Tenant Patterns** *(CONDITIONAL)* | Pool Manager, JWT tenantId, context injection — only if MULTITENANT=true |

### Category C: Operational Readiness (5 dimensions)

| # | Dimension | Focus Area |
|---|-----------|------------|
| 11 | **Telemetry & Observability** | OpenTelemetry integration, tracing, metrics, lib-commons tracking |
| 12 | **Health Checks** | Liveness/readiness probes, dependency health, degraded status |
| 13 | **Configuration Management** | Env var validation, production constraints, secrets handling |
| 14 | **Connection Management** | DB/Redis pool settings, timeouts, replica support |
| 15 | **Logging & PII Safety** | Structured logging, sensitive data protection, log levels |

### Category D: Quality & Maintainability (13 dimensions)

| # | Dimension | Focus Area |
|---|-----------|------------|
| 16 | **Idempotency** | Idempotency keys, retry safety, duplicate prevention |
| 17 | **API Documentation** | Swaggo/OpenAPI annotations, response schemas, examples |
| 18 | **Technical Debt** | TODOs, FIXMEs, deprecated code, incomplete implementations |
| 19 | **Unit Testing** | Table-driven tests, t.Parallel, loop capture, assertions, GoMock, t.Setenv |
| 20 | **Dependency Management** | Pinned versions, CVE scanning, deprecated packages |
| 21 | **Performance Patterns** | N+1 queries, SELECT *, slice pre-allocation, batching |
| 22 | **Concurrency Safety** | Race conditions, goroutine leaks, mutex usage, worker pools |
| 23 | **Migration Safety** | Up/down pairs, CONCURRENTLY indexes, NOT NULL defaults |
| 31 | **Linting & Code Quality** | Import ordering (3 groups), magic numbers, golangci-lint config |
| 35 | **Fuzz Testing** | Native Go fuzz (Fuzz prefix), seed corpus, input bounding |
| 36 | **Property-Based Testing** | testing/quick.Check, domain invariants, TestProperty_ prefix |
| 37 | **Integration Testing** | Testcontainers, build tags, fixture/stub centralization, no t.Parallel |
| 38 | **Chaos Testing** | Toxiproxy, dual-gate (CHAOS=1), failure injection, recovery verification |

### Category E: Infrastructure & Hardening (5-6 dimensions)

| # | Dimension | Focus Area |
|---|-----------|------------|
| 24 | **Container Security** | Dockerfile best practices, non-root user, multi-stage, image pinning |
| 25 | **HTTP Hardening** | Security headers (X-Content-Type-Options, X-Frame-Options) per Ring standards |
| 26 | **CI/CD Pipeline** | Pipeline definitions, automated tests, security scanning |
| 27 | **Async Reliability** | DLQs, retry policies, consumer group usage, message durability |
| 32 | **Makefile & Dev Tooling** | 17+ required Makefile commands, dev workflow automation |
| 34 | **License Headers** | Copyright headers on all .go files |

## Execution Protocol

This skill runs **up to 37 explorer agents in 5 batches** (35 base + 2 conditional), writing results incrementally to a single report file. Before dispatch, it detects the project stack and loads Ring standards as the source of truth.

### Output File

All results are appended to: `docs/audits/production-readiness-{YYYY-MM-DD}-{hh:mm}.md`

### Batch Execution Schedule

| Batch | Agents | Category Focus |
|-------|--------|----------------|
| 1 | 1-9 | Structure (Pagination, Errors, Routes, Bootstrap, Runtime) + Security (Auth, IDOR*, SQL, Input) *conditional on MULTITENANT |
| 2 | 11-20 | Operations (Telemetry, Health, Config, Connections, Logging) + Quality (Idempotency, API Docs, Tech Debt, Unit Testing, Dependencies) |
| 3 | 21-30 | Quality (Performance, Concurrency, Migrations) + Infrastructure (Containers, Hardening, CI/CD, Async) + Structure (Core Deps, Naming, Domain Modeling) |
| 4 | 31-34 | Quality (Linting) + Infrastructure (Makefile, Multi-Tenant*, License) (* = conditional) |
| 5 | 35-38 + Summary | Quality (Fuzz Testing, Property Testing, Integration Testing, Chaos Testing) + Final Summary |

### Step 0: Stack Detection

Before running any explorers, detect the project stack to determine which Ring standards to load.

**Detection via Glob:**

| Check | Flag | Standards to Load |
|-------|------|-------------------|
| `**/go.mod` exists | GO=true | All golang/*.md modules |
| `**/package.json` + React/Next.js deps | FRONTEND=true | (future enrichment) |
| `**/package.json` + Express/Fastify deps | TS_BACKEND=true | (future enrichment) |
| `**/Dockerfile*` exists | DOCKER=true | devops.md |
| `**/Makefile` exists | MAKEFILE=true | devops.md → Makefile Standards |
| `**/LICENSE*` exists | LICENSE=true | For reference in dimension 34 |
| Multi-tenant indicators (`tenantId`, `tenant_id`, `pool_manager` in config/code) | MULTITENANT=true | multi-tenant.md |

**Detection Logic:**
```
Glob("**/go.mod") → if found: GO=true
Glob("**/package.json") → Read for React/Next.js → if found: FRONTEND=true
Glob("**/package.json") → Read for Express/Fastify → if found: TS_BACKEND=true
Glob("**/Dockerfile*") → if found: DOCKER=true
Glob("**/Makefile") → if found: MAKEFILE=true
Glob("**/LICENSE*") → if found: LICENSE=true
Grep("tenantId|tenant_id|pool.?[Mm]anager") → if found: MULTITENANT=true
```

**Stack determines which standards are loaded in Step 0.5 and which conditional dimensions are activated.**

### Step 0.5: Load Ring Standards

Based on detected stack, load Ring development standards via WebFetch from the canonical source of truth. Store fetched content for injection into explorer prompts.

**WebFetch URL Map** (from `dev-team/docs/standards/golang/index.md`):

If **GO=true**, WebFetch these and store content:

| Module | Variable | URL |
|--------|----------|-----|
| core.md | `standards_core` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/core.md` |
| bootstrap.md | `standards_bootstrap` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/bootstrap.md` |
| security.md | `standards_security` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/security.md` |
| domain.md | `standards_domain` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/domain.md` |
| api-patterns.md | `standards_api` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/api-patterns.md` |
| quality.md | `standards_quality` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/quality.md` |
| architecture.md | `standards_arch` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/architecture.md` |
| messaging.md | `standards_messaging` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/messaging.md` |
| domain-modeling.md | `standards_dm` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/domain-modeling.md` |
| idempotency.md | `standards_idempotency` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/idempotency.md` |
| testing-unit.md | `standards_testing_unit` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-unit.md` |
| testing-fuzz.md | `standards_testing_fuzz` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-fuzz.md` |
| testing-property.md | `standards_testing_property` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-property.md` |
| testing-integration.md | `standards_testing_integration` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-integration.md` |
| testing-chaos.md | `standards_testing_chaos` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-chaos.md` |

If **MULTITENANT=true**, also WebFetch:

| Module | Variable | URL |
|--------|----------|-----|
| multi-tenant.md | `standards_multitenant` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` |

**Always** WebFetch (stack-independent):

| Module | Variable | URL |
|--------|----------|-----|
| devops.md | `standards_devops` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/devops.md` |
| sre.md | `standards_sre` | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/sre.md` |

**Fallback:** If any WebFetch fails, note the failure in the audit report and proceed with existing generic patterns for that dimension. Do not abort the audit.

**Standards Injection Pattern:**
Each explorer prompt receives relevant standards content between `---BEGIN STANDARDS---` and `---END STANDARDS---` markers. The explorer uses these as the authoritative reference for its audit dimension.

### Step 1: Initialize Report File

```markdown
Write to docs/audits/production-readiness-{YYYY-MM-DD}-{hh:mm}.md:

# Production Readiness Audit Report

**Date:** {YYYY-MM-DD}
**Hour:** {hh:mm}
**Codebase:** {project-name}
**Auditor:** Claude Code (Production Readiness Skill v3.0)
**Status:** In Progress...

## Audit Configuration

| Property | Value |
|----------|-------|
| **Detected Stack** | {Go / TypeScript / Frontend / Mixed} |
| **Standards Loaded** | {list of loaded standards files} |
| **Active Dimensions** | {35 if single-tenant, 37 if multi-tenant} |
| **Max Possible Score** | {350 if single-tenant, 370 if multi-tenant} |
| **Conditional: Multi-Tenant** | {Active / Inactive} |

**⛔ SCORING RULE:** When **Multi-Tenant = Inactive**, dimensions 7 (IDOR) and 33 (Multi-Tenant) are **completely excluded** from scoring. They do NOT count as 0/10 - they simply don't exist for single-tenant projects. Max score is 350, not 370.

---
```

### Step 2: Execute Batch 1 (Agents 1-10)

Launch 10 explorers in parallel:
```
Task(subagent_type="Explore", prompt="<Agent 1: Pagination Standards>")
Task(subagent_type="Explore", prompt="<Agent 2: Error Framework>")
Task(subagent_type="Explore", prompt="<Agent 3: Route Organization>")
Task(subagent_type="Explore", prompt="<Agent 4: Bootstrap & Init>")
Task(subagent_type="Explore", prompt="<Agent 5: Runtime Safety>")
Task(subagent_type="Explore", prompt="<Agent 6: Auth Protection>")
# Only if MULTITENANT=true:
Task(subagent_type="Explore", prompt="<Agent 7: IDOR Protection>")  # CONDITIONAL
Task(subagent_type="Explore", prompt="<Agent 8: SQL Safety>")
Task(subagent_type="Explore", prompt="<Agent 9: Input Validation>")
```

**After completion:** Append results to the report file.

### Step 3: Execute Batch 2 (Agents 11-20)

Launch 10 explorers in parallel:
```
Task(subagent_type="Explore", prompt="<Agent 11: Telemetry & Observability>")
Task(subagent_type="Explore", prompt="<Agent 12: Health Checks>")
Task(subagent_type="Explore", prompt="<Agent 13: Configuration Management>")
Task(subagent_type="Explore", prompt="<Agent 14: Connection Management>")
Task(subagent_type="Explore", prompt="<Agent 15: Logging & PII Safety>")
Task(subagent_type="Explore", prompt="<Agent 16: Idempotency>")
Task(subagent_type="Explore", prompt="<Agent 17: API Documentation>")
Task(subagent_type="Explore", prompt="<Agent 18: Technical Debt>")
Task(subagent_type="Explore", prompt="<Agent 19: Unit Testing>")
Task(subagent_type="Explore", prompt="<Agent 20: Dependency Management>")
```

**After completion:** Append results to the report file.

### Step 4: Execute Batch 3 (Agents 21-30)

Launch 10 explorers in parallel:
```
Task(subagent_type="Explore", prompt="<Agent 21: Performance Patterns>")
Task(subagent_type="Explore", prompt="<Agent 22: Concurrency Safety>")
Task(subagent_type="Explore", prompt="<Agent 23: Migration Safety>")
Task(subagent_type="Explore", prompt="<Agent 24: Container Security>")
Task(subagent_type="Explore", prompt="<Agent 25: HTTP Hardening>")
Task(subagent_type="Explore", prompt="<Agent 26: CI/CD Pipeline>")
Task(subagent_type="Explore", prompt="<Agent 27: Async Reliability>")
Task(subagent_type="Explore", prompt="<Agent 28: Core Dependencies & Frameworks>")
Task(subagent_type="Explore", prompt="<Agent 29: Naming Conventions>")
Task(subagent_type="Explore", prompt="<Agent 30: Domain Modeling>")
```

**After completion:** Append results to the report file.

### Step 5: Execute Batch 4 (Agents 31-34 + Summary)

Launch conditional and remaining explorers:
```
Task(subagent_type="Explore", prompt="<Agent 31: Linting & Code Quality>")
Task(subagent_type="Explore", prompt="<Agent 32: Makefile & Dev Tooling>")
# CONDITIONAL: Only if MULTITENANT=true
Task(subagent_type="Explore", prompt="<Agent 33: Multi-Tenant Patterns>")
Task(subagent_type="Explore", prompt="<Agent 34: License Headers>")
```

**After completion:** Append results to the report file.

### Step 6: Execute Batch 5 (Agents 35-38 - Advanced Testing)

Launch 4 testing auditors in parallel:
```
Task(subagent_type="Explore", prompt="<Agent 35: Fuzz Testing>")
Task(subagent_type="Explore", prompt="<Agent 36: Property-Based Testing>")
Task(subagent_type="Explore", prompt="<Agent 37: Integration Testing>")
Task(subagent_type="Explore", prompt="<Agent 38: Chaos Testing>")
```

**After completion:** Append results to the report file.

### Step 7: Finalize Report

1. Read the complete report file
2. Calculate scores for each dimension
3. Generate Executive Summary with totals
4. Prepend Executive Summary to the report
5. Add remediation priorities
6. Add Standards Compliance Cross-Reference table
7. Present verbal summary to user

---

## Explorer Agent Prompts

### Agent 1: Pagination Standards Auditor

```prompt
Audit pagination implementation across the codebase for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Pagination Patterns" section from api-patterns.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/pagination*.go`, `**/handlers.go`, `**/dto.go`
- Keywords: `limit`, `offset`, `cursor`, `NextCursor`, `PrevCursor`, `HasMore`
- Standards-specific: `CursorPagination`, `PaginationResponse`, `maxLimit`

**Reference Implementation (GOOD):**
```go
// Cursor-based pagination with proper validation (camelCase JSON)
type CursorResponse struct {
    NextCursor string `json:"nextCursor,omitempty"`
    PrevCursor string `json:"prevCursor,omitempty"`
    Limit      int    `json:"limit"`
    HasMore    bool   `json:"hasMore"`
}

// Limit validation with ceiling
if limit > maxLimit {
    limit = maxLimit // Auto-cap, don't error
}
if limit < 1 {
    return ErrLimitMustBePositive
}
```

**Check Against Ring Standards For:**
1. HARD GATE: Consistent pagination response structure matching Ring standards across all list endpoints
2. HARD GATE: Maximum limit enforcement (typically 100-200) per api-patterns.md
3. HARD GATE: Cursor-based pagination for all list endpoints. FORBIDDEN: offset pagination
4. MUST: Proper error handling for invalid pagination params
5. MUST: Default values when params missing
6. MUST: Response field names match Ring API conventions (camelCase JSON)

**Severity Ratings:**
- CRITICAL: No limit validation (allows unlimited queries)
- CRITICAL: HARD GATE violation per Ring standards — pagination response structure missing entirely
- CRITICAL: Using offset pagination instead of cursor-based (HARD GATE violation)
- HIGH: Inconsistent pagination structures across endpoints
- HIGH: Missing cursor fields (nextCursor, prevCursor, hasMore)
- MEDIUM: Cursor implementation incomplete (missing prevCursor for bidirectional navigation)
- LOW: Missing pagination metadata (total count, page info)

**Output Format:**
```
## Pagination Audit Findings

### Summary
- Total list endpoints: X
- Using cursor pagination: Y (REQUIRED: should equal X)
- Using offset pagination: Z (CRITICAL: should be 0)
- Missing limit validation: N

### Critical Issues
[file:line] - Description

### Recommendations
1. Migrate all offset pagination to cursor-based
2. ...
```
```

### Agent 2: Error Framework Auditor

```prompt
Audit error handling framework usage for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Error Codes Convention" and "Error Handling" sections from domain.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/assert*.go`, `**/error*.go`, `**/handlers.go`
- Keywords: `assert.New`, `AssertionError`, `ErrRepo`, `errors.Is`, `errors.As`
- Also search: `panic(`, `log.Fatal`
- Standards-specific: `ErrCode`, `DomainError`, `ErrorResponse`

**Reference Implementation (GOOD):**
```go
// Using pkg/assert for validation
asserter := assert.New(ctx, logger, "module", "operation")
if err := asserter.NotNil(ctx, config, "config required"); err != nil {
    return fmt.Errorf("validation: %w", err)
}

// Domain error types
var (
    ErrNotFound        = errors.New("resource not found")
    ErrInvalidInput    = errors.New("invalid input")
)

// Error mapping in handlers
if errors.Is(err, domain.ErrNotFound) {
    return httputil.NotFoundError(c, span, logger, "resource not found", err)
}
```

**Reference Implementation (BAD):**
```go
// Direct panic in production code
if config == nil {
    panic("config is nil")  // BAD: Use assert or return error
}

// Swallowing errors
result, _ := doSomething()  // BAD: Ignoring error

// Generic error messages
return errors.New("error")  // BAD: Not descriptive
```

**Check Against Ring Standards For:**
1. (HARD GATE) pkg/assert used instead of panic for validation per Ring standards
2. (HARD GATE) Named error variables (sentinel errors) per module following Ring error codes convention
3. (HARD GATE) No panic() in non-test production code
4. Proper error wrapping with %w
5. errors.Is/errors.As for error matching
6. No swallowed errors (_, err := ignored)
7. HTTP error responses follow Ring ErrorResponse structure from domain.md

**Severity Ratings:**
- CRITICAL: panic() in production code paths (HARD GATE violation per Ring standards)
- CRITICAL: Swallowed errors in critical paths
- HIGH: Generic error messages without context
- HIGH: Error response format does not match Ring standards
- MEDIUM: Inconsistent error types across modules
- LOW: Missing error wrapping context

**Output Format:**
```
## Error Framework Audit Findings

### Summary
- Modules using pkg/assert: X
- Panic calls in production: Y
- Swallowed errors: Z

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 3: Route Organization Auditor

```prompt
Audit route organization and handler structure for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Architecture Patterns" and "Directory Structure" sections from architecture.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/routes.go`, `**/handlers.go`, `internal/**/adapters/http/*.go`
- Keywords: `RegisterRoutes`, `protected(`, `fiber.Router`, `NewHandler`
- Standards-specific: `internal/{module}/adapters/`, `hexagonal`, `ports`

**Reference Implementation (GOOD):**
```go
// Centralized route registration
func RegisterRoutes(protected func(resource, action string) fiber.Router, handler *Handler) error {
    if handler == nil {
        return errors.New("handler is nil")
    }
    protected("resource", "create").Post("/v1/resources", handler.Create)
    protected("resource", "read").Get("/v1/resources", handler.List)
    protected("resource", "read").Get("/v1/resources/:id", handler.Get)
    return nil
}

// Handler constructor with validation
func NewHandler(deps ...interface{}) (*Handler, error) {
    if dep == nil {
        return nil, ErrNilDependency
    }
    return &Handler{...}, nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Hexagonal structure: `internal/{module}/adapters/http/` per architecture.md
2. (HARD GATE) Centralized route registration per module
3. Handler constructors validate all dependencies
4. Consistent URL patterns (v1, kebab-case, plural resources) per Ring conventions
5. All routes use protected() wrapper (no public endpoints without explicit exemption)
6. Clear separation: routes.go vs handlers.go per Ring directory structure

**Severity Ratings:**
- CRITICAL: Unprotected routes (missing auth middleware)
- CRITICAL: HARD GATE violation — project does not follow hexagonal architecture per Ring standards
- HIGH: Scattered route definitions
- MEDIUM: Handler accepts nil dependencies
- LOW: Inconsistent URL naming conventions

**Output Format:**
```
## Route Organization Audit Findings

### Summary
- Modules following hexagonal: X/Y
- Routes with protection: X/Y
- Handlers validating deps: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 4: Bootstrap & Initialization Auditor

```prompt
Audit application bootstrap and initialization for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Bootstrap" section from bootstrap.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/main.go`, `**/init.go`, `**/bootstrap/*.go`
- Keywords: `InitServers`, `startupSucceeded`, `defer`, `cleanup`, `graceful`
- Standards-specific: `NewServiceBootstrap`, `staged initialization`

**Reference Implementation (GOOD):**
```go
// Staged initialization with cleanup
func InitServers(opts *Options) (*Service, error) {
    startupSucceeded := false
    defer func() {
        if !startupSucceeded {
            cleanupConnections(...)  // Only cleanup on failure
        }
    }()

    // 1. Load config
    cfg, err := loadConfig()
    if err != nil {
        return nil, fmt.Errorf("config: %w", err)
    }

    // 2. Initialize logger
    logger := initLogger(cfg)

    // 3. Initialize telemetry
    telemetry := initTelemetry(cfg, logger)

    // 4. Connect infrastructure (DB, Redis, MQ)
    db, err := connectDB(cfg)
    if err != nil {
        return nil, fmt.Errorf("database: %w", err)
    }

    // 5. Initialize modules in dependency order
    ...

    startupSucceeded = true
    return &Service{...}, nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Staged initialization order per bootstrap.md (config -> logger -> telemetry -> infra)
2. (HARD GATE) Cleanup handlers for failed startup
3. (HARD GATE) Graceful shutdown support
4. Module initialization in dependency order per Ring bootstrap pattern
5. Error propagation (not just logging and continuing)
6. Production vs development mode handling

**Severity Ratings:**
- CRITICAL: No graceful shutdown (HARD GATE violation per Ring standards)
- CRITICAL: HARD GATE violation — bootstrap does not follow Ring staged initialization pattern
- HIGH: Resources not cleaned up on startup failure
- HIGH: Errors logged but not returned
- MEDIUM: Initialization order issues
- LOW: Missing development mode toggles

**Output Format:**
```
## Bootstrap Audit Findings

### Summary
- Graceful shutdown: Yes/No
- Cleanup on failure: Yes/No
- Staged initialization: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 5: Runtime Safety Auditor

```prompt
Audit pkg/runtime usage and panic handling for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns:**
- Files: `**/runtime/*.go`, `**/recover*.go`, `**/*.go`
- Keywords: `RecoverAndLog`, `RecoverWithPolicy`, `InitPanicMetrics`, `SetProductionMode`
- Also search: `panic(`, `recover()` (manual usage)

**Reference Implementation (GOOD):**
```go
// Bootstrap initialization
runtime.InitPanicMetrics(telemetry.MetricsFactory)
if cfg.EnvName == "production" {
    runtime.SetProductionMode(true)
}

// In HTTP handlers
defer runtime.RecoverAndLogWithContext(ctx, logger, "module", "handler_name")

// In worker goroutines
defer runtime.RecoverWithPolicyAndContext(ctx, logger, "module", "worker", runtime.CrashProcess)

// In background jobs (should retry, not crash)
defer runtime.RecoverWithPolicyAndContext(ctx, logger, "module", "job", runtime.LogAndContinue)
```

**Check For:**
1. pkg/runtime initialized at startup
2. Production mode set based on environment
3. All goroutines have panic recovery
4. Appropriate recovery policies per context
5. Panic metrics enabled for alerting
6. No raw recover() without pkg/runtime

**Severity Ratings:**
- CRITICAL: Goroutines without panic recovery
- HIGH: Missing production mode setting
- HIGH: Raw recover() without proper handling
- MEDIUM: Inconsistent recovery policies
- LOW: Missing panic metrics

**Output Format:**
```
## Runtime Safety Audit Findings

### Summary
- Runtime initialized: Yes/No
- Handlers with recovery: X/Y
- Goroutines with recovery: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 6: Auth Protection Auditor

```prompt
Audit authentication and authorization implementation for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Access Manager Integration" section from security.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/auth/*.go`, `**/middleware*.go`, `**/routes.go`
- Keywords: `Authorize`, `protected`, `JWT`, `tenant`, `ExtractToken`
- Standards-specific: `AccessManager`, `lib-auth`, `ProtectedGroup`

**Reference Implementation (GOOD):**
```go
// Protected route group
protected := func(resource, action string) fiber.Router {
    return auth.ProtectedGroup(api, authClient, tenantExtractor, resource, action)
}

// All routes use protected
protected("contexts", "create").Post("/v1/config/contexts", handler.Create)

// JWT validation
func parseTokenClaims(tokenString string, secret []byte) (jwt.MapClaims, error) {
    parser := jwt.NewParser(jwt.WithValidMethods(validSigningMethods))
    token, err := parser.ParseWithClaims(...)
    if err != nil || !token.Valid {
        return nil, ErrInvalidToken
    }
    // Check expiration
    if exp, ok := claims["exp"].(float64); ok {
        if time.Now().Unix() > int64(exp) {
            return nil, ErrTokenExpired
        }
    }
    return claims, nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All routes protected via Access Manager integration per security.md
2. (HARD GATE) lib-auth used for JWT validation (not custom JWT parsing)
3. Resource/action authorization granularity per Ring access control model
4. Token expiration enforcement
5. Tenant extraction from JWT claims
6. Auth bypass for health/ready endpoints only

**Severity Ratings:**
- CRITICAL: Unprotected data endpoints (HARD GATE violation per Ring standards)
- CRITICAL: JWT parsed but not validated
- CRITICAL: HARD GATE violation — not using lib-auth for access management
- HIGH: Missing token expiration check
- HIGH: Tenant claims not enforced
- MEDIUM: Overly broad permissions
- LOW: Missing fine-grained actions

**Output Format:**
```
## Auth Protection Audit Findings

### Summary
- Protected routes: X/Y
- JWT validation: Complete/Partial/Missing
- Tenant enforcement: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 7: IDOR & Access Control Auditor (CONDITIONAL)

**⚠️ CONDITIONAL: Only execute if MULTITENANT=true. Skip if MULTITENANT=false.**

```prompt
Audit IDOR (Insecure Direct Object Reference) protection for production readiness.

**Detected Stack:** {DETECTED_STACK}
**Condition:** MULTITENANT=true (skip if false)

**Search Patterns:**
- Files: `**/verifier*.go`, `**/handlers.go`, `**/context.go`
- Keywords: `VerifyOwnership`, `tenantID`, `contextID`, `ParseAndVerify`

**Reference Implementation (GOOD):**
```go
// 4-layer IDOR protection
func ParseAndVerifyContextParam(fiberCtx *fiber.Ctx, verifier ContextOwnershipVerifier) (uuid.UUID, uuid.UUID, error) {
    // 1. UUID format validation
    contextID, err := uuid.Parse(fiberCtx.Params("contextId"))
    if err != nil {
        return uuid.Nil, uuid.Nil, ErrInvalidID
    }

    // 2. Extract tenant from auth context (cannot be spoofed)
    tenantID := auth.GetTenantID(ctx)

    // 3. Database query filtered by tenant
    // 4. Post-query ownership verification
    if err := verifier.VerifyOwnership(ctx, tenantID, contextID); err != nil {
        return uuid.Nil, uuid.Nil, err
    }
    return contextID, tenantID, nil
}

// Verifier implementation
func (v *verifier) VerifyOwnership(ctx context.Context, tenantID, resourceID uuid.UUID) error {
    resource, err := v.query.Get(ctx, tenantID, resourceID)  // Query WITH tenant filter
    if errors.Is(err, sql.ErrNoRows) {
        return ErrNotFound
    }
    if resource.TenantID != tenantID {  // Double-check ownership
        return ErrNotOwned
    }
    return nil
}
```

**Reference Implementation (BAD):**
```go
// BAD: No ownership verification
func GetResource(c *fiber.Ctx) error {
    id := c.Params("id")
    resource, err := repo.FindByID(ctx, id)  // No tenant filter!
    return c.JSON(resource)
}
```

**Check For:**
1. All resource access verifies ownership
2. Tenant ID from JWT context (not request params)
3. Database queries include tenant filter
4. Post-query ownership double-check
5. UUID validation before database lookup
6. Consistent verifier pattern across modules

**Severity Ratings:**
- CRITICAL: Resource access without ownership check
- CRITICAL: Tenant ID from user input (not JWT)
- HIGH: Missing post-query ownership verification
- MEDIUM: Inconsistent verifier implementation
- LOW: Missing UUID format validation

**Output Format:**
```
## IDOR Protection Audit Findings

### Summary
- Modules with verifiers: X/Y
- Multi-tenant filtered queries: X/Y
- Post-query verification: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 8: SQL Safety Auditor

```prompt
Audit SQL injection prevention for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns:**
- Files: `**/*.postgresql.go`, `**/repository/*.go`, `**/*_repo.go`
- Keywords: `ExecContext`, `QueryContext`, `Exec(`, `Query(`, `$1`, `$2`
- Also search for: String concatenation in SQL: `"SELECT.*" +`, `fmt.Sprintf.*SELECT`

**Reference Implementation (GOOD):**
```go
// Parameterized queries
query := `INSERT INTO resources (id, name, tenant_id) VALUES ($1, $2, $3)`
_, err = tx.ExecContext(ctx, query, id, name, tenantID)

// SQL identifier escaping for dynamic schemas
func QuoteIdentifier(identifier string) string {
    return "\"" + strings.ReplaceAll(identifier, "\"", "\"\"") + "\""
}
schemaQuery := "SET LOCAL search_path TO " + QuoteIdentifier(tenantID)

// Query builder (Squirrel)
query := sq.Select("*").From("resources").Where(sq.Eq{"tenant_id": tenantID})
```

**Reference Implementation (BAD):**
```go
// BAD: String concatenation
query := "SELECT * FROM users WHERE name = '" + name + "'"

// BAD: fmt.Sprintf for values
query := fmt.Sprintf("SELECT * FROM users WHERE id = '%s'", id)

// BAD: Unescaped identifier
query := "SET search_path TO " + tenantID  // SQL injection via tenant
```

**Check For:**
1. All queries use parameterized statements ($1, $2, ...)
2. No string concatenation in SQL queries
3. Dynamic identifiers properly escaped (QuoteIdentifier)
4. Query builders used for complex WHERE clauses
5. No raw SQL with user input

**Severity Ratings:**
- CRITICAL: String concatenation with user input
- CRITICAL: fmt.Sprintf with user values
- HIGH: Unescaped dynamic identifiers
- MEDIUM: Raw SQL where builder would be safer
- LOW: Inconsistent query patterns

**Output Format:**
```
## SQL Safety Audit Findings

### Summary
- Parameterized queries: X/Y
- String concatenation risks: Z
- Identifier escaping: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 9: Input Validation Auditor

```prompt
Audit input validation patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Frameworks & Libraries" section from core.md — specifically go-playground/validator/v10 reference}
---END STANDARDS---

**Search Patterns:**
- Files: `**/dto.go`, `**/handlers.go`, `**/value_objects/*.go`
- Keywords: `validate:`, `BodyParser`, `IsValid()`, `Parse`, `required`
- Standards-specific: `validator/v10`, `go-playground/validator`

**Reference Implementation (GOOD):**
```go
// DTO with validation tags
type CreateRequest struct {
    Name   string `json:"name" validate:"required,min=1,max=255"`
    Type   string `json:"type" validate:"required,oneof=TYPE_A TYPE_B"`
    Amount int    `json:"amount" validate:"gte=0,lte=1000000"`
}

// Handler with body parsing error handling
func (h *Handler) Create(c *fiber.Ctx) error {
    var payload CreateRequest
    if err := c.BodyParser(&payload); err != nil {
        return badRequest(c, span, logger, "invalid request body", err)
    }
    // Validate struct
    if err := h.validator.Struct(payload); err != nil {
        return badRequest(c, span, logger, "validation failed", err)
    }
    ...
}

// Value object with domain validation
func (vo ValueObject) IsValid() bool {
    if vo.value == "" || len(vo.value) > maxLength {
        return false
    }
    return validPattern.MatchString(vo.value)
}
```

**Reference Implementation (BAD):**
```go
// BAD: No validation tags
type Request struct {
    Name string `json:"name"`  // No validation!
}

// BAD: Ignoring body parse error
payload := Request{}
c.BodyParser(&payload)  // Error ignored!

// BAD: No bounds checking
amount := c.QueryInt("amount")  // Could be negative or huge
```

**Check Against Ring Standards For:**
1. (HARD GATE) go-playground/validator/v10 used for struct validation per Ring core.md
2. (HARD GATE) All DTOs have validate: tags on required fields
3. BodyParser errors are handled (not ignored)
4. Query/path params validated before use
5. Numeric bounds enforced (min/max)
6. String length limits enforced
7. Enum values constrained (oneof=)
8. Value objects have IsValid() methods
9. File upload size/type validation

**Severity Ratings:**
- CRITICAL: BodyParser errors ignored
- CRITICAL: HARD GATE violation — not using go-playground/validator/v10 per Ring standards
- HIGH: No validation on user input DTOs
- HIGH: Unbounded numeric inputs
- MEDIUM: Missing string length limits
- LOW: Value objects without IsValid()

**Output Format:**
```
## Input Validation Audit Findings

### Summary
- DTOs with validation tags: X/Y
- BodyParser error handling: X/Y
- Value objects with IsValid: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 11: Telemetry & Observability Auditor

```prompt
Audit telemetry and observability implementation for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Observability" section from bootstrap.md and "OpenTelemetry with lib-commons" section from sre.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/observability*.go`, `**/telemetry*.go`, `**/handlers.go`
- Keywords: `NewTrackingFromContext`, `tracer.Start`, `span`, `logger`, `metrics`
- Standards-specific: `libCommons.NewTrackingFromContext`, `otel`, `OpenTelemetry`

**Reference Implementation (GOOD):**
```go
// Handler with proper telemetry
func (h *Handler) DoSomething(c *fiber.Ctx) error {
    ctx := c.UserContext()
    logger, tracer, headerID, _ := libCommons.NewTrackingFromContext(ctx)
    ctx, span := tracer.Start(ctx, "handler.DoSomething")
    defer span.End()

    span.SetAttributes(attribute.String("request_id", headerID))

    // On error
    span.RecordError(err)
    span.SetStatus(codes.Error, err.Error())
    logger.Errorf("operation failed: %v", err)

    return nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) lib-commons NewTrackingFromContext used for telemetry initialization per Ring standards
2. (HARD GATE) OpenTelemetry integration (not custom tracing) per sre.md
3. All handlers start spans with descriptive names
4. Errors recorded to spans before returning
5. Request IDs propagated through context
6. Metrics initialized at startup per bootstrap.md observability section
7. Structured logging with context (not fmt.Println)
8. Graceful telemetry shutdown

**Severity Ratings:**
- CRITICAL: No tracing in handlers (HARD GATE violation per Ring standards)
- CRITICAL: HARD GATE violation — not using lib-commons for telemetry
- HIGH: Errors not recorded to spans
- MEDIUM: Missing request ID propagation
- LOW: Inconsistent span naming conventions

**Output Format:**
```
## Telemetry Audit Findings

### Summary
- Handlers with tracing: X/Y
- Handlers with error recording: X/Y
- Metrics initialization: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 12: Health Checks Auditor

```prompt
Audit health check endpoints for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Health Checks" section from sre.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/fiber_server.go`, `**/health*.go`, `**/routes.go`
- Keywords: `/health`, `/ready`, `/live`, `healthHandler`, `readinessHandler`
- Standards-specific: `liveness`, `readiness`, `degraded`

**Reference Implementation (GOOD):**
```go
// Liveness probe - always returns healthy if process is running
func healthHandler(c *fiber.Ctx) error {
    return c.SendString("healthy")
}

// Readiness probe - checks all dependencies
func readinessHandler(deps *HealthDependencies) fiber.Handler {
    return func(c *fiber.Ctx) error {
        checks := fiber.Map{}
        status := fiber.StatusOK

        // Required dependency - fails readiness if down
        if err := deps.DB.Ping(c.Context()); err != nil {
            checks["database"] = "unhealthy"
            status = fiber.StatusServiceUnavailable
        } else {
            checks["database"] = "healthy"
        }

        // Optional dependency - reports degraded but doesn't fail
        if deps.Redis != nil {
            if err := deps.Redis.Ping(c.Context()).Err(); err != nil {
                checks["redis"] = "degraded"
            } else {
                checks["redis"] = "healthy"
            }
        }

        return c.Status(status).JSON(fiber.Map{
            "status": statusString(status),
            "checks": checks,
        })
    }
}

// Register without auth middleware
app.Get("/health", healthHandler)
app.Get("/ready", readinessHandler(deps))
```

**Check Against Ring Standards For:**
1. (HARD GATE) /health endpoint exists (liveness) per sre.md
2. (HARD GATE) /ready endpoint exists (readiness) per sre.md
3. Health endpoints bypass auth middleware
4. Database connectivity checked in readiness
5. Message queue connectivity checked
6. Optional deps don't fail readiness (just report degraded) per Ring health check pattern
7. Response includes individual check status
8. Appropriate HTTP status codes (200 vs 503)

**Severity Ratings:**
- CRITICAL: No health endpoints at all (HARD GATE violation per Ring standards)
- HIGH: No readiness probe (only liveness)
- HIGH: Health endpoints require auth
- MEDIUM: Missing dependency checks in readiness
- LOW: No degraded status for optional deps

**Output Format:**
```
## Health Checks Audit Findings

### Summary
- Liveness endpoint: Yes/No (/path)
- Readiness endpoint: Yes/No (/path)
- Dependencies checked: [list]

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 13: Configuration Management Auditor

```prompt
Audit configuration management for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Configuration" section from core.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/config.go`, `**/bootstrap/*.go`, `**/.env*`
- Keywords: `env:`, `envDefault:`, `Validate()`, `LoadConfig`, `production`
- Standards-specific: `envconfig`, `caarlos0/env`

**Reference Implementation (GOOD):**
```go
// Config with validation
type Config struct {
    EnvName    string `env:"ENV_NAME" envDefault:"development"`
    DBPassword string `env:"POSTGRES_PASSWORD"`
    AuthEnabled bool  `env:"AUTH_ENABLED" envDefault:"false"`
}

// Production validation
func (c *Config) Validate() error {
    if c.EnvName == "production" {
        // Require auth in production
        if !c.AuthEnabled {
            return errors.New("AUTH_ENABLED must be true in production")
        }
        // Require DB password in production
        if c.DBPassword == "" {
            return errors.New("POSTGRES_PASSWORD required in production")
        }
        // Require TLS for databases
        if c.PostgresSSLMode == "disable" {
            return errors.New("POSTGRES_SSLMODE cannot be disable in production")
        }
    }
    return nil
}

// Load with validation
func LoadConfig() (*Config, error) {
    cfg := &Config{}
    if err := envconfig.Process("", cfg); err != nil {
        return nil, fmt.Errorf("load env: %w", err)
    }
    if err := cfg.Validate(); err != nil {
        return nil, fmt.Errorf("validate: %w", err)
    }
    return cfg, nil
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All config loaded from env vars (not hardcoded) per Ring core.md configuration section
2. (HARD GATE) Production-specific validation exists
3. Sensible defaults for non-production
4. Auth required in production
5. TLS/SSL required in production
6. Default credentials rejected in production
7. Secrets not logged during startup
8. Config validation fails fast (at startup)

**Severity Ratings:**
- CRITICAL: Hardcoded secrets in code (HARD GATE violation per Ring standards)
- CRITICAL: No production validation
- HIGH: Auth can be disabled in production
- HIGH: TLS not enforced in production
- MEDIUM: Missing sensible defaults
- LOW: Config not validated at startup

**Output Format:**
```
## Configuration Management Audit Findings

### Summary
- Env vars used: X fields
- Production validation: Yes/No
- Constraints enforced: [list]

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 14: Connection Management Auditor

```prompt
Audit database and cache connection management for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Core Dependency: lib-commons" section from core.md — specifically connection packages}
---END STANDARDS---

**Search Patterns:**
- Files: `**/config.go`, `**/database*.go`, `**/redis*.go`, `**/postgres*.go`
- Keywords: `MaxOpenConns`, `MaxIdleConns`, `PoolSize`, `Timeout`, `SetConnMaxLifetime`
- Standards-specific: `lib-commons`, `mpostgres`, `mredis`, `mmongo`

**Reference Implementation (GOOD):**
```go
// Database pool configuration
type DBConfig struct {
    MaxOpenConnections int `env:"POSTGRES_MAX_OPEN_CONNS" envDefault:"25"`
    MaxIdleConnections int `env:"POSTGRES_MAX_IDLE_CONNS" envDefault:"5"`
    ConnMaxLifetime    int `env:"POSTGRES_CONN_MAX_LIFETIME_MINS" envDefault:"30"`
}

// Apply pool settings
func ConfigurePool(db *sql.DB, cfg *DBConfig) {
    db.SetMaxOpenConns(cfg.MaxOpenConnections)
    db.SetMaxIdleConns(cfg.MaxIdleConnections)
    db.SetConnMaxLifetime(time.Duration(cfg.ConnMaxLifetime) * time.Minute)
}

// Redis pool configuration
type RedisConfig struct {
    PoolSize       int `env:"REDIS_POOL_SIZE" envDefault:"10"`
    MinIdleConns   int `env:"REDIS_MIN_IDLE_CONNS" envDefault:"2"`
    ReadTimeoutMs  int `env:"REDIS_READ_TIMEOUT_MS" envDefault:"3000"`
    WriteTimeoutMs int `env:"REDIS_WRITE_TIMEOUT_MS" envDefault:"3000"`
    DialTimeoutMs  int `env:"REDIS_DIAL_TIMEOUT_MS" envDefault:"5000"`
}

// Primary + Replica support
type DatabaseConnections struct {
    Primary *sql.DB
    Replica *sql.DB  // Falls back to primary if not configured
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) lib-commons connection packages used (mpostgres, mredis, mmongo) per core.md
2. DB connection pool limits configured
3. Redis pool settings configured
4. Connection timeouts set (not infinite)
5. Connection max lifetime set (prevents stale connections)
6. Idle connection limits reasonable
7. Read replica support (for scaling reads)
8. Connection health checks (ping on checkout)
9. Graceful connection shutdown

**Severity Ratings:**
- CRITICAL: No connection pool limits (unbounded connections)
- CRITICAL: HARD GATE violation — not using lib-commons connection packages
- HIGH: No connection timeouts (hang forever)
- HIGH: No max lifetime (stale connections)
- MEDIUM: Missing read replica support
- LOW: Pool sizes not tuned

**Output Format:**
```
## Connection Management Audit Findings

### Summary
- DB pool configured: Yes/No (max: X, idle: Y)
- Redis pool configured: Yes/No (size: X)
- Timeouts configured: Yes/No
- Replica support: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 15: Logging & PII Safety Auditor

```prompt
Audit logging practices and PII protection for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Logging" section from quality.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*.go`
- Keywords: `logger.`, `log.`, `Errorf`, `Infof`, `WithFields`, `password`, `token`, `secret`
- Also search: `fmt.Print`, `fmt.Println` (should not be used for logging)
- Standards-specific: `zap`, `zerolog`, structured logging library references

**Reference Implementation (GOOD):**
```go
// Structured logging with context
logger, tracer, requestID, _ := libCommons.NewTrackingFromContext(ctx)
logger.WithFields(
    "request_id", requestID,
    "user_id", userID,
    "action", "create_resource",
).Info("resource created")

// Production-safe error logging
if isProduction {
    // Don't include error details that might leak PII
    logger.Errorf("operation failed: status=%d path=%s", code, path)
} else {
    // Development can have full details
    logger.Errorf("operation failed: error=%v", err)
}

// Config DSN without password
func (c *Config) DSN() string {
    // Returns connection string without logging password
    return fmt.Sprintf("host=%s port=%d user=%s dbname=%s",
        c.Host, c.Port, c.User, c.DBName)
}
```

**Reference Implementation (BAD):**
```go
// BAD: fmt.Println for logging
fmt.Println("User logged in:", userEmail)

// BAD: Logging sensitive data
logger.Infof("Login attempt: email=%s password=%s", email, password)

// BAD: Logging full request body (might contain PII)
logger.Debugf("Request body: %+v", requestBody)

// BAD: Not using structured logging
log.Printf("Error: %v", err)
```

**Check Against Ring Standards For:**
1. (HARD GATE) Structured logging used (not fmt.Print or log.Printf) per quality.md logging section
2. Logger obtained from context (request tracking)
3. No passwords/tokens logged
4. Production mode sanitizes error details
5. Request/response bodies not logged raw
6. Log levels appropriate (not everything at INFO)
7. Request IDs included for tracing
8. No PII in log messages (emails, names, etc.)

**Severity Ratings:**
- CRITICAL: Passwords/tokens logged
- CRITICAL: PII logged in production
- HIGH: fmt.Print used instead of logger (HARD GATE violation per Ring standards)
- HIGH: Full error details in production
- MEDIUM: Missing request ID in logs
- LOW: Inappropriate log levels

**Output Format:**
```
## Logging & PII Safety Audit Findings

### Summary
- Structured logging: Yes/No
- PII protection: Yes/No
- Production mode: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 16: Idempotency Auditor

```prompt
Audit idempotency implementation for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Full module content from idempotency.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/idempotency*.go`, `**/value_objects/*.go`, `**/redis/*.go`
- Keywords: `IdempotencyKey`, `TryAcquire`, `MarkComplete`, `SetNX`, `idempotent`
- Standards-specific: `IdempotencyRepository`, `idempotency middleware`

**Reference Implementation (GOOD):**
```go
// Idempotency key value object
type IdempotencyKey string

const (
    idempotencyKeyMaxLength = 128
    idempotencyKeyPattern   = `^[A-Za-z0-9:_-]+$`
)

func (key IdempotencyKey) IsValid() bool {
    s := string(key)
    if s == "" || len(s) > idempotencyKeyMaxLength {
        return false
    }
    return regexp.MustCompile(idempotencyKeyPattern).MatchString(s)
}

// Redis-backed idempotency
type IdempotencyRepository struct {
    client *redis.Client
    ttl    time.Duration  // e.g., 7 days
}

func (r *IdempotencyRepository) TryAcquire(ctx context.Context, key IdempotencyKey) (bool, error) {
    // SetNX is atomic - only first caller wins
    result, err := r.client.SetNX(ctx, r.keyName(key), "acquired", r.ttl).Result()
    return result, err
}

func (r *IdempotencyRepository) MarkComplete(ctx context.Context, key IdempotencyKey) error {
    return r.client.Set(ctx, r.keyName(key), "complete", r.ttl).Err()
}

// Usage in handler
func (h *Handler) ProcessCallback(c *fiber.Ctx) error {
    key := extractIdempotencyKey(c)

    acquired, err := h.idempotency.TryAcquire(ctx, key)
    if err != nil {
        return internalError(c, "idempotency check failed", err)
    }
    if !acquired {
        return c.Status(200).JSON(fiber.Map{"status": "already_processed"})
    }

    // Process...

    h.idempotency.MarkComplete(ctx, key)
    return c.JSON(result)
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Idempotency keys for financial/critical operations per idempotency.md
2. (HARD GATE) Atomic acquire mechanism (SetNX or similar)
3. TTL to prevent unbounded storage
4. Key validation (format, length) per Ring idempotency patterns
5. Proper state transitions (acquired -> complete/failed)
6. Retry-safe (failed operations can be retried)
7. Idempotency for webhook callbacks
8. Idempotency for payment operations

**Severity Ratings:**
- CRITICAL: No idempotency for financial operations (HARD GATE violation per Ring standards)
- HIGH: Non-atomic acquire (race conditions)
- HIGH: No TTL (memory leak)
- MEDIUM: Missing key validation
- LOW: No failed state handling

**Output Format:**
```
## Idempotency Audit Findings

### Summary
- Idempotency implemented: Yes/No
- Operations covered: [list]
- Storage backend: Redis/DB/Memory
- TTL configured: X days

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 17: API Documentation Auditor

```prompt
Audit API documentation (Swagger/OpenAPI) for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Swaggo/OpenAPI subsection from "Pagination Patterns" in api-patterns.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/main.go`, `**/handlers.go`, `**/dto.go`, `**/swagger/*`
- Keywords: `@Summary`, `@Router`, `@Param`, `@Success`, `@Failure`, `@Security`
- Standards-specific: `swaggo`, `swag init`, `docs/swagger.json`

**Reference Implementation (GOOD):**
```go
// Main entry with API metadata
// @title           My API
// @version         v1.0.0
// @description     API description
// @BasePath        /
// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization

// Handler with full documentation
// @Summary      Create a resource
// @Description  Creates a new resource with the given parameters
// @Tags         resources
// @Accept       json
// @Produce      json
// @Param        request body CreateRequest true "Resource to create"
// @Success      201 {object} ResourceResponse
// @Failure      400 {object} ErrorResponse "Invalid input"
// @Failure      401 {object} ErrorResponse "Unauthorized"
// @Failure      403 {object} ErrorResponse "Forbidden"
// @Failure      500 {object} ErrorResponse "Internal error"
// @Security     BearerAuth
// @Router       /v1/resources [post]
func (h *Handler) Create(c *fiber.Ctx) error { ... }

// DTO with documentation
type CreateRequest struct {
    Name   string `json:"name" example:"my-resource" validate:"required"`
    Type   string `json:"type" example:"TYPE_A" enums:"TYPE_A,TYPE_B"`
    Amount int    `json:"amount" example:"100" minimum:"0" maximum:"1000000"`
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Swaggo annotations present per Ring api-patterns.md
2. API title, version, description in main.go
3. Security definitions (Bearer token)
4. All endpoints have @Router annotation
5. Request/response types documented
6. All error codes documented (@Failure)
7. Examples in DTOs (example: tag)
8. Enums documented (enums: tag)
9. Parameter constraints documented (minimum, maximum)
10. Tags organize endpoints logically
11. Swagger UI accessible

**Severity Ratings:**
- HIGH: No Swagger annotations at all (HARD GATE violation per Ring standards)
- HIGH: Missing security definitions
- MEDIUM: Endpoints without documentation
- MEDIUM: Error responses not documented
- LOW: Missing examples in DTOs
- LOW: Inconsistent tag usage

**Output Format:**
```
## API Documentation Audit Findings

### Summary
- Swagger annotations: Yes/No
- Documented endpoints: X/Y
- Security definitions: Yes/No
- Error responses documented: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 18: Technical Debt Auditor

```prompt
Audit technical debt indicators for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns (with context):**
- `TODO` - Planned work
- `FIXME` - Known bugs
- `HACK` - Workarounds
- `XXX` - Danger zones
- `deprecated` (case-insensitive)
- `"in a real implementation"` or `"real implementation"`
- `"temporary"` or `"temp fix"`
- `"workaround"`
- `panic("not implemented")`

**Risk Assessment Criteria:**

**Implement Now (High Risk):**
- Security-related TODOs (auth, validation, encryption)
- Error handling TODOs in critical paths
- Data integrity issues
- "FIXME" in production code paths

**Monitor (Medium Risk):**
- Performance optimization TODOs
- Incomplete logging
- "deprecated" usage without migration plan

**Acceptable Debt (Low Risk):**
- Future feature ideas
- Code style improvements
- Test coverage expansion
- Documentation improvements

**Output Format:**
```
## Technical Debt Audit Findings

### Summary
- Total TODOs: X
- Total FIXMEs: Y
- Deprecated usage: Z
- "Real implementation" markers: N

### HIGH RISK - Implement Now
| File:Line | Type | Description | Risk |
|-----------|------|-------------|------|
| path:123 | TODO | Auth bypass for testing | Security |

### MEDIUM RISK - Monitor
| File:Line | Type | Description | Risk |
|-----------|------|-------------|------|

### LOW RISK - Acceptable Debt
| File:Line | Type | Description | Risk |
|-----------|------|-------------|------|

### Recommendations
1. ...
```
```

### Agent 19: Unit Testing Auditor

```prompt
Audit unit testing patterns for production readiness against Ring testing-unit.md standards.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: standards_testing_unit from testing-unit.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*_test.go` (excluding `*_integration_test.go`)
- Keywords: `func Test`, `t.Run`, `t.Parallel`, `gomock`, `assert.`, `require.`
- Anti-patterns: `os.Setenv`, hand-written mocks, missing `tt := tt`

**Reference Implementation (GOOD):**
```go
func TestHandler_Create(t *testing.T) {
    t.Parallel()  // REQUIRED at function level

    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockRepo := mocks.NewMockRepository(ctrl)
    mockRepo.EXPECT().Save(gomock.Any(), gomock.Any()).Return(nil)

    tests := []struct {
        name    string
        input   CreateInput
        wantErr bool
        errContains string  // REQUIRED: never empty for error cases
    }{
        {name: "valid input", input: validInput()},
        {name: "empty name", input: emptyName(), wantErr: true, errContains: "name required"},
    }

    for _, tt := range tests {
        tt := tt  // REQUIRED: capture loop variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()  // REQUIRED at subtest level
            result, err := handler.Create(ctx, tt.input)
            if tt.wantErr {
                require.Error(t, err)
                assert.Contains(t, err.Error(), tt.errContains)
                return
            }
            require.NoError(t, err)
            assert.IsType(t, &Response{}, result)  // REQUIRED: verify response type
        })
    }
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Table-driven tests for all test functions
2. (HARD GATE) t.Parallel() at function AND subtest levels
3. (HARD GATE) Loop variable capture (`tt := tt`) before t.Run
4. (HARD GATE) GoMock for mocks (no hand-written mocks)
5. (HARD GATE) t.Setenv() instead of os.Setenv()
6. (HARD GATE) Strong error assertions (errContains never empty)
7. (HARD GATE) Response type verification (assert.IsType)
8. Test naming convention: Test{Unit}_{Scenario}
9. Shared utilities from tests/utils/ (no local Ptr helpers)
10. Edge case coverage (3+ per acceptance criterion)

**Severity Ratings:**
- CRITICAL: Missing t.Parallel() (slows CI, hides race conditions)
- CRITICAL: Missing loop variable capture (causes flaky tests)
- HIGH: Hand-written mocks (should use GoMock)
- HIGH: Empty errContains (weak assertion)
- HIGH: os.Setenv usage (breaks test isolation)
- MEDIUM: Missing table-driven tests
- MEDIUM: Response type not verified
- LOW: Missing edge cases

**Output Format:**
```
## Unit Testing Audit Findings

### Summary
- Unit test files found: X
- Tests with t.Parallel(): X/Y
- Loop variable capture: X/Y
- GoMock usage: Yes/No
- t.Setenv compliance: Yes/No

### Critical Issues
[file:line] - Description (Ring standard reference)

### Recommendations
1. ...
```
```

### Agent 20: Dependency Management Auditor

```prompt
Audit dependency management for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Frameworks & Libraries" section from core.md — specifically the version table}
---END STANDARDS---

**Search Patterns:**
- Files: `go.mod`, `go.sum`, `**/vendor/**`
- Commands: Run `go list -m -u all` mentally based on go.mod
- Standards-specific: Check for required Ring dependencies in go.mod

**Reference Implementation (GOOD):**
```go
// go.mod with pinned versions
module github.com/company/project

go 1.24

require (
    github.com/gofiber/fiber/v2 v2.52.10  // Pinned, not "latest"
    github.com/lib/pq v1.10.9
    go.opentelemetry.io/otel v1.39.0
)

// Indirect deps managed automatically
require (
    github.com/valyala/fasthttp v1.52.0 // indirect
)
```

**Reference Implementation (BAD):**
```go
// BAD: Using replace for production
replace github.com/some/lib => ../local-lib

// BAD: Unpinned versions
require github.com/some/lib latest

// BAD: Very old versions with known CVEs
require github.com/dgrijalva/jwt-go v3.2.0  // Has CVE, use golang-jwt
```

**Check Against Ring Standards For:**
1. (HARD GATE) Required Ring framework dependencies present in go.mod per core.md version table
2. All dependencies pinned (no "latest")
3. No local replace directives in production
4. Known vulnerable packages identified
5. Unused dependencies (not imported anywhere)
6. Major version mismatches
7. Deprecated packages (e.g., dgrijalva/jwt-go -> golang-jwt)
8. go.sum exists and is committed
9. Framework versions meet Ring minimum requirements (Go 1.24+, Fiber v2, etc.)

**Known Vulnerable Packages to Flag:**
- github.com/dgrijalva/jwt-go (use golang-jwt/jwt)
- github.com/pkg/sftp < v1.13.5
- golang.org/x/crypto < recent
- golang.org/x/net < recent

**Severity Ratings:**
- CRITICAL: Known CVE in dependency
- CRITICAL: HARD GATE violation — required Ring framework dependency missing from go.mod
- HIGH: Local replace directive
- HIGH: Deprecated package with security issues
- MEDIUM: Significantly outdated dependencies
- MEDIUM: Framework versions below Ring minimum requirements
- LOW: Minor version behind

**Output Format:**
```
## Dependency Audit Findings

### Summary
- Total dependencies: X
- Direct dependencies: Y
- Potentially outdated: Z
- Known vulnerabilities: N

### Critical Issues
[package] - Description

### Recommendations
1. ...
```
```

### Agent 21: Performance Patterns Auditor

```prompt
Audit performance patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Search Patterns:**
- Files: `**/*.go`
- Keywords: `for.*range`, `append(`, `make(`, `sync.Pool`, `SELECT *`, `N+1`

**Reference Implementation (GOOD):**
```go
// Pre-allocate slices when size is known
items := make([]Item, 0, len(input))  // Capacity hint

// Use sync.Pool for frequently allocated objects
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

// Batch database operations
func (r *Repo) CreateBatch(ctx context.Context, items []Item) error {
    return r.db.WithContext(ctx).CreateInBatches(items, 100).Error
}

// Select only needed columns
func (r *Repo) List(ctx context.Context) ([]Item, error) {
    return r.db.WithContext(ctx).
        Select("id", "name", "status").  // Not SELECT *
        Find(&items).Error
}

// Avoid N+1 with preloading
func (r *Repo) GetWithRelations(ctx context.Context, id uuid.UUID) (*Item, error) {
    return r.db.WithContext(ctx).
        Preload("Children").
        First(&item, id).Error
}
```

**Reference Implementation (BAD):**
```go
// BAD: SELECT * fetches unnecessary data
db.Find(&items)

// BAD: N+1 query pattern
for _, item := range items {
    db.Where("parent_id = ?", item.ID).Find(&children)  // Query per item!
}

// BAD: Growing slice without capacity
var items []Item
for _, input := range inputs {
    items = append(items, transform(input))  // Reallocates repeatedly
}

// BAD: Large allocations in hot path without pooling
func handleRequest() {
    buf := make([]byte, 1<<20)  // 1MB allocation per request
}
```

**Check For:**
1. SELECT * avoided (explicit column selection)
2. N+1 queries prevented (use Preload/joins)
3. Slice pre-allocation when size known
4. sync.Pool for frequent allocations
5. Batch operations for bulk inserts/updates
6. Indexes exist for filtered/sorted columns
7. Connection pooling configured
8. Context timeouts on DB operations

**Severity Ratings:**
- HIGH: N+1 query pattern in production code
- HIGH: SELECT * on large tables
- MEDIUM: Missing slice pre-allocation
- MEDIUM: No batch operations for bulk data
- LOW: Missing sync.Pool optimization
- LOW: Minor inefficiencies

**Output Format:**
```
## Performance Audit Findings

### Summary
- N+1 patterns found: X
- SELECT * usage: Y
- Missing pre-allocations: Z

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 22: Concurrency Safety Auditor

```prompt
Audit concurrency patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Concurrency Patterns" section from architecture.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*.go`
- Keywords: `go func`, `sync.Mutex`, `sync.RWMutex`, `chan`, `select {`, `sync.WaitGroup`
- Standards-specific: `errgroup`, `semaphore`, `worker pool`

**Reference Implementation (GOOD):**
```go
// Mutex protecting shared state
type Cache struct {
    mu    sync.RWMutex
    items map[string]Item
}

func (c *Cache) Get(key string) (Item, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, ok := c.items[key]
    return item, ok
}

func (c *Cache) Set(key string, item Item) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = item
}

// WaitGroup for goroutine coordination
func processAll(items []Item) error {
    var wg sync.WaitGroup
    errCh := make(chan error, len(items))

    for _, item := range items {
        wg.Add(1)
        go func(i Item) {
            defer wg.Done()
            if err := process(i); err != nil {
                errCh <- err
            }
        }(item)  // Pass item to avoid closure capture
    }

    wg.Wait()
    close(errCh)

    // Collect errors
    for err := range errCh {
        return err
    }
    return nil
}

// Context for cancellation
func worker(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case item := <-workCh:
            process(item)
        }
    }
}
```

**Reference Implementation (BAD):**
```go
// BAD: Race condition - map access without lock
var cache = make(map[string]Item)
func Get(key string) Item { return cache[key] }  // Concurrent read/write!

// BAD: Goroutine leak - no way to stop
go func() {
    for {
        process()  // Runs forever, no context check
    }
}()

// BAD: Closure captures loop variable
for _, item := range items {
    go func() {
        process(item)  // All goroutines see last item!
    }()
}

// BAD: Unbounded goroutine spawning
for _, item := range millionItems {
    go process(item)  // 1M goroutines!
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Maps protected by mutex when shared per architecture.md concurrency patterns
2. Loop variables not captured in closures
3. Goroutines have cancellation (context)
4. WaitGroup used for coordination
5. Bounded concurrency (worker pools) per Ring patterns
6. Channels closed by sender
7. Select with default for non-blocking
8. No goroutine leaks (all paths exit)

**Severity Ratings:**
- CRITICAL: Race condition on shared map (HARD GATE violation per Ring standards)
- CRITICAL: Goroutine leak (no exit path)
- HIGH: Loop variable capture bug
- HIGH: Unbounded goroutine spawning
- MEDIUM: Missing context cancellation
- LOW: Inefficient locking patterns

**Output Format:**
```
## Concurrency Audit Findings

### Summary
- Goroutine spawns: X locations
- Mutex usage: Y locations
- Potential race conditions: Z

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 23: Migration Safety Auditor

```prompt
Audit database migration safety for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Core Dependency: lib-commons" section from core.md — database migration patterns}
---END STANDARDS---

**Search Patterns:**
- Files: `migrations/*.sql`, `migrations/*.go`
- Keywords: `DROP`, `ALTER`, `RENAME`, `NOT NULL`, `CREATE INDEX`
- Standards-specific: `golang-migrate`, `lib-commons migration`

**Reference Implementation (GOOD):**
```sql
-- 000001_create_users.up.sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);

-- 000001_create_users.down.sql
DROP INDEX IF EXISTS idx_users_email;
DROP TABLE IF EXISTS users;

-- Adding nullable column (safe)
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);

-- Adding NOT NULL with default (safe)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';
```

**Reference Implementation (BAD):**
```sql
-- BAD: Adding NOT NULL without default (locks table, fails if data exists)
ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL;

-- BAD: Non-concurrent index (locks table)
CREATE INDEX idx_users_email ON users(email);

-- BAD: Destructive without IF EXISTS
DROP TABLE users;
DROP COLUMN email;

-- BAD: Renaming column (breaks application)
ALTER TABLE users RENAME COLUMN email TO user_email;
```

**Check Against Ring Standards For:**
1. (HARD GATE) All migrations have up AND down files per Ring migration patterns
2. (HARD GATE) CREATE INDEX uses CONCURRENTLY
3. New NOT NULL columns have DEFAULT
4. DROP/ALTER use IF EXISTS
5. No column renames (add new, migrate data, drop old)
6. No destructive operations in up migrations
7. Migrations are additive (safe rollback)
8. Sequential numbering (no gaps)
9. Migration tool matches Ring standard (golang-migrate or lib-commons)

**Severity Ratings:**
- CRITICAL: NOT NULL without default (HARD GATE violation per Ring standards)
- CRITICAL: Missing down migration (HARD GATE violation)
- HIGH: Non-concurrent index creation
- HIGH: Column rename (breaking change)
- MEDIUM: DROP without IF EXISTS
- LOW: Migration naming inconsistency

**Output Format:**
```
## Migration Safety Audit Findings

### Summary
- Total migrations: X
- Up migrations: Y
- Down migrations: Z
- Potentially unsafe: N

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 24: Container Security Auditor

```prompt
Audit container security and Dockerfile best practices for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Containers" section from devops.md}
---END STANDARDS---

**Search Patterns:**
- Files: `Dockerfile*`, `docker-compose*.yml`, `Makefile`
- Keywords: `FROM`, `USER`, `COPY`, `ADD`, `HEALTHCHECK`
- Standards-specific: `distroless`, `nonroot`, `multi-stage`

**Reference Implementation (GOOD):**
```dockerfile
# Multi-stage build
FROM golang:1.24-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /main cmd/app/main.go

# Distroless or minimal runtime image
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /
COPY --from=builder /main .
# Non-root user
USER nonroot:nonroot
# Healthcheck defined
HEALTHCHECK --interval=30s --timeout=3s CMD ["/main", "-health"]
ENTRYPOINT ["/main"]
```

**Check Against Ring Standards For:**
1. (HARD GATE) Multi-stage builds (builder vs runtime) per devops.md containers section
2. (HARD GATE) Non-root user execution (`USER nonroot` or numeric ID) per Ring standards
3. Minimal/Distroless runtime images per Ring container patterns
4. Pinned base image versions (not `latest`)
5. `COPY` used instead of `ADD` (unless extracting tar)
6. .dockerignore file exists and excludes secrets/git
7. Sensitive args not passed as build-args (secrets)

**Severity Ratings:**
- CRITICAL: Running as root in production image (HARD GATE violation per Ring standards)
- CRITICAL: HARD GATE violation — no multi-stage build per devops.md
- HIGH: Secrets in Dockerfile/history
- MEDIUM: Using `latest` tag
- LOW: Missing HEALTHCHECK in Dockerfile

**Output Format:**
```
## Container Security Audit Findings

### Summary
- Multi-stage build: Yes/No
- Non-root user: Yes/No
- Base image pinned: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 25: HTTP Hardening Auditor

```prompt
Audit HTTP security headers and hardening configuration for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "HTTP Security Headers" section from security.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/fiber_server.go`, `**/middleware*.go`, `**/security*.go`
- Keywords: `X-Content-Type-Options`, `X-Frame-Options`, `Helmet`, `Secure`, `HttpOnly`, `SameSite`

**Reference Implementation (GOOD):**
```go
// Security headers per Ring standards (security.md)
func SecurityHeaders() fiber.Handler {
    return func(c *fiber.Ctx) error {
        // MANDATORY per Ring standards
        c.Set("X-Content-Type-Options", "nosniff")
        c.Set("X-Frame-Options", "DENY")
        return c.Next()
    }
}

// Or using Helmet middleware
app.Use(helmet.New(helmet.Config{
    ContentTypeNosniff:        "nosniff",      // MANDATORY per Ring standards
    XFrameOptions:             "DENY",         // MANDATORY per Ring standards
    HSTSMaxAge:                31536000,
    HSTSExcludeSubdomains:     false,
    ContentSecurityPolicy:     "default-src 'self'",
}))
```

**Check Against Ring Standards For:**
1. HARD GATE: X-Content-Type-Options set to "nosniff" per security.md
2. HARD GATE: X-Frame-Options set to "DENY" per security.md
3. HSTS enabled (Strict-Transport-Security)
4. CSP configured (Content-Security-Policy)
5. Secure cookies (Secure, HttpOnly, SameSite=Strict/Lax)
6. Server banner suppressed (Server: value removed)

**Severity Ratings:**
- CRITICAL: Missing X-Content-Type-Options (HARD GATE per Ring standards)
- CRITICAL: Missing X-Frame-Options (HARD GATE per Ring standards)
- HIGH: Missing HSTS
- MEDIUM: Missing CSP or overly permissive
- LOW: Server banner exposed

**Output Format:**
```
## HTTP Hardening Audit Findings

### Summary
- X-Content-Type-Options: Present/Missing (Ring HARD GATE)
- X-Frame-Options: Present/Missing (Ring HARD GATE)
- HSTS enabled: Yes/No
- CSP configured: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 26: CI/CD Pipeline Auditor

```prompt
Audit CI/CD pipelines for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: CI section from devops.md}
---END STANDARDS---

**Search Patterns:**
- Files: `.github/workflows/*.yml`, `.gitlab-ci.yml`, `Makefile`
- Keywords: `test`, `lint`, `build`, `docker`, `sign`
- Standards-specific: `golangci-lint`, `gosec`, `trivy`, `cosign`

**Reference Implementation (GOOD):**
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
      - run: go test -race -v ./...
      - run: golangci-lint run

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: securego/gosec@master
        with:
          args: ./...
```

**Check Against Ring Standards For:**
1. (HARD GATE) CI pipeline exists (GitHub Actions/GitLab CI) per devops.md
2. (HARD GATE) Tests run on PRs per Ring CI requirements
3. Linting runs on PRs (golangci-lint)
4. Security scanning (gosec, trivy) integrated
5. Artifact signing (cosign/sigstore)
6. Docker image build and push stages
7. Automated deployment stages (if applicable)

**Severity Ratings:**
- CRITICAL: No CI pipeline (HARD GATE violation per Ring standards)
- CRITICAL: Tests not running on PR (HARD GATE violation)
- HIGH: Missing linting in CI
- MEDIUM: Missing security scanning
- LOW: Artifacts not signed

**Output Format:**
```
## CI/CD Pipeline Audit Findings

### Summary
- CI Pipeline: Active/Missing
- Tests on PR: Yes/No
- Linting: Yes/No
- Security Scans: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 27: Async Reliability Auditor

```prompt
Audit asynchronous processing reliability for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "RabbitMQ Worker Pattern" section from messaging.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/worker/*.go`, `**/queue/*.go`, `**/kafka/*.go`, `**/rabbitmq/*.go`
- Keywords: `Ack`, `Nack`, `Retry`, `DeadLetter`, `DLQ`, `ConsumerGroup`
- Standards-specific: `amqp`, `RabbitMQ`, `lib-commons messaging`

**Reference Implementation (GOOD):**
```go
// Reliable consumer with DLQ strategy
func (c *Consumer) Handle(msg *Message) error {
    if err := c.process(msg); err != nil {
        if msg.RetryCount >= maxRetries {
            // Move to Dead Letter Queue
            return c.dlq.Publish(msg)
        }
        // Retry with backoff
        return c.RetryLater(msg, backoff(msg.RetryCount))
    }
    return msg.Ack()
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Dead Letter Queues (DLQ) configured for failed messages per messaging.md
2. (HARD GATE) Explicit Ack/Nack handling (no auto-ack) per Ring RabbitMQ worker pattern
3. Retry policies with exponential backoff
4. Consumer groups for parallel processing
5. Graceful shutdown of consumers (wait for processing to finish)
6. Message durability settings (persistent queues)
7. lib-commons messaging integration where applicable

**Severity Ratings:**
- CRITICAL: Messages auto-acked before processing (HARD GATE violation per Ring standards)
- HIGH: No DLQ for poison messages (infinite loops) — HARD GATE violation
- HIGH: No retry backoff strategy
- MEDIUM: Missing graceful shutdown for workers

**Output Format:**
```
## Async Reliability Audit Findings

### Summary
- Async processing detected: Yes/No
- DLQ configured: Yes/No
- Retry strategy: Yes/No

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 28: Core Dependencies & Frameworks Auditor

```prompt
Audit core dependency usage and framework compliance for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Sections 2 and 3 from core.md — "Core Dependency: lib-commons" and "Frameworks & Libraries"}
---END STANDARDS---

**Search Patterns:**
- Files: `go.mod`, `go.sum`, `**/utils/*.go`, `**/helpers/*.go`, `**/common/*.go`
- Keywords: `lib-commons`, `github.com/LerianStudio`, `go 1.`, `fiber`, `gorm`, `validator`
- Also search: Custom utility packages that may duplicate lib-commons functionality

**Reference Implementation (GOOD):**
```go
// go.mod with lib-commons v2 and required frameworks
module github.com/company/project

go 1.24

require (
    github.com/LerianStudio/lib-commons/v2 v2.x.x   // lib-commons present
    github.com/gofiber/fiber/v2 v2.52.x               // Fiber v2
    gorm.io/gorm v1.25.x                              // GORM
    github.com/go-playground/validator/v10 v10.x.x     // Validator
    github.com/stretchr/testify v1.9.x                 // Testify
)
```

**Reference Implementation (BAD):**
```go
// BAD: Custom utilities that duplicate lib-commons
// internal/utils/database.go
func ConnectDB(dsn string) (*sql.DB, error) {
    // Custom connection logic duplicating lib-commons/mpostgres
}

// BAD: Custom telemetry wrapper duplicating lib-commons
// internal/common/tracing.go
func StartSpan(ctx context.Context, name string) (context.Context, trace.Span) {
    // Custom wrapper duplicating lib-commons/NewTrackingFromContext
}

// BAD: Missing lib-commons entirely
// go.mod without github.com/LerianStudio/lib-commons
```

**Check Against Ring Standards For:**
1. (HARD GATE) lib-commons v2 present in go.mod — this is mandatory per Ring standards
2. (HARD GATE) No custom utility packages that duplicate lib-commons functionality (check utils/, helpers/, common/)
3. Go version 1.24+ in go.mod
4. Fiber v2 framework present
5. GORM ORM present
6. go-playground/validator/v10 present
7. testify present for testing
8. No alternative libraries used for functionality already covered by lib-commons

**Severity Ratings:**
- CRITICAL: lib-commons not in go.mod (HARD GATE violation per Ring standards)
- CRITICAL: Custom utilities duplicating lib-commons functionality (HARD GATE violation)
- HIGH: Framework versions below Ring minimum requirements
- MEDIUM: Using alternative libraries for functionality covered by Ring stack
- LOW: Minor version discrepancies

**Output Format:**
```
## Core Dependencies & Frameworks Audit Findings

### Summary
- lib-commons v2 present: Yes/No
- Go version: X (minimum 1.24)
- Required frameworks present: X/Y
- Custom utility packages found: [list]
- lib-commons duplication detected: Yes/No

### Critical Issues
[file:line or go.mod] - Description

### Recommendations
1. ...
```
```

### Agent 29: Naming Conventions Auditor

```prompt
Audit naming conventions across the codebase for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Naming conventions from core.md section 5 (if exists) and JSON naming subsection from api-patterns.md section 1}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*.go` for struct tags, `**/migrations/*.sql` for column names
- Keywords: `json:"`, `db:"`, `gorm:"`, `column:`, `CREATE TABLE`
- Also search: Query parameter handling for naming consistency

**Reference Implementation (GOOD):**
```go
// Go struct with correct naming conventions
type Account struct {
    ID          uuid.UUID `json:"id" gorm:"column:id"`
    DisplayName string    `json:"displayName" gorm:"column:display_name"`   // camelCase JSON, snake_case DB
    AccountType string    `json:"accountType" gorm:"column:account_type"`   // camelCase JSON, snake_case DB
    CreatedAt   time.Time `json:"createdAt" gorm:"column:created_at"`       // camelCase JSON, snake_case DB
}

// Query parameters use snake_case
// GET /v1/accounts?account_type=savings&created_after=2024-01-01

// SQL migration with snake_case columns
// CREATE TABLE accounts (
//     id UUID PRIMARY KEY,
//     display_name VARCHAR(255),
//     account_type VARCHAR(50),
//     created_at TIMESTAMP WITH TIME ZONE
// );
```

**Reference Implementation (BAD):**
```go
// BAD: Inconsistent JSON naming (using snake_case instead of camelCase)
type Account struct {
    ID          uuid.UUID `json:"id"`
    DisplayName string    `json:"display_name"`   // snake_case — should be camelCase!
    AccountType string    `json:"accountType"`    // camelCase — inconsistent with above!
    CreatedAt   time.Time `json:"CreatedAt"`      // PascalCase — wrong!
}

// BAD: Mixed naming in query params
// GET /v1/accounts?accountType=savings&created_after=2024-01-01
```

**Check Against Ring Standards For:**
1. snake_case for database column names in migrations and GORM tags
2. camelCase for JSON response body fields (json:"fieldName")
3. snake_case for query parameters
4. PascalCase for Go exported types and functions
5. camelCase for Go unexported fields and variables
6. Consistent naming convention within each context (no mixing)

**Severity Ratings:**
- HIGH: Inconsistent JSON field naming across response DTOs (mix of conventions)
- HIGH: JSON fields using snake_case instead of camelCase
- MEDIUM: Query params not using snake_case
- MEDIUM: Database columns not using snake_case
- LOW: Minor naming inconsistencies within a single file

**Output Format:**
```
## Naming Conventions Audit Findings

### Summary
- JSON fields audited: X
- Using camelCase JSON: Y/X (REQUIRED: should equal X)
- DB columns using snake_case: Y/Z
- Query params using snake_case: Y/Z
- Naming convention violations: N

### Issues by Convention
#### JSON Naming
[file:line] - Field "display_name" should be "displayName" (camelCase)

#### Database Naming
[file:line] - Column "displayName" should be "display_name" (snake_case)

#### Query Parameter Naming
[file:line] - Param "accountType" should be "account_type" (snake_case)

### Recommendations
1. ...
```
```

### Agent 30: Domain Modeling Auditor

```prompt
Audit domain modeling patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "ToEntity/FromEntity" section 9 from domain.md and "Always-Valid Domain Model" section 21 from domain-modeling.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/domain/*.go`, `**/entity/*.go`, `**/model/*.go`, `**/value_objects/*.go`
- Keywords: `ToEntity`, `FromEntity`, `NewXxx`, `IsValid()`, `private fields`
- Also search: `**/adapters/**/*.go` for mapping patterns

**Reference Implementation (GOOD):**
```go
// Always-valid domain model with private fields and constructor
type Account struct {
    id          uuid.UUID   // Private fields
    name        string
    accountType AccountType
    status      Status
    createdAt   time.Time
}

// Constructor enforces invariants
func NewAccount(name string, accountType AccountType) (*Account, error) {
    if name == "" {
        return nil, ErrNameRequired
    }
    if !accountType.IsValid() {
        return nil, ErrInvalidAccountType
    }
    return &Account{
        id:          uuid.New(),
        name:        name,
        accountType: accountType,
        status:      StatusActive,
        createdAt:   time.Now(),
    }, nil
}

// Exported getters (no setters for immutable fields)
func (a *Account) ID() uuid.UUID       { return a.id }
func (a *Account) Name() string        { return a.name }
func (a *Account) Status() Status      { return a.status }

// ToEntity/FromEntity mapping in adapters
func (dto *CreateAccountDTO) ToEntity() (*domain.Account, error) {
    return domain.NewAccount(dto.Name, domain.AccountType(dto.Type))
}

func FromEntity(account *domain.Account) *AccountResponse {
    return &AccountResponse{
        ID:     account.ID().String(),
        Name:   account.Name(),
        Status: string(account.Status()),
    }
}
```

**Reference Implementation (BAD):**
```go
// BAD: Domain model with exported mutable fields and no constructor
type Account struct {
    ID          uuid.UUID `json:"id"`           // Exported + mutable!
    Name        string    `json:"name"`         // Can be set to "" directly
    AccountType string    `json:"account_type"` // No type safety
    Status      string    `json:"status"`       // No validation
}

// BAD: Direct field access without validation
account := &Account{Name: ""}  // Invalid state allowed!

// BAD: No ToEntity/FromEntity — DTOs used directly as domain models
func (h *Handler) Create(c *fiber.Ctx) error {
    var account Account
    c.BodyParser(&account)
    repo.Save(ctx, &account)  // DTO goes straight to persistence!
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Domain models use private fields with exported getters per domain-modeling.md always-valid pattern
2. (HARD GATE) Constructors (NewXxx) enforce invariants — no invalid domain objects can be created
3. (HARD GATE) ToEntity/FromEntity mapping patterns in adapters per domain.md section 9
4. Value objects have IsValid() methods
5. No direct field access on domain models from outside the package
6. DTOs are separate from domain models (not the same struct)
7. Consistent domain modeling across all bounded contexts

**Severity Ratings:**
- CRITICAL: Domain models with exported mutable fields and no constructor (HARD GATE violation per Ring standards)
- CRITICAL: DTOs used directly as domain models (no ToEntity/FromEntity)
- HIGH: Missing ToEntity/FromEntity in adapters (HARD GATE violation)
- MEDIUM: Inconsistent domain modeling across modules
- MEDIUM: Value objects without IsValid()
- LOW: Minor modeling inconsistencies

**Output Format:**
```
## Domain Modeling Audit Findings

### Summary
- Domain models found: X
- Using always-valid pattern: Y/X
- With constructors (NewXxx): Y/X
- ToEntity/FromEntity present: Y/Z adapters
- Value objects with IsValid: Y/Z

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 31: Linting & Code Quality Auditor

```prompt
Audit linting configuration and code quality patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Linting" section 16 from quality.md}
---END STANDARDS---

**Search Patterns:**
- Files: `.golangci.yml`, `.golangci.yaml`, `**/*.go`
- Keywords: `//nolint`, `golangci-lint`, import grouping patterns
- Also search: Magic numbers in business logic code

**Reference Implementation (GOOD):**
```go
// Import ordering: 3 groups (stdlib, external, internal)
import (
    "context"
    "fmt"
    "time"

    "github.com/gofiber/fiber/v2"
    "github.com/google/uuid"
    "go.opentelemetry.io/otel"

    "github.com/company/project/internal/domain"
    "github.com/company/project/pkg/assert"
)

// Named constants instead of magic numbers
const (
    maxRetries       = 3
    defaultTimeout   = 30 * time.Second
    maxPageSize      = 100
    minPasswordLen   = 8
)

// Using named constants in logic
if retryCount >= maxRetries {
    return ErrMaxRetriesExceeded
}
```

**Reference Implementation (BAD):**
```go
// BAD: Import ordering not following convention
import (
    "github.com/company/project/internal/domain"
    "fmt"
    "github.com/gofiber/fiber/v2"
    "context"
)

// BAD: Magic numbers in business logic
if retryCount >= 3 {           // What is 3?
    time.Sleep(30 * time.Second) // What is 30?
}
if len(password) < 8 {          // What is 8?
    return errors.New("too short")
}
if pageSize > 100 {             // What is 100?
    pageSize = 100
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) golangci-lint configuration exists per quality.md linting section
2. Import ordering follows 3-group convention (stdlib, external, internal)
3. Magic numbers replaced with named constants in business logic
4. Required linters enabled in golangci-lint config
5. No blanket //nolint without specific linter name
6. Consistent code formatting (gofmt/goimports applied)

**Severity Ratings:**
- HIGH: No golangci-lint configuration (HARD GATE violation per Ring standards)
- MEDIUM: Magic numbers in business logic
- MEDIUM: Import ordering not following 3-group convention
- MEDIUM: Blanket //nolint without justification
- LOW: Minor style inconsistencies

**Output Format:**
```
## Linting & Code Quality Audit Findings

### Summary
- golangci-lint config: Yes/No
- Import ordering violations: X files
- Magic numbers found: Y locations
- Blanket //nolint usage: Z locations

### Issues
#### golangci-lint Configuration
[config status and missing linters]

#### Import Ordering
[file:line] - Imports not following 3-group convention

#### Magic Numbers
[file:line] - Magic number N used (suggest: named constant)

### Recommendations
1. ...
```
```

### Agent 32: Makefile & Dev Tooling Auditor

```prompt
Audit Makefile and development tooling for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: "Makefile Standards" section 7 from devops.md}
---END STANDARDS---

**Search Patterns:**
- Files: `Makefile`, `makefile`, `GNUmakefile`
- Keywords: `.PHONY`, `build`, `test`, `lint`, `help`, `docker`
- Also search: `scripts/*.sh` for development scripts

**Reference Implementation (GOOD):**
```makefile
.PHONY: build test lint cover up down logs setup migrate seed generate swagger docker-build docker-push clean help check

build: ## Build the application binary
	go build -o bin/app cmd/app/main.go

test: ## Run all unit tests
	go test -race -v ./...

lint: ## Run linters
	golangci-lint run

cover: ## Run tests with coverage
	go test -race -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

up: ## Start local dependencies (docker-compose)
	docker compose up -d

down: ## Stop local dependencies
	docker compose down

logs: ## Tail local dependency logs
	docker compose logs -f

setup: ## Initial project setup
	go mod download
	go install github.com/swaggo/swag/cmd/swag@latest

migrate: ## Run database migrations
	migrate -path migrations -database "$$DATABASE_URL" up

seed: ## Seed database with test data
	go run cmd/seed/main.go

generate: ## Run code generators (mockgen, etc.)
	go generate ./...

swagger: ## Generate Swagger documentation
	swag init -g cmd/app/main.go

docker-build: ## Build Docker image
	docker build -t app:latest .

docker-push: ## Push Docker image
	docker push app:latest

clean: ## Clean build artifacts
	rm -rf bin/ coverage.out coverage.html

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

check: ## Run all checks (lint + test + cover)
	$(MAKE) lint
	$(MAKE) test
	$(MAKE) cover
```

**Check Against Ring Standards For:**
1. (HARD GATE) Makefile exists in project root per devops.md
2. Required targets present: build, lint, test, cover, up, down, logs, setup, migrate, seed, generate, swagger, docker-build, docker-push, clean, help, check
3. All targets have help descriptions (## comments)
4. .PHONY declarations for non-file targets
5. `help` target shows available commands
6. `check` target runs full validation pipeline

**Severity Ratings:**
- HIGH: No Makefile in project (HARD GATE violation per Ring standards)
- MEDIUM: Missing required Makefile targets (list which ones are missing)
- MEDIUM: Targets without help descriptions
- LOW: Missing .PHONY declarations
- LOW: Targets without error handling

**Output Format:**
```
## Makefile & Dev Tooling Audit Findings

### Summary
- Makefile present: Yes/No
- Required targets present: X/17
- Missing targets: [list]
- Targets with help: X/Y

### Required Targets Checklist
| Target | Present | Has Help |
|--------|---------|----------|
| build | Yes/No | Yes/No |
| test | Yes/No | Yes/No |
| lint | Yes/No | Yes/No |
| cover | Yes/No | Yes/No |
| up | Yes/No | Yes/No |
| down | Yes/No | Yes/No |
| logs | Yes/No | Yes/No |
| setup | Yes/No | Yes/No |
| migrate | Yes/No | Yes/No |
| seed | Yes/No | Yes/No |
| generate | Yes/No | Yes/No |
| swagger | Yes/No | Yes/No |
| docker-build | Yes/No | Yes/No |
| docker-push | Yes/No | Yes/No |
| clean | Yes/No | Yes/No |
| help | Yes/No | Yes/No |
| check | Yes/No | Yes/No |

### Recommendations
1. ...
```
```

### Agent 33: Multi-Tenant Patterns Auditor

```prompt
**CONDITIONAL: Only run this auditor if MULTITENANT=true is set. If the project does not use multi-tenancy, skip this audit and report "N/A - Single-tenant project".**

Audit multi-tenant architecture patterns for production readiness.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: Section 23 from multi-tenant.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/tenant*.go`, `**/pool*.go`, `**/middleware*.go`, `**/context*.go`
- Keywords: `tenantID`, `PoolManager`, `TenantContext`, `schema`, `search_path`
- Also search: `**/jwt*.go`, `**/auth*.go` for tenant extraction

**Reference Implementation (GOOD):**
```go
// Pool Manager for tenant connection management
type PoolManager struct {
    mu       sync.RWMutex
    pools    map[string]*sql.DB
    config   *PoolConfig
    maxPools int
}

func (pm *PoolManager) GetConnection(tenantID string) (*sql.DB, error) {
    pm.mu.RLock()
    if pool, ok := pm.pools[tenantID]; ok {
        pm.mu.RUnlock()
        return pool, nil
    }
    pm.mu.RUnlock()

    // Create new pool for tenant
    pm.mu.Lock()
    defer pm.mu.Unlock()

    // Double-check after acquiring write lock
    if pool, ok := pm.pools[tenantID]; ok {
        return pool, nil
    }

    pool, err := pm.createPool(tenantID)
    if err != nil {
        return nil, fmt.Errorf("create pool for tenant %s: %w", tenantID, err)
    }
    pm.pools[tenantID] = pool
    return pool, nil
}

// Tenant context injection middleware
func TenantMiddleware(next fiber.Handler) fiber.Handler {
    return func(c *fiber.Ctx) error {
        claims := auth.GetClaims(c)
        tenantID := claims["tenant_id"].(string)
        if tenantID == "" {
            return fiber.NewError(401, "missing tenant context")
        }
        ctx := context.WithValue(c.UserContext(), TenantKey, tenantID)
        c.SetUserContext(ctx)
        return next(c)
    }
}

// Tenant-scoped query — ALWAYS filter by tenant
func (r *Repo) FindByID(ctx context.Context, id uuid.UUID) (*Entity, error) {
    tenantID := GetTenantID(ctx)  // From context, never from request
    var entity Entity
    err := r.db.WithContext(ctx).
        Where("id = ? AND tenant_id = ?", id, tenantID).
        First(&entity).Error
    return &entity, err
}
```

**Reference Implementation (BAD):**
```go
// BAD: Query without tenant filter — data leakage!
func (r *Repo) FindByID(ctx context.Context, id uuid.UUID) (*Entity, error) {
    var entity Entity
    err := r.db.WithContext(ctx).Where("id = ?", id).First(&entity).Error
    return &entity, err
}

// BAD: Tenant ID from request header (can be spoofed)
func GetTenantID(c *fiber.Ctx) string {
    return c.Get("X-Tenant-ID")  // User-controlled!
}

// BAD: No schema isolation — shared tables
func (r *Repo) Save(ctx context.Context, entity *Entity) error {
    return r.db.Create(entity).Error  // Which tenant's data?
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) Tenant ID extracted from JWT claims (not user-controlled headers/params) per multi-tenant.md
2. (HARD GATE) All database queries include tenant filter — no query without tenant scope
3. (HARD GATE) Tenant context middleware injects tenant into request context
4. Pool Manager implementation for connection management
5. Database schema isolation (schema-per-tenant or row-level filtering)
6. Tenant-scoped cache keys (Redis keys include tenant prefix)
7. No cross-tenant data leakage in list/search operations

**Severity Ratings:**
- CRITICAL: Queries without tenant filter — data leakage (HARD GATE violation per Ring standards)
- CRITICAL: Tenant ID from user-controlled input (HARD GATE violation)
- CRITICAL: Missing tenant context middleware (HARD GATE violation)
- HIGH: No Pool Manager for connection management
- HIGH: Cache keys not tenant-scoped
- MEDIUM: Inconsistent tenant extraction across modules
- LOW: Missing tenant validation in non-critical paths

**Output Format:**
```
## Multi-Tenant Patterns Audit Findings

### Summary
- Multi-tenant detection: Yes/No/N/A
- Tenant extraction: JWT / Header / Missing
- Tenant middleware: Yes/No
- Pool Manager: Yes/No
- Queries with tenant filter: X/Y

### Critical Issues
[file:line] - Description

### Recommendations
1. ...
```
```

### Agent 34: License Headers Auditor

```prompt
Audit license/copyright headers on source files for production readiness. All source files MUST have proper license headers.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: License header section from core.md section 7 (if exists), otherwise use organizational defaults}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*.go` (check first 5 lines for copyright/license header)
- Also check: `LICENSE`, `LICENSE.md`, `NOTICE` files in project root
- Keywords: `Copyright`, `Licensed under`, `SPDX-License-Identifier`

**Reference Implementation (GOOD):**
```go
// Copyright 2025 LerianStudio. All rights reserved.
// Use of this source code is governed by the Apache License 2.0
// that can be found in the LICENSE file.
// SPDX-License-Identifier: Apache-2.0

package domain

import (
    ...
)
```

**Reference Implementation (BAD):**
```go
// BAD: No license header at all
package domain

import (
    ...
)

// BAD: Outdated year
// Copyright 2020 LerianStudio. All rights reserved.
// (If current year is 2025+)

// BAD: Inconsistent header format
/* This file is part of Project X
 * (c) Company Name
 */
package domain
```

**Check Against Ring Standards For:**
1. LICENSE file exists in project root
2. All .go files have copyright/license header comment in first 5 lines
3. Consistent header format across all files
4. Year in copyright is current or includes current year (e.g., "2024-2025")
5. SPDX-License-Identifier present (preferred for machine-readability)
6. License matches LICENSE file (e.g., Apache-2.0 header matches Apache-2.0 LICENSE)

**Severity Ratings:**
- HIGH: .go files missing license headers (if license headers are required)
- MEDIUM: Inconsistent license header format across files
- MEDIUM: License header does not match LICENSE file
- LOW: Outdated year in copyright header
- LOW: Missing SPDX identifier

**Output Format:**
```
## License Headers Audit Findings

### Summary
- LICENSE file present: Yes/No (type: Apache-2.0/MIT/etc.)
- Total .go files: X
- Files with headers: Y/X
- Consistent format: Yes/No
- Year current: Yes/No

### Files Missing Headers
[file] - No license header found

### Inconsistent Headers
[file] - Header differs from standard format

### Recommendations
1. ...
```
```

### Agent 35: Fuzz Testing Auditor

```prompt
Audit fuzz testing implementation for production readiness against Ring testing-fuzz.md standards.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: standards_testing_fuzz from testing-fuzz.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*_test.go` (excluding `*_integration_test.go`)
- Keywords: `func Fuzz`, `*testing.F`, `f.Add`, `f.Fuzz`
- Anti-patterns: Empty seed corpus, missing input bounds

**Reference Implementation (GOOD):**
```go
func FuzzCreateOrganization_LegalName(f *testing.F) {
    // REQUIRED: Comprehensive seed corpus (5+ seeds)
    f.Add("Acme, Inc.")                // valid
    f.Add("")                          // empty
    f.Add("日本語")                     // unicode
    f.Add("<script>alert(1)</script>") // XSS attempt
    f.Add(strings.Repeat("x", 1000))   // long string

    f.Fuzz(func(t *testing.T, name string) {
        // REQUIRED: Bound input to prevent resource exhaustion
        if len(name) > 512 {
            name = name[:512]
        }

        // PROPERTY: No panic, returns error gracefully
        result, err := ValidateOrganizationName(name)
        if err == nil {
            assert.NotEmpty(t, result)
        }
    })
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All input validation functions have fuzz tests
2. (HARD GATE) All parsers have fuzz tests
3. (HARD GATE) Naming convention: `Fuzz{Subject}_{Field}`
4. (HARD GATE) Seed corpus with 5+ seeds (valid, empty, boundary, unicode, security)
5. (HARD GATE) Input bounding to prevent resource exhaustion
6. Go 1.18+ native fuzz syntax (`*testing.F`)
7. No empty seed corpus
8. Fuzz tests run without panic

**Severity Ratings:**
- CRITICAL: Input validation without fuzz tests (security risk)
- CRITICAL: Empty seed corpus (ineffective fuzzing)
- HIGH: Missing input bounds (resource exhaustion)
- HIGH: Parser without fuzz tests
- MEDIUM: Insufficient seed corpus (<5 seeds)
- MEDIUM: Wrong naming convention
- LOW: Missing security payloads in seed corpus

**Output Format:**
```
## Fuzz Testing Audit Findings

### Summary
- Validation functions found: X
- Parsers found: Y
- Fuzz tests written: Z
- Seed corpus coverage: X/Y (avg seeds per test)

### Critical Issues
[file:line] - Description (Ring standard reference)

### Recommendations
1. ...
```
```

### Agent 36: Property-Based Testing Auditor

```prompt
Audit property-based testing implementation for production readiness against Ring testing-property.md standards.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: standards_testing_property from testing-property.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*_test.go`
- Keywords: `testing/quick`, `quick.Check`, `TestProperty_`, `property :=`
- Domain patterns: `Add`, `Equals`, `Marshal`, `Unmarshal`, `Normalize`

**Reference Implementation (GOOD):**
```go
import "testing/quick"

func TestProperty_Money_AdditionCommutative(t *testing.T) {
    property := func(a, b int64) bool {
        m1 := NewMoney(a, "USD")
        m2 := NewMoney(b, "USD")
        // PROPERTY: a + b == b + a
        return m1.Add(m2).Equals(m2.Add(m1))
    }

    err := quick.Check(property, nil)
    require.NoError(t, err)
}

func TestProperty_User_JSONRoundtrip(t *testing.T) {
    property := func(name string, age uint8) bool {
        original := User{Name: name, Age: int(age)}
        data, err := json.Marshal(original)
        if err != nil {
            return true // Skip invalid inputs
        }
        var decoded User
        if json.Unmarshal(data, &decoded) != nil {
            return true
        }
        // PROPERTY: Unmarshal(Marshal(x)) == x
        return original.Name == decoded.Name && original.Age == decoded.Age
    }

    require.NoError(t, quick.Check(property, nil))
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All domain invariants have property tests
2. (HARD GATE) Naming convention: `TestProperty_{Subject}_{Property}`
3. (HARD GATE) Using `testing/quick.Check` for property tests
4. Mathematical operations tested for commutativity/associativity
5. Serialization tested for roundtrip property
6. Normalization functions tested for idempotency
7. No hardcoded iterations (use default or configure `MaxCount`)

**Common Properties to Test:**
- Commutativity: `a + b == b + a`
- Roundtrip: `Unmarshal(Marshal(x)) == x`
- Idempotency: `f(f(x)) == f(x)`
- Non-negative: `Jitter(x) >= 0`
- Invariant preservation: `Balance >= 0 after debit`

**Severity Ratings:**
- CRITICAL: Domain invariants without property tests
- HIGH: Missing roundtrip tests for serialization
- HIGH: Not using testing/quick.Check
- MEDIUM: Wrong naming convention
- MEDIUM: Missing commutativity/associativity tests
- LOW: Missing idempotency tests for normalization

**Output Format:**
```
## Property-Based Testing Audit Findings

### Summary
- Domain entities found: X
- Properties identified: Y
- Property tests written: Z
- Iterations per property: 100 (default)

### Critical Issues
[file:line] - Description (Ring standard reference)

### Recommendations
1. ...
```
```

### Agent 37: Integration Testing Auditor

```prompt
Audit integration testing implementation for production readiness against Ring testing-integration.md standards.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: standards_testing_integration from testing-integration.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*_integration_test.go`, `**/*_test.go` (with integration behavior)
- Keywords: `testcontainers`, `TestIntegration_`, `//go:build integration`
- Anti-patterns: `t.Parallel()` in integration tests, `os.Setenv`, hardcoded ports

**Reference Implementation (GOOD):**
```go
//go:build integration

package postgres_test

import (
    "testing"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
)

func TestIntegration_UserRepository_Create(t *testing.T) {
    // NO t.Parallel() - integration tests run sequentially
    ctx := context.Background()

    // Use testcontainers, not production deps
    container, err := postgres.Run(ctx, "postgres:15-alpine", ...)
    require.NoError(t, err)
    defer container.Terminate(ctx)

    // Get dynamic connection string (no hardcoded ports)
    connStr, err := container.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)

    // Use centralized fixtures
    repo := NewUserRepository(connStr)
    userID := pgtestutil.CreateTestUser(t, container.DB, nil)

    // Test
    user, err := repo.Find(ctx, userID)
    require.NoError(t, err)
    assert.NotEmpty(t, user.ID)
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All files named `*_integration_test.go`
2. (HARD GATE) All files have `//go:build integration` tag
3. (HARD GATE) All functions named `TestIntegration_{Component}_{Scenario}`
4. (HARD GATE) No `t.Parallel()` in integration tests
5. (HARD GATE) Testcontainers for external dependencies
6. (HARD GATE) Fixtures from `tests/utils/`, no local helpers
7. No hardcoded ports (`:5432`, `:6379`, `:27017`)
8. No `os.Setenv` (use `t.Setenv`)
9. No `time.Sleep` (use wait strategies)
10. Cleanup via `t.Cleanup()` or `defer`

**11 Anti-Patterns to Detect:**
1. Hardcoded ports
2. Shared database state
3. time.Sleep for sync
4. os.Setenv pollution
5. Global test state
6. Missing build tag
7. t.Parallel() usage
8. Local fixtures
9. Network-dependent tests
10. Missing timeout
11. Production credentials

**Severity Ratings:**
- CRITICAL: Missing build tag (runs with unit tests)
- CRITICAL: t.Parallel() in integration tests (race conditions)
- HIGH: Hardcoded ports (CI conflicts)
- HIGH: Local fixtures (duplication)
- HIGH: No testcontainers (production deps)
- MEDIUM: Missing function naming convention
- MEDIUM: os.Setenv usage
- LOW: time.Sleep usage

**Output Format:**
```
## Integration Testing Audit Findings

### Summary
- External dependencies: X
- Integration test files: Y
- Build tags present: Y/Y
- t.Parallel() violations: 0
- Testcontainers usage: Yes/No

### Anti-Pattern Detection
| Anti-Pattern | Found | Files |
|--------------|-------|-------|
| t.Parallel() | 0 | - |
| Hardcoded ports | 0 | - |
| Missing build tag | 0 | - |

### Critical Issues
[file:line] - Description (Ring standard reference)

### Recommendations
1. ...
```
```

### Agent 38: Chaos Testing Auditor

```prompt
Audit chaos testing implementation for production readiness against Ring testing-chaos.md standards.

**Detected Stack:** {DETECTED_STACK}

**Ring Standards (Source of Truth):**
---BEGIN STANDARDS---
{INJECTED: standards_testing_chaos from testing-chaos.md}
---END STANDARDS---

**Search Patterns:**
- Files: `**/*_integration_test.go`, `**/chaos/*.go`
- Keywords: `Chaos`, `Toxiproxy`, `CHAOS=1`, `proxy.Disconnect`, `proxy.AddLatency`
- Infrastructure: `tests/utils/chaos/`

**Reference Implementation (GOOD):**
```go
//go:build integration

func TestIntegration_Chaos_Redis_ConnectionLoss(t *testing.T) {
    // REQUIRED: Gate 1 - Chaos tests disabled by default
    if os.Getenv("CHAOS") != "1" {
        t.Skip("Chaos tests disabled (set CHAOS=1)")
    }

    // REQUIRED: Gate 2 - Skip in short mode
    if testing.Short() {
        t.Skip("Skipping chaos test in short mode")
    }

    ctx := context.Background()
    redisC := redistestutil.SetupContainer(t)
    proxy := chaosutil.SetupToxiproxy(t, redisC)

    client := redis.NewClient(&redis.Options{Addr: proxy.ListenAddr()})

    // Phase 1: Verify normal operation
    err := client.Set(ctx, "key", "value", 0).Err()
    require.NoError(t, err, "normal operation should work")

    // Phase 2: Inject failure
    err = proxy.Disconnect()
    require.NoError(t, err)

    // Phase 3: Verify expected failure behavior
    err = client.Set(ctx, "key2", "value2", time.Second).Err()
    require.Error(t, err, "operation should fail when disconnected")

    // Phase 4: Restore connection
    err = proxy.Reconnect()
    require.NoError(t, err)

    // Phase 5: Verify recovery
    err = client.Set(ctx, "key3", "value3", 0).Err()
    require.NoError(t, err, "operation should work after recovery")
}
```

**Check Against Ring Standards For:**
1. (HARD GATE) All external dependencies have chaos tests
2. (HARD GATE) Dual-gate pattern (`CHAOS=1` + `testing.Short()`)
3. (HARD GATE) Naming convention: `TestIntegration_Chaos_{Component}_{Scenario}`
4. (HARD GATE) 5-phase structure: Normal → Inject → Verify → Restore → Recovery
5. Toxiproxy infrastructure in `tests/utils/chaos/`
6. Connection loss scenarios tested
7. High latency scenarios tested
8. Recovery verification after fault removal

**Failure Scenarios to Test:**
- Connection loss (database, cache, queue)
- High latency (timeout behavior)
- Network partition (intermittent failures)
- Slow close (connection pool exhaustion)

**Severity Ratings:**
- CRITICAL: External dependency without chaos tests
- CRITICAL: Missing dual-gate pattern (accidental CI runs)
- HIGH: Missing recovery verification
- HIGH: No Toxiproxy infrastructure
- MEDIUM: Incomplete 5-phase structure
- MEDIUM: Wrong naming convention
- LOW: Missing latency/partition scenarios

**Output Format:**
```
## Chaos Testing Audit Findings

### Summary
- External dependencies: X
- Chaos tests written: Y
- Dual-gate compliance: Y/Y
- Failure scenarios: Z

### Chaos Tests by Component
| Component | Scenario | Test Function | 5-Phase | Status |
|-----------|----------|---------------|---------|--------|
| PostgreSQL | Connection loss | TestIntegration_Chaos_Postgres_ConnectionLoss | Yes | PASS |
| Redis | High latency | TestIntegration_Chaos_Redis_HighLatency | Yes | PASS |

### Critical Issues
[file:line] - Description (Ring standard reference)

### Recommendations
1. ...
```
```

---

## Consolidated Report Template

After all explorers complete, generate this report:

```markdown
# Production Readiness Audit Report

**Date:** {YYYY-MM-DD}
**Codebase:** {project-name}
**Auditor:** Claude Code (Production Readiness Skill v3.0)

## Audit Configuration

| Property | Value |
|----------|-------|
| **Detected Stack** | {Go / TypeScript / Frontend / Mixed} |
| **Standards Loaded** | {list of loaded standards files} |
| **Active Dimensions** | {35 if single-tenant, 37 if multi-tenant} |
| **Max Possible Score** | {350 if single-tenant, 370 if multi-tenant} |
| **Conditional: Multi-Tenant** | {Active / Inactive} |

**⛔ SCORING RULE:** When **Multi-Tenant = Inactive**, dimensions 7 (IDOR) and 33 (Multi-Tenant) are **completely excluded** from scoring. Do NOT include them as 0/10.

## Executive Summary

### Category A: Code Structure & Patterns

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| 1. Pagination Standards | X/10 | 0 | 0 | 0 | 0 |
| 2. Error Framework | X/10 | 0 | 0 | 0 | 0 |
| 3. Route Organization | X/10 | 0 | 0 | 0 | 0 |
| 4. Bootstrap & Init | X/10 | 0 | 0 | 0 | 0 |
| 5. Runtime Safety | X/10 | 0 | 0 | 0 | 0 |
| 28. Core Dependencies | X/10 | 0 | 0 | 0 | 0 |
| 29. Naming Conventions | X/10 | 0 | 0 | 0 | 0 |
| 30. Domain Modeling | X/10 | 0 | 0 | 0 | 0 |
| **Category A Total** | **X/80** | **0** | **0** | **0** | **0** |

### Category B: Security & Access Control

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| 6. Auth Protection | X/10 | 0 | 0 | 0 | 0 |
| 8. SQL Safety | X/10 | 0 | 0 | 0 | 0 |
| 9. Input Validation | X/10 | 0 | 0 | 0 | 0 |
| **Category B Total** | **X/30** | **0** | **0** | **0** | **0** |

**If MULTITENANT=true, add these rows (otherwise OMIT entirely - do NOT include in score):**

| *7. IDOR Protection* | *X/10* | *0* | *0* | *0* | *0* |
| *33. Multi-Tenant* | *X/10* | *0* | *0* | *0* | *0* |
| **Conditional Total** | **X/20** | **0** | **0** | **0** | **0** |

**⛔ CRITICAL: When MULTITENANT=false, dimensions 7 and 33 MUST be omitted from score calculation. Do NOT include them as 0/10 - they do not exist for single-tenant projects.**

### Category C: Operational Readiness

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| 11. Telemetry & Observability | X/10 | 0 | 0 | 0 | 0 |
| 12. Health Checks | X/10 | 0 | 0 | 0 | 0 |
| 13. Configuration Mgmt | X/10 | 0 | 0 | 0 | 0 |
| 14. Connection Mgmt | X/10 | 0 | 0 | 0 | 0 |
| 15. Logging & PII Safety | X/10 | 0 | 0 | 0 | 0 |
| **Category C Total** | **X/50** | **0** | **0** | **0** | **0** |

### Category D: Quality & Maintainability

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| 16. Idempotency | X/10 | 0 | 0 | 0 | 0 |
| 17. API Documentation | X/10 | 0 | 0 | 0 | 0 |
| 18. Technical Debt | X/10 | 0 | 0 | 0 | 0 |
| 19. Unit Testing | X/10 | 0 | 0 | 0 | 0 |
| 20. Dependency Mgmt | X/10 | 0 | 0 | 0 | 0 |
| 21. Performance | X/10 | 0 | 0 | 0 | 0 |
| 22. Concurrency | X/10 | 0 | 0 | 0 | 0 |
| 23. Migrations | X/10 | 0 | 0 | 0 | 0 |
| 31. Linting & Quality | X/10 | 0 | 0 | 0 | 0 |
| 35. Fuzz Testing | X/10 | 0 | 0 | 0 | 0 |
| 36. Property-Based Testing | X/10 | 0 | 0 | 0 | 0 |
| 37. Integration Testing | X/10 | 0 | 0 | 0 | 0 |
| 38. Chaos Testing | X/10 | 0 | 0 | 0 | 0 |
| **Category D Total** | **X/130** | **0** | **0** | **0** | **0** |

### Category E: Infrastructure & Hardening

| Dimension | Score | Critical | High | Medium | Low |
|-----------|-------|----------|------|--------|-----|
| 24. Container Security | X/10 | 0 | 0 | 0 | 0 |
| 25. HTTP Hardening | X/10 | 0 | 0 | 0 | 0 |
| 26. CI/CD Pipeline | X/10 | 0 | 0 | 0 | 0 |
| 27. Async Reliability | X/10 | 0 | 0 | 0 | 0 |
| 32. Makefile & Tooling | X/10 | 0 | 0 | 0 | 0 |
| 34. License Headers | X/10 | 0 | 0 | 0 | 0 |
| **Category E Total** | **X/60** | **0** | **0** | **0** | **0** |

### Overall Score

| Metric | Value |
|--------|-------|
| **Total Score** | **X/{dynamic_max}** |
| **Percentage** | **X%** |
| **Critical Issues** | **0** |
| **High Issues** | **0** |
| **Medium Issues** | **0** |
| **Low Issues** | **0** |

### Readiness Classification

| Score Range | Classification | Deployment Recommendation |
|-------------|----------------|---------------------------|
| 90%+ | **Production Ready** | Clear to deploy |
| 75-89% | **Ready with Minor Remediation** | Deploy after addressing HIGH issues |
| 50-74% | **Needs Significant Work** | Do not deploy until CRITICAL/HIGH resolved |
| Below 50% | **Not Production Ready** | Major remediation required |

**Current Status:** {classification}

## Standards Compliance Cross-Reference

| Dimension | Standards Source | Section | Status |
|-----------|----------------|---------|--------|
| 1. Pagination | api-patterns.md | Pagination Patterns | {PASS/FAIL} |
| 2. Error Framework | domain.md | Error Codes, Error Handling | {PASS/FAIL} |
| 3. Route Organization | architecture.md | Architecture Patterns, Directory Structure | {PASS/FAIL} |
| 4. Bootstrap | bootstrap.md | Bootstrap | {PASS/FAIL} |
| 5. Runtime Safety | (generic) | — | {PASS/FAIL} |
| 6. Auth Protection | security.md | Access Manager Integration | {PASS/FAIL} |
| 7. IDOR Protection* | (generic) | — | {PASS/FAIL} |
| 8. SQL Safety | security.md | SQL Safety | {PASS/FAIL} |
| 9. Input Validation | api-patterns.md | Input Validation | {PASS/FAIL} |
| 11. Telemetry | bootstrap.md + sre.md | Observability, OpenTelemetry | {PASS/FAIL} |
| 12. Health Checks | sre.md | Health Checks | {PASS/FAIL} |
| 13. Configuration | core.md | Configuration | {PASS/FAIL} |
| 14. Connections | core.md | Core Dependency: lib-commons | {PASS/FAIL} |
| 15. Logging | quality.md | Logging | {PASS/FAIL} |
| 16. Idempotency | idempotency.md | Full module | {PASS/FAIL} |
| 17. API Documentation | api-patterns.md | OpenAPI (Swaggo) | {PASS/FAIL} |
| 18. Technical Debt | (generic) | — | {PASS/FAIL} |
| 19. Testing | quality.md | Testing | {PASS/FAIL} |
| 20. Dependencies | core.md | Frameworks & Libraries | {PASS/FAIL} |
| 21. Performance | (generic) | — | {PASS/FAIL} |
| 22. Concurrency | architecture.md | Concurrency Patterns | {PASS/FAIL} |
| 23. Migrations | core.md | Database patterns | {PASS/FAIL} |
| 24. Containers | devops.md | Containers | {PASS/FAIL} |
| 25. HTTP Hardening | security.md | HTTP Security Headers | {PASS/FAIL} |
| 26. CI/CD | devops.md | CI section | {PASS/FAIL} |
| 27. Async | messaging.md | RabbitMQ Worker Pattern | {PASS/FAIL} |
| 28. Core Deps | core.md | lib-commons, Frameworks | {PASS/FAIL} |
| 29. Naming | core.md + api-patterns.md | Naming conventions | {PASS/FAIL} |
| 30. Domain Modeling | domain.md + domain-modeling.md | ToEntity, Always-Valid | {PASS/FAIL} |
| 31. Linting | quality.md | Linting | {PASS/FAIL} |
| 32. Makefile | devops.md | Makefile Standards | {PASS/FAIL} |
| 33. Multi-Tenant* | multi-tenant.md | Full module | {PASS/FAIL} |
| 34. License Headers* | core.md | License section | {PASS/FAIL} |

*\*Conditional dimensions — only if detected*

## Critical Blockers (Must Fix Before Production)

{List all CRITICAL severity issues from all dimensions}

## High Priority Issues

{List all HIGH severity issues}

## Detailed Findings by Category

### Category A: Code Structure & Patterns

#### 1. Pagination Standards
{Agent 1 output}

#### 2. Error Framework
{Agent 2 output}

#### 3. Route Organization
{Agent 3 output}

#### 4. Bootstrap & Initialization
{Agent 4 output}

#### 5. Runtime Safety
{Agent 5 output}

#### 28. Core Dependencies & Frameworks
{Agent 28 output}

#### 29. Naming Conventions
{Agent 29 output}

#### 30. Domain Modeling
{Agent 30 output}

### Category B: Security & Access Control

#### 6. Auth Protection
{Agent 6 output}

#### 7. IDOR Protection (if applicable)
{Agent 7 output — or "Dimension not activated (MULTITENANT=false)"}

#### 8. SQL Safety
{Agent 8 output}

#### 9. Input Validation
{Agent 9 output}

#### 33. Multi-Tenant Patterns (if applicable)
{Agent 33 output — or "Dimension not activated (MULTITENANT=false)"}

### Category C: Operational Readiness

#### 11. Telemetry & Observability
{Agent 11 output}

#### 12. Health Checks
{Agent 12 output}

#### 13. Configuration Management
{Agent 13 output}

#### 14. Connection Management
{Agent 14 output}

#### 15. Logging & PII Safety
{Agent 15 output}

### Category D: Quality & Maintainability

#### 16. Idempotency
{Agent 16 output}

#### 17. API Documentation
{Agent 17 output}

#### 18. Technical Debt
{Agent 18 output}

#### 19. Unit Testing
{Agent 19 output}

#### 20. Dependency Management
{Agent 20 output}

#### 21. Performance Patterns
{Agent 21 output}

#### 22. Concurrency Safety
{Agent 22 output}

#### 23. Migration Safety
{Agent 23 output}

#### 31. Linting & Code Quality
{Agent 31 output}

#### 35. Fuzz Testing
{Agent 35 output}

#### 36. Property-Based Testing
{Agent 36 output}

#### 37. Integration Testing
{Agent 37 output}

#### 38. Chaos Testing
{Agent 38 output}

### Category E: Infrastructure & Hardening

#### 24. Container Security
{Agent 24 output}

#### 25. HTTP Hardening
{Agent 25 output}

#### 26. CI/CD Pipeline
{Agent 26 output}

#### 27. Async Reliability
{Agent 27 output}

#### 32. Makefile & Dev Tooling
{Agent 32 output}

#### 34. License Headers (if applicable)
{Agent 34 output — or "Dimension not activated (no LICENSE file detected)"}

## Recommended Remediation Order

### 1. Immediate (before any deployment)
- {Critical security issues}
- {Critical HARD GATE violations per Ring standards}
- {Critical data integrity issues}
- {Critical operational gaps}

### 2. Short-term (within 1 sprint)
- {High priority items}

### 3. Medium-term (within 1 quarter)
- {Medium priority items}

### 4. Backlog (track but don't block)
- {Low priority items}

## Appendix A: Files Audited

{List of all files examined with line counts}

## Appendix B: Audit Metadata

| Property | Value |
|----------|-------|
| Audit Duration | X minutes |
| Explorers Launched | {32 + conditional count} |
| Files Examined | X |
| Lines of Code | X |
| Skill Version | 3.0 |
| Standards Source | Ring Development Standards (GitHub) |
| Standards Files Loaded | {list} |
| Stack Detected | {Go/TypeScript/Frontend/Mixed} |
| Conditional Dimensions Active | {list or "None"} |
```

---

## Scoring Guide

### Per-Dimension Scoring (0-10 each)

| Score | Criteria |
|-------|----------|
| 10 | Exemplary - fully aligned with Ring standards, could serve as reference |
| 8-9 | Strong - minor deviations from Ring standards |
| 6-7 | Adequate - meets basic requirements but missing some Ring patterns |
| 4-5 | Concerning - multiple gaps vs Ring standards |
| 2-3 | Poor - significant non-compliance with Ring standards |
| 0-1 | Critical - fundamentally misaligned or missing |

### Deductions Per Dimension

- Each CRITICAL issue: -3 points (includes HARD GATE violations)
- Each HIGH issue: -1.5 points
- Each MEDIUM issue: -0.5 points
- Each LOW issue: -0.25 points
- Minimum score: 0 (no negative scores)

### Category Weights

| Category | Dimensions | Always-Active | Max Score |
|----------|------------|---------------|-----------|
| A: Code Structure | 1-5, 28-30 | 8 | 80 |
| B: Security | 6, 7*, 8, 9, 33* | 3 (+2 conditional) | 30 (+20) |
| C: Operations | 11-15 | 5 | 50 |
| D: Quality | 16-23, 31, 35-38 | 13 | 130 |
| E: Infrastructure | 24-27, 32, 34 | 6 | 60 |
| **Total** | | **35 (+2 conditional)** | **350 (+20)** |

### Dynamic Max Calculation

```
dynamic_max = 350 + (MULTITENANT ? 20 : 0)
```

Possible values: 350 or 370.

### Overall Classification (Percentage-Based)

| Score Range | Percentage | Classification |
|-------------|------------|----------------|
| 90%+ of dynamic_max | 90%+ | Production Ready |
| 75-89% of dynamic_max | 75-89% | Ready with Minor Remediation |
| 50-74% of dynamic_max | 50-74% | Needs Significant Work |
| Below 50% of dynamic_max | <50% | Not Production Ready |

---

## Usage Example

```
User: /production-readiness-audit
```

---

## Assistant Execution Protocol

When this skill is invoked, follow this exact protocol:

### Step 1: Initialize Todo List

```
TodoWrite: Create todos for stack detection, standards loading, all 4 batches + consolidation
```

### Step 2: Detect Stack (Step 0)

Use Glob and Grep to detect:
- GO, TS_BACKEND, FRONTEND, DOCKER, MAKEFILE, LICENSE, MULTITENANT flags

### Step 3: Load Standards (Step 0.5)

Use WebFetch to load Ring standards based on detected stack. Store content for injection into explorer prompts.

**If WebFetch fails for any module:** Note the failure and proceed with generic patterns for affected dimensions.

### Step 4: Initialize Report File

Write the report header with Audit Configuration to `docs/audits/production-readiness-{YYYY-MM-DD}-{hh:mm}.md`

### Step 5: Launch Parallel Explorers (Batch 1)

**CRITICAL**: Use a SINGLE response with 10 Task tool calls for agents 1-10.

Each Task call should include:
- The full explorer prompt from the dimension
- Injected Ring standards content between ---BEGIN STANDARDS--- / ---END STANDARDS--- markers
- Detected stack information
- Instruction to search the codebase thoroughly

### Step 6: Launch Parallel Explorers (Batch 2)

Launch 10 agents (11-20) in a SINGLE response.

### Step 7: Launch Parallel Explorers (Batch 3)

Launch 10 agents (21-30) in a SINGLE response.

### Step 8: Launch Parallel Explorers (Batch 4)

Launch agents 31-34 (conditionally for 33 and 34) in a SINGLE response.

### Step 9: Launch Parallel Explorers (Batch 5 - Advanced Testing)

Launch agents 35-38 (Fuzz Testing, Property-Based Testing, Integration Testing, Chaos Testing) in a SINGLE response.

### Step 10: Collect Results

As each explorer completes, mark its todo as completed and append to report.

### Step 11: Consolidate Report

Once ALL explorers complete:
1. Calculate scores for each dimension (0-10 scale)
2. Calculate category totals (A: /80, B: /50-60, C: /50, D: /130, E: /50-60)
3. Calculate overall score (/{dynamic_max})
4. Aggregate critical/high/medium/low counts
5. Determine readiness classification (percentage-based)
6. Generate Standards Compliance Cross-Reference table
7. Generate the consolidated report

### Step 12: Write Report

```
Write: docs/audits/production-readiness-{YYYY-MM-DD}-{hh:mm}.md
```

### Step 12: Present Summary

Provide a verbal summary to the user including:
- Detected stack and standards loaded
- Overall score and classification
- Number of critical/high issues
- HARD GATE violations summary
- Top 3 recommendations
- Link to full report

---

## Customization Options

Users can customize the audit:

### Scope Limiting

```
User: /production-readiness-audit --modules=matching,ingestion
```

Only audit specified modules.

### Dimension Selection

```
User: /production-readiness-audit --dimensions=security
```

Run only security-related auditors (6, 7, 8, 9, 10, 33).

### Output Format

```
User: /production-readiness-audit --format=json
```

Output structured JSON instead of markdown.

### Standards Override

```
User: /production-readiness-audit --no-standards
```

Run without Ring standards injection (generic mode, equivalent to v2.0 behavior).

---

## Integration with CI/CD

This skill can be automated:

1. Run audit on every release branch
2. Block merges if CRITICAL issues exist
3. Block merges if HARD GATE violations exist (Ring standards)
4. Track debt trends over time
5. Generate dashboards from JSON output
6. Compare scores across audit runs to measure standards adoption

---

## Reference Patterns Source

The reference implementations in this skill are derived from two sources:

### Ring Development Standards (Primary - Source of Truth)
Standards loaded at runtime via WebFetch from `dev-team/docs/standards/`:
- **golang/*.md** — Go-specific standards (core, bootstrap, security, domain, API patterns, quality, architecture, messaging, domain-modeling, idempotency, multi-tenant)
- **devops.md** — Container, Makefile, and infrastructure standards
- **sre.md** — Observability and health check standards

### Matcher Codebase (Legacy Reference)
Original reference implementations derived from the Matcher codebase, which serves as the organizational standard for:
- Hexagonal architecture per bounded context
- lib-commons integration (telemetry, database, messaging)
- lib-auth integration (JWT validation, tenant extraction)
- Fiber HTTP framework conventions

When auditing projects, findings are compared against Ring standards as the authoritative reference. Matcher patterns remain as supplementary examples.

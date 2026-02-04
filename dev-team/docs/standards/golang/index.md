# Go Standards - Index

> **⚠️ MAINTENANCE:** This directory is indexed in `dev-team/skills/shared-patterns/standards-coverage-table.md`.
> When adding/removing sections, follow FOUR-FILE UPDATE RULE in CLAUDE.md.

This directory contains modular Go standards for Lerian Studio. Load only the modules you need.

> **Reference**: Always consult `docs/PROJECT_RULES.md` for common project standards.

---

## Quick Reference - Which File for What

| Task | Load These Files |
|------|------------------|
| **New feature (full)** | core.md → bootstrap.md → domain.md → quality.md |
| **Auth implementation** | core.md → security.md |
| **Add tracing/observability** | bootstrap.md |
| **Testing** | quality.md |
| **Idempotency** | idempotency.md (+ domain.md for error codes) |
| **Multi-tenant** | multi-tenant.md (+ bootstrap.md for context) |
| **Compliance check** | ALL modules |

---

## Module Index

| # | Module | Sections | Lines | Description |
|---|--------|----------|-------|-------------|
| 1 | [core.md](core.md) | §1-4 | ~225 | Version, lib-commons, Frameworks, Configuration |
| 2 | [bootstrap.md](bootstrap.md) | §5-6 | ~820 | Observability, Bootstrap initialization |
| 3 | [security.md](security.md) | §7-8 | ~530 | Access Manager, License Manager |
| 4 | [domain.md](domain.md) | §9-12 | ~255 | ToEntity/FromEntity, Error Codes, Error Handling, Functions |
| 5 | [api-patterns.md](api-patterns.md) | §13 | ~280 | Pagination Patterns (cursor and page-based) |
| 6 | [quality.md](quality.md) | §14-16 | ~245 | Testing, Logging, Linting |
| 7 | [architecture.md](architecture.md) | §17-19 | ~130 | Architecture Patterns, Directory Structure, Concurrency |
| 8 | [messaging.md](messaging.md) | §20 | ~220 | RabbitMQ Worker Pattern |
| 9 | [domain-modeling.md](domain-modeling.md) | §21 | ~170 | Always-Valid Domain Model |
| 10 | [idempotency.md](idempotency.md) | §22 | ~510 | Idempotency Patterns (Redis SetNX, hash fallback) |
| 11 | [multi-tenant.md](multi-tenant.md) | §23 | ~460 | Multi-Tenant Patterns (Pool Manager, JWT) |
| 12 | [compliance.md](compliance.md) | Meta | ~125 | Standards Compliance Output Format, Checklist |

---

## Section Index (Full)

### Core Foundation (core.md)

| # | Section | Anchor |
|---|---------|--------|
| 1 | Version | [#version](core.md#version) |
| 2 | Core Dependency: lib-commons (MANDATORY) | [#core-dependency-lib-commons-mandatory](core.md#core-dependency-lib-commons-mandatory) |
| 3 | Frameworks & Libraries | [#frameworks--libraries](core.md#frameworks--libraries) |
| 4 | Configuration | [#configuration](core.md#configuration) |

### Bootstrap & Observability (bootstrap.md)

| # | Section | Anchor |
|---|---------|--------|
| 5 | Observability | [#observability](bootstrap.md#observability) |
| 6 | Bootstrap | [#bootstrap](bootstrap.md#bootstrap) |

### Security (security.md)

| # | Section | Anchor |
|---|---------|--------|
| 7 | Access Manager Integration (MANDATORY) | [#access-manager-integration-mandatory](security.md#access-manager-integration-mandatory) |
| 8 | License Manager Integration (MANDATORY) | [#license-manager-integration-mandatory](security.md#license-manager-integration-mandatory) |

### Domain Patterns (domain.md)

| # | Section | Anchor |
|---|---------|--------|
| 9 | Data Transformation: ToEntity/FromEntity (MANDATORY) | [#data-transformation-toentityfromentity-mandatory](domain.md#data-transformation-toentityfromentity-mandatory) |
| 10 | Error Codes Convention (MANDATORY) | [#error-codes-convention-mandatory](domain.md#error-codes-convention-mandatory) |
| 11 | Error Handling | [#error-handling](domain.md#error-handling) |
| 12 | Function Design (MANDATORY) | [#function-design-mandatory](domain.md#function-design-mandatory) |

### API Patterns (api-patterns.md)

| # | Section | Anchor |
|---|---------|--------|
| 13 | Pagination Patterns | [#pagination-patterns](api-patterns.md#pagination-patterns) |

### Quality (quality.md)

| # | Section | Anchor |
|---|---------|--------|
| 14 | Testing | [#testing](quality.md#testing) |
| 15 | Logging | [#logging](quality.md#logging) |
| 16 | Linting | [#linting](quality.md#linting) |

### Architecture (architecture.md)

| # | Section | Anchor |
|---|---------|--------|
| 17 | Architecture Patterns | [#architecture-patterns](architecture.md#architecture-patterns) |
| 18 | Directory Structure | [#directory-structure](architecture.md#directory-structure) |
| 19 | Concurrency Patterns | [#concurrency-patterns](architecture.md#concurrency-patterns) |

### Messaging (messaging.md)

| # | Section | Anchor |
|---|---------|--------|
| 20 | RabbitMQ Worker Pattern | [#rabbitmq-worker-pattern](messaging.md#rabbitmq-worker-pattern) |

### Domain Modeling (domain-modeling.md)

| # | Section | Anchor |
|---|---------|--------|
| 21 | Always-Valid Domain Model (MANDATORY) | [#always-valid-domain-model-mandatory](domain-modeling.md#always-valid-domain-model-mandatory) |

### Idempotency (idempotency.md)

| # | Section | Anchor |
|---|---------|--------|
| 22 | Idempotency Patterns (MANDATORY for Transaction APIs) | [#idempotency-patterns-mandatory-for-transaction-apis](idempotency.md#idempotency-patterns-mandatory-for-transaction-apis) |

### Multi-Tenant (multi-tenant.md)

| # | Section | Anchor |
|---|---------|--------|
| 23 | Multi-Tenant Patterns (CONDITIONAL) | [#multi-tenant-patterns-conditional](multi-tenant.md#multi-tenant-patterns-conditional) |

---

## Dependency Graph

```
core.md (foundation - load first)
    │
    ├── bootstrap.md (depends on core.md)
    │   └── Initializes: Observability, Logger, Telemetry
    │
    ├── security.md (depends on core.md, bootstrap.md)
    │   └── Access Manager, License Manager
    │
    ├── domain.md (depends on core.md)
    │   └── ToEntity/FromEntity, Error Codes, Error Handling
    │
    ├── api-patterns.md (depends on domain.md)
    │   └── Pagination (uses error handling)
    │
    ├── quality.md (depends on core.md, bootstrap.md)
    │   └── Testing, Logging (uses telemetry context)
    │
    ├── architecture.md (depends on core.md)
    │   └── Hexagonal, Directory Structure, Concurrency
    │
    ├── messaging.md (depends on bootstrap.md, architecture.md)
    │   └── RabbitMQ (uses concurrency patterns)
    │
    ├── domain-modeling.md (depends on domain.md)
    │   └── Always-Valid Domain Model (uses error codes)
    │
    ├── idempotency.md (depends on domain.md, multi-tenant.md)
    │   └── Idempotency (uses error codes, tenant prefix)
    │
    └── multi-tenant.md (depends on bootstrap.md, security.md)
        └── Pool Manager, JWT extraction, Context injection
```

---

## WebFetch URLs

For agents loading standards via WebFetch:

| Module | URL |
|--------|-----|
| **index.md** | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/index.md` |
| core.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/core.md` |
| bootstrap.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/bootstrap.md` |
| security.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/security.md` |
| domain.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/domain.md` |
| api-patterns.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/api-patterns.md` |
| quality.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/quality.md` |
| architecture.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/architecture.md` |
| messaging.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/messaging.md` |
| domain-modeling.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/domain-modeling.md` |
| idempotency.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/idempotency.md` |
| multi-tenant.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md` |
| compliance.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/compliance.md` |

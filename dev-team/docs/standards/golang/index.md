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
| **Unit testing** | quality.md |
| **Integration testing** | testing-integration.md |
| **Idempotency** | idempotency.md (+ domain.md for error codes) |
| **Multi-tenant** | multi-tenant.md (+ bootstrap.md for context) |
| **Compliance check** | ALL modules |

---

## Module Index

| # | Module | Sections | Lines | Description |
|---|--------|----------|-------|-------------|
| 1 | [core.md](core.md) | §1-8 | ~1100 | Version, lib-commons, Frameworks, Configuration, DB Naming, Migrations, License, MongoDB |
| 2 | [bootstrap.md](bootstrap.md) | §5-8 | ~1050 | Observability, Bootstrap, Health Checks, Rate Limiting |
| 3 | [security.md](security.md) | §9-11 | ~700 | Access Manager, License Manager, Secret Redaction |
| 4 | [domain.md](domain.md) | §9-12 | ~255 | ToEntity/FromEntity, Error Codes, Error Handling, Functions |
| 5 | [api-patterns.md](api-patterns.md) | §13 | ~280 | Pagination Patterns (cursor and page-based) |
| 6 | [quality.md](quality.md) | §18-22 | ~1050 | Testing, Logging, Linting, Config Validation, Container Security |
| 7 | [architecture.md](architecture.md) | §23-27 | ~350 | Architecture, Directory, Concurrency, Goroutine Recovery, N+1 Detection |
| 8 | [messaging.md](messaging.md) | §20 | ~220 | RabbitMQ Worker Pattern |
| 9 | [domain-modeling.md](domain-modeling.md) | §21 | ~170 | Always-Valid Domain Model |
| 10 | [idempotency.md](idempotency.md) | §22 | ~510 | Idempotency Patterns (Redis SetNX, hash fallback) |
| 11 | [multi-tenant.md](multi-tenant.md) | §23 | ~460 | Multi-Tenant Patterns (Pool Manager, JWT) |
| 12 | [compliance.md](compliance.md) | Meta | ~125 | Standards Compliance Output Format, Checklist |
| 13 | [testing-integration.md](testing-integration.md) | INT-1-15 | ~600 | Integration Testing Patterns |

---

## Section Index (Full)

### Core Foundation (core.md)

| # | Section | Anchor |
|---|---------|--------|
| 1 | Version | [#version](core.md#version) |
| 2 | Core Dependency: lib-commons (MANDATORY) | [#core-dependency-lib-commons-mandatory](core.md#core-dependency-lib-commons-mandatory) |
| 3 | Frameworks & Libraries | [#frameworks--libraries](core.md#frameworks--libraries) |
| 4 | Configuration | [#configuration](core.md#configuration) |
| 5 | Database Naming Convention (snake_case) (MANDATORY) | [#database-naming-convention-snake-case-mandatory](core.md#database-naming-convention-snake-case-mandatory) |
| 6 | Database Migrations (MANDATORY) | [#database-migrations-mandatory](core.md#database-migrations-mandatory) |
| 7 | License Headers (CONDITIONAL) | [#license-headers-conditional](core.md#license-headers-conditional) |
| 8 | MongoDB Patterns (MANDATORY) | [#mongodb-patterns-mandatory](core.md#mongodb-patterns-mandatory) |

### Bootstrap & Observability (bootstrap.md)

| # | Section | Anchor |
|---|---------|--------|
| 5 | Observability | [#observability](bootstrap.md#observability) |
| 6 | Bootstrap | [#bootstrap](bootstrap.md#bootstrap) |
| 7 | Health Checks (MANDATORY) | [#health-checks-mandatory](bootstrap.md#health-checks-mandatory) |
| 8 | Rate Limiting (CONDITIONAL) | [#rate-limiting-conditional](bootstrap.md#rate-limiting-conditional) |

### Security (security.md)

| # | Section | Anchor |
|---|---------|--------|
| 9 | Access Manager Integration (MANDATORY) | [#access-manager-integration-mandatory](security.md#access-manager-integration-mandatory) |
| 10 | License Manager Integration (MANDATORY) | [#license-manager-integration-mandatory](security.md#license-manager-integration-mandatory) |
| 11 | Secret Redaction Patterns (MANDATORY) | [#secret-redaction-patterns-mandatory](security.md#secret-redaction-patterns-mandatory) |

### Domain Patterns (domain.md)

| # | Section | Anchor |
|---|---------|--------|
| 12 | Data Transformation: ToEntity/FromEntity (MANDATORY) | [#data-transformation-toentityfromentity-mandatory](domain.md#data-transformation-toentityfromentity-mandatory) |
| 13 | Error Codes Convention (MANDATORY) | [#error-codes-convention-mandatory](domain.md#error-codes-convention-mandatory) |
| 14 | Error Handling | [#error-handling](domain.md#error-handling) |
| 15 | Exit/Fatal Location Rules (MANDATORY) | [#exitfatal-location-rules-mandatory](domain.md#exitfatal-location-rules-mandatory) |
| 16 | Function Design (MANDATORY) | [#function-design-mandatory](domain.md#function-design-mandatory) |

### API Patterns (api-patterns.md)

| # | Section | Anchor |
|---|---------|--------|
| 17 | Pagination Patterns | [#pagination-patterns](api-patterns.md#pagination-patterns) |

### Quality (quality.md)

| # | Section | Anchor |
|---|---------|--------|
| 18 | Testing | [#testing](quality.md#testing) |
| 19 | Logging | [#logging](quality.md#logging) |
| 20 | Linting | [#linting](quality.md#linting) |
| 21 | Production Config Validation (MANDATORY) | [#production-config-validation-mandatory](quality.md#production-config-validation-mandatory) |
| 22 | Container Security (CONDITIONAL) | [#container-security-conditional](quality.md#container-security-conditional) |

### Architecture (architecture.md)

| # | Section | Anchor |
|---|---------|--------|
| 23 | Architecture Patterns | [#architecture-patterns](architecture.md#architecture-patterns) |
| 24 | Directory Structure | [#directory-structure](architecture.md#directory-structure) |
| 25 | Concurrency Patterns | [#concurrency-patterns](architecture.md#concurrency-patterns) |
| 26 | Goroutine Recovery Patterns (MANDATORY) | [#goroutine-recovery-patterns-mandatory](architecture.md#goroutine-recovery-patterns-mandatory) |
| 27 | N+1 Query Detection (MANDATORY) | [#n1-query-detection-mandatory](architecture.md#n1-query-detection-mandatory) |

### Messaging (messaging.md)

| # | Section | Anchor |
|---|---------|--------|
| 28 | RabbitMQ Worker Pattern | [#rabbitmq-worker-pattern](messaging.md#rabbitmq-worker-pattern) |

### Domain Modeling (domain-modeling.md)

| # | Section | Anchor |
|---|---------|--------|
| 29 | Always-Valid Domain Model (MANDATORY) | [#always-valid-domain-model-mandatory](domain-modeling.md#always-valid-domain-model-mandatory) |

### Idempotency (idempotency.md)

| # | Section | Anchor |
|---|---------|--------|
| 30 | Idempotency Patterns (MANDATORY for Transaction APIs) | [#idempotency-patterns-mandatory-for-transaction-apis](idempotency.md#idempotency-patterns-mandatory-for-transaction-apis) |

### Multi-Tenant (multi-tenant.md)

| # | Section | Anchor |
|---|---------|--------|
| 31 | Multi-Tenant Patterns (CONDITIONAL) | [#multi-tenant-patterns-conditional](multi-tenant.md#multi-tenant-patterns-conditional) |

### Integration Testing (testing-integration.md)

| # | Section | Anchor |
|---|---------|--------|
| INT-1 | Test Pyramid | [#test-pyramid](testing-integration.md#test-pyramid) |
| INT-2 | Decision Tree for Test Level | [#decision-tree-for-test-level](testing-integration.md#decision-tree-for-test-level) |
| INT-3 | File Naming Convention (MANDATORY) | [#file-naming-convention-mandatory](testing-integration.md#file-naming-convention-mandatory) |
| INT-4 | Function Naming Convention (MANDATORY) | [#function-naming-convention-mandatory](testing-integration.md#function-naming-convention-mandatory) |
| INT-5 | Build Tags (MANDATORY) | [#build-tags-mandatory](testing-integration.md#build-tags-mandatory) |
| INT-6 | Testcontainers Patterns (MANDATORY) | [#testcontainers-patterns-mandatory](testing-integration.md#testcontainers-patterns-mandatory) |
| INT-7 | Parallel Test Prohibition (MANDATORY) | [#parallel-test-prohibition-mandatory](testing-integration.md#parallel-test-prohibition-mandatory) |
| INT-8 | Fixture Centralization (MANDATORY) | [#fixture-centralization-mandatory](testing-integration.md#fixture-centralization-mandatory) |
| INT-9 | Stub Centralization (MANDATORY) | [#stub-centralization-mandatory](testing-integration.md#stub-centralization-mandatory) |
| INT-10 | Property-Based Testing | [#property-based-testing](testing-integration.md#property-based-testing) |
| INT-11 | Native Fuzz Testing | [#native-fuzz-testing](testing-integration.md#native-fuzz-testing) |
| INT-12 | Chaos Testing | [#chaos-testing](testing-integration.md#chaos-testing) |
| INT-13 | Logger Testing | [#logger-testing](testing-integration.md#logger-testing) |
| INT-14 | Guardrails (11 Anti-Patterns) (MANDATORY) | [#guardrails-11-anti-patterns-mandatory](testing-integration.md#guardrails-11-anti-patterns-mandatory) |
| INT-15 | Test Failure Analysis | [#test-failure-analysis-no-greenwashing](testing-integration.md#test-failure-analysis-no-greenwashing) |

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
    │   └── Unit Testing, Logging (uses telemetry context)
    │
    ├── testing-integration.md (depends on quality.md)
    │   └── Integration Testing (testcontainers, property-based, chaos)
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
| testing-integration.md | `https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/testing-integration.md` |

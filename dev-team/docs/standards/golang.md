# Go Standards

> **DEPRECATED - Moved to golang/**
>
> This file has been split into modular files for better performance and selective loading.

---

## New Location

**Directory:** `dev-team/docs/standards/golang/`

**Index:** [golang/index.md](golang/index.md)

---

## Module Structure

| Module | Sections | Description |
|--------|----------|-------------|
| [index.md](golang/index.md) | - | Master TOC and routing guide |
| [core.md](golang/core.md) | §1-4 | Version, lib-commons, Frameworks, Configuration |
| [bootstrap.md](golang/bootstrap.md) | §5-6 | Observability, Bootstrap |
| [security.md](golang/security.md) | §7-8 | Access Manager, License Manager |
| [domain.md](golang/domain.md) | §9-12 | ToEntity/FromEntity, Error Codes, Error Handling, Functions |
| [api-patterns.md](golang/api-patterns.md) | §13 | Pagination Patterns |
| [quality.md](golang/quality.md) | §14-16 | Testing, Logging, Linting |
| [architecture.md](golang/architecture.md) | §17-19 | Architecture Patterns, Directory Structure, Concurrency |
| [messaging.md](golang/messaging.md) | §20 | RabbitMQ Worker Pattern |
| [domain-modeling.md](golang/domain-modeling.md) | §21 | Always-Valid Domain Model |
| [idempotency.md](golang/idempotency.md) | §22 | Idempotency Patterns |
| [multi-tenant.md](golang/multi-tenant.md) | §23 | Multi-Tenant Patterns |
| [compliance.md](golang/compliance.md) | Meta | Standards Compliance Output Format, Checklist |

---

## Migration Guide

**For WebFetch:**
```
# Old (deprecated)
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang.md

# New (use this)
https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/index.md
```

**For selective loading:**
1. Fetch `golang/index.md` first
2. Use the "Which File for What" table to identify required modules
3. Fetch only the modules you need

---

## Deprecation Timeline

- **Current:** Redirect notice (this file)
- **Next release:** File will be removed

**Update your references to use `golang/index.md` and specific modules.**

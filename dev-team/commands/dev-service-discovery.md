---
name: ring:dev-service-discovery
description: Scan project and identify Service, Modules, and Resources for tenant-manager
---

Scan the current Go project and produce a visual report of the **Service → Module → Resource** hierarchy for tenant-manager registration.

## Usage

```
/ring:dev-service-discovery
```

No arguments needed. Runs in the current working directory.

## What It Does

1. **Detects the Service** — ApplicationName, type (product/plugin)
2. **Detects Modules** — via `WithModule()` calls or component structure
3. **Detects Resources per Module** — PostgreSQL, MongoDB, RabbitMQ (Redis excluded)
4. **Generates visual HTML report** — saves to `docs/service-discovery.html`

## Output

A visual HTML page with:
- Service overview card
- Module cards with resources
- Hierarchy diagram (Mermaid)
- Tenant-manager registration checklist

## Skill Reference

```yaml
Use Skill tool: ring:dev-service-discovery
```

The skill contains the complete detection logic and visual report generation.

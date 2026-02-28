# Multi-Tenant Analysis Checklist (MANDATORY)

**⛔ MULTI-TENANT ANALYSIS (MANDATORY):**

1. WebFetch multi-tenant.md (all languages): https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md
2. Check if service supports both single-tenant (`MULTI_TENANT_ENABLED=false`) and multi-tenant (`MULTI_TENANT_ENABLED=true`) modes
3. Verify backward compatibility: service MUST work without any `MULTI_TENANT_*` env vars
4. If multi-tenant code exists → verify TenantMiddleware, connection pooling, context propagation
5. If multi-tenant code is MISSING → ISSUE-XXX (CRITICAL): "Service does not support multi-tenant mode"

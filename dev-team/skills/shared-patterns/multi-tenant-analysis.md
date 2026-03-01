# Multi-Tenant Analysis Checklist (MANDATORY)

**⛔ MULTI-TENANT ANALYSIS (MANDATORY):**

See [multi-tenant.md § Canonical Model Compliance](../../docs/standards/golang/multi-tenant.md#hard-gate-canonical-model-compliance) for the canonical patterns and [multi-tenant.md § Canonical File Map](../../docs/standards/golang/multi-tenant.md#canonical-file-map) for valid file locations.

**Existence ≠ Compliance.** Code that has "some multi-tenant" but does not match the Ring canonical model is NON-COMPLIANT and MUST be flagged as a gap.

1. WebFetch multi-tenant.md: https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/golang/multi-tenant.md
2. **Detection:** Check if any multi-tenant code exists (`MULTI_TENANT_ENABLED`, `tenant-manager` in go.mod, `TenantMiddleware`)
3. **If multi-tenant code exists → run compliance audit:**
   - Config vars: MUST use the 7 canonical `MULTI_TENANT_*` names (not `TENANT_MANAGER_ADDRESS`, `TENANT_URL`, etc.)
   - Middleware: MUST use `tmmiddleware.NewTenantMiddleware` or `tmmiddleware.NewMultiPoolMiddleware` from lib-commons v3
   - Repositories: MUST use `core.ResolvePostgres`/`core.ResolveMongo`/`core.ResolveModuleDB` (not static connections)
   - Redis: MUST use `valkey.GetKeyFromContext` for every key operation
   - S3: MUST use `s3.GetObjectStorageKeyForTenant` for every object key
   - RabbitMQ: MUST use `tmrabbitmq.Manager` (Layer 1) + `X-Tenant-ID` header (Layer 2)
   - Circuit breaker: MUST have `client.WithCircuitBreaker` on Tenant Manager client
   - Backward compat: MUST have `TestMultiTenant_BackwardCompatibility` test
   - Non-canonical files: MUST NOT have custom tenant packages (`internal/tenant/`, `pkg/multitenancy/`, custom middleware). See [dev-multi-tenant SKILL.md § Phase 3](../dev-multi-tenant/SKILL.md#phase-3-non-canonical-file-detection-mandatory) for specific grep commands.
   - Each non-compliant item → ISSUE-XXX with severity based on impact
4. **If multi-tenant code is MISSING entirely** → ISSUE-XXX (CRITICAL): "Service does not support multi-tenant mode. MUST run ring:dev-multi-tenant."
5. **If non-compliant** → ISSUE-XXX per component: "Multi-tenant [component] is non-compliant. MUST be replaced with canonical lib-commons v3 pattern."
6. **Backward compatibility:** Service MUST work with `MULTI_TENANT_ENABLED=false` (default) and without any `MULTI_TENANT_*` env vars

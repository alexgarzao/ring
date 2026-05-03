### Standard Mode Dispatch (When Slicing Is NOT Active)

The following dispatch is used when `review_state.slicing.enabled == false` (unchanged from current flow):

**⛔ MANDATORY SCOPE HEADER — inject into every reviewer prompt below.**

When `scope == "task"` (the default, set by `ring:dev-cycle` orchestrator), the orchestrator MUST inject the following block into each of the 10 reviewer prompts, immediately after the `## Code Review Request` / `## Business Logic Review Request` / etc. header:

```markdown
**REVIEW SCOPE: TASK-LEVEL**
This review covers the CUMULATIVE diff of task {task_id}, which includes changes from
{N} subtasks: {subtask_ids}. Review the full task as an integrated unit; subtask
boundaries are implementation detail, not review boundaries.
```

Substitution: `{task_id}` = `task_id` input, `{N}` = `len(subtask_ids)`, `{subtask_ids}` = comma-separated `subtask_ids`. When `scope == "subtask"` (standalone/legacy), omit the block entirely.

Additionally, when `scope == "task"`, each reviewer prompt's `**Base SHA:**` and `**Head SHA:**` MUST be populated from `cumulative_diff_range.base_sha` and `cumulative_diff_range.head_sha` respectively.

```yaml
# Task 1: Code Reviewer
Task:
  subagent_type: "ring:code-reviewer"
  description: "Code review for [unit_id]"
  prompt: |
    ## Code Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]
    
    ## What Was Implemented
    [implementation_summary]
    
    ## Requirements
    [requirements]
    
    ## Files Changed
    [implementation_files or "Use git diff"]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:code-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:code-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Architecture and design patterns
    - Code quality and maintainability
    - Naming conventions
    - Error handling patterns
    - Performance concerns
    - **File size compliance** — Files > 1000 lines = MEDIUM+ (apply cohesion judgment). Files > 1500 lines = CRITICAL. Excludes auto-generated (*.pb.go, *.d.ts, */generated/*, */mocks/*). See shared-patterns/file-size-enforcement.md for cohesion judgment.

    ## ⛔ Ring Standards Verification (MANDATORY)

    **Standards slice for this reviewer** (orchestrator emits one `<standard>` per URL, filtered by detected language):

    Go:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/CLAUDE.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/_index.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/core.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/quality.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/domain.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/api-patterns.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/bootstrap.md

    TypeScript:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/CLAUDE.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/_index.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Check the changed code against ALL applicable sections.** Use the section index from `standards-coverage-table.md`.

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |

    ### Standards Compliance
    | Standard | Section | Status | Evidence |
    |----------|---------|--------|----------|
    | [module.md] | [section name] | ✅/❌ | [file:line or N/A] |

    ### What Was Done Well
    [positive observations]

# Task 2: Business Logic Reviewer
Task:
  subagent_type: "ring:business-logic-reviewer"
  description: "Business logic review for [unit_id]"
  prompt: |
    ## Business Logic Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]
    
    ## What Was Implemented
    [implementation_summary]
    
    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:business-logic-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:business-logic-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Domain correctness
    - Business rules implementation
    - Edge cases handling
    - Requirements coverage
    - Data validation

    ## ⛔ Ring Standards Verification (MANDATORY)

    **Standards slice for this reviewer** (orchestrator emits one `<standard>` per URL, filtered by detected language):

    Go:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/domain.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/domain-modeling.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/api-patterns.md

    TypeScript:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/_index.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Focus areas from these standards:** domain modeling invariants, aggregate boundaries, entity/value-object distinctions, API contract fidelity, request/response validation semantics.

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |

    ### Requirements Traceability
    | Requirement | Status | Evidence |
    |-------------|--------|----------|
    | [req] | ✅/❌ | [file:line] |

# Task 3: Security Reviewer
Task:
  subagent_type: "ring:security-reviewer"
  description: "Security review for [unit_id]"
  prompt: |
    ## Security Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:security-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:security-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Authentication and authorization
    - Input validation
    - SQL injection, XSS, CSRF
    - Sensitive data handling
    - OWASP Top 10 risks

    ## ⛔ Ring Security Standards Verification (MANDATORY)

    **Standards slice for this reviewer** (orchestrator emits one `<standard>` per URL, filtered by detected language):

    Go:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/security.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/multi-tenant.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/api-patterns.md

    TypeScript:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/_index.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/multi-tenant.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Check ALL applicable sections from standards-coverage-table.md → ring:backend-engineer-golang:**
    - #15 Access Manager Integration (if auth code changed)
    - #16 License Manager Integration (if licensed project)
    - #17 Secret Redaction Patterns (MANDATORY — credential leak prevention)
    - #18 SQL Safety (MANDATORY — parameterized queries, injection prevention)
    - #19 HTTP Security Headers (MANDATORY — X-Content-Type-Options, X-Frame-Options)
    - #51 Rate Limiting Three-Tier (MANDATORY — if API endpoints changed)
    - #52 CORS Configuration (MANDATORY — if middleware changed)
    
    **Also check from core.md:**
    - #8 MongoDB Injection Prevention (CRITICAL — if MongoDB code present)

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | OWASP Category | Recommendation |
    |----------|-------------|-----------|----------------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [A01-A10] | [fix] |

    ### Ring Security Standards Compliance
    | Standard Section | Status | Evidence |
    |-----------------|--------|----------|
    | Secret Redaction | ✅/❌/N/A | [file:line] |
    | SQL Safety | ✅/❌/N/A | [file:line] |
    | HTTP Security Headers | ✅/❌/N/A | [file:line] |
    | Rate Limiting | ✅/❌/N/A | [file:line] |
    | CORS Configuration | ✅/❌/N/A | [file:line] |
    | MongoDB Injection Prevention | ✅/❌/N/A | [file:line] |

    ### Security Checklist
    | Check | Status |
    |-------|--------|
    | Input validation | ✅/❌ |
    | Auth checks | ✅/❌ |
    | No hardcoded secrets | ✅/❌ |

# Task 4: Test Reviewer
Task:
  subagent_type: "ring:test-reviewer"
  description: "Test quality review for [unit_id]"
  prompt: |
    ## Test Quality Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:test-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:test-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Test coverage for business logic
    - Edge case testing (empty, null, boundary)
    - Error path coverage
    - Test independence and isolation
    - Assertion quality (not just "no error")
    - Test anti-patterns (testing mock behavior)

    ## ⛔ Ring Testing Standards Verification (MANDATORY)

    **Standards slice for this reviewer** (orchestrator emits one `<standard>` per URL, filtered by detected language):

    Go:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/quality.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/testing-fuzz.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/testing-property.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/testing-integration.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/testing-chaos.md

    TypeScript:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/_index.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Focus areas from these standards:** unit test coverage thresholds, fuzz corpus quality, property invariants, integration test isolation, chaos injection patterns.

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [fix] |

    ### Test Coverage Analysis
    | Test Type | Count | Coverage |
    |-----------|-------|----------|
    | Unit | [N] | [areas] |
    | Integration | [N] | [areas] |
    | E2E | [N] | [areas] |

# Task 5: Nil-Safety Reviewer
Task:
  subagent_type: "ring:nil-safety-reviewer"
  description: "Nil/null safety review for [unit_id]"
  prompt: |
    ## Nil-Safety Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]
    **Languages:** [Go|TypeScript|both - detect from files]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:nil-safety-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:nil-safety-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Nil/null pointer risks in changed code
    - Missing nil guards before dereference
    - Map access without ok check (Go)
    - Type assertions without ok check (Go)
    - Optional chaining misuse (TypeScript)
    - Error-then-use patterns

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [fix] |

    ### Nil Risk Trace
    [For each risk: Source → Propagation → Dereference point]

# Task 6: Consequences Reviewer
Task:
  subagent_type: "ring:consequences-reviewer"
  description: "Consequences review for [unit_id]"
  prompt: |
    ## Consequences Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:consequences-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:consequences-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Caller chain impact analysis
    - Consumer contract integrity
    - Shared state and configuration consequences
    - Type and interface propagation
    - Error handling chain consequences
    - Database/schema ripple effects

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [fix] |

    ### Impact Trace Analysis
    [For each changed symbol: callers found, consumers found, impact status]

# Task 7: Dead Code Reviewer
Task:
  subagent_type: "ring:dead-code-reviewer"
  description: "Dead code review for [unit_id]"
  prompt: |
    ## Dead Code Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:dead-code-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:dead-code-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Code that became orphaned/dead as a consequence of the changes
    - Ring 1: Dead code within the changed files
    - Ring 2: First-derivative dependents now orphaned (helpers, validators, converters)
    - Ring 3: Transitive cascade orphans (entire packages, utility chains)
    - Test infrastructure that only served removed code
    - Orphaned validation/security logic (CRITICAL in financial systems)

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [issue] | [location] | [fix] |

    ### Orphan Trace Analysis
    [For each orphan: What happened, caller count evidence, ring, cascade check]

# Task 8: Performance Reviewer
Task:
  subagent_type: "ring:performance-reviewer"
  description: "Performance review for [unit_id]"
  prompt: |
    ## Performance Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Files Changed
    [implementation_files or "Use git diff"]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:performance-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:performance-reviewer"]]
    [ELSE:]
    _No pre-analysis context available. Perform standard review based on git diff._

    ---

    ## Your Focus — Layer 1: Code-Level Performance
    - **Allocations in hot paths** — repeated heap allocations in request handlers, tight loops; missing sync.Pool usage
    - **Goroutine leaks** — missing context cancellation, unbounded `go func()` spawning, channels without consumers
    - **N+1 queries** — loop-based DB queries where a JOIN or batch query would suffice
    - **Event loop blocking** (TypeScript) — synchronous file I/O, CPU-heavy computation in main thread
    - **String concatenation in loops** — using `+` or `fmt.Sprintf` in loops instead of `strings.Builder`
    - **Connection pool sizing** — pool size vs expected concurrency mismatch
    - **GC pressure** — excessive small allocations creating GC churn in short-lived objects
    - **defer in tight loops** — deferred call stack growth inside loops
    - **reflect in hot paths** — `reflect` package usage in request handlers or frequently-called functions
    - **Missing b.Loop() in benchmarks** — Go 1.24+ requires `b.Loop()` instead of `for i := 0; i < b.N; i++`

    ## Your Focus — Layer 2: Runtime/Infrastructure
    - **GOMAXPROCS vs cgroup limits** — Go <1.25 reads host CPUs, not cgroup limits; must use `automaxprocs` or explicit setting
    - **GC tuning (GOGC, GOMEMLIMIT)** — memory-constrained pods without `GOMEMLIMIT` risk OOMKill before GC triggers
    - **CFS throttling** — high GOMAXPROCS + low CPU limit causes CFS throttling
    - **Container resource ratio** — `requests` vs `limits` spread >4x is suspicious
    - **Connection pool vs replica count** — total pool across replicas must not exceed DB `max_connections × 0.8`
    - **HPA alignment** — scaling metrics must match workload classification (I/O-bound vs CPU-bound)
    - **Workload classification** — verify resource strategy matches actual workload type

    ## ⛔ Ring Standards Verification (MANDATORY)

    **Standards slice for this reviewer** (orchestrator emits one `<standard>` per URL, filtered by detected language; Layer 2 URLs apply to both languages):

    Go (Layer 1 code-level):
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/architecture.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/core.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/golang/bootstrap.md

    TypeScript (Layer 1):
    - https://raw.githubusercontent.com/LerianStudio/ring/main/platforms/opencode/standards/typescript/_index.md

    Layer 2 runtime/infra (both languages):
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/docs/standards/sre.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Focus sections:** `architecture.md` (Performance Patterns, Concurrency Patterns, N+1 Query Detection, Goroutine Leak Detection); `core.md` (Dependency Management); `bootstrap.md` (Connection Management, Graceful Shutdown); `sre.md` (Health Checks, Observability).

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Performance Review Summary
    | Layer | Checks Run | Issues Found | Severity Breakdown |
    |-------|-----------|--------------|-------------------|
    | Code-Level | [N] | [N] | [critical/warning/info counts] |
    | Runtime/Infra | [N] | [N] | [critical/warning/info counts] |

    ### Issues Found
    | Severity | Check ID | Description | File:Line | Estimated Impact | Recommendation |
    |----------|----------|-------------|-----------|-----------------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW] | [G-1..G-13/T-1..T-7/P-1..P-5/R-1..R-8] | [issue] | [location] | [latency/throughput/memory impact] | [fix] |

    ### Standards Compliance
    | Standard | Section | Status | Evidence |
    |----------|---------|--------|----------|
    | [module.md] | [section name] | ✅/❌ | [file:line or N/A] |

    ### Recommended Actions
    [Prioritized list of performance improvements with estimated impact]

# Task 9: Multi-Tenant Reviewer
Task:
  subagent_type: "ring:multi-tenant-reviewer"
  description: "Multi-tenant review for [unit_id]"
  prompt: |
    ## Multi-Tenant Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Files Changed
    [implementation_files or "Use git diff"]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:multi-tenant-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:multi-tenant-reviewer"]]
    [ELSE:]
    _No pre-analysis context available - DEGRADED MODE. Perform standard review based on git diff._

    ---

    ## Your Focus
    - lib-commons/multitenancy contract compliance
    - tenantId extraction from JWT and propagation through handlers, services, data access
    - Database-per-tenant isolation (PostgreSQL, MongoDB) with mandatory tenant filtering
    - Event-driven tenant discovery
    - Tenant-scoped cache, queue, and event contexts
    - X-Tenant-ID header validation

    ## ⛔ Ring Standards Verification (MANDATORY)

    **Standards:** Loaded at runtime via WebFetch from:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/dev-multi-tenant/SKILL.md
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/using-lib-commons/SKILL.md (for multitenancy package)

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Scope exclusions (do NOT review):**
    - OWASP generic concerns → delegated to ring:security-reviewer
    - General code quality → delegated to ring:code-reviewer

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |

    ### Standards Compliance
    | Standard | Section | Status | Evidence |
    |----------|---------|--------|----------|
    | [module.md] | [section name] | ✅/❌ | [file:line or N/A] |

    ### What Was Done Well
    [positive observations]

# Task 10: lib-commons Reviewer
Task:
  subagent_type: "ring:lib-commons-reviewer"
  description: "lib-commons usage review for [unit_id]"
  prompt: |
    ## lib-commons Usage Review Request

    [INJECT REVIEW SCOPE: TASK-LEVEL block here when scope=task]

    **Unit ID:** [unit_id]
    **Base SHA:** [base_sha or cumulative_diff_range.base_sha when scope=task]
    **Head SHA:** [head_sha or cumulative_diff_range.head_sha when scope=task]

    ## What Was Implemented
    [implementation_summary]

    ## Requirements
    [requirements]

    ## Files Changed
    [implementation_files or "Use git diff"]

    ## Pre-Analysis Context

    **Static Analysis Results:**
    The following findings were automatically extracted by the pre-analysis pipeline.
    Use these to INFORM your review, not REPLACE your analysis.

    ---

    [IF preanalysis_state.context["ring:lib-commons-reviewer"] exists AND is not empty:]
    [INSERT the content of preanalysis_state.context["ring:lib-commons-reviewer"]]
    [ELSE:]
    _No pre-analysis context available - DEGRADED MODE. Perform standard review based on git diff._

    ---

    ## Your Focus
    - Correct usage of lib-commons API patterns across 35+ packages
    - Reinvented-wheel detection: manual implementations where lib-commons packages exist (resilience, database, observability, http, messaging, security, runtime)
    - Version consistency (lib-commons version across services)
    - Deprecated API usage

    ## ⛔ Ring Standards Verification (MANDATORY)

    **Standards:** Loaded at runtime via WebFetch from:
    - https://raw.githubusercontent.com/LerianStudio/ring/main/dev-team/skills/using-lib-commons/SKILL.md

    See [`shared-patterns/standards-cache-protocol.md`](../../../../dev-team/skills/shared-patterns/standards-cache-protocol.md) for the cache-first resolution protocol (cache hit / cache miss / standalone fallback) and the canonical `<standards>` block format.

    **Scope exclusions (do NOT review):**
    - lib-commons/multitenancy specifically → delegated to ring:multi-tenant-reviewer
    - General code quality → delegated to ring:code-reviewer

    **Include a Standards Compliance section in your output** listing which standards were verified and any violations found.

    ## Required Output
    ### VERDICT: PASS / FAIL

    ### Issues Found
    | Severity | Description | File:Line | Recommendation |
    |----------|-------------|-----------|----------------|
    | [CRITICAL/HIGH/MEDIUM/LOW/COSMETIC] | [issue] | [location] | [fix] |

    ### Standards Compliance
    | Standard | Section | Status | Evidence |
    |----------|---------|--------|----------|
    | [module.md] | [section name] | ✅/❌ | [file:line or N/A] |

    ### What Was Done Well
    [positive observations]
```


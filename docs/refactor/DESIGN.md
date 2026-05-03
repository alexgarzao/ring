# Prompt Quality Optimization — Design Document

## Problem

Ring's current context loading is monolithic. When a task needs rate limiting knowledge, the agent loads all 3,321 lines of Go standards. When qa-analyst runs unit tests, it carries 1,857 lines including chaos testing, fuzz testing, and goroutine leak detection modes it won't use.

This causes **context rot** — as token count increases, model attention per instruction decreases quadratically. The result: the model sees MORE rules but follows FEWER of them.

## Goal

Load **only what the task needs** into context. A rate limiting task loads ~100 lines of rate limiting standards, not 3,321 lines of everything. Unit testing loads unit testing instructions, not chaos testing.

**Expected outcome:** Higher adherence to loaded standards (more attention per instruction), lower token cost, faster execution.

## Architecture: Selective Context Loading

### 1. Modular Standards

**Before:** `platforms/opencode/standards/golang.md` (3,321 lines, 1 file)

**After:** `platforms/opencode/standards/golang/` (directory with ~20 focused modules + index)

```
platforms/opencode/standards/golang/
├── _index.md              # Topic manifest with descriptions (~60 lines)
├── version.md             # Go version requirements (~10 lines)
├── core-deps.md           # lib-commons v5, required imports (~60 lines)
├── frameworks.md          # Required packages and versions (~50 lines)
├── configuration.md       # Env vars, config structs (~150 lines)
├── observability.md       # OpenTelemetry, tracing, metrics (~530 lines)
├── bootstrap.md           # App initialization, staged startup (~380 lines)
├── auth.md                # Access Manager, OAuth2, JWT (~275 lines)
├── licensing.md           # License Manager integration (~245 lines)
├── data-transform.md      # ToEntity/FromEntity patterns (~60 lines)
├── error-handling.md      # Error codes, wrapping, checking (~110 lines)
├── function-design.md     # Single responsibility, examples (~85 lines)
├── pagination.md          # Cursor/offset patterns (~275 lines)
├── testing.md             # Table-driven, mocks, edge cases (~110 lines)
├── logging.md             # Structured logging, forbidden patterns (~110 lines)
├── linting.md             # golangci-lint config (~40 lines)
├── architecture.md        # Hexagonal, interfaces, directory structure (~120 lines)
├── concurrency.md         # Goroutines, channels, errgroup (~50 lines)
├── rabbitmq.md            # Worker pattern, producers, handlers (~240 lines)
├── safe-goroutines.md     # cruntime, panic recovery (~40 lines)
├── assertions.md          # cassert, domain validation (~40 lines)
├── metrics.md             # cmetrics typed metrics (~40 lines)
├── safe-math.md           # commons/safe financial calculations (~20 lines)
├── crypto.md              # AES-GCM, HMAC-SHA256 (~20 lines)
├── backoff.md             # Exponential backoff with jitter (~20 lines)
├── circuit-breaker.md     # sony/gobreaker, health checker (~110 lines)
├── outbox.md              # Reliable event publishing (~20 lines)
└── compliance-format.md   # Standards compliance output format (~95 lines)
```

### 2. The Index File (`_index.md`)

The index is the **only file always loaded**. It's a lightweight manifest that lets the agent (or pre-router) decide what to fetch:

```markdown
# Go Standards Index

| Module | Keywords | When to Load |
|--------|----------|-------------|
| core-deps.md | lib-commons, imports, v5 | Always (foundation) |
| observability.md | tracing, metrics, spans, otel | Instrumentation, new service methods |
| bootstrap.md | main.go, service.go, config.go, startup | New projects, initialization |
| auth.md | JWT, OAuth2, Access Manager, middleware | Auth routes, protected endpoints |
| pagination.md | cursor, offset, page, limit | List endpoints, collection APIs |
| testing.md | table-driven, mock, coverage | Writing/reviewing tests |
| error-handling.md | error codes, wrapping, domain errors | Error handling, new endpoints |
| rabbitmq.md | worker, queue, consumer, producer | Async processing, message queues |
| circuit-breaker.md | breaker, retry, external calls | External service integration |
| ...etc |
```

### 3. Selective Loading Mechanism

Two approaches (can coexist):

#### A. Agent Self-Selection (Simple)

The agent reads `_index.md`, analyzes the task, and loads only matching modules:

```
1. Read _index.md (always loaded, ~60 lines)
2. Match task keywords against module keywords
3. WebFetch/Read only matching modules
4. Proceed with focused context
```

**Pros:** Simple, no extra infrastructure. Agent intelligence does the routing.
**Cons:** Agent might over-fetch or under-fetch.

#### B. Orchestrator Pre-Selection (Robust)

The orchestrator (dev-cycle, codereview skill) determines which standards modules are needed before dispatching the agent:

```
1. Orchestrator analyzes task description + files changed
2. Maps to relevant standard modules
3. Fetches and injects only those modules in the dispatch prompt
4. Agent receives pre-filtered context
```

**Pros:** More reliable, agent starts with exactly what it needs.
**Cons:** Requires orchestrator changes. Adds a planning step.

#### Recommended: Hybrid

- Orchestrator does coarse pre-selection (loads ~3-5 modules based on task type)
- Agent can load additional modules from index if needed during execution
- Standards Loading section in agents becomes: "Read _index.md. If orchestrator provided <standards>, use them. If you need additional standards not provided, load from index."

### 4. Modular Agents

Same principle applied to agents:

**Before:** `qa-analyst.md` (1,857 lines, 6 testing modes)

**After:**
```
agents/
├── qa-analyst.md              # Core persona + shared logic (~250 lines)
├── qa-analyst-unit.md         # Unit testing specifics (~200 lines)
├── qa-analyst-fuzz.md         # Fuzz testing specifics (~150 lines)
├── qa-analyst-property.md     # Property testing specifics (~150 lines)
├── qa-analyst-integration.md  # Integration testing specifics (~200 lines)
├── qa-analyst-chaos.md        # Chaos testing specifics (~150 lines)
└── qa-analyst-goroutine.md    # Goroutine leak detection (~100 lines)
```

The orchestrator dispatches the right variant:
- Gate 3: `Task(agent="ring:qa-analyst-unit", ...)`
- Gate 4: `Task(agent="ring:qa-analyst-fuzz", ...)`

Each variant loads ONLY its mode-specific instructions + core.

### 5. Modular Skills

**Before:** `dev-cycle/SKILL.md` (3,720 lines, all 10 gates)

**After:**
```
dev-cycle/
├── SKILL.md                # Core orchestration logic, state machine (~500 lines)
├── gates/
│   ├── gate-0-implementation.md
│   ├── gate-1-devops.md
│   ├── gate-2-sre.md
│   ├── gate-3-unit-testing.md
│   ├── ...
│   └── gate-9-validation.md
└── shared/
    ├── state-management.md
    └── standards-loading.md    # Single source of truth
```

The orchestrator loads `SKILL.md` (lean) + the current gate file. Not all gates at once.

### 6. Shared Patterns — Single Source

**Before:** Standards Loading protocol duplicated in 24 agents.

**After:** `shared/standards-loading.md` referenced by all agents:
```markdown
## Standards Loading
For the standards loading protocol, read @shared/standards-loading.md
```

Same for anti-rationalization — one file, referenced where needed, not copy-pasted into every agent.

## Refactor Sequence

### Phase 1: Standards Modularization (POC)
1. Split `golang.md` into modular files + `_index.md`
2. Update `backend-engineer-golang` to use selective loading
3. A/B test: same task, original vs modular — compare adherence

### Phase 2: Agent Modularization
4. Split `qa-analyst` into mode-specific variants
5. Refactor `backend-engineer-golang` — core + lazy extensions
6. Extract shared patterns (standards-loading, anti-rationalization)

### Phase 3: Skill Modularization
7. Split `dev-cycle` into core + gate files
8. Split `codereview` — core dispatch + reviewer-specific context
9. Lean down `production-readiness-audit` (acknowledged 6,907-line problem)

### Phase 4: Apply to Remaining
10. Apply pattern to all dev-team agents
11. Apply to pm-team, finops-team
12. Apply to remaining skills
13. Update typescript.md, frontend.md, devops.md, sre.md standards

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Avg agent context (lines) | ~1,200 | ~300 |
| Standards loaded per task (lines) | ~3,300 | ~200-500 |
| Skill orchestrator size (lines) | ~3,700 | ~500 |
| Total context per gate execution | ~9,500 lines | ~1,500 lines |
| Standards adherence (measured via review pass rate) | baseline | ≥ baseline |

## Risks

1. **Under-fetching:** Agent loads too few standards, misses a requirement
   - Mitigation: `_index.md` always available, agent can load more on demand
   - Mitigation: `core-deps.md` always loaded (foundation)

2. **Routing errors:** Orchestrator picks wrong modules
   - Mitigation: Keyword matching + agent can supplement from index
   - Mitigation: Phase 1 validates with A/B testing before scaling

3. **Fragmentation:** Too many small files become hard to maintain
   - Mitigation: Modules follow natural section boundaries (already exist in current file)
   - Mitigation: Index file serves as single navigation point

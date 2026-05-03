# Comparison: backend-engineer-golang v1 vs v2

## Numbers

| Metric | v1 (current) | v2 (refactored) | Delta |
|--------|-------------|-----------------|-------|
| Total lines | 1,230 | 226 | -82% |
| Frontmatter | 75 lines | 5 lines | -93% |
| Anti-rationalization tables | 55 lines across 6 tables | 0 (replaced by examples) | -100% |
| Pressure resistance table | 20 lines | 0 (consolidated into blockers) | -100% |
| Duplicated standards content | ~200 lines (FORBIDDEN patterns, instrumentation template, bootstrap check) | 0 (referenced from modular standards) | -100% |
| Concrete examples | 1 (output format) | 4 (standards loading ×2, instrumentation pattern, output format) | +300% |
| Standards loading instructions | ~120 lines | ~40 lines with 2 examples | -67% |

## What Was Removed and Why

### 1. Frontmatter output_schema (70 lines → 0)
**Why:** The YAML output_schema with regex patterns, conditional sections, and metrics is tooling metadata. If OpenCode doesn't programmatically validate agent output against this schema at runtime, it's pure token waste. The model follows the example output instead.

**Risk:** If there IS tooling that validates output_schema → keep it but in a separate metadata file.

### 2. "When to Use This Agent" capability lists (115 lines → 7 lines)
**Why:** A detailed taxonomy of 10 capability domains (API Dev, Auth, Business Logic, Data Layer, Multi-Tenancy, Event-Driven, Workers, Testing, Performance, Serverless) doesn't help the model write better code. The orchestrator already decided to use this agent. The model needs to know HOW to implement, not a catalog of WHAT it can implement.

**Replaced with:** 7-line "Core Responsibilities" that establishes identity and constraints.

### 3. Anti-Rationalization Tables (55 lines across 6 tables → 0)
**Why:** Anthropic's research shows positive examples outperform prohibitions. "Don't use fmt.Println" × 5 different phrasings across 3 tables consumes tokens repeating the same concept. One code example showing the correct pattern (clog from lib-commons) is more effective.

**Replaced with:** The instrumentation code example shows the correct pattern once. The forbidden patterns section is a concise list (4 bullets) instead of a table with "Why It's WRONG" and "Required Action" columns that repeat the same idea.

### 4. Duplicated Standards Content (~200 lines → 0)
**Why:** The FORBIDDEN Patterns Check section duplicates what's already in golang/logging.md and golang/observability.md. The MANDATORY Instrumentation section duplicates golang/observability.md. The Bootstrap Pattern Check duplicates golang/bootstrap.md.

**Replaced with:** Selective loading from modular standards. The agent loads only the relevant modules and gets the actual standards content from source-of-truth files rather than duplicated excerpts.

### 5. Standards Loading Protocol (120 lines → 40 lines)
**Why:** The v1 protocol had: a <cannot_skip> block, a HARD GATE section, an anti-rationalization table, a WebFetch strategy table, a conditional loading table, and multiple warnings about cherry-picking. The same concept ("load standards before coding") was repeated 5 different ways.

**Replaced with:** Clear 2-step process (load index → match task to modules) with 2 concrete examples showing exactly which modules to load for different task types. The examples teach the pattern better than the tables.

### 6. Standards Compliance Report (120 lines → 5 lines)
**Why:** This section is only needed when invoked from `ring:dev-refactor` with `**MODE: ANALYSIS only**`. That's a specific orchestration context, not the default. Loading 120 lines about compliance reporting for every feature implementation task wastes attention.

**Replaced with:** 5-line reference to the shared-patterns file, loaded on demand when the mode triggers.

### 7. Pressure Resistance Table (20 lines → 0)
**Why:** "User says 'skip tests'" → "Your response: 'Tests are mandatory'" is theater. The model doesn't face social pressure from users in a subagent context — it's dispatched by an orchestrator skill. The Blockers section handles genuine decision points.

### 8. Self-Check Section (100 lines → 4 lines)
**Why:** "No TODO comments (searched: 0 found)" template output is busywork that doesn't improve code quality. The model either writes clean code or it doesn't — a mandatory self-check template doesn't change that.

**Replaced with:** `goimports` + `golangci-lint` commands (actual automated validation) kept. The rest folded into general quality expectations set by loaded standards.

## What Was Kept

1. **Instrumentation pattern** — the Go code example showing the correct tracing pattern. This is the highest-value content.
2. **Standards loading with selective modules** — improved with concrete examples.
3. **Blockers / STOP conditions** — architectural decisions the agent must not make.
4. **TDD flow** — RED/GREEN with required output format.
5. **Post-implementation validation** — goimports + golangci-lint.
6. **Complete output example** — expanded with more detail.

## What Was Added

1. **Two standards loading examples** — showing exact module selection for different task types.
2. **"When Code Is Already Compliant" section** — prevents unnecessary refactoring.
3. **Scope boundary** — what this agent handles vs what to delegate.

## Expected Impact

| Dimension | Prediction | Reasoning |
|-----------|-----------|-----------|
| **Standards adherence** | ↑ Higher | Fewer instructions with more attention per instruction. Model processes 226 lines instead of 1,230. Each rule gets ~5× more attention weight. |
| **Instrumentation quality** | = Same or ↑ | The code example is preserved (highest-signal content). Removing duplicated text about instrumentation doesn't remove the pattern. |
| **FORBIDDEN pattern violations** | = Same or ↑ | Concise 4-bullet list is easier to internalize than 55 lines of tables. The forbidden patterns are also in the standards modules the agent loads. |
| **Token cost** | ↓ 80%+ | 226 lines × ~40 chars/line × 0.25 tokens/char ≈ 2,260 tokens vs ~12,300 tokens for v1. |
| **Selective loading quality** | ↑ Higher | Agent loads ~200-500 lines of relevant standards instead of 3,321 lines of everything. Attention budget focused on task-relevant knowledge. |

## How to Validate

Run the same implementation task with both v1 and v2:

**Suggested test task:** "Add cursor-based pagination to the GET /accounts endpoint following Ring standards."

**Measure:**
1. Does the agent load only pagination + core standards (v2) vs everything (v1)?
2. Does the output follow the correct pagination pattern from standards?
3. Does it include proper instrumentation?
4. Does it produce clean golangci-lint output?
5. Count: how many standards violations in each output?

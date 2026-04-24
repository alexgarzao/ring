---
name: ring:dev-simplify
description: |
  Whole-codebase structural simplification sweep. Dispatches parallel explorers
  to identify adapters, shims, single-implementation interfaces, translation-free
  layers, and speculative abstractions that exist only to accommodate constraints,
  legacy decisions, or hypothetical future needs. Applies dead-code Three-Rings
  cascade analysis across the live codebase (not a diff). Produces a KILL /
  REVIEW / KEEP classification with an inverted burden of proof — every
  abstraction must justify itself or be removed. Optimized for pre-public
  applications where refactor cost is low and a single hard constraint (public
  API contract) gates all decisions.

trigger: |
  - User asks to simplify, flatten, or audit architecture of a whole codebase
  - User mentions "too much indirection", "kill shims", "unnecessary abstractions"
  - Pre-public application where break-compatibility refactor is cheap
  - Post-pivot cleanup: speculative scaffolding accumulated during exploration
  - Stop-the-world structural audit before v1 release or public announcement

skip_when: |
  - Diff review on a feature branch → use ring:codereview
  - Standards-conformance refactor (golang.md / typescript.md) → use ring:dev-refactor
  - Dead code introduced by a specific change → use ring:dead-code-reviewer in ring:codereview
  - 44-dimension production readiness → use ring:production-readiness-audit
  - Application already has external clients depending on internals — the public-API
    constraint expands beyond what this skill tracks; hand-audit first

NOT_skip_when: |
  - "Codebase looks clean" → Clean code can still be over-abstracted. Run anyway.
  - "Only a small refactor" → Small targets are where speculative scaffolding hides.
  - "Recent dev-refactor pass" → Standards conformance ≠ structural simplification.

related:
  similar:
    - ring:dev-refactor
    - ring:production-readiness-audit
  complementary:
    - ring:codereview
    - ring:codebase-explorer
    - ring:dead-code-reviewer

input_schema:
  optional:
    - name: hard_constraint
      type: string
      description: |
        The one interface the refactor MUST NOT break. Default: "public API —
        HTTP routes, SDK surface, webhooks, event contracts consumed by external
        clients". Override when the load-bearing surface is different (e.g.,
        "database schemas", "event log format", "gRPC service definitions").
    - name: scope
      type: string
      enum: [whole_codebase, module]
      default: whole_codebase
      description: |
        Scanning scope. `whole_codebase` is the default. `module` scopes the
        sweep to a single top-level package/module — useful for very large
        repos where whole-codebase dispatch dilutes reviewer focus.
    - name: module_path
      type: string
      description: Required when scope=module. Path to the module to audit.
    - name: output_path
      type: string
      default: docs/dev-simplify/simplify-report-{timestamp}.md
      description: Where to write the consolidated KILL/REVIEW/KEEP report.
    - name: tasks_output_path
      type: string
      default: docs/dev-simplify/simplify-tasks-{timestamp}.json
      description: |
        Where to write the ring:dev-cycle-compatible task JSON. MUST sit alongside
        the markdown report — same timestamp, parallel directory.

output_schema:
  format: markdown+json
  required_sections:
    - name: "Simplify Summary"
      pattern: "^## Simplify Summary"
      required: true
    - name: "Hard Constraint"
      pattern: "^## Hard Constraint"
      required: true
    - name: "Kill List"
      pattern: "^## Kill List"
      required: true
    - name: "Review List"
      pattern: "^## Review List"
      required: true
    - name: "Keep List"
      pattern: "^## Keep List"
      required: true
    - name: "Cascade Chains"
      pattern: "^## Cascade Chains"
      required: true
    - name: "Cascade Execution Plan"
      pattern: "^## Cascade Execution Plan"
      required: true
    - name: "Remaining Risks"
      pattern: "^## Remaining Risks"
      required: true
  required_artifacts:
    - path: "{output_path}"
      format: markdown
    - path: "{tasks_output_path}"
      format: json
      description: ring:dev-cycle task array — see "Task JSON Schema" section
---

# Dev Simplify — Whole-Codebase Structural Sweep

## Overview

Pre-public applications accumulate speculative abstractions: single-implementation
interfaces built "for flexibility", adapters that translate nothing, shims added
to preserve a pattern, factories that construct one thing. This skill finds them
and proposes a kill list with an inverted burden of proof — the abstraction must
earn its keep, not the other way around.

**Core principle:** DELETE is the default verdict. An abstraction survives only
by presenting concrete evidence of the swap it enables. "Might need it later",
"it's the pattern", and "makes testing easier" (without a test that actually
differs) all FAIL the test.

**Not a gate.** This is a standalone diagnostic. Output is a classified report,
not a refactor execution. To execute, feed the KILL LIST into `ring:dev-cycle`
as tasks.

---

## When to Use This Skill vs Neighbors

| Skill | Scope | What it detects | When |
|---|---|---|---|
| `ring:dev-simplify` | whole codebase | Unjustified indirection, speculative abstraction | Pre-public cleanup, architectural audit |
| `ring:dev-refactor` | whole codebase | Standards-conformance gaps (golang.md / typescript.md) | Align codebase to Ring standards |
| `ring:codereview` | diff | Quality of a specific change | After implementation, before merge |
| `ring:dead-code-reviewer` | diff | Code orphaned BY a change | Part of codereview pool |
| `ring:production-readiness-audit` | whole codebase | 44 production dimensions (security, ops, quality) | Pre-production gate |

`ring:dev-refactor` asks "does it match our standards?"
`ring:dev-simplify` asks "does it need to exist at all?"

---

## Hard Constraint (The Only One)

By default: **public APIs MUST NOT break.** HTTP routes, published SDK surface,
webhooks, event contracts consumed by external clients, database schemas exposed
through replication, CLI flags in released binaries — anything a client outside
this repository depends on.

Everything behind that surface is fair game, including wire-internal DTOs that
are not part of the published contract.

**Override via `hard_constraint` input** when the load-bearing surface is
different. Examples:

| Application type | Typical hard constraint |
|---|---|
| Pre-public web service | Public HTTP routes |
| SDK / library | Published package API surface |
| Event-driven system | Event contract (topic + schema) |
| Financial ledger | Database schema + double-entry invariants |
| CLI tool | Released command-line flags |

The hard constraint is the ONLY thing the sweep treats as untouchable. All
other indirection is under review.

---

## Dispatch Protocol

Dispatch six explorer agents in **parallel** (single message, 6 Task calls —
or 5 if the branch has no commits ahead of main, skipping Task 5). Each
explorer handles one cluster of abstraction smells. Results are aggregated
into a single consolidated report.

### Task 1a — Unexercised Seam Hunter

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Hunt single-impl interfaces, ports, and repositories without swap pressure"
  prompt: |
    ## Abstraction Hunt — Cluster 1a: Unexercised Seams

    Scan this entire codebase (committed + dirty working tree) for declared
    extension points — "seams" — where the swap the seam promises is not
    actually exercised. A seam without swap pressure is scaffolding, not
    architecture. Default verdict is DELETE.

    ### Smells to find
    | Smell | Signal |
    |---|---|
    | Single-implementation interface | Interface type with exactly one concrete impl; test doubles (if any) are identical to prod impl |
    | Hexagonal port with one adapter | Ports-and-adapters scaffolding where no second adapter exists or is planned |
    | Repository over a single SQL backend | Repository pattern with no alternate store, no swap test |

    ### Detection heuristic
    Declared seams look identical whether exercised or not. The exercise test:
    - Is there a second implementation in the repo, in a feature branch, or in an ADR?
    - Is there a test that uses a divergent double (not an identical fake)?
    - Is there commit history of swapping the impl?
    All three "no" ⇒ the seam is declarative only.

    ### For each finding
    Report: name, file:line of the interface/port/repository declaration,
    smell category, the seam's self-justification (if any — read comments,
    docs, ADRs), rebuttal given pre-public state, blast radius (files/packages
    affected by collapse), public-API impact (none/indirect/at-boundary),
    recommended action (delete / collapse-into-caller / inline-to-single-consumer).

    ### Evidence requirement
    Every finding MUST include: (a) exact file:line of the declaration,
    (b) grep-counted impls AND call sites, (c) evidence the swap is hypothetical
    (no second impl, no swap test, no ADR justifying the seam).

    ### Output
    Markdown table per smell category. Plus a "potentially justified" sub-list
    for seams with suggestive evidence of real swappability — these feed the
    KEEP list in the final report.

    Public API constraint: {hard_constraint}. Do not propose changes that affect it.
```

### Task 1b — Speculative Construction & Dispatch Hunter

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Hunt speculative factories, builders, strategies, and facades"
  prompt: |
    ## Abstraction Hunt — Cluster 1b: Speculative Construction & Dispatch

    Scan this entire codebase (committed + dirty working tree) for construction
    and dispatch patterns where the variation the pattern exists to handle does
    not actually occur. These are different from seams (1a) — the concern is
    not swappable implementations but over-engineered control flow.
    Default verdict is DELETE or COLLAPSE.

    ### Smells to find
    | Smell | Signal |
    |---|---|
    | Speculative factory | Factory function/class that always constructs the same concrete type |
    | Speculative builder | Builder pattern where all callers set the same fields in the same order |
    | One-strategy strategy | Strategy pattern dispatching over an enum with one non-trivial case |
    | One-consumer facade | Facade/aggregator with a single call site |

    ### Detection heuristic
    A construction/dispatch pattern is suspect when variation collapses:
    - Factory: all call sites pass identical (or no) arguments and receive the same type
    - Builder: all call sites chain the same methods in the same order
    - Strategy: the dispatch-over-enum has only one non-trivial branch
    - Facade: grep shows exactly one caller

    ### For each finding
    Report: name, file:line, smell category, self-justification (if any),
    rebuttal, blast radius, public-API impact, recommended action
    (delete / collapse-into-caller / inline-callers).

    ### Evidence requirement
    Every finding MUST include: (a) exact file:line, (b) caller count via grep,
    (c) evidence variation does not occur — identical call sites, single case,
    single consumer.

    ### Output
    Markdown table per smell category. Plus a "potentially justified" sub-list
    for constructors/dispatch sites with suggestive evidence of real variation
    needs.

    Public API constraint: {hard_constraint}. Do not propose changes that affect it.
```

### Task 2 — Translation-Layer Hunter

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Hunt translation-free layers and identity adapters"
  prompt: |
    ## Abstraction Hunt — Cluster 2: Translation Layers

    Scan this entire codebase for layers whose ONLY job is type translation
    between essentially identical shapes. Default verdict is DELETE.

    ### Smells to find
    | Smell | Signal |
    |---|---|
    | Translation-free adapter | Converts A to B where B is a renamed A, 1:1 field mapping, no semantic translation |
    | Pass-through shim | Wraps a call site-for-site, adds no cross-cutting concern (no logging, no auth, no retry) |
    | Internal DTO ↔ domain entity with 1:1 fields | Translation across identical shapes within the same process |
    | Config seam over a constant | Indirection layer for a value that never varies |
    | Feature flag for one value | Flag with only one branch ever taken |

    ### Detection heuristics
    - Adapter is suspect if every field in source maps to a same-named field in
      target with no transform
    - Shim is suspect if it's a one-line method body calling its parameter
    - DTO translation is suspect if source and target have identical field sets
      with identical types

    ### For each finding
    Report: name, file:line, smell category, self-justification, rebuttal,
    blast radius, public-API impact (none/indirect/at-boundary),
    recommended action.

    ### Special note on at-boundary translations
    If a translation exists between the public API DTO and an internal entity,
    that translation may be load-bearing for the public contract. Flag
    public-API impact as `at-boundary` and recommend REVIEW, not DELETE.

    Public API constraint: {hard_constraint}. Do not propose changes that affect it.
```

### Task 3 — Architecture Topology Mapper

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Map module topology and indirection depth"
  prompt: |
    ## Architecture Map — Cluster 3: Topology

    Produce a structural map of this codebase focused on identifying
    indirection depth and accommodation layers.

    ### Output required
    1. **Module list** — top-level packages/modules with line counts
    2. **Dependency graph** — which modules import which (depth-1)
    3. **Indirection depth per request path** — for each public API entry point,
       trace to terminal handler and count layers (handler → service → domain →
       repository → driver). Flag paths with >4 layers where no layer adds
       observable behavior
    4. **Interface-to-impl ratio per module** — module with many interfaces and
       few implementations is suspect
    5. **Accommodation clusters** — groups of files that appear to exist
       primarily to bridge other files (not to deliver functionality)

    ### Flag as suspicious
    | Pattern | Why suspicious |
    |---|---|
    | Module with >3 interfaces, 0 alternate impls | Speculative seam cluster |
    | Request path with handler → service → usecase → service → repo (5+ hops) | Indirection without semantic content at each hop |
    | Package named `adapters/`, `ports/`, `shims/`, `compat/` | Lexical flags for accommodation-by-construction |
    | Two modules with identical public surface | Candidate for merge |

    ### Output format
    Structured markdown. Include a "simplification pressure" score per module
    (0-10) — high means ripe for collapse, low means earned its structure.

    Public API constraint: {hard_constraint}. Note where the public surface
    actually lives in the topology; everything else is in-scope for reshaping.
```

### Task 4 — Cascade Detector (Three Rings Applied to Codebase)

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Trace cascade chains where collapsing one abstraction collapses many"
  prompt: |
    ## Cascade Detection — Three Rings Applied to Whole Codebase

    The Three Rings model from ring:dead-code-reviewer, reframed from "code
    orphaned by a diff" to "code sustained only by other suspect code".

    ### Goal
    Find cascade chains: abstraction A exists, B exists only to serve A,
    C exists only to serve B. If A falls, the whole chain falls. A single
    kill operation can eliminate many files.

    ### Method
    1. Start from leaf abstractions in the codebase (deepest packages, innermost
       interfaces)
    2. For each leaf: count callers. Identify callers that ONLY call this leaf
       (no other production use)
    3. If such callers exist, they are Ring 2 — they exist to serve the leaf
    4. Recurse: what calls the Ring 2 caller? If its only purpose is to call
       Ring 2, it's Ring 3
    5. When the chain terminates at a real consumer (handler, test, public API),
       the chain is sustained by that consumer. When the chain terminates in
       more Ring N code, the whole chain is speculative

    ### Output per chain
    MUST emit each chain as an ordered list, leaf first (Ring 1), so the
    aggregator can decompose it into a task DAG. Ring N depends on Ring N-1.

    ```
    Chain ID: cascade-{N} (sequential, 1-indexed)
    Ring 1 (leaf):  [leaf_abstraction] @ file:line
    Ring 2:         [caller] @ file:line — serves only Ring 1
    Ring 3:         [grandcaller] @ file:line — serves only Ring 2
    ...
    Terminal: [consumer] — [REAL | SPECULATIVE]
      If SPECULATIVE: collapse blast radius = [N files, M lines]
      If REAL: chain is sustained; flag weakest link for review
    ```

    MUST number rings starting at 1 (leaf = Ring 1). MUST list rings in
    execution order — the order in which a refactor would remove them
    (leaf first, then each caller in turn).

    ### Evidence requirement
    Every Ring assignment MUST include grep-based caller count. "Probably only
    called by X" is not evidence. Count and cite.

    Public API constraint: {hard_constraint}. Handlers/endpoints serving the
    public API are REAL terminals; chains ending there are sustained.
```

### Task 5 — Branch AI Slop Hunter (Diff vs Main)

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Hunt AI-generated residue introduced in branch diff vs main"
  prompt: |
    ## AI Slop Hunt — Cluster 5: Branch Diff vs Main

    Scan `git diff main...HEAD` for AI-generated residue — code that a human
    author writing the same change would not produce. The baseline is
    literally main; every added line has an exact counterfactual. Default
    verdict is DELETE (or revert-to-main-style).

    ### Smells to find
    | Smell | Signal |
    |---|---|
    | Narrating comment | Comment restates what the next line literally does; adds no WHY. Surrounding file has few/no comments of this density |
    | Inconsistent comment density | Added block annotates steps with line-by-line comments in a file that otherwise uses none |
    | Defensive check in trusted path | try/catch, nil guard, or input validation added where the caller is already validated (controller/service boundary already ran the check) |
    | Redundant error wrapping | Wrapping an error that already carries full context, producing `"fetch failed: fetch failed: <root>"` |
    | `any` / `unknown` / `interface{}` escape hatch | Cast used to bypass a type mismatch the AI could not resolve, not because the value is genuinely untyped |
    | Style inconsistency with file | Naming, formatting, idiom, import ordering, or error-handling pattern diverges from the surrounding file's existing convention |
    | Speculative error branch | Error handling for a case the upstream code already excludes (e.g., checking for nil on a value just constructed with `new`) |

    ### For each finding
    Report: file:line, smell category, exact diff hunk added, the pre-existing
    file convention the change breaks with (cite surrounding lines as evidence),
    for defensive checks — the caller that already validates the input,
    recommended action (delete / revert-to-main-style / rewrite-to-match-file).

    ### Evidence requirement
    Every finding MUST cite BOTH:
    1. The exact diff hunk from `git diff main...HEAD`
    2. The pre-existing file style or caller contract it violates (grep the
       surrounding file or call sites)

    "Looks AI-generated" is not evidence. Name the convention broken.

    ### Burden of proof (same inversion as other clusters)
    An added line survives only with concrete evidence:

    | Case | Evidence required |
    |---|---|
    | Comment explains a non-obvious WHY | Names a constraint, incident, or invariant not visible in the code |
    | Defensive check at a system boundary | Input is from user/network/untrusted source, not an internal caller |
    | `any` cast at a genuinely untyped boundary | Parsing JSON, reflection, external SDK with no types — not bridging internal types |
    | Style "divergence" is newer preferred style | Named in a style guide or adopted in 2+ other recent files |

    ### Rejected justifications
    | Claim | Why rejected |
    |---|---|
    | "Defensive coding is good practice" | Defensive coding at trusted boundaries is noise. The trust boundary is where checks live. |
    | "Comment makes it clearer" | If the code is unclear without the comment, rename the variable or extract the function |
    | "`any` unblocks the feature" | `any` hides type errors, does not resolve them. The feature is not unblocked, it is fragile |
    | "This is the style I prefer" | File convention beats author preference. Match the file. |

    ### Behavior-preservation escape hatch (CRITICAL)
    Some branch-slop findings *look* like noise but silently guard behavior
    the test suite does not cover. Deleting them regresses production without
    test failure.

    Before marking a finding as KILL, apply this test:
    1. Does the added code handle an input/error/state case? (try/catch, nil
       guard, fallback value, retry, log)
    2. If yes: is there a test that covers that case post-deletion?
       (grep test files for the case description)
    3. If no test covers it: route to **REVIEW** with recommended action
       "write regression test, then delete". DO NOT mark KILL.

    Pure-cosmetic findings (narrating comments, style divergence, `any` cast
    that doesn't change runtime behavior) are exempt from this test — delete
    them freely.

    ### Output
    Findings feed the Kill List with smell category prefix `[BRANCH-SLOP]`
    to distinguish from structural findings. Severity is LOW by default
    (localized, single-line edits) unless the slop touches an integration
    point — then MEDIUM. Findings routed to REVIEW under the behavior-preservation
    escape hatch go to the Review List with prefix `[BRANCH-SLOP-GUARDED]`.

    Public API constraint: {hard_constraint}. Do not propose reverting changes
    that touch the public surface, even if they look AI-generated — the branch
    may legitimately be adding the public contract.

    Diff base: `main`. Use `git diff main...HEAD -- '*.go' '*.ts' '*.tsx' '*.js'`
    to scope to source files; exclude generated code (protobuf, OpenAPI stubs,
    lockfiles).
```

### Dispatch Notes

- **Single message, 6 Task calls.** Parallel execution is non-negotiable —
  sequential would 6x the wall time for the same work. (5 Task calls if the
  branch has no commits ahead of main — skip Task 5.)
- **For very large codebases (>50k files),** dispatch Tasks 1a, 1b, and 2
  once per top-level module instead of once globally. The architecture mapper
  (Task 3) produces the module list; use it to parameterize the per-module
  dispatches in a second round.
- **Use `ring:codebase-explorer`** rather than diff-scoped reviewers
  (`ring:code-reviewer`, `ring:dead-code-reviewer`). Those reviewers expect
  a diff; redirecting them here fights their wiring. Task 5 is the sole
  exception — it is diff-scoped by design (branch vs main) and uses
  `ring:codebase-explorer` configured for diff analysis.
- **Task 5 skip condition:** if the current branch has no commits ahead of
  main (`git rev-list --count main..HEAD` == 0), skip Task 5 and dispatch
  only Tasks 1–4. Document the skip in the final report.

---

## Abstraction Smell Rubric (Canonical)

The authoritative reference for what counts as a simplification target.
Individual explorer prompts reference subsets; this is the union.

| # | Smell | Signal | Default action |
|---|---|---|---|
| 1 | Single-implementation interface | One concrete impl; test doubles identical to prod | DELETE |
| 2 | Translation-free adapter | A→B is rename-only, 1:1 field mapping | DELETE |
| 3 | Pass-through shim | Wraps call site-for-site, no cross-cutting concern | DELETE |
| 4 | Speculative factory/builder | Always constructs the same concrete type | DELETE |
| 5 | One-strategy strategy | Dispatch over enum with one case | COLLAPSE |
| 6 | One-consumer facade | Exists "for future reuse" | COLLAPSE INTO CALLER |
| 7 | Config seam over constant | Indirection for a value that never varies | DELETE |
| 8 | Internal DTO ↔ entity with 1:1 fields | Translation across identical shapes | DELETE |
| 9 | Hexagonal port with one adapter | Ports-and-adapters without the swap | COLLAPSE |
| 10 | Repository over a single SQL backend | No alternate store, no swap pressure | REVIEW |
| 11 | Narrating / inconsistent-density comments (branch diff) | Added lines annotate what the code literally does; surrounding file uses few/no such comments | DELETE |
| 12 | Defensive check in trusted path (branch diff) | try/catch or guard added where caller is already validated | DELETE |
| 13 | `any` / `interface{}` escape hatch (branch diff) | Cast bypasses a type mismatch rather than bridging a genuinely untyped boundary | DELETE |
| 14 | Style inconsistency with file (branch diff) | Naming, formatting, idiom, or error-handling diverges from surrounding file | REWRITE TO MATCH |

Rows 1–10 are structural (whole-codebase, detected by Tasks 1–4). Rows 11–14
are branch-diff (detected by Task 5). Structural smells survive beyond the
current branch; branch-diff smells are exactly what was just introduced.

---

## Burden of Proof: DELETE Is the Default

**Every abstraction starts at DELETE.** It must present a case to survive.

### Accepted cases (abstraction earns the KEEP list)

| Case | Evidence required |
|---|---|
| Second implementation exists TODAY in this repo | File path of the second impl |
| Swappability exercised in tests with divergent behavior | Test file showing both impls with different assertions |
| Cross-process or cross-language boundary | Network/IPC call, serialization format |
| Compiler-inexpressible domain invariant | Named invariant + enforcement point |
| Regulatory or contractual requirement | Requirement doc or external reference |

### Rejected cases (abstraction goes to KILL or REVIEW)

| Case | Why rejected |
|---|---|
| "Clean architecture says so" | Architecture style ≠ evidence of need |
| "Might be reused later" | YAGNI. Reusability lives in git history. |
| "Makes testing easier" without a test that actually differs | Hypothetical testability is not testability |
| "It's the pattern we use here" | Patterns without pressure are cargo cult |
| "Someone might want to swap implementations" | Unexercised swappability is dead weight |

---

## Acceptance Criteria Templates

MANDATORY: The aggregator MUST attach the matching template to every task's
`acceptance_criteria[]` field AND to the Kill List table in the markdown report.
Each template is the minimum bar — the aggregator may append task-specific
criteria, but MUST NOT remove template rows.

| Smell category | Default acceptance criteria |
|---|---|
| `unexercised-seam` | 1. all call sites refactored to use concrete type directly. 2. Interface file deleted. 3. Test files updated to construct the concrete type. 4. Mocks/fakes of the interface removed. 5. No public-API signature change (or explicitly acknowledged if one exists). |
| `speculative-construction` | 1. Factory/Builder/Strategy removed. 2. Call sites construct the concrete type inline or via the simplest possible constructor. 3. Related tests removed or simplified. 4. No dead options/branches left behind. |
| `translation-layer` | 1. Adapter/DTO removed. 2. Producers write the canonical shape directly; consumers read it directly. 3. Tests for translation logic removed. 4. Serialization boundary verified (wire format unchanged). |
| `topology` | 1. Module/package removed or merged. 2. Imports updated across blast-radius. 3. No orphan helpers left. 4. Build graph verified (no circular/dangling deps). |
| `cascade` | 1. Leaf item removed first. 2. Ring-2 callers refactored. 3. Ring-3 transitive dependents refactored. 4. Each ring verified green (tests + build) before advancing. |
| `branch-slop` | 1. Unused helpers/types/files deleted. 2. Branch diff re-minimized against main. 3. No dead imports or references remain. |

**Cascade scope note:** MUST scope each ring's task to its own ring only. Task
for `simplify-cascade-1-ring-1` has acceptance criterion "Leaf item removed";
task for `ring-2` has "Ring-2 callers refactored"; task for `ring-3` has
"Ring-3 transitive dependents refactored". The "each ring verified green"
criterion applies to every cascade task.

---

## Task JSON Schema (ring:dev-cycle Handoff)

MANDATORY: The aggregator MUST emit `tasks_output_path` (default
`docs/dev-simplify/simplify-tasks-{timestamp}.json`) alongside the markdown
report. REQUIRED: Write BOTH the markdown report AND the JSON task file.
FORBIDDEN: emitting one without the other — downstream `ring:dev-cycle`
consumption depends on the JSON; reviewers depend on the markdown.

### Mapping rules

| Report classification | JSON task emission |
|---|---|
| KILL item | One task, `severity: "KILL"`, `rebuttal_if_kept: null` |
| REVIEW item | One task, `severity: "REVIEW"`, `rebuttal_if_kept` populated with the surfaced justification (if any; `null` only when no rationale was surfaced) |
| KEEP item | NO task emitted |
| Cascade chain with N rings | N tasks, one per ring, chained via `depends_on` |

### Schema

```json
{
  "generated_at": "ISO-8601",
  "source_report": "docs/dev-simplify/simplify-report-{timestamp}.md",
  "hard_constraint": "<user-supplied constraint>",
  "tasks": [
    {
      "id": "simplify-001",
      "title": "Remove UserRepository single-impl interface",
      "severity": "KILL | REVIEW",
      "smell_category": "unexercised-seam | speculative-construction | translation-layer | topology | cascade | branch-slop",
      "description": "Short explanation of what and why",
      "files_affected": ["internal/repo/user.go:12", "internal/service/user.go:45"],
      "blast_radius": {"files": 4, "lines": 120},
      "acceptance_criteria": ["...", "..."],
      "estimated_complexity": "trivial | moderate | complex",
      "depends_on": [],
      "rebuttal_if_kept": "Why the item survived (REVIEW items only) or null"
    }
  ]
}
```

### Cascade → task DAG

MANDATORY: Every cascade chain from Task 4 MUST decompose into an ordered
task list with `depends_on` wiring. The refactor order is leaf-first:

- Chain of length N produces N tasks.
- Task IDs follow: `simplify-cascade-{chain-index}-ring-{ring-number}`
  (e.g., `simplify-cascade-1-ring-1`, `simplify-cascade-1-ring-2`,
  `simplify-cascade-1-ring-3`).
- `depends_on` wires ring-N to ring-(N-1). Leaf (ring-1) has `depends_on: []`.
- `smell_category` is `"cascade"` for every ring task.
- `acceptance_criteria` uses the `cascade` template above, scoped per ring
  (see "Cascade scope note" in Acceptance Criteria Templates).

**Example** — chain of 3 rings (leaf → Ring-2 caller → Ring-3 transitive):

```json
[
  {
    "id": "simplify-cascade-1-ring-1",
    "title": "Remove leaf: {leaf_abstraction}",
    "severity": "KILL",
    "smell_category": "cascade",
    "depends_on": [],
    "acceptance_criteria": ["Leaf item removed first", "Tests + build green"]
  },
  {
    "id": "simplify-cascade-1-ring-2",
    "title": "Refactor Ring-2 caller: {caller}",
    "severity": "KILL",
    "smell_category": "cascade",
    "depends_on": ["simplify-cascade-1-ring-1"],
    "acceptance_criteria": ["Ring-2 callers refactored", "Tests + build green"]
  },
  {
    "id": "simplify-cascade-1-ring-3",
    "title": "Refactor Ring-3 transitive dependents: {grandcaller}",
    "severity": "KILL",
    "smell_category": "cascade",
    "depends_on": ["simplify-cascade-1-ring-2"],
    "acceptance_criteria": ["Ring-3 transitive dependents refactored", "Tests + build green"]
  }
]
```

### Aggregator contract

After the 6 (or 5) explorers complete, the orchestrator MUST synthesize
findings into two artifacts. The aggregator's prompt MUST state verbatim:

> Write BOTH the markdown report AND the JSON task file. Do not emit one
> without the other. Map KILL findings to `severity: "KILL"`, REVIEW findings
> to `severity: "REVIEW"` with `rebuttal_if_kept` populated, and KEEP findings
> to NO task. Decompose every cascade chain into ordered per-ring tasks with
> `depends_on` wiring (leaf = ring-1, depends_on: []). Attach the acceptance
> criteria template matching each task's `smell_category`.

---

## Output Schema

One consolidated markdown file at `output_path` (default
`docs/dev-simplify/simplify-report-{timestamp}.md`).

### Required sections

```markdown
## Simplify Summary
- Codebase: [repo name]
- Scope: [whole_codebase | module:{path}]
- Generated: [ISO 8601]
- Total candidates identified: [N]
- Kill list: [N] | Review list: [N] | Keep list: [N]
- Estimated collapse: [total files affected] files / [lines] lines

## Hard Constraint
- Declared constraint: [verbatim from input or default]
- Load-bearing surface located at: [list of files/routes/schemas that define the public contract]
- Touch policy: Nothing in this list is modified. Internal changes that preserve this surface are permitted.

## Kill List
HIGH confidence, no public-API impact, ready for `ring:dev-cycle`.
| Name | file:line | Smell | Rebuttal | Blast radius | Action | Acceptance Criteria |
|---|---|---|---|---|---|---|

## Review List
MEDIUM confidence OR requires caller coordination OR touches a cascade chain.
| Name | file:line | Smell | Why uncertain | Public-API impact | Recommended next step |
|---|---|---|---|---|---|

## Keep List
Earned abstractions. Stop questioning these until evidence changes.
| Name | file:line | Smell category resembled | Evidence that justifies it |
|---|---|---|---|

## Cascade Chains
Chains where killing one abstraction cascades through the codebase.
| Chain ID | Leaf | Ring depth | Terminal type | Collapse blast radius |
|---|---|---|---|---|

## Cascade Execution Plan
Per-chain DAG showing refactor order. Ring-1 (leaf) runs first; each
subsequent ring depends on the previous. MUST match the `depends_on` wiring
in the JSON task file.

### Chain cascade-1
| Ring | Task ID | Target | depends_on |
|---|---|---|---|
| 1 | simplify-cascade-1-ring-1 | [leaf_abstraction] @ file:line | [] |
| 2 | simplify-cascade-1-ring-2 | [caller] @ file:line | [simplify-cascade-1-ring-1] |
| 3 | simplify-cascade-1-ring-3 | [grandcaller] @ file:line | [simplify-cascade-1-ring-2] |

(Repeat per chain.)

## Remaining Risks
Kills the report cannot fully characterize — flagged so execution doesn't
silently inherit them.
| Risk ID | Related finding(s) | Risk type | Why uncertain | Mitigation before execution |
|---|---|---|---|---|

Risk types:
- **Coverage gap**: Kill removes code that lacks test coverage; behavior drift is invisible
- **Cross-module coordination**: Kill requires synchronized changes across >1 module
- **At-boundary adjacency**: Kill sits one hop from the public API surface
- **Cascade fragility**: Cascade chain passes through a hot path or untested branch

## Next Steps
- If executing: feed Kill List into `ring:dev-cycle` as one task per chain,
  ordered by smell type (dead code → duplicates → abstraction collapse)
- Before executing items flagged under "Remaining Risks": apply the listed
  mitigation (add regression test, coordinate with owning team, etc.)
- Re-run this skill after any kill batch to detect newly-exposed cascade chains
- Reassess the Hard Constraint surface before each release
```

---

## Blocker Criteria — STOP and Report

| Decision | Blocker | Required action |
|---|---|---|
| Hard constraint ambiguous | Cannot determine what the public API actually is | STOP, ask user to specify `hard_constraint` input |
| External consumers detected | Codebase imported by another repo you can see | STOP, report scope expansion — this is no longer pre-public |
| Generated code dominates | >70% of codebase is generated (protobuf, GraphQL, OpenAPI) | STOP, report — generated code is not in scope; run skill against source manifests instead |
| Single file, single function | Nothing to simplify | STOP, exit with empty report |
| Explorer dispatch fails | Cannot launch parallel Task calls | STOP, report infrastructure issue |

### Cannot Be Overridden

| Requirement | Why |
|---|---|
| 6 explorer tasks dispatched in parallel (5 if branch has no commits ahead of main) | Sequential dispatch is 6x slower for the same work |
| Hard constraint respected verbatim | Breaking the public API invalidates the entire sweep |
| Evidence required for every finding | "Probably unused" is not evidence |
| KEEP list populated with justification | Without it, re-runs re-flag the same earned abstractions |
| Output schema fully populated | Partial reports degrade to noise |
| Both artifacts emitted (markdown report AND JSON task file) | `ring:dev-cycle` consumes the JSON; reviewers consume the markdown. Missing either breaks handoff. |
| Cascade chains decomposed into per-ring tasks with `depends_on` wiring | Single-task chains erase leaf-first execution order |
| Acceptance criteria template attached to every task by `smell_category` | Without templates, dev-cycle has no completion test |
| `hard_constraint` user-supplied (never auto-inferred) | Auto-inference hides an AI guess as user intent — inverts the burden-of-proof pivot |

User cannot waive these. Time pressure cannot waive these. "Simple codebase" cannot waive these.

---

## Severity Calibration

| Severity | Condition | Placement |
|---|---|---|
| **CRITICAL** | Abstraction violates hard constraint (would break public API if collapsed) | Do not touch — document as "load-bearing, do not collapse" in report |
| **HIGH** | Cascade chain with >5 files collapsible; no public-API impact | KILL LIST |
| **HIGH** | Single-impl interface across architectural boundary with no swap evidence | KILL LIST |
| **MEDIUM** | Translation-free adapter between internal types, caller coordination needed | REVIEW LIST |
| **MEDIUM** | Indirection layer at boundary of public API (at-boundary impact) | REVIEW LIST |
| **LOW** | Single-file shim, <20 lines, localized blast radius | KILL LIST (easy wins batch) |
| **COSMETIC** | Naming-only concerns | Excluded — use `ring:dev-refactor` for naming |

---

## Pressure Resistance

| User says | Your response |
|---|---|
| "Skip the keep list, just give me the kills" | KEEP list is mandatory. Without it, the next run re-flags the same earned abstractions and wastes your time. Producing it. |
| "This adapter is important, don't flag it" | If it's important, it lives in the KEEP list with the evidence. If you can't name the evidence, the importance is imagined. |
| "Just look at core modules" | Then pass `scope=module` with `module_path` explicitly. Ad-hoc narrowing loses cascade visibility. |
| "The constraint should be lighter" | The hard constraint is the ONE contract. Softening it softens the whole sweep. Reject unless a new `hard_constraint` input is supplied. |
| "We'll fix these later" | "Later" is what created this list. Execution is `ring:dev-cycle`'s job; this skill only reports. |
| "Don't be so aggressive" | Burden of proof is inverted by design. The skill's value is in the aggression. Softening it produces `ring:dev-refactor`, which already exists. |

CANNOT weaken the burden-of-proof inversion under any pressure scenario.

---

## Anti-Rationalization Table

| Rationalization | Why it's WRONG | Required action |
|---|---|---|
| "This abstraction is common, must be justified" | Commonness ≠ justification. Many codebases replicate the same unjustified pattern. | **Evaluate against rubric anyway** |
| "The team chose this pattern deliberately" | Deliberate ≠ correct. Verify the pattern is exercised, not just declared. | **Require evidence of swap/test/divergence** |
| "Removing this would be a big refactor" | Blast radius is a data point, not a veto. Big refactors are often the highest-leverage ones pre-public. | **Report the size; let the user decide** |
| "Interface might be implemented externally" | Pre-public — external implementers don't exist yet. This only applies post-public. | **Confirm pre-public state, then flag** |
| "Makes onboarding easier" | Onboarding is easier when there's less to learn, not more indirection to navigate. | **Flag as suspect** |
| "Future-proofing is a valid reason" | Future-proofing is YAGNI rebranded. Real future-proofing tracks concrete anticipated swaps. | **Require anticipated swap to be named** |
| "I found 3 obvious kills, that's enough" | Partial reports lose cascade chains. Scan completely. | **Complete all 6 explorer dispatches** |
| "Branch-diff slop is just style, skip it" | Style inconsistency is where AI generation betrays itself. Skipping Task 5 is skipping the cheapest kills in the sweep. | **Run Task 5 whenever branch has commits ahead of main** |
| "The defensive check is harmless, leave it" | Harmless noise is still noise. Defensive checks at trusted boundaries mislead future readers about where validation happens. | **Delete unless the caller contract actually permits the case being guarded** |
| "We'll clean up the comments in a later pass" | Comment slop compounds — reviewers stop trusting comments, then real comments get ignored too. | **Delete now, while the diff is small** |
| "The codebase looks clean already" | Clean code can still be over-abstracted. Clean over-abstraction is the failure mode this skill targets. | **Run the sweep regardless** |
| "Only emit the markdown report, skip the JSON" | `ring:dev-cycle` consumes the JSON. Markdown alone is a human read, not an executable handoff. | **REQUIRED: Emit both artifacts or neither** |
| "Only emit the JSON, skip the markdown" | Reviewers and the user audit the markdown. JSON alone is opaque to humans. | **REQUIRED: Emit both artifacts or neither** |
| "Skip acceptance criteria, the task title explains it" | Acceptance criteria are the execution contract. Without them, dev-cycle has no completion test. | **Attach template for every task's smell_category** |
| "Cascade chain is obvious, skip the DAG decomposition" | An N-ring chain as a single task erases the leaf-first execution order. dev-cycle needs N ordered tasks. | **Decompose every chain into per-ring tasks with depends_on wiring** |
| "Auto-detect hard_constraint from go.mod / Dockerfile" | Auto-inference hides an AI guess as user intent. The constraint is the burden-of-proof pivot — it must be declared. | **Keep hard_constraint user-supplied; STOP if ambiguous** |

---

## When Dev-Simplify Is Not Needed

| Condition | Why |
|---|---|
| Codebase has external consumers and stable public surface | Public API constraint expands beyond what this skill tracks; hand-audit first |
| Just finished `ring:dev-refactor` run | Let the dev-cycle complete before re-auditing |
| Pure frontend UI codebase | Abstraction smells here follow different rubric — use `ring:dev-refactor-frontend` |
| Prototype / throwaway code | Refactoring throwaway code is waste. Ship or delete it. |
| Single-file script | Nothing to simplify. |

**Still required (do not skip):**

| Condition | Why |
|---|---|
| Pre-public application of any size | Now is the cheapest moment to collapse accumulated scaffolding |
| Post-pivot codebase | Pivots leave the highest density of speculative-flexibility debt |
| Before first external integration | Lock in the internals before clients pin them by depending on them |

---

## Execution Report Format

When the skill completes, emit the following summary alongside the written report:

```markdown
## Dev Simplify Complete

**Scope:** [whole_codebase | module:{path}]
**Hard Constraint:** [declared value]
**Report:** [output_path]
**Tasks:** [tasks_output_path] ([N] tasks)

**Findings**
- Kill list: [N] items, [M] files / [L] lines collapsible
- Review list: [N] items requiring coordination
- Keep list: [N] earned abstractions documented
- Cascade chains detected: [N] → [M] ordered ring-tasks in DAG
- Branch-slop findings: [N] kills / [M] routed to review under behavior-preservation
- Remaining risks flagged: [N] ([K] require regression tests before execution)

**Next Actions**
1. Review the Kill List in [output_path]
2. Feed [tasks_output_path] directly to `ring:dev-cycle` — tasks are pre-ordered
   via `depends_on` (cascade chains refactor leaf-first)
3. Execute with TDD and parallel review
4. Re-run `ring:dev-simplify` after execution to detect newly-exposed cascades

**Status:** COMPLETE
```

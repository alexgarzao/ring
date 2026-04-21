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

output_schema:
  format: markdown
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

Dispatch four explorer agents in **parallel** (single message, 4 Task calls).
Each explorer handles one cluster of abstraction smells. Results are aggregated
into a single consolidated report.

### Task 1 — Interface & Speculative Abstraction Hunter

```yaml
Task:
  subagent_type: "ring:codebase-explorer"
  description: "Hunt single-impl interfaces and speculative abstractions"
  prompt: |
    ## Abstraction Hunt — Cluster 1: Interfaces & Speculation

    Scan this entire codebase (committed + dirty working tree) for abstractions
    in the following smell categories. Default verdict for every finding is
    DELETE — the abstraction must present concrete evidence to survive.

    ### Smells to find
    | Smell | Signal |
    |---|---|
    | Single-implementation interface | Interface type with exactly one concrete impl; test doubles (if any) are identical to prod impl |
    | Speculative factory | Factory function/class that always constructs the same concrete type |
    | Speculative builder | Builder pattern where all callers set the same fields |
    | One-strategy strategy | Strategy pattern dispatching over an enum with one case |
    | One-consumer facade | Facade with a single call site |
    | Hexagonal port with one adapter | Ports-and-adapters scaffolding where no second adapter exists or is planned |
    | Repository over a single SQL backend | Repository pattern with no alternate store, no swap test |

    ### For each finding
    Report: name, file:line, smell category, the abstraction's self-justification
    (if any — read comments/docs), rebuttal given pre-public state, blast radius
    (files/packages affected by collapse), public-API impact (none/indirect/at-boundary),
    recommended action (delete / collapse-into-caller / merge-with-peer).

    ### Evidence requirement
    Every finding MUST include: (a) exact file:line, (b) caller count via grep,
    (c) evidence the swap is hypothetical (no second impl, no swap test,
    no ADR justifying the seam).

    ### Output
    Markdown table per smell category. Plus a "potentially justified" sub-list
    for abstractions with suggestive evidence of real swappability — these feed
    the KEEP list in the final report.

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
    ```
    Chain: [leaf_abstraction] @ file:line
      Ring 2: [caller] @ file:line — serves only the leaf
      Ring 3: [grandcaller] @ file:line — serves only Ring 2
      Terminal: [consumer] — [REAL | SPECULATIVE]
      If SPECULATIVE: collapse blast radius = [N files, M lines]
      If REAL: chain is sustained; flag weakest link for review
    ```

    ### Evidence requirement
    Every Ring assignment MUST include grep-based caller count. "Probably only
    called by X" is not evidence. Count and cite.

    Public API constraint: {hard_constraint}. Handlers/endpoints serving the
    public API are REAL terminals; chains ending there are sustained.
```

### Dispatch Notes

- **Single message, 4 Task calls.** Parallel execution is non-negotiable —
  sequential would 4x the wall time for the same work.
- **For very large codebases (>50k files),** dispatch Task 1 and Task 2 once
  per top-level module instead of once globally. The architecture mapper
  (Task 3) produces the module list; use it to parameterize the per-module
  dispatches in a second round.
- **Use `ring:codebase-explorer`** rather than diff-scoped reviewers
  (`ring:code-reviewer`, `ring:dead-code-reviewer`). Those reviewers expect
  a diff; redirecting them here fights their wiring.

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
| Name | file:line | Smell | Rebuttal | Blast radius | Action |
|---|---|---|---|---|---|

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

## Next Steps
- If executing: feed Kill List into `ring:dev-cycle` as one task per chain
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
| 4 explorer tasks dispatched in parallel | Sequential dispatch is 4x slower for the same work |
| Hard constraint respected verbatim | Breaking the public API invalidates the entire sweep |
| Evidence required for every finding | "Probably unused" is not evidence |
| KEEP list populated with justification | Without it, re-runs re-flag the same earned abstractions |
| Output schema fully populated | Partial reports degrade to noise |

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
| "I found 3 obvious kills, that's enough" | Partial reports lose cascade chains. Scan completely. | **Complete all 4 explorer dispatches** |
| "The codebase looks clean already" | Clean code can still be over-abstracted. Clean over-abstraction is the failure mode this skill targets. | **Run the sweep regardless** |

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

**Findings**
- Kill list: [N] items, [M] files / [L] lines collapsible
- Review list: [N] items requiring coordination
- Keep list: [N] earned abstractions documented
- Cascade chains detected: [N] ([K] collapsible as units)

**Next Actions**
1. Review the Kill List in [output_path]
2. Batch items into cascade-aware tasks (one task per chain)
3. Feed to `ring:dev-cycle` for execution with TDD and parallel review
4. Re-run `ring:dev-simplify` after execution to detect newly-exposed cascades

**Status:** COMPLETE
```

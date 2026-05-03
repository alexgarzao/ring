---
name: ring:explore-codebase
description: |
  Autonomous multi-phase codebase exploration - scopes the target, discovers natural
  perspectives (layers, components, boundaries), dispatches adaptive deep-dive explorers
  based on what was discovered, then synthesizes findings into actionable insights.

trigger: |
  - Need to understand how a feature/system works across the codebase
  - Starting work on unfamiliar codebase or component
  - Planning changes that span multiple layers/components
  - User asks "how does X work?" for non-trivial X
  - Need architecture understanding before implementation

skip_when: |
  - Pure reference lookup (function signature, type definition)
  - Checking if specific file exists (yes/no question)
  - Reading error message from known file location

related:
  similar: [dispatching-parallel-agents, systematic-debugging]
  sequence_after: [ring:brainstorm]
  sequence_before: [ring:write-plan, ring:execute-plan]
---

# Autonomous Multi-Phase Codebase Exploration

Multi-phase approach: **Phase 0 scopes** the target, **Phase 1 discovers** the natural structure of the codebase, **Phase 2 deep-dives** into each discovered area in parallel, **Phase 3 collects** results, and **Phase 4 synthesizes** findings.

**Announce at start:** "Using ring:explore-codebase for multi-phase autonomous exploration."

## How It Works

```
Phase 1: Discovery (3-4 parallel agents)
  → Architecture, Components, Layers, Organization

Phase 2: Deep Dive (N adaptive agents, one per discovered perspective)
  → Target implementation in each area

Phase 3: Synthesis → Actionable guidance with file:line evidence
```

## Phase 0: Scope Definition

Extract from user request: core subject, context/intent, depth needed. Set exploration boundaries (include/exclude directories).

## Phase 1: Discovery Pass

**Dispatch 3-4 discovery agents in a SINGLE message (parallel):**

**Architecture Discovery:** Find pattern (Hexagonal, Layered, Microservices, Monolith, etc.). Evidence: top-level directory structure, layer separation, file paths. Output: pattern name + confidence + ASCII diagram.

**Component Discovery:** Identify all major components/modules. For each: name, location, responsibility, tech stack, size. Map dependencies between components.

**Layer Discovery:** Within each component, identify layers (HTTP/API, Business Logic, Data Access, Infrastructure). Document how layers are separated and how they communicate.

**Organization Discovery:** Find organizing principle (by layer vs by feature vs by domain). Document file naming conventions, test organization, config locations.

**After Phase 1:** Validate quality — all areas have file:line evidence, no major "unknowns" remain. Determine how many deep-dive agents to launch (one per discovered perspective).

<example>
3-component system → 3 deep-dive agents
4-layer monolith → 4 deep-dive agents (one per layer)
6-service microservices → 6 deep-dive agents
</example>

## Phase 2: Deep Dive Pass

**Dispatch N adaptive agents in a SINGLE message (parallel).** One agent per discovered perspective.

Each agent prompt includes:
- Discovered context (architecture, component responsibility, location)
- Specific target to find
- Scope boundaries (directory, depth)

Each agent traces the target through: entry points → execution flow (with file:line) → data transformations → integration points.

## Phase 3: Result Collection

Organize results into Discovery (structure) and Deep Dive (target implementation per area). Cross-reference: do deep dive findings align with Phase 1 structure? Note gaps explicitly.

## Phase 4: Synthesis

Integrate findings into a unified document:

```markdown
# Codebase Exploration: [Target]

## Executive Summary
[Architecture + how target works — 2-3 sentences]

## Phase 1: Discovery Findings
### Architecture Pattern | Component Structure | Layer Organization | Tech Stack | Diagram

## Phase 2: Deep Dive Findings
### [Discovered Area 1]
- Entry point: file:line
- Flow: step-by-step with file:line
- Patterns: [observed]
- Integration: [connections]

### [Discovered Area 2]
[same structure]

## Cross-Cutting Insights
### Pattern Consistency | Variations | Integration Points | Data Flow | Key Decisions

## Implementation Guidance
### Adding new functionality: where, patterns to follow, integration requirements
### Modifying existing: files to change, ripple effects
### Debugging: starting points, data inspection points, common failures
```

## Phase 5: Action Recommendations

Context-aware next steps based on user's goal:
- **Implementation** → suggest ring:write-plan with discovered entry points
- **Debugging** → investigation starting points with file:line
- **Learning** → reading path through key files

## Discovery Agent Templates

### Architecture Agent
```
Goal: Discover architecture pattern.
Examine top-level structure. Identify: Hexagonal/Layered/Microservices/Monolith/MVC/Other.
Provide: pattern name, directory evidence, key paths, confidence level, ASCII diagram.
```

### Component Agent
```
Goal: Identify all major components/modules.
For each component: name, path, responsibility, stack, size.
Map dependencies. Identify shared libraries.
```

### Layer Agent
```
Goal: Discover layers within components.
For each layer: name, location, responsibility, dependencies.
Check for layer violations. Document communication patterns (DI, interfaces, direct).
```

### Organization Agent
```
Goal: Find organizing principle.
Identify: by-layer vs by-feature vs by-domain.
Document: file naming conventions, test co-location, config locations.
```

## Deep Dive Agent Template

```
Goal: Explore [TARGET] in [DISCOVERED_PERSPECTIVE].
Context: architecture=[X], component=[Y], location=[Z], responsibility=[R].
Task:
1. Find [TARGET] — entry points with file:line
2. Trace execution flow — each step with file:line
3. Document patterns — error handling, validation, testing
4. Identify integration points — inbound/outbound with file:line
Scope: Stay within [directory]. Maximum depth: [based on layer].
Output: entry points, execution flow, patterns, integration points, key files.
```

## Verification Checklist

**Phase 1 complete:**
- [ ] Architecture pattern identified with evidence
- [ ] All major components enumerated
- [ ] Layers/boundaries documented
- [ ] File:line references for structural elements

**Phase 2 complete:**
- [ ] All discovered perspectives explored
- [ ] Target found and documented per area
- [ ] Execution flows traced with file:line
- [ ] Integration points identified

**Synthesis quality:**
- [ ] Discovery and deep dive integrated
- [ ] Cross-cutting insights identified
- [ ] Implementation guidance is specific and actionable

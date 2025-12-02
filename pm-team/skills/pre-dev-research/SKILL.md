---
name: pre-dev-research
description: |
  Gate 0 research phase for pre-dev workflow. Dispatches 3 parallel research agents
  to gather codebase patterns, external best practices, and framework documentation
  BEFORE creating PRD/TRD. Outputs research.md with file:line references.

trigger: |
  - Before any pre-dev workflow (Gate 0)
  - When planning new features or modifications
  - Invoked by /ring-pm-team:pre-dev-full and /ring-pm-team:pre-dev-feature

skip_when: |
  - Trivial changes that don't need planning
  - Research already completed (research.md exists and is recent)

sequence:
  before: [pre-dev-prd-creation, pre-dev-feature-map]

related:
  complementary: [pre-dev-prd-creation, pre-dev-trd-creation]

research_modes:
  greenfield:
    description: "New feature with no existing patterns to follow"
    primary_agents: [best-practices-researcher, framework-docs-researcher]
    secondary_agents: [repo-research-analyst]
    focus: "External best practices and framework patterns"

  modification:
    description: "Changing or extending existing functionality"
    primary_agents: [repo-research-analyst]
    secondary_agents: [best-practices-researcher, framework-docs-researcher]
    focus: "Existing codebase patterns and conventions"

  integration:
    description: "Connecting systems or adding external dependencies"
    primary_agents: [framework-docs-researcher, best-practices-researcher, repo-research-analyst]
    secondary_agents: []
    focus: "API documentation and integration patterns"
---

# Pre-Dev Research Skill (Gate 0)

**Purpose:** Gather comprehensive research BEFORE writing planning documents, ensuring PRDs and TRDs are grounded in codebase reality and industry best practices.

## The Research-First Principle

```
Traditional:  Request → PRD → Discover problems during implementation
Research-First:  Request → Research → Informed PRD → Smoother implementation

Research prevents:
- Reinventing patterns that already exist
- Ignoring project conventions
- Missing framework constraints
- Repeating solved problems
```

---

## Step 1: Determine Research Mode

**BLOCKING GATE:** Before dispatching agents, determine the research mode.

Ask the user or infer from context:

| Mode | When to Use | Example |
|------|-------------|---------|
| **greenfield** | No existing patterns to follow | "Add GraphQL API" (when project has none) |
| **modification** | Extending existing functionality | "Add pagination to user list API" |
| **integration** | Connecting external systems | "Integrate Stripe payments" |

**If unclear, ask:**
```
Before starting research, I need to understand the context:

1. **Greenfield** - This is a completely new capability with no existing patterns
2. **Modification** - This extends or changes existing functionality
3. **Integration** - This connects with external systems/APIs

Which mode best describes this feature?
```

**Mode affects agent priority:**
- Greenfield → Web research is primary (best-practices, framework-docs)
- Modification → Codebase research is primary (repo-research)
- Integration → All agents equally weighted

---

## Step 2: Dispatch Research Agents

**Run 3 agents in PARALLEL** (single message, 3 Task calls):

```markdown
## Dispatching Research Agents

Research mode: [greenfield|modification|integration]
Feature: [feature description]

Launching parallel research:
1. ring-pm-team:repo-research-analyst
2. ring-pm-team:best-practices-researcher
3. ring-pm-team:framework-docs-researcher
```

**Agent Prompts:**

### ring-pm-team:repo-research-analyst
```
Research the codebase for patterns relevant to: [feature description]

Research mode: [mode]
- If modification: This is your PRIMARY focus - find all existing patterns
- If greenfield: Focus on conventions and project structure
- If integration: Look for existing integration patterns

Search docs/solutions/ knowledge base for prior related solutions.
Return findings with exact file:line references.
```

### ring-pm-team:best-practices-researcher
```
Research external best practices for: [feature description]

Research mode: [mode]
- If greenfield: This is your PRIMARY focus - go deep on industry standards
- If modification: Focus on specific patterns for this feature type
- If integration: Emphasize API design and integration patterns

Use Context7 for framework documentation.
Use WebSearch for industry best practices.
Return findings with URLs.
```

### ring-pm-team:framework-docs-researcher
```
Analyze tech stack and fetch documentation for: [feature description]

Research mode: [mode]
- If greenfield: Focus on framework setup and project structure patterns
- If modification: Focus on specific APIs being used/modified
- If integration: Focus on SDK/API documentation for external services

Detect versions from manifest files.
Use Context7 as primary documentation source.
Return version constraints and official patterns.
```

---

## Step 3: Aggregate Research Findings

After all agents return, create unified research document:

**File:** `docs/pre-dev/{feature-name}/research.md`

```markdown
---
date: [YYYY-MM-DD]
feature: [feature name]
research_mode: [greenfield|modification|integration]
agents_dispatched:
  - ring-pm-team:repo-research-analyst
  - ring-pm-team:best-practices-researcher
  - ring-pm-team:framework-docs-researcher
---

# Research: [Feature Name]

## Executive Summary

[2-3 sentences synthesizing key findings across all agents]

## Research Mode: [Mode]

[Why this mode was selected and what it means for the research focus]

---

## Codebase Research (ring-pm-team:repo-research-analyst)

[Paste agent output here]

---

## Best Practices Research (ring-pm-team:best-practices-researcher)

[Paste agent output here]

---

## Framework Documentation (ring-pm-team:framework-docs-researcher)

[Paste agent output here]

---

## Synthesis & Recommendations

### Key Patterns to Follow
1. [Pattern from codebase] - `file:line`
2. [Best practice] - [URL]
3. [Framework pattern] - [doc reference]

### Constraints Identified
1. [Version constraint]
2. [Convention requirement]
3. [Integration limitation]

### Prior Solutions to Reference
1. `docs/solutions/[category]/[file].md` - [relevance]

### Open Questions for PRD
1. [Question that research couldn't answer]
2. [Decision that needs stakeholder input]
```

---

## Step 4: Gate 0 Validation

**BLOCKING CHECKLIST** - All must pass before proceeding to Gate 1:

```
Gate 0 Research Validation:
□ Research mode determined and documented
□ All 3 agents dispatched and returned
□ research.md created in docs/pre-dev/{feature}/
□ At least one file:line reference (if modification mode)
□ At least one external URL (if greenfield mode)
□ docs/solutions/ knowledge base searched
□ Tech stack versions documented
□ Synthesis section completed with recommendations
```

**If validation fails:**
- Missing agent output → Re-run that specific agent
- No codebase patterns found (modification mode) → Escalate, may need mode change
- No external docs found (greenfield mode) → Try different search terms

---

## Integration with Pre-Dev Workflow

### In pre-dev-full (9-gate workflow):
```
Gate 0: Research Phase (NEW - this skill)
Gate 1: PRD Creation (reads research.md)
Gate 2: Feature Map
Gate 3: TRD Creation (reads research.md)
...remaining gates
```

### In pre-dev-feature (4-gate workflow):
```
Gate 0: Research Phase (NEW - this skill)
Gate 1: PRD Creation (reads research.md)
Gate 2: TRD Creation
Gate 3: Task Breakdown
```

---

## Research Document Usage

**In Gate 1 (PRD Creation):**
```markdown
Before writing the PRD, load:
- docs/pre-dev/{feature}/research.md

Required in PRD:
- Reference existing patterns with file:line notation
- Cite knowledge base findings from docs/solutions/
- Include external URLs for best practices
- Note framework constraints that affect requirements
```

**In Gate 3 (TRD Creation):**
```markdown
The TRD must reference:
- Implementation patterns from research.md
- Version constraints from framework analysis
- Similar implementations from codebase research
```

---

## Quick Reference

| Research Mode | Primary Agent(s) | Secondary Agent(s) |
|---------------|-----------------|-------------------|
| greenfield | best-practices, framework-docs | repo-research |
| modification | repo-research | best-practices, framework-docs |
| integration | all equally weighted | none |

| Validation Check | Required For |
|-----------------|--------------|
| file:line reference | modification, integration |
| external URL | greenfield, integration |
| docs/solutions/ searched | all modes |
| version documented | all modes |

---

## Anti-Patterns

1. **Skipping research for "simple" features**
   - Even simple features benefit from convention checks
   - "Simple" often becomes complex during implementation

2. **Not using research mode appropriately**
   - Greenfield with heavy codebase research wastes time
   - Modification without codebase research misses patterns

3. **Ignoring docs/solutions/ knowledge base**
   - Prior solutions are gold - always search first
   - Prevents repeating mistakes

4. **Vague references without file:line**
   - "There's a pattern somewhere" is not useful
   - Exact locations enable quick reference during implementation
